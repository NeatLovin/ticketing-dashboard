<template>
  <main class="page">
    <div class="page-header">
      <h1 class="page-title">Agenda</h1>
      <p class="page-subtitle">Sessions du mois (événements agrégés).</p>
    </div>

    <div v-if="loading" class="panel p-6">
      <div class="space-y-3">
        <SkeletonBlock class-name="h-6 w-48" />
        <SkeletonBlock class-name="h-4 w-80 max-w-full" />
        <div class="grid grid-cols-7 gap-2 mt-4">
          <SkeletonBlock v-for="i in 28" :key="i" class-name="h-20 w-full" />
        </div>
      </div>
    </div>

    <div v-else-if="error" class="panel p-6">
      <div class="text-sm text-red-600 font-semibold">Erreur</div>
      <div class="mt-2 text-sm text-zinc-600 break-words">{{ error }}</div>
    </div>

    <div v-else class="space-y-4">
      <div class="panel p-4 flex items-center justify-between">
        <div>
          <div class="text-sm font-semibold text-zinc-900">{{ monthLabel }}</div>
          <div class="text-xs text-zinc-500">{{ periodLabel }}</div>
        </div>

        <div class="flex items-center gap-2">
          <button type="button" class="btn" @click="goPrevMonth">←</button>

          <label class="sr-only" for="agenda-month">Mois</label>
          <input
            id="agenda-month"
            type="month"
            class="input w-[160px]"
            :value="selectedMonthInput"
            @change="onMonthInputChange"
          />

          <button type="button" class="btn" @click="goNextMonth">→</button>
        </div>
      </div>

      <div v-if="calendarItems.length === 0" class="panel p-4">
        <div class="text-sm text-zinc-700 font-semibold">Aucune session sur la période</div>
        <div class="mt-1 text-sm text-zinc-500">Le calendrier reste affiché (mois navigable).</div>
      </div>

      <div class="grid grid-cols-7 gap-2">
        <div
          v-for="(cell, idx) in monthGrid"
          :key="idx"
          class="panel p-2 min-h-[120px]"
        >
          <div v-if="!cell" class="h-full" />
          <div v-else>
            <div class="flex items-baseline justify-between">
              <div class="text-xs font-semibold text-zinc-700">{{ cell.day }}</div>
              <div class="text-[10px] text-zinc-400">{{ cell.weekdayShort }}</div>
            </div>

            <div class="mt-2 space-y-1">
              <button
                v-for="item in itemsByDate[cell.dateKey] || []"
                :key="item.key"
                type="button"
                class="w-full text-left rounded-md border border-zinc-200 bg-white px-2 py-1 hover:bg-zinc-50"
                @click="goToEvent(item.eventId)"
              >
                <div class="text-[11px] font-semibold text-zinc-900 truncate" :title="item.eventName">
                  {{ item.eventName || 'Événement' }}
                </div>
                <div class="text-[11px] text-zinc-600">
                  <span v-if="item.time" class="font-semibold">{{ formatTime(item.time) }}</span>
                  <span v-if="item.time && item.locationName" class="text-zinc-400"> · </span>
                  <span v-if="item.locationName" class="truncate">{{ item.locationName }}</span>
                </div>
                <div class="text-[10px] text-zinc-500">
                  <span class="font-semibold">{{ item.ticketsCount }}</span> billet(s)
                  <span v-if="item.amountLabel" class="text-zinc-400"> · </span>
                  <span v-if="item.amountLabel" class="font-semibold text-green-700">{{ item.amountLabel }}</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { collection, getDocs } from "firebase/firestore";
import { db } from "../firebase";
import SkeletonBlock from "../components/SkeletonBlock.vue";

const router = useRouter();

const loading = ref(true);
const error = ref(null);

const today = new Date();
const selectedMonth = ref(new Date(today.getFullYear(), today.getMonth(), 1));

const monthStart = computed(() => new Date(selectedMonth.value.getFullYear(), selectedMonth.value.getMonth(), 1));
const monthEnd = computed(() => new Date(selectedMonth.value.getFullYear(), selectedMonth.value.getMonth() + 1, 0));

