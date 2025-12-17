<template>
  <div class="panel p-6">
    <h2 class="text-xl font-bold mb-4">Récapitulation mensuelle - Comparaison année sur année</h2>
    
    <div class="mb-4">
      <label class="block text-sm font-medium mb-2">Sélectionner les années :</label>
      <div class="flex flex-wrap gap-4">
        <label v-for="year in availableYears" :key="year" class="inline-flex items-center cursor-pointer">
          <input 
            type="checkbox" 
            :value="year" 
            v-model="selectedYears" 
            class="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
          >
          <span class="ml-2 text-gray-700">{{ year }}</span>
        </label>
      </div>
    </div>

    <div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div 
          v-for="(stat, index) in selectedYearsTotals" 
          :key="stat.year"
          class="p-4 rounded-lg border"
          :style="{ borderColor: getColor(index).border, backgroundColor: getColor(index).bg.replace('0.6', '0.1') }"
        >
          <div class="text-sm text-gray-600 mb-1">Année {{ stat.year }}</div>
          <div class="text-3xl font-bold" :style="{ color: getColor(index).border }">
            {{ stat.count }}
          </div>
          <div class="text-xs text-gray-500 mt-1">tickets vendus</div>
          <div class="text-sm font-semibold mt-2" :style="{ color: getColor(index).border }">
            {{ stat.revenue.toLocaleString('fr-CH', { style: 'currency', currency: 'CHF' }) }}
          </div>
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-3">Comparaison mensuelle</h3>
        <div class="relative" style="height: 400px">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-3">Évolution des revenus</h3>
        <div class="relative" style="height: 400px">
          <Line :data="revenueChartData" :options="revenueChartOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { Bar, Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { TicketsService } from "../services/ticketsService";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const props = defineProps({
  tickets: { type: Array, default: () => [] }
});

const selectedYears = ref([new Date().getFullYear()]);

const getTicketDate = (ticket) => {
  return TicketsService.toDate(ticket.generatedAt || ticket.createdAt);
};

// Calculer les années disponibles
const availableYears = computed(() => {
  const years = new Set();
  props.tickets.forEach((ticket) => {
    const date = getTicketDate(ticket);
    if (date) {
      years.add(date.getFullYear());
    }
  });
  // Ajouter l'année courante si pas de données
  if (years.size === 0) years.add(new Date().getFullYear());
  return Array.from(years).sort((a, b) => b - a);
});

// Mettre à jour les années sélectionnées si nécessaire
watch(availableYears, (years) => {
  if (years.length > 0 && selectedYears.value.length === 0) {
    selectedYears.value = [years[0]];
  }
});

// Filtrer les tickets pour une année donnée
const getTicketsForYear = (year) => {
  return props.tickets.filter((ticket) => {
    const date = getTicketDate(ticket);
    return date && date.getFullYear() === year;
  });
};

// Totaux par année sélectionnée
const selectedYearsTotals = computed(() => {
  return [...selectedYears.value].sort((a, b) => b - a).map((year, index) => {
    const tickets = getTicketsForYear(year);
    return {
      year,
      count: tickets.length,
      revenue: tickets.reduce((sum, t) => sum + (t.priceAmount || 0), 0),
      colorIndex: index
    };
  });
});

// Couleurs pour les graphiques
const colors = [
  { bg: 'rgba(59, 130, 246, 0.6)', border: 'rgb(59, 130, 246)' }, // Blue
  { bg: 'rgba(34, 197, 94, 0.6)', border: 'rgb(34, 197, 94)' },   // Green
  { bg: 'rgba(239, 68, 68, 0.6)', border: 'rgb(239, 68, 68)' },   // Red
  { bg: 'rgba(245, 158, 11, 0.6)', border: 'rgb(245, 158, 11)' }, // Amber
  { bg: 'rgba(168, 85, 247, 0.6)', border: 'rgb(168, 85, 247)' }, // Purple
  { bg: 'rgba(236, 72, 153, 0.6)', border: 'rgb(236, 72, 153)' }, // Pink
];

const getColor = (index) => colors[index % colors.length];

// Grouper par mois
function groupByMonth(ticketsList) {
  const months = Array.from({ length: 12 }, (_, i) => ({
    month: i + 1,
    count: 0,
    revenue: 0,
  }));

  ticketsList.forEach((ticket) => {
    const date = getTicketDate(ticket);
    if (date) {
      const monthIndex = date.getMonth();
      months[monthIndex].count++;
      if (ticket.priceAmount && typeof ticket.priceAmount === "number") {
        months[monthIndex].revenue += ticket.priceAmount;
      }
    }
  });

  return months;
}

// Données pour le graphique de comparaison mensuelle
const chartData = computed(() => {
  const monthNames = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
  ];

  const datasets = [...selectedYears.value].sort((a, b) => b - a).map((year, index) => {
    const tickets = getTicketsForYear(year);
    const months = groupByMonth(tickets);
    const color = getColor(index);

    return {
      label: `${year}`,
      data: months.map((m) => m.count),
      backgroundColor: color.bg,
      borderColor: color.border,
      borderWidth: 1,
    };
  });

  return {
    labels: monthNames,
    datasets,
  };
});

// Données pour le graphique des revenus
const revenueChartData = computed(() => {
  const monthNames = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
  ];

  const datasets = [...selectedYears.value].sort((a, b) => b - a).map((year, index) => {
    const tickets = getTicketsForYear(year);
    const months = groupByMonth(tickets);
    const color = getColor(index);

    return {
      label: `Revenus ${year}`,
      data: months.map((m) => m.revenue),
      borderColor: color.border,
      backgroundColor: color.bg.replace('0.6', '0.1'),
      fill: true,
      tension: 0.4,
    };
  });

  return {
    labels: monthNames,
    datasets,
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top",
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Nombre de tickets",
      },
    },
  },
};

const revenueChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: "top",
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Revenus (CHF)",
      },
    },
  },
};
</script>

<style scoped>
/* Styles additionnels si nécessaire */
</style>

