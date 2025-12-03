<script setup>
import { ref, onMounted } from "vue";
import { collection, getDocs, query, orderBy } from "firebase/firestore";
import { db } from "../firebase";

// états
const tickets = ref([]);
const loading = ref(true);
const error = ref(null);

// helper format prix
function formatPrice(amount, currency) {
  // affiche comme "24.00 CHF"
  const fixed = Number(amount).toFixed(2);
  return currency ? `${fixed} ${currency}` : `${fixed}`;
}

onMounted(async () => {
  loading.value = true;
  error.value = null;

  // Timeout de secours pour éviter "Chargement..." infini
  const TIMEOUT_MS = 10000;
  const timeoutId = setTimeout(() => {
    if (loading.value) {
      console.error("Timeout: lecture tickets trop longue");
      loading.value = false;
      error.value =
        "Timeout: impossible de charger les tickets. Vérifie la connexion Firebase et la console du navigateur.";
    }
  }, TIMEOUT_MS);

  try {
    if (!db) {
      throw new Error("Firestore (db) non initialisé — vérifie frontend/src/firebase.js et .env.local");
    }

    console.debug("Requête Firestore tickets (orderBy createdAt desc)...");
    const q = query(collection(db, "tickets"), orderBy("createdAt", "desc"));
    const snap = await getDocs(q);

    // transformer en objets JS simples
    tickets.value = snap.docs.map((doc) => {
      const data = doc.data();

      // createdAt peut être un Timestamp Firestore, une ISO string, ou autre.
      let createdAtRaw = data.createdAt;
      try {
        // si c'est un objet avec toDate (Firestore Timestamp), convertir en ISO string pour affichage brut lisible
        if (createdAtRaw && typeof createdAtRaw.toDate === "function") {
          createdAtRaw = createdAtRaw.toDate().toISOString();
        } else if (typeof createdAtRaw === "object" && createdAtRaw !== null) {
          // si c'est un objet quelconque, stringify minimal
          createdAtRaw = JSON.stringify(createdAtRaw);
        }
      } catch (e) {
        // leave as-is si erreur
      }

      return {
        id: doc.id,
        eventName: data.eventName ?? null,
        sessionDate: data.sessionDate ?? null,
        sessionTime: data.sessionTime ?? null,
        ticketNumber: data.ticketNumber ?? null,
        priceAmount: typeof data.priceAmount === "number" ? data.priceAmount : (data.priceAmount ? Number(data.priceAmount) : undefined),
        priceCurrency: data.priceCurrency ?? null,
        createdAtRaw,
        // conserver payload si utile plus tard
        // raw: data.rawPayload ?? null,
      };
    });

    console.debug(`Tickets chargés: ${tickets.value.length}`);
  } catch (err) {
    console.error("Erreur lecture tickets:", err);
    error.value = err?.message || String(err);
  } finally {
    clearTimeout(timeoutId);
    loading.value = false;
  }
});
</script>

<template>
  <main class="p-4">
    <h1 class="text-2xl font-bold mb-4">Tickets</h1>

    <router-link to="/" class="underline text-blue-600 mb-4 inline-block">
      Retour à l’accueil
    </router-link>

    <div v-if="loading" class="mt-4">Chargement des tickets…</div>

    <div v-else-if="error" class="mt-4 text-red-600">
      Erreur : {{ error }}
    </div>

    <table v-else class="mt-4 border-collapse w-full">
      <thead>
        <tr>
          <th class="border px-2 py-1 text-left">Event</th>
          <th class="border px-2 py-1 text-left">Date</th>
          <th class="border px-2 py-1 text-left">Heure</th>
          <th class="border px-2 py-1 text-left">Ticket #</th>
          <th class="border px-2 py-1 text-left">Prix</th>
          <th class="border px-2 py-1 text-left">Créé le</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tickets" :key="t.id">
          <td class="border px-2 py-1">{{ t.eventName ?? "—" }}</td>
          <td class="border px-2 py-1">{{ t.sessionDate ?? "—" }}</td>
          <td class="border px-2 py-1">{{ t.sessionTime ?? "—" }}</td>
          <td class="border px-2 py-1">{{ t.ticketNumber ?? "—" }}</td>
          <td class="border px-2 py-1">
            <span v-if="typeof t.priceAmount === 'number'">
              {{ formatPrice(t.priceAmount, t.priceCurrency) }}
            </span>
            <span v-else>—</span>
          </td>
          <td class="border px-2 py-1">
            <span v-if="t.createdAtRaw !== undefined">{{ t.createdAtRaw }}</span>
            <span v-else>—</span>
          </td>
        </tr>
        <tr v-if="tickets.length === 0 && !loading">
          <td class="border px-2 py-1" colspan="6">Aucun ticket trouvé.</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
/* Pas de CSS compliqué — utilitaires légers déjà fournis inline */
</style>
