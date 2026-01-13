<template>
  <div class="panel p-5">
    <h2 class="section-heading mb-4">Heatmap des ventes</h2>
    <p class="text-sm text-zinc-500 mb-6">Visualisez les jours et heures où les achats sont les plus fréquents.</p>

    <div v-if="!hasData" class="text-center py-12 text-zinc-400">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <p>Aucune donnée disponible</p>
    </div>

    <div v-else class="overflow-x-auto">
      <!-- Légende des heures -->
      <div class="flex mb-2">
        <div class="w-20 flex-shrink-0"></div>
        <div class="flex-1 grid grid-cols-24 gap-px text-xs text-zinc-500">
          <div v-for="hour in 24" :key="hour" class="text-center">
            {{ hour - 1 }}h
          </div>
        </div>
      </div>

      <!-- Grille heatmap -->
      <div class="space-y-px">
        <div v-for="(day, dayIndex) in days" :key="dayIndex" class="flex items-center">
          <div class="w-20 flex-shrink-0 text-sm font-medium text-zinc-700 pr-3 text-right">
            {{ day }}
          </div>
          <div class="flex-1 grid grid-cols-24 gap-px">
            <div
              v-for="hour in 24"
              :key="hour"
              class="aspect-square rounded-sm transition-all duration-200 cursor-default"
              :class="getCellClasses(dayIndex, hour - 1)"
              :title="getCellTooltip(dayIndex, hour - 1)"
            ></div>
          </div>
        </div>
      </div>

      <!-- Légende couleurs -->
      <div class="mt-6 flex items-center justify-end gap-2">
        <span class="text-xs text-zinc-500">Moins</span>
        <div class="flex gap-px">
          <div class="w-4 h-4 rounded-sm bg-zinc-100"></div>
          <div class="w-4 h-4 rounded-sm bg-emerald-100"></div>
          <div class="w-4 h-4 rounded-sm bg-emerald-300"></div>
          <div class="w-4 h-4 rounded-sm bg-emerald-500"></div>
          <div class="w-4 h-4 rounded-sm bg-emerald-700"></div>
        </div>
        <span class="text-xs text-zinc-500">Plus</span>
      </div>

      <!-- Stats résumées -->
      <div class="mt-6 pt-6 border-t border-zinc-100 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="text-center">
          <p class="text-2xl font-bold text-zinc-900">{{ peakDay }}</p>
          <p class="text-sm text-zinc-500">Jour le plus actif</p>
        </div>
        <div class="text-center">
          <p class="text-2xl font-bold text-zinc-900">{{ peakHour }}h</p>
          <p class="text-sm text-zinc-500">Heure de pointe</p>
        </div>
        <div class="text-center">
          <p class="text-2xl font-bold text-zinc-900">{{ peakCount }}</p>
          <p class="text-sm text-zinc-500">Ventes au pic</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  tickets: { type: Array, default: () => [] },
});

const days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

// Construire la matrice jour/heure
const heatmapData = computed(() => {
  // Matrice 7 jours x 24 heures
  const matrix = Array.from({ length: 7 }, () => Array(24).fill(0));
  
  props.tickets.forEach(ticket => {
    const timestamp = ticket.generatedAt || ticket.createdAt;
    if (!timestamp) return;
    
    let date;
    if (timestamp.toDate) {
      date = timestamp.toDate();
    } else if (typeof timestamp === 'string') {
      date = new Date(timestamp);
    } else {
      return;
    }
    
    if (isNaN(date.getTime())) return;
    
    // getDay() : 0 = Dimanche, 1 = Lundi, ..., 6 = Samedi
    // On veut : 0 = Lundi, ..., 6 = Dimanche
    const jsDay = date.getDay();
    const dayIndex = jsDay === 0 ? 6 : jsDay - 1;
    const hour = date.getHours();
    
    matrix[dayIndex][hour]++;
  });
  
  return matrix;
});

// Valeur maximale pour la normalisation
const maxValue = computed(() => {
  let max = 0;
  heatmapData.value.forEach(row => {
    row.forEach(val => {
      if (val > max) max = val;
    });
  });
  return max;
});

const hasData = computed(() => maxValue.value > 0);

// Classes CSS selon l'intensité
function getCellClasses(dayIndex, hour) {
  const value = heatmapData.value[dayIndex][hour];
  const max = maxValue.value;
  
  if (max === 0 || value === 0) {
    return 'bg-zinc-100 hover:bg-zinc-200';
  }
  
  const ratio = value / max;
  
  if (ratio <= 0.2) return 'bg-emerald-100 hover:bg-emerald-200';
  if (ratio <= 0.4) return 'bg-emerald-200 hover:bg-emerald-300';
  if (ratio <= 0.6) return 'bg-emerald-300 hover:bg-emerald-400';
  if (ratio <= 0.8) return 'bg-emerald-500 hover:bg-emerald-600';
  return 'bg-emerald-700 hover:bg-emerald-800';
}

// Tooltip avec le nombre de ventes
function getCellTooltip(dayIndex, hour) {
  const value = heatmapData.value[dayIndex][hour];
  const day = days[dayIndex];
  return `${day} ${hour}h-${hour + 1}h : ${value} vente${value > 1 ? 's' : ''}`;
}

// Trouver le pic combiné (jour + heure spécifique)
const peakSlot = computed(() => {
  if (!hasData.value) return { dayIndex: 0, hour: 0, count: 0 };
  
  let maxDayIndex = 0;
  let maxHour = 0;
  let maxCount = 0;
  
  heatmapData.value.forEach((row, dayIndex) => {
    row.forEach((count, hour) => {
      if (count > maxCount) {
        maxCount = count;
        maxDayIndex = dayIndex;
        maxHour = hour;
      }
    });
  });
  
  return { dayIndex: maxDayIndex, hour: maxHour, count: maxCount };
});

// Stats : jour le plus actif (du créneau pic)
const peakDay = computed(() => {
  if (!hasData.value) return '—';
  return days[peakSlot.value.dayIndex];
});

// Stats : heure de pointe (du créneau pic)
const peakHour = computed(() => {
  if (!hasData.value) return '—';
  return peakSlot.value.hour;
});

// Stats : nombre de ventes au pic
const peakCount = computed(() => {
  if (!hasData.value) return 0;
  return peakSlot.value.count;
});
</script>

<style scoped>
.grid-cols-24 {
  grid-template-columns: repeat(24, minmax(0, 1fr));
}
</style>
