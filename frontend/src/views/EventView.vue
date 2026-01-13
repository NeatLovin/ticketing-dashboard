<template>
  <main class="page">
    <div class="page-header">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-zinc-200 hover:text-white hover:bg-white/10 transition"
          @click="goBackToAgenda"
        >
          <span aria-hidden="true">←</span>
          <span>Retour à l'agenda</span>
        </button>

        <div v-if="eventNameDisplay" class="text-sm text-zinc-300 truncate max-w-[min(60ch,70vw)]" :title="eventNameDisplay">
          {{ eventNameDisplay }}
        </div>
      </div>

      <h1 class="page-title">{{ eventNameDisplay || "Événement" }}</h1>
      <p class="page-subtitle">Tickets pour l'événement {{ eventIdLabel }}</p>
    </div>

    <div v-if="loading" class="panel p-6">
      <div class="space-y-3">
        <SkeletonBlock class-name="h-6 w-64 max-w-full" />
        <SkeletonBlock class-name="h-4 w-80 max-w-full" />
        <div class="space-y-2 mt-4">
          <SkeletonBlock v-for="i in 8" :key="i" class-name="h-10 w-full" />
        </div>
      </div>
    </div>

    <div v-else-if="error" class="panel p-6">
      <div class="text-sm text-red-600 font-semibold">Erreur</div>
      <div class="mt-2 text-sm text-zinc-600 break-words">{{ error }}</div>
      <div class="mt-4 flex items-center gap-2">
        <button type="button" class="btn" @click="goBackToAgenda">Retour à l'agenda</button>
      </div>
    </div>

    <div v-else-if="tickets.length === 0" class="panel p-6">
      <div class="text-sm text-zinc-700 font-semibold">Aucun ticket</div>
      <div class="mt-1 text-sm text-zinc-500">Pas de vente trouvée pour cet événement.</div>
      <div class="mt-4 flex flex-wrap items-center gap-2">
        <button type="button" class="btn" @click="goBackToAgenda">Retour à l'agenda</button>
        <button type="button" class="btn" @click="goToTickets">Ouvrir Tickets</button>
      </div>
    </div>

    <div v-else class="panel overflow-hidden">
      <div class="p-4 border-b border-zinc-100 flex items-center justify-between">
        <div class="text-sm font-semibold text-zinc-900">{{ tickets.length }} ticket(s)</div>
        <button type="button" class="btn" @click="goToTickets">Voir dans Tickets</button>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Acheteur</th>
              <th>Date</th>
              <th>Session</th>
              <th class="text-right">Montant</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tickets" :key="t.id">
              <td>
                <div class="font-medium text-zinc-900">
                  {{ buyerLabel(t) }}
                </div>
                <div class="text-xs text-zinc-500 truncate" :title="t.ticketNumber">{{ t.ticketNumber }}</div>
              </td>
              <td class="text-xs text-zinc-500">{{ formatCreatedAt(t.createdAt) }}</td>
              <td>
                <div class="font-medium text-zinc-900">{{ t.sessionDate || '—' }} <span v-if="t.sessionTime" class="text-zinc-400">·</span> {{ formatTime(t.sessionTime) }}</div>
                <div class="text-xs text-zinc-500 truncate" :title="t.venueName">{{ t.venueName || '' }}</div>
              </td>
              <td class="text-right font-semibold text-green-700">{{ formatCurrency(t.priceAmount, t.priceCurrency) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { doc as fsDoc, getDoc } from "firebase/firestore";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import { TicketsService } from "../services/ticketsService";
import { db } from "../firebase";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const error = ref(null);
const tickets = ref([]);
const eventNameFromEvents = ref(null);

let unsubscribe = null;

const eventId = computed(() => route.params.eventId);
const eventIdLabel = computed(() => (eventId.value ? String(eventId.value) : "—"));

const eventNameDisplay = computed(() => {
  const fromEvents = typeof eventNameFromEvents.value === "string" ? eventNameFromEvents.value.trim() : "";
  if (fromEvents) return fromEvents;
  const sample = tickets.value[0];
  const fromTicket = typeof sample?.eventName === "string" ? sample.eventName.trim() : "";
  return fromTicket || "";
});

function formatTime(hms) {
  if (typeof hms !== "string") return "";
  const parts = hms.split(":");
  if (parts.length < 2) return hms;
  return `${parts[0]}:${parts[1]}`;
}

function formatCreatedAt(value) {
  const d = TicketsService.toDate(value);
  if (!d) return "";
  return new Intl.DateTimeFormat("fr-CH", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

function formatCurrency(value, currency) {
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return "—";
  const cur = typeof currency === "string" && currency ? currency : "CHF";
  try {
    return new Intl.NumberFormat("fr-CH", { style: "currency", currency: cur }).format(num);
  } catch {
    return `${num} ${cur}`;
  }
}

function buyerLabel(t) {
  const name = `${t?.buyerFirstName || ""} ${t?.buyerLastName || ""}`.trim();
  return name || "Acheteur";
}

function goToTickets() {
  const sample = tickets.value[0];
  const eventName = sample?.eventName || eventNameFromEvents.value;
  if (eventName) {
    router.push({ path: "/tickets", query: { eventName } });
  } else {
    router.push({ path: "/tickets" });
  }
}

function goBackToAgenda() {
  // Retour simple et prévisible (évite un back() qui peut repartir ailleurs)
  router.push({ path: "/agenda" });
}

async function loadEventNameFromEvents(eventIdValue) {
  try {
    if (!db) return;
    const ref = fsDoc(db, "events", String(eventIdValue));
    const snap = await getDoc(ref);
    if (!snap.exists()) return;
    const data = snap.data() || {};
    if (typeof data.eventName === "string" && data.eventName.trim()) {
      eventNameFromEvents.value = data.eventName;
    }
  } catch (e) {
    // non bloquant
    console.error("EventView: cannot load eventName from events", e);
  }
}

onMounted(() => {
  loading.value = true;
  error.value = null;

  try {
    const id = eventId.value;
    if (!id) throw new Error("eventId manquant dans l'URL");

    // Firestore est typé: si `tickets.eventId` est stocké en number,
    // une requête avec une string ne retournera rien.
    const numericId = Number(String(id));
    const queryId = Number.isFinite(numericId) ? numericId : String(id);

    // Permet au bouton "Voir dans Tickets" de fonctionner même si aucun ticket n'est encore chargé.
    loadEventNameFromEvents(id);

    unsubscribe = TicketsService.subscribeToEventTickets(queryId, (rows, err) => {
      if (err) {
        error.value = err?.message || String(err);
        loading.value = false;
        tickets.value = [];
        return;
      }

      tickets.value = Array.isArray(rows) ? rows : [];

      // Fallback (si le nom n'est pas encore récupéré depuis `events`).
      if (!eventNameFromEvents.value && tickets.value.length > 0) {
        const name = tickets.value[0]?.eventName;
        if (typeof name === "string" && name.trim()) {
          eventNameFromEvents.value = name;
        }
      }

      loading.value = false;
    });
  } catch (e) {
    console.error(e);
    error.value = e?.message || String(e);
    loading.value = false;
  }
});

onUnmounted(() => {
  if (unsubscribe) unsubscribe();
});
</script>
