<template>
  <div class="panel p-6">
    <h2 class="text-xl font-bold mb-4">Récapitulation mensuelle - Comparaison année sur année</h2>
    
    <div class="mb-4">
      <label class="block text-sm font-medium mb-2">Sélectionner une année :</label>
      <select 
        v-model="selectedYear" 
        class="border rounded px-3 py-2"
      >
        <option v-for="year in availableYears" :key="year" :value="year">
          {{ year }}
        </option>
      </select>
    </div>

    <div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded-lg">
          <div class="text-sm text-gray-600 mb-1">Année {{ selectedYear }}</div>
          <div class="text-3xl font-bold text-blue-600">
            {{ currentYearTotal }}
          </div>
          <div class="text-xs text-gray-500 mt-1">tickets vendus</div>
        </div>
        
        <div class="bg-green-50 p-4 rounded-lg">
          <div class="text-sm text-gray-600 mb-1">Année {{ previousYear }}</div>
          <div class="text-3xl font-bold text-green-600">
            {{ previousYearTotal }}
          </div>
          <div class="text-xs text-gray-500 mt-1">tickets vendus</div>
        </div>
      </div>

      <div class="mb-4">
        <div class="text-lg font-semibold">
          Évolution : 
          <span :class="evolutionClass">
            {{ evolutionPercentage > 0 ? "+" : "" }}{{ evolutionPercentage.toFixed(1) }}%
          </span>
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

const selectedYear = ref(new Date().getFullYear());

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

// Mettre à jour l'année sélectionnée si elle n'est pas dans la liste
watch(availableYears, (years) => {
  if (years.length > 0 && !years.includes(selectedYear.value)) {
    selectedYear.value = years[0];
  }
});

const previousYear = computed(() => selectedYear.value - 1);

// Filtrer les tickets par année
const currentYearTickets = computed(() => {
  return props.tickets.filter((ticket) => {
    const date = getTicketDate(ticket);
    return date && date.getFullYear() === selectedYear.value;
  });
});

const previousYearTickets = computed(() => {
  return props.tickets.filter((ticket) => {
    const date = getTicketDate(ticket);
    return date && date.getFullYear() === previousYear.value;
  });
});

// Totaux
const currentYearTotal = computed(() => currentYearTickets.value.length);
const previousYearTotal = computed(() => previousYearTickets.value.length);

// Calcul de l'évolution
const evolutionPercentage = computed(() => {
  if (previousYearTotal.value === 0) {
    return currentYearTotal.value > 0 ? 100 : 0;
  }
  return ((currentYearTotal.value - previousYearTotal.value) / previousYearTotal.value) * 100;
});

const evolutionClass = computed(() => {
  return evolutionPercentage.value >= 0 ? "text-green-600" : "text-red-600";
});

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
  const currentMonths = groupByMonth(currentYearTickets.value);
  const previousMonths = groupByMonth(previousYearTickets.value);

  const monthNames = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
  ];

  return {
    labels: monthNames,
    datasets: [
      {
        label: `${selectedYear.value}`,
        data: currentMonths.map((m) => m.count),
        backgroundColor: "rgba(59, 130, 246, 0.6)",
        borderColor: "rgb(59, 130, 246)",
        borderWidth: 1,
      },
      {
        label: `${previousYear.value}`,
        data: previousMonths.map((m) => m.count),
        backgroundColor: "rgba(34, 197, 94, 0.6)",
        borderColor: "rgb(34, 197, 94)",
        borderWidth: 1,
      },
    ],
  };
});

// Données pour le graphique des revenus
const revenueChartData = computed(() => {
  const currentMonths = groupByMonth(currentYearTickets.value);
  const previousMonths = groupByMonth(previousYearTickets.value);

  const monthNames = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
  ];

  return {
    labels: monthNames,
    datasets: [
      {
        label: `Revenus ${selectedYear.value}`,
        data: currentMonths.map((m) => m.revenue),
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.4,
      },
      {
        label: `Revenus ${previousYear.value}`,
        data: previousMonths.map((m) => m.revenue),
        borderColor: "rgb(34, 197, 94)",
        backgroundColor: "rgba(34, 197, 94, 0.1)",
        fill: true,
        tension: 0.4,
      },
    ],
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

