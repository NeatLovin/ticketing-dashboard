<template>
  <main class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Tableaux de bord - Case à Chocs</h1>
      
      <DashboardFilters 
        :events="uniqueEvents" 
        :categories="uniqueCategories"
        @update:filters="handleFiltersUpdate"
      />

      <div v-if="loading" class="text-center py-10">
        <p class="text-gray-500">Chargement des données...</p>
      </div>

      <div v-else class="space-y-6">
        <!-- Courbes de vente en temps réel -->
        <div class="bg-white p-4 rounded-lg shadow">
          <div class="mb-3 flex items-center gap-4">
            <label class="inline-flex items-center gap-2">
              <input type="checkbox" v-model="showCumulative" />
              <span>Ventes cumulées</span>
            </label>
            <label class="inline-flex items-center gap-2">
              <input type="checkbox" v-model="showHourly" />
              <span>Ventes par heure</span>
            </label>
          </div>
          <SalesChart 
            :tickets="filteredTickets" 
            :show-cumulative="showCumulative" 
            :show-hourly="showHourly" 
          />
        </div>
        
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
import GeographicMap from "../components/GeographicMap.vue";
import AverageBasket from "../components/AverageBasket.vue";
import MonthlyComparison from "../components/MonthlyComparison.vue";
import DashboardFilters from "../components/DashboardFilters.vue";
import { TicketsService } from "../services/ticketsService";

// Par défaut, afficher les deux courbes
const showCumulative = ref(true);
const showHourly = ref(true);

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
  // Si aucun filtre n'est actif, ne rien afficher
  if (
    filters.value.selectedEvents.length === 0 &&
    filters.value.selectedCategories.length === 0
  ) {
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

