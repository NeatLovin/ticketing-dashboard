<script setup>
import { ref, onMounted } from "vue";
import { collection, getDocs, query, orderBy } from "firebase/firestore";
import { db } from "../firebase";

const tickets = ref([]);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const colRef = collection(db, "tickets");
    const q = query(colRef, orderBy("createdAt", "desc"));
    const snap = await getDocs(q);

    tickets.value = snap.docs.map((doc) => {
      const data = doc.data();
      return {
        id: doc.id,
        eventName: data.eventName ?? null,
        sessionDate: data.sessionDate ?? null,
        sessionTime: data.sessionTime ?? null,
        ticketNumber: data.ticketNumber ?? null,
        priceAmount: data.priceAmount ?? null,
        priceCurrency: data.priceCurrency ?? null,
        createdAt: data.createdAt ?? null,
      };
    });
  } catch (e) {
    console.error(e);
    error.value = "Erreur lors du chargement des tickets.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <main class="p-6">
    <h1 class="text-2xl font-bold mb-4">Tickets</h1>

    <router-link to="/" class="underline text-blue-600 mb-4 inline-block">
      ⟵ Retour à l’accueil
    </router-link>

    <p v-if="loading">Chargement des tickets...</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>

    <table v-else class="min-w-full border border-gray-300 text-sm">
      <thead class="bg-gray-100">
        <tr>
          <th class="border px-2 py-1 text-left">Event</th>
          <th class="border px-2 py-1 text-left">Date</th>
          <th class="border px-2 py-1 text-left">Heure</th>
          <th class="border px-2 py-1 text-left">Ticket #</th>
          <th class="border px-2 py-1 text-right">Prix</th>
          <th class="border px-2 py-1 text-left">Créé le</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tickets" :key="t.id">
          <td class="border px-2 py-1">{{ t.eventName || "—" }}</td>
          <td class="border px-2 py-1">{{ t.sessionDate || "—" }}</td>
          <td class="border px-2 py-1">{{ t.sessionTime || "—" }}</td>
          <td class="border px-2 py-1">{{ t.ticketNumber || "—" }}</td>
          <td class="border px-2 py-1 text-right">
            <span v-if="t.priceAmount != null">
              {{ t.priceAmount.toFixed(2) }} {{ t.priceCurrency || "" }}
            </span>
            <span v-else>—</span>
          </td>
          <td class="border px-2 py-1">
            {{ t.createdAt || "—" }}
          </td>
        </tr>
      </tbody>
    </table>
  </main>
</template>
