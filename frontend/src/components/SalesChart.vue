<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Évolution des ventes - {{ selectedEventName || "Tous les événements" }}</h2>
    
    <div class="mb-4">
      <label class="block text-sm font-medium mb-2">Sélectionner un événement :</label>
      <select 
        v-model="selectedEventId" 
        @change="onEventChange"
        class="border rounded px-3 py-2 w-full max-w-md"
      >
        <option value="">Tous les événements</option>
        <option v-for="event in uniqueEvents" :key="event.id" :value="event.id">
          {{ event.name }} ({{ event.date }})
        </option>
      </select>
    </div>

    <div v-if="loading" class="text-center py-8">Chargement des données...</div>
    <div v-else-if="error" class="text-red-600 py-8">Erreur : {{ error }}</div>
    <div v-else class="relative" style="height: 400px">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { TicketsService } from "../services/ticketsService";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedEventId = ref("");
const selectedEventName = ref("");
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
          date: ticket.sessionDate || "Date inconnue",
        });
      }
    }
  });
  return Array.from(eventsMap.values()).sort((a, b) => b.date.localeCompare(a.date));
});

// Filtrer les tickets selon l'événement sélectionné
const filteredTickets = computed(() => {
  if (!selectedEventId.value) {
    return tickets.value;
  }
  return tickets.value.filter((t) => t.eventId === selectedEventId.value);
});

// Préparer les données pour le graphique
const chartData = computed(() => {
  const filtered = filteredTickets.value;
  
  if (filtered.length === 0) {
    return {
      labels: [],
      datasets: [
        {
          label: "Ventes cumulées",
          data: [],
          borderColor: "rgb(59, 130, 246)",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          fill: true,
          tension: 0.4,
        },
        {
          label: "Ventes par heure",
          data: [],
          borderColor: "rgb(34, 197, 94)",
          backgroundColor: "rgba(34, 197, 94, 0.1)",
          fill: false,
          tension: 0.4,
        },
      ],
    };
  }
  
  // Grouper par heure de création pour voir l'évolution temporelle
  const hourlyData = {};
  
  filtered.forEach((ticket) => {
    // Utiliser generatedAt si disponible (date réelle de génération du ticket), sinon createdAt
    const ticketDate = ticket.generatedAt || ticket.createdAt;
    const date = TicketsService.toDate(ticketDate);
    
    if (date && !isNaN(date.getTime())) {
      // Format: "DD/MM HH:00" avec l'année pour un tri correct
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      const hour = String(date.getHours()).padStart(2, "0");
      const hourKey = `${day}/${month} ${hour}:00`;
      
      if (!hourlyData[hourKey]) {
        hourlyData[hourKey] = {
          count: 0,
          timestamp: new Date(year, date.getMonth(), date.getDate(), date.getHours()).getTime(),
        };
      }
      hourlyData[hourKey].count++;
    } else {
      // Debug: tickets sans date valide
      if (import.meta.env.DEV) {
        console.warn("⚠️ Ticket sans date valide:", {
          id: ticket.id,
          createdAt: ticket.createdAt,
          generatedAt: ticket.generatedAt,
        });
      }
    }
  });

  // Trier par timestamp pour un tri correct
  const sortedKeys = Object.keys(hourlyData).sort((a, b) => {
    return hourlyData[a].timestamp - hourlyData[b].timestamp;
  });

  // Calculer les ventes cumulées
  let cumulative = 0;
  const cumulativeData = sortedKeys.map((key) => {
    cumulative += hourlyData[key].count;
    return cumulative;
  });

  const hourlyCounts = sortedKeys.map((key) => hourlyData[key].count);
  
  const numPoints = sortedKeys.length;
  const pointSize = numPoints <= 10 ? 5 : 3;

  // Si on n'a qu'un seul point, ajouter un point avant pour créer une ligne visible
  if (numPoints === 1 && cumulativeData[0] > 0) {
    // Ajouter un point avant pour créer une ligne
    const singleTimestamp = hourlyData[sortedKeys[0]].timestamp;
    const oneHourBefore = new Date(singleTimestamp - 3600000); // 1 heure avant
    const prevDay = String(oneHourBefore.getDate()).padStart(2, "0");
    const prevMonth = String(oneHourBefore.getMonth() + 1).padStart(2, "0");
    const prevHour = String(oneHourBefore.getHours()).padStart(2, "0");
    const prevKey = `${prevDay}/${prevMonth} ${prevHour}:00`;
    
    sortedKeys.unshift(prevKey);
    cumulativeData.unshift(0);
    hourlyCounts.unshift(0);
  }

  // Debug
  if (import.meta.env.DEV) {
    console.log("📊 Données du graphique:", {
      totalTickets: filtered.length,
      timeSlots: sortedKeys.length,
      labels: sortedKeys,
      cumulativeData,
      hourlyCounts,
      sampleTicket: filtered.length > 0 ? {
        id: filtered[0].id,
        createdAt: filtered[0].createdAt,
        generatedAt: filtered[0].generatedAt,
        parsedDate: TicketsService.toDate(filtered[0].generatedAt || filtered[0].createdAt),
      } : null,
    });
  }

  return {
    labels: sortedKeys,
    datasets: [
      {
        label: "Ventes cumulées",
        data: cumulativeData,
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.1, // Réduire la tension pour des lignes plus droites
        pointRadius: pointSize,
        pointHoverRadius: 7,
        pointBackgroundColor: "rgb(59, 130, 246)",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        showLine: true, // Forcer l'affichage de la ligne
        spanGaps: false,
      },
      {
        label: "Ventes par heure",
        data: hourlyCounts,
        borderColor: "rgb(34, 197, 94)",
        backgroundColor: "rgba(34, 197, 94, 0.1)",
        fill: false,
        tension: 0.1,
        pointRadius: pointSize,
        pointHoverRadius: 7,
        pointBackgroundColor: "rgb(34, 197, 94)",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        showLine: true,
        spanGaps: false,
      },
    ],
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: "index",
    intersect: false,
  },
  plugins: {
    legend: {
      position: "top",
      display: true,
    },
    title: {
      display: false,
    },
    tooltip: {
      mode: "index",
      intersect: false,
      callbacks: {
        label: function(context) {
          let label = context.dataset.label || "";
          if (label) {
            label += ": ";
          }
          label += context.parsed.y;
          return label;
        },
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Nombre de tickets",
      },
      ticks: {
        stepSize: 1,
        precision: 0,
      },
    },
    x: {
      title: {
        display: true,
        text: "Date et heure",
      },
      ticks: {
        maxRotation: 45,
        minRotation: 45,
      },
    },
  },
};

function onEventChange() {
  const event = uniqueEvents.value.find((e) => e.id === selectedEventId.value);
  selectedEventName.value = event ? event.name : "";
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

