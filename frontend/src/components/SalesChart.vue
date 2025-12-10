<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Évolution des ventes - {{ selectedEventName || "Tous les événements" }}</h2>
    
    <div class="mb-4">
      <label class="block text-sm font-medium mb-2">Sélectionner un ou plusieurs événements :</label>
      <select 
        v-model="selectedEventIds" 
        multiple
        class="border rounded px-3 py-2 w-full max-w-md h-40"
      >
        <option v-for="event in uniqueEvents" :key="event.id" :value="event.id">
          {{ event.name }} ({{ event.date }})
        </option>
      </select>
      <p class="mt-2 text-xs text-gray-500">Astuce: maintenez Ctrl/Cmd pour sélectionner plusieurs éléments.</p>
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

// Props pour afficher/masquer les courbes
const props = defineProps({
  showCumulative: { type: Boolean, default: true },
  showHourly: { type: Boolean, default: true },
});

const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedEventIds = ref([]);
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

// Grouper les tickets par événement, en appliquant la sélection multiple si présente
const ticketsByEvent = computed(() => {
  const groups = new Map();
  const selectionActive = Array.isArray(selectedEventIds.value) && selectedEventIds.value.length > 0;
  tickets.value.forEach((t) => {
    if (!t.eventId) return;
    if (selectionActive && !selectedEventIds.value.includes(t.eventId)) return;
    const key = t.eventId;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(t);
  });
  return groups; // Map<eventId, Ticket[]>
});

// Préparer les données pour le graphique
const chartData = computed(() => {
  const groups = ticketsByEvent.value;
  const groupEntries = Array.from(groups.entries());
  
  if (groupEntries.length === 0) {
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
  
  // Construire les axes horaires par événement et une union triée des labels
  const perEventHourly = new Map(); // Map<eventId, Record<label,{count,timestamp}>>
  const labelSet = new Map(); // label -> timestamp
  
  groupEntries.forEach(([eventId, evTickets]) => {
    const hourlyData = {};
    evTickets.forEach((ticket) => {
      const ticketDate = ticket.generatedAt || ticket.createdAt;
      const date = TicketsService.toDate(ticketDate);
      if (date && !isNaN(date.getTime())) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const hour = String(date.getHours()).padStart(2, "0");
        const hourKey = `${day}/${month} ${hour}:00`;
        const ts = new Date(year, date.getMonth(), date.getDate(), date.getHours()).getTime();
        if (!hourlyData[hourKey]) {
          hourlyData[hourKey] = { count: 0, timestamp: ts };
        }
        hourlyData[hourKey].count++;
        if (!labelSet.has(hourKey)) labelSet.set(hourKey, ts);
      }
    });
    perEventHourly.set(eventId, hourlyData);
  });

  const sortedLabels = Array.from(labelSet.entries())
    .sort((a, b) => a[1] - b[1])
    .map(([label]) => label);

  // Déterminer la taille des points selon le nombre de labels
  const numPoints = sortedLabels.length;
  const pointSize = numPoints <= 10 ? 5 : 3;

  // Debug
  if (import.meta.env.DEV) {
    console.log("📊 Données du graphique (multi):", {
      selectedEventIds: selectedEventIds.value,
      labelsCount: sortedLabels.length,
    });
  }

  // Construire les datasets par événement selon les options
  const colorPalette = [
    { border: "rgb(59, 130, 246)", background: "rgba(59, 130, 246, 0.1)" }, // blue
    { border: "rgb(34, 197, 94)", background: "rgba(34, 197, 94, 0.1)" },  // green
    { border: "rgb(234, 179, 8)", background: "rgba(234, 179, 8, 0.1)" },  // amber
    { border: "rgb(244, 63, 94)", background: "rgba(244, 63, 94, 0.1)" },  // rose
    { border: "rgb(99, 102, 241)", background: "rgba(99, 102, 241, 0.1)" }, // indigo
  ];
  const datasets = [];

  groupEntries.forEach(([eventId, evTickets], idx) => {
    const hourlyData = perEventHourly.get(eventId) || {};
    // Construire la série horaire alignée sur les labels globaux
    const hourlyCounts = sortedLabels.map((label) => (hourlyData[label]?.count ?? 0));
    // Construire la série cumulée
    const cumulativeData = [];
    let acc = 0;
    hourlyCounts.forEach((c) => { acc += c; cumulativeData.push(acc); });

    const colors = colorPalette[idx % colorPalette.length];
    const eventName = uniqueEvents.value.find((e) => e.id === eventId)?.name || `Événement ${eventId}`;

    if (props.showCumulative) {
      datasets.push({
        label: `Ventes cumulées — ${eventName}`,
        data: cumulativeData,
        borderColor: colors.border,
        backgroundColor: colors.background,
        fill: true,
        tension: 0.1,
        pointRadius: pointSize,
        pointHoverRadius: 7,
        pointBackgroundColor: colors.border,
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        showLine: true,
        spanGaps: false,
      });
    }
    if (props.showHourly) {
      datasets.push({
        label: `Ventes par heure — ${eventName}`,
        data: hourlyCounts,
        borderColor: colors.border,
        backgroundColor: colors.background,
        fill: false,
        tension: 0.1,
        pointRadius: pointSize,
        pointHoverRadius: 7,
        pointBackgroundColor: colors.border,
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        showLine: true,
        spanGaps: false,
      });
    }
  });

  return {
    labels: sortedLabels,
    datasets,
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

function setupSubscription() {
  if (unsubscribe.value) {
    unsubscribe.value();
  }

  loading.value = true;
  error.value = null;

  // En mode multi-sélection, on s'abonne à tous les tickets pour simplicité,
  // puis on filtre côté client (évite multiplexer plusieurs abonnements simultanés).
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

watch(selectedEventIds, () => {
  // Pas besoin de refaire l'abonnement, on filtre côté client.
}, { deep: true });

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

