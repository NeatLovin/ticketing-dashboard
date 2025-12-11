<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Évolution des ventes</h2>
    
    <div class="relative" style="height: 400px">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
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

// Props
const props = defineProps({
  tickets: { type: Array, default: () => [] },
  showCumulative: { type: Boolean, default: true },
  showHourly: { type: Boolean, default: true },
  viewMode: { type: String, default: 'daily' },
});

// Extraire les événements uniques pour les noms
const uniqueEvents = computed(() => {
  const eventsMap = new Map();
  props.tickets.forEach((ticket) => {
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

// Grouper les tickets par événement
const ticketsByEvent = computed(() => {
  const groups = new Map();
  props.tickets.forEach((t) => {
    if (!t.eventId) return;
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
      datasets: [],
    };
  }
  
  // 1. Calculer les index temporels (J-x ou S-x) pour chaque ticket et trouver le min global
  const perEventData = new Map(); // Map<eventId, Map<timeIndex, count>>
  let minIndex = 0;

  groupEntries.forEach(([eventId, evTickets]) => {
    const timeData = new Map(); // timeIndex -> count
    
    evTickets.forEach((ticket) => {
      if (!ticket.sessionDate) return;
      
      const eventDate = new Date(ticket.sessionDate);
      const saleDate = TicketsService.toDate(ticket.generatedAt || ticket.createdAt);
      
      if (eventDate && saleDate && !isNaN(eventDate.getTime()) && !isNaN(saleDate.getTime())) {
        // Normaliser à minuit pour comparer les jours
        const eDate = new Date(eventDate.getFullYear(), eventDate.getMonth(), eventDate.getDate());
        const sDate = new Date(saleDate.getFullYear(), saleDate.getMonth(), saleDate.getDate());
        
        // Différence en jours (sale - event)
        const diffTime = sDate.getTime() - eDate.getTime();
        const diffDays = Math.round(diffTime / (1000 * 3600 * 24));
        
        // Calculer l'index selon le mode
        let timeIndex = diffDays;
        if (props.viewMode === 'weekly') {
          // Semaine 0 = [J-6, J0], Semaine -1 = [J-13, J-7], etc.
          // Ou simplement division par 7
          timeIndex = Math.floor(diffDays / 7);
        }

        // On ne s'intéresse qu'aux ventes avant ou le jour même (<= 0)
        if (timeIndex <= 0) {
          if (timeIndex < minIndex) minIndex = timeIndex;
          
          const currentCount = timeData.get(timeIndex) || 0;
          timeData.set(timeIndex, currentCount + 1);
        }
      }
    });
    perEventData.set(eventId, timeData);
  });

  // 2. Générer les labels de minIndex à 0
  const labels = [];
  for (let i = minIndex; i <= 0; i++) {
    labels.push(props.viewMode === 'weekly' ? `S${i}` : `J${i}`);
  }

  // 3. Construire les datasets
  const colorPalette = [
    { border: "rgb(59, 130, 246)", background: "rgba(59, 130, 246, 0.1)" }, // blue
    { border: "rgb(34, 197, 94)", background: "rgba(34, 197, 94, 0.1)" },  // green
    { border: "rgb(234, 179, 8)", background: "rgba(234, 179, 8, 0.1)" },  // amber
    { border: "rgb(244, 63, 94)", background: "rgba(244, 63, 94, 0.1)" },  // rose
    { border: "rgb(99, 102, 241)", background: "rgba(99, 102, 241, 0.1)" }, // indigo
  ];
  const datasets = [];

  // Déterminer la taille des points
  const numPoints = labels.length;
  const pointSize = numPoints <= 20 ? 4 : 2;

  groupEntries.forEach(([eventId, evTickets], idx) => {
    const timeData = perEventData.get(eventId);
    const eventName = uniqueEvents.value.find((e) => e.id === eventId)?.name || `Événement ${eventId}`;
    const colors = colorPalette[idx % colorPalette.length];

    // Construire les données alignées sur les labels
    const counts = [];
    const cumulativeData = [];
    let acc = 0;

    for (let i = minIndex; i <= 0; i++) {
      const count = timeData.get(i) || 0;
      counts.push(count);
      acc += count;
      cumulativeData.push(acc);
    }

    if (props.showCumulative) {
      datasets.push({
        label: `Ventes cumulées — ${eventName}`,
        data: cumulativeData,
        borderColor: colors.border,
        backgroundColor: colors.background,
        fill: true,
        tension: 0.1,
        pointRadius: pointSize,
        pointHoverRadius: 6,
        pointBackgroundColor: colors.border,
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        showLine: true,
        spanGaps: false,
      });
    }
    if (props.showHourly) {
      datasets.push({
        label: `Ventes ${props.viewMode === 'weekly' ? 'hebdomadaires' : 'journalières'} — ${eventName}`,
        data: counts,
        borderColor: colors.border,
        backgroundColor: colors.background,
        fill: false,
        tension: 0.1,
        pointRadius: pointSize,
        pointHoverRadius: 6,
        pointBackgroundColor: colors.border,
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        showLine: true,
        spanGaps: false,
        borderDash: [5, 5], // Pointillés pour différencier
      });
    }
  });

  return {
    labels,
    datasets,
  };
});

const chartOptions = computed(() => ({
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
        text: props.viewMode === 'weekly' ? "Semaines avant l'événement" : "Jours avant l'événement",
      },
      ticks: {
        maxRotation: 45,
        minRotation: 0,
        autoSkip: true,
        maxTicksLimit: 20,
      },
    },
  },
}));
</script>

<style scoped>
/* Styles additionnels si nécessaire */
</style>