function pad2(n) {
  return String(n).padStart(2, "0");
}

function dateKeyFromDate(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function normalizeDateKey(dateStr) {
  if (typeof dateStr !== "string") return null;
  // attend en entrée un format type YYYY-M-D ou YYYY-MM-DD
  const m = dateStr.trim().match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (!m) return null;
  const year = Number(m[1]);
  const month = Number(m[2]);
  const day = Number(m[3]);
  if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) return null;
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  return `${year}-${pad2(month)}-${pad2(day)}`;
}

function formatTime(hms) {
  // attend "HH:MM:SS" (payload Petzi)
  if (typeof hms !== "string") return "";
  const parts = hms.split(":");
  if (parts.length < 2) return hms;
  return `${parts[0]}:${parts[1]}`;
}

function formatMoneyAny(revenue) {
  // Supporte:
  // - map: { CHF: 10 }
  // - array: [ { currency: 'CHF', amount: 10 } ]
  if (!revenue) return "";

  let currency = null;
  let amount = null;

  if (Array.isArray(revenue)) {
    const first = revenue.find((x) => x && typeof x === "object" && typeof x.currency === "string" && typeof x.amount === "number" && Number.isFinite(x.amount) && x.amount !== 0);
    if (!first) return "";
    currency = first.currency;
    amount = first.amount;
  } else if (typeof revenue === "object") {
    const entries = Object.entries(revenue)
      .filter(([, v]) => typeof v === "number" && Number.isFinite(v) && v !== 0);
    if (!entries.length) return "";
    [currency, amount] = entries[0];
  } else {
    return "";
  }

  try {
    return new Intl.NumberFormat("fr-CH", { style: "currency", currency }).format(amount);
  } catch {
    return `${amount} ${currency}`;
  }
}

const monthLabel = computed(() => {
  return new Intl.DateTimeFormat("fr-CH", { month: "long", year: "numeric" }).format(monthStart.value);
});

const periodLabel = computed(() => {
  const start = new Intl.DateTimeFormat("fr-CH", { day: "2-digit", month: "2-digit", year: "numeric" }).format(monthStart.value);
  const end = new Intl.DateTimeFormat("fr-CH", { day: "2-digit", month: "2-digit", year: "numeric" }).format(monthEnd.value);
  return `${start} → ${end}`;
});

