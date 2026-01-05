<template>
  <main class="page">
    <div class="page-header">
      <h1 class="page-title">Tableaux de bord</h1>
      <p class="page-subtitle">Visualisations temps réel — ventes, répartition, carte, panier moyen.</p>
    </div>
      
      <DashboardFilters 
        :events="uniqueEvents" 
        :categories="uniqueCategories"
        @update:filters="handleFiltersUpdate"
      />

      <div v-if="loading" class="space-y-6">
        <div class="panel p-6">
          <SkeletonBlock class-name="h-7 w-56 mb-6" />
          <SkeletonBlock class-name="h-[400px] w-full" />
        </div>

        <div class="panel p-6">
          <SkeletonBlock class-name="h-7 w-80 mb-6" />
          <SkeletonBlock class-name="h-[350px] w-full" />
        </div>

        <div class="panel p-6">
          <SkeletonBlock class-name="h-7 w-72 mb-6" />
          <SkeletonBlock class-name="h-[500px] w-full" />
        </div>

        <div class="panel p-6">
          <SkeletonBlock class-name="h-7 w-40 mb-6" />
          <SkeletonBlock class-name="h-28 w-full mb-6" />
          <SkeletonBlock class-name="h-6 w-64 mb-3" />
          <SkeletonBlock class-name="h-[300px] w-full" />
        </div>

        <div class="panel p-6">
          <SkeletonBlock class-name="h-7 w-[520px] max-w-full mb-6" />
          <SkeletonBlock class-name="h-10 w-[420px] max-w-full mb-6" />
          <SkeletonBlock class-name="h-28 w-full mb-6" />
          <SkeletonBlock class-name="h-6 w-56 mb-3" />
          <SkeletonBlock class-name="h-[400px] w-full mb-6" />
          <SkeletonBlock class-name="h-6 w-48 mb-3" />
          <SkeletonBlock class-name="h-[400px] w-full" />
        </div>
      </div>

        <div v-else>
          <div v-if="hasSelectedEvents" class="space-y-6">
            <!-- Courbes de vente en temps réel -->
            <div class="space-y-3">
              <div class="panel p-4">
                <div class="flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-4">
                  <label class="inline-flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" v-model="showCumulative" class="rounded text-blue-600 focus:ring-blue-500" />
                    <span class="text-sm text-zinc-700">Ventes cumulées</span>
                  </label>
                  <label class="inline-flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" v-model="showHourly" class="rounded text-blue-600 focus:ring-blue-500" />
                    <span class="text-sm text-zinc-700">Ventes par période</span>
                  </label>
                </div>
              
                <div class="flex items-center bg-zinc-100 p-1 rounded-lg">
                  <button 
                    @click="viewMode = 'daily'"
                    :class="['px-3 py-1.5 rounded-md text-sm transition-all', viewMode === 'daily' ? 'bg-white shadow text-blue-600 font-medium' : 'text-gray-500 hover:text-gray-700']"
                  >
                    Journalier
                  </button>
                  <button 
                    @click="viewMode = 'weekly'"
                    :class="['px-3 py-1.5 rounded-md text-sm transition-all', viewMode === 'weekly' ? 'bg-white shadow text-blue-600 font-medium' : 'text-gray-500 hover:text-gray-700']"
                  >
                    Hebdomadaire
                  </button>
                </div>
              </div>
              </div>
              <SalesChart 
                :tickets="filteredTickets" 
                :show-cumulative="showCumulative" 
                :show-hourly="showHourly" 
                :view-mode="viewMode"
              />
            </div>

            <!-- Répartition des ventes -->
            <TicketsDistributionChart :tickets="filteredTickets" />
          
            <!-- Localisation géographique -->
            <GeographicMap :tickets="filteredTickets" />
          
            <!-- Panier moyen -->
            <AverageBasket :tickets="filteredTickets" />
          
            <!-- Comparaison mensuelle -->
            <MonthlyComparison :tickets="filteredTickets" />
          </div>
        </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import SalesChart from "../components/SalesChart.vue";
import TicketsDistributionChart from "../components/TicketsDistributionChart.vue";
import GeographicMap from "../components/GeographicMap.vue";
import AverageBasket from "../components/AverageBasket.vue";
import MonthlyComparison from "../components/MonthlyComparison.vue";
import DashboardFilters from "../components/DashboardFilters.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import { TicketsService } from "../services/ticketsService";

// Par défaut, afficher les deux courbes
const showCumulative = ref(true);
const showHourly = ref(true);
const viewMode = ref('daily');

const allTickets = ref([]);
const loading = ref(true);
const filters = ref({
  selectedEvents: [],
  selectedCategories: []
});

const uniqueEvents = computed(() => {
  const eventsMap = new Map();
  allTickets.value.forEach(t => {
    if (t.eventName && !eventsMap.has(t.eventName)) {
      eventsMap.set(t.eventName, t.sessionDate);
    }
  });
  return Array.from(eventsMap.entries())
    .map(([name, date]) => ({ name, date }))
    .sort((a, b) => a.name.localeCompare(b.name));
});

const uniqueCategories = computed(() => {
  const categories = new Set(allTickets.value.map(t => t.ticketCategory).filter(Boolean));
  return Array.from(categories).sort();
});

const filteredTickets = computed(() => {
  // Si aucun événement n'est sélectionné, ne rien afficher
  if (filters.value.selectedEvents.length === 0) {
    return [];
  }

  return allTickets.value.filter(ticket => {
    // Filter by Event
    if (filters.value.selectedEvents.length > 0) {
      if (!filters.value.selectedEvents.includes(ticket.eventName)) {
        return false;
      }
    }

    // Filter by Category
    if (filters.value.selectedCategories.length > 0) {
      if (!filters.value.selectedCategories.includes(ticket.ticketCategory)) {
        return false;
      }
    }

    return true;
  });
});

function handleFiltersUpdate(newFilters) {
  filters.value = newFilters;
}

const hasSelectedEvents = computed(() => filters.value.selectedEvents.length > 0);

let unsubscribe = null;

onMounted(() => {
  unsubscribe = TicketsService.subscribeToAllTickets((tickets) => {
    allTickets.value = tickets;
    loading.value = false;
  });
});

onUnmounted(() => {
  if (unsubscribe) unsubscribe();
});
</script>

<style scoped>
/* Styles globaux si nécessaire */
</style>

