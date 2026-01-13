<template>
  <div class="panel p-5">
    <h2 class="section-heading mb-4">Répartition des ventes par événement</h2>
    
    <div v-if="hasData" class="flex flex-col md:flex-row h-[350px]">
      <!-- Chart -->
      <div class="flex-1 relative min-h-0">
        <Pie :data="chartData" :options="chartOptions" />
      </div>
      
      <!-- Custom Legend -->
      <div class="w-full md:w-64 overflow-y-auto pl-4 border-l border-zinc-100 mt-4 md:mt-0 custom-scrollbar">
        <ul class="space-y-2 text-sm">
          <li v-for="(label, index) in chartData.labels" :key="index" class="flex items-start">
            <span 
              class="inline-block w-3 h-3 rounded-full mt-1 mr-2 flex-shrink-0"
              :style="{ backgroundColor: chartData.datasets[0].backgroundColor[index] }"
            ></span>
            <div class="flex-1 min-w-0">
              <p class="text-zinc-700 truncate" :title="label">{{ label }}</p>
            </div>
            <span class="text-zinc-500 text-xs ml-2 font-mono">
              {{ chartData.datasets[0].data[index] }}
            </span>
          </li>
        </ul>
      </div>
    </div>

    <div v-else class="h-[350px] flex items-center justify-center text-zinc-400">
      Aucune donnée à afficher
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Pie } from 'vue-chartjs';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const props = defineProps({
  tickets: {
    type: Array,
    default: () => []
  }
});

const hasData = computed(() => props.tickets.length > 0);

const chartData = computed(() => {
  const counts = {};
  props.tickets.forEach(ticket => {
    const name = ticket.eventName || 'Inconnu';
    counts[name] = (counts[name] || 0) + 1;
  });

  // Sort by count descending
  const sortedEntries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  
  const labels = sortedEntries.map(e => e[0]);
  const data = sortedEntries.map(e => e[1]);

  // Palette de couleurs (Tailwind colors inspired)
  const backgroundColors = [
    'rgba(59, 130, 246, 0.8)',   // blue-500
    'rgba(16, 185, 129, 0.8)',   // emerald-500
    'rgba(245, 158, 11, 0.8)',   // amber-500
    'rgba(239, 68, 68, 0.8)',    // red-500
    'rgba(139, 92, 246, 0.8)',   // violet-500
    'rgba(236, 72, 153, 0.8)',   // pink-500
    'rgba(99, 102, 241, 0.8)',   // indigo-500
    'rgba(20, 184, 166, 0.8)',   // teal-500
    'rgba(249, 115, 22, 0.8)',   // orange-500
    'rgba(132, 204, 22, 0.8)',   // lime-500
    'rgba(6, 182, 212, 0.8)',    // cyan-500
    'rgba(168, 85, 247, 0.8)',   // purple-500
  ];

  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: labels.map((_, i) => backgroundColors[i % backgroundColors.length]),
        borderColor: '#ffffff',
        borderWidth: 2
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          const value = context.raw || 0;
          const total = context.chart._metasets[context.datasetIndex].total;
          const percentage = Math.round((value / total) * 100) + '%';
          return `${value} tickets (${percentage})`;
        }
      }
    }
  }
};
</script>
