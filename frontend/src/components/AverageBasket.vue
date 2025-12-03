<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Panier moyen</h2>
    
    <div class="mb-4">
      <label class="block text-sm font-medium mb-2">Filtrer par événement :</label>
      <select 
        v-model="selectedEventId" 
        @change="onEventChange"
        class="border rounded px-3 py-2 w-full max-w-md"
      >
        <option value="">Tous les événements</option>
        <option v-for="event in uniqueEvents" :key="event.id" :value="event.id">
          {{ event.name }}
        </option>
      </select>
    </div>

    <div v-if="loading" class="text-center py-8">Chargement des données...</div>
    <div v-else-if="error" class="text-red-600 py-8">Erreur : {{ error }}</div>
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded-lg">
          <div class="text-sm text-gray-600 mb-1">Panier moyen</div>
          <div class="text-3xl font-bold text-blue-600">
            {{ averageBasket.toFixed(2) }}
          </div>
          <div class="text-xs text-gray-500 mt-1">tickets par transaction</div>
        </div>
        
        <div class="bg-green-50 p-4 rounded-lg">
          <div class="text-sm text-gray-600 mb-1">Total transactions</div>
          <div class="text-3xl font-bold text-green-600">
            {{ totalTransactions }}
          </div>
          <div class="text-xs text-gray-500 mt-1">transactions</div>
        </div>
        
        <div class="bg-purple-50 p-4 rounded-lg">
          <div class="text-sm text-gray-600 mb-1">Total tickets</div>
          <div class="text-3xl font-bold text-purple-600">
            {{ filteredTickets.length }}
          </div>
          <div class="text-xs text-gray-500 mt-1">tickets vendus</div>
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-3">Répartition des transactions</h3>
        <div class="relative" style="height: 300px">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { TicketsService } from "../services/ticketsService";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedEventId = ref("");
const unsubscribe = ref(null);

// Extraire les événements uniques
const uniqueEvents = computed(() => {
  const eventsMap = new Map();
  tickets.value.forEach((ticket) => {
    if (ticket.eventId && ticket.eventName) {
      const key = `${ticket.eventId}`;
      if (!eventsMap.has(key)) {
        eventsMap.set(key, {
          id: ticket.eventId,
          name: ticket.eventName,
        });
      }
    }
  });
  return Array.from(eventsMap.values());
});

// Filtrer les tickets selon l'événement sélectionné
const filteredTickets = computed(() => {
  if (!selectedEventId.value) {
    return tickets.value;
  }
  return tickets.value.filter((t) => t.eventId === selectedEventId.value);
});

// Calculer le panier moyen
const averageBasket = computed(() => {
  return TicketsService.calculateAverageBasket(filteredTickets.value);
});

// Calculer le nombre total de transactions
const totalTransactions = computed(() => {
  const transactions = new Map();
  filteredTickets.value.forEach((ticket) => {
    const key = ticket.ticketNumber || ticket.id;
    if (!transactions.has(key)) {
      transactions.set(key, []);
    }
    transactions.get(key).push(ticket);
  });
  return transactions.size;
});

// Préparer les données pour le graphique de répartition
const chartData = computed(() => {
  const transactions = new Map();
  filteredTickets.value.forEach((ticket) => {
    const key = ticket.ticketNumber || ticket.id;
    if (!transactions.has(key)) {
      transactions.set(key, 0);
    }
    transactions.set(key, transactions.get(key) + 1);
  });

  // Compter combien de transactions ont 1, 2, 3, etc. tickets
  const distribution = {};
  transactions.forEach((count) => {
    if (!distribution[count]) {
      distribution[count] = 0;
    }
    distribution[count]++;
  });

  const sortedKeys = Object.keys(distribution)
    .map(Number)
    .sort((a, b) => a - b)
    .slice(0, 10); // Limiter à 10 pour la lisibilité

  return {
    labels: sortedKeys.map((k) => `${k} ticket${k > 1 ? "s" : ""}`),
    datasets: [
      {
        label: "Nombre de transactions",
        data: sortedKeys.map((k) => distribution[k]),
        backgroundColor: "rgba(59, 130, 246, 0.6)",
        borderColor: "rgb(59, 130, 246)",
        borderWidth: 1,
      },
    ],
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    title: {
      display: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Nombre de transactions",
      },
    },
    x: {
      title: {
        display: true,
        text: "Nombre de tickets par transaction",
      },
    },
  },
};

function onEventChange() {
  // La logique est gérée par les computed properties
}

function setupSubscription() {
  if (unsubscribe.value) {
    unsubscribe.value();
  }

  loading.value = true;
  error.value = null;

  if (selectedEventId.value) {
    unsubscribe.value = TicketsService.subscribeToEventTickets(
      selectedEventId.value,
      (newTickets, err) => {
        if (err) {
          error.value = err.message;
          loading.value = false;
        } else {
          tickets.value = newTickets;
          loading.value = false;
        }
      }
    );
  } else {
    unsubscribe.value = TicketsService.subscribeToAllTickets(
      (newTickets, err) => {
        if (err) {
          error.value = err.message;
          loading.value = false;
        } else {
          tickets.value = newTickets;
          loading.value = false;
        }
      }
    );
  }
}

watch(selectedEventId, () => {
  setupSubscription();
});

onMounted(() => {
  setupSubscription();
});

onUnmounted(() => {
  if (unsubscribe.value) {
    unsubscribe.value();
  }
});
</script>

<style scoped>
/* Styles additionnels si nécessaire */
</style>

