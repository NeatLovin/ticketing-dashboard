<template>
  <div class="panel p-5">
    <h2 class="section-heading mb-4">Panier moyen</h2>
    
    <div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-blue-50 p-4 rounded-xl">
          <div class="text-sm text-zinc-600 mb-1">Panier moyen</div>
          <div class="text-3xl font-bold text-blue-600">
            {{ averageBasket.toFixed(2) }}
          </div>
          <div class="text-xs text-zinc-500 mt-1">tickets par transaction</div>
        </div>
        
        <div class="bg-green-50 p-4 rounded-xl">
          <div class="text-sm text-zinc-600 mb-1">Total transactions</div>
          <div class="text-3xl font-bold text-green-600">
            {{ totalTransactions }}
          </div>
          <div class="text-xs text-zinc-500 mt-1">transactions</div>
        </div>
        
        <div class="bg-purple-50 p-4 rounded-xl">
          <div class="text-sm text-zinc-600 mb-1">Total tickets</div>
          <div class="text-3xl font-bold text-purple-600">
            {{ props.tickets.length }}
          </div>
          <div class="text-xs text-zinc-500 mt-1">tickets vendus</div>
        </div>
      </div>

      <div class="mt-6">
        <h3 class="text-base font-semibold text-zinc-900 mb-3">Répartition des transactions</h3>
        <div class="relative" style="height: 300px">
          <Bar :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
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

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const props = defineProps({
  tickets: { type: Array, default: () => [] }
});

// Grouper les tickets par transaction (même acheteur, même moment à peu près)
// Note: Petzi ne donne pas d'ID de transaction unique dans le webhook ticket_created
// On va essayer de grouper par (email + timestamp à la minute près) ou juste par email pour simplifier
// Pour une approximation, on va grouper par (firstName + lastName + generatedAt)
const transactions = computed(() => {
  const groups = {};
  props.tickets.forEach((ticket) => {
    // Clé de regroupement : nom + prénom + date de génération (sans les ms)
    const dateStr = ticket.generatedAt ? ticket.generatedAt.substring(0, 16) : "unknown";
    const key = `${ticket.buyerFirstName}-${ticket.buyerLastName}-${dateStr}`;
    
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(ticket);
  });
  return Object.values(groups);
});

const totalTransactions = computed(() => transactions.value.length);

const averageBasket = computed(() => {
  if (totalTransactions.value === 0) return 0;
  return props.tickets.length / totalTransactions.value;
});

// Distribution de la taille du panier
const basketSizeDistribution = computed(() => {
  const distribution = {};
  transactions.value.forEach((transaction) => {
    const size = transaction.length;
    if (!distribution[size]) distribution[size] = 0;
    distribution[size]++;
  });
  return distribution;
});

const chartData = computed(() => {
  const sizes = Object.keys(basketSizeDistribution.value).map(Number).sort((a, b) => a - b);
  const counts = sizes.map((size) => basketSizeDistribution.value[size]);
  
  return {
    labels: sizes.map((s) => `${s} ticket${s > 1 ? 's' : ''}`),
    datasets: [
      {
        label: "Nombre de transactions",
        data: counts,
        backgroundColor: "rgba(59, 130, 246, 0.5)",
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
  },
  scales: {
    y: {
      beginAtZero: true,
      title: {
        display: true,
        text: "Nombre de transactions",
      },
      ticks: {
        stepSize: 1,
        precision: 0,
      },
    },
    x: {
      title: {
        display: true,
        text: "Taille du panier",
      },
    },
  },
};
</script>

<style scoped>
/* Styles additionnels si nécessaire */
</style>