const selectedMonthInput = computed(() => {
  const d = selectedMonth.value;
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}`;
});

const monthGrid = computed(() => {
  const start = monthStart.value;
  const end = monthEnd.value;

  const startDow = (start.getDay() + 6) % 7; // lundi=0
  const daysInMonth = end.getDate();

  const cells = [];
  for (let i = 0; i < startDow; i += 1) cells.push(null);

  for (let day = 1; day <= daysInMonth; day += 1) {
    const d = new Date(start.getFullYear(), start.getMonth(), day);
    const weekdayShort = new Intl.DateTimeFormat("fr-CH", { weekday: "short" }).format(d);
    cells.push({
      day,
      weekdayShort,
      dateKey: dateKeyFromDate(d),
    });
  }

  // Remplir pour avoir une grille complète
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
});

const allSessionItems = ref([]);

const itemsByDate = computed(() => {
  const startKey = dateKeyFromDate(monthStart.value);
  const endKey = dateKeyFromDate(monthEnd.value);

  const grouped = {};
  const items = Array.isArray(allSessionItems.value) ? allSessionItems.value : [];

  items.forEach((item) => {
    const date = item?.date;
    if (typeof date !== "string") return;
    if (date < startKey || date > endKey) return;
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(item);
  });

  Object.keys(grouped).forEach((date) => {
    grouped[date].sort((a, b) => {
      const ta = typeof a.time === "string" ? a.time : "";
      const tb = typeof b.time === "string" ? b.time : "";
      return ta.localeCompare(tb);
    });
  });

  return grouped;
});

const calendarItems = computed(() => Object.values(itemsByDate.value).flat());

function goToEvent(eventId) {
  if (!eventId) return;
  router.push({ path: `/events/${encodeURIComponent(String(eventId))}` });
}

function normalizeSessionsMap(sessions) {
  if (!sessions || typeof sessions !== "object") return [];
  return Object.entries(sessions)
    .map(([key, value]) => ({ key, value }))
    .filter((x) => x.value && typeof x.value === "object");
}

function extractSessionsFromEventDoc(data) {
  // Nouveau format (v2): data.sessions = [ { date, time, locationName, ticketsCount, revenueByCurrency: [{currency,amount}] } ]
  if (data && Array.isArray(data.sessions)) {
    return data.sessions
      .map((value, idx) => ({ key: `idx-${idx}`, value }))
      .filter((x) => x.value && typeof x.value === "object");
  }

  // Format (v1): data.sessions = { [sessionKey]: { date, time, locationName, ticketsCount, revenue: { CHF: 10 } } }
  if (data && typeof data.sessions === "object" && data.sessions !== null && !Array.isArray(data.sessions)) {
    return normalizeSessionsMap(data.sessions);
  }

  // Compat (ancien): champs à plat style "sessions.<sessionKey>.date" au niveau racine du doc.
  const sessions = {};
  if (!data || typeof data !== "object") return [];

  Object.entries(data).forEach(([k, v]) => {
    if (typeof k !== "string" || !k.startsWith("sessions.")) return;

    const rest = k.slice("sessions.".length);
    const parts = rest.split(".");
    if (parts.length < 2) return;

    const sessionKey = parts[0];
    const field = parts[1];

    if (!sessions[sessionKey]) sessions[sessionKey] = {};

    if (field === "revenue" && parts.length >= 3) {
      const currency = parts[2];
      if (!sessions[sessionKey].revenue) sessions[sessionKey].revenue = {};
      sessions[sessionKey].revenue[currency] = v;
      return;
    }

    sessions[sessionKey][field] = v;
  });

  return Object.entries(sessions)
    .map(([key, value]) => ({ key, value }))
    .filter((x) => x.value && typeof x.value === "object");
}

async function loadAgenda() {
  loading.value = true;
  error.value = null;

  try {
    if (!db) throw new Error("Firebase non initialisé (db indisponible).");

    const snap = await getDocs(collection(db, "events"));
    const items = [];

    snap.forEach((docSnap) => {
      const data = docSnap.data() || {};
      const eventId = data.eventId ?? docSnap.id;
      const eventName = data.eventName ?? null;
      const sessions = extractSessionsFromEventDoc(data);

      sessions.forEach(({ key, value }) => {
        const rawDate = value.date ?? null;
        const date = normalizeDateKey(rawDate);
        if (!date) return;

        const item = {
          key: `${docSnap.id}::${key}`,
          eventId,
          eventName,
          date,
          time: value.time ?? null,
          locationName: value.locationName ?? null,
          ticketsCount: typeof value.ticketsCount === "number" ? value.ticketsCount : 0,
          amountLabel: formatMoneyAny(value.revenueByCurrency || value.revenue),
        };

        items.push(item);
      });
    });

    allSessionItems.value = items;
  } catch (e) {
    console.error(e);
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

function goPrevMonth() {
  const d = selectedMonth.value;
  selectedMonth.value = new Date(d.getFullYear(), d.getMonth() - 1, 1);
}

function goNextMonth() {
  const d = selectedMonth.value;
  selectedMonth.value = new Date(d.getFullYear(), d.getMonth() + 1, 1);
}

function onMonthInputChange(e) {
  const value = e?.target?.value;
  if (typeof value !== "string" || !value) return;
  // value: YYYY-MM
  const [y, m] = value.split("-").map((x) => Number(x));
  if (!Number.isFinite(y) || !Number.isFinite(m) || m < 1 || m > 12) return;
  selectedMonth.value = new Date(y, m - 1, 1);
}

onMounted(() => {
  loadAgenda();
});
</script>
