<template>
  <main class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Tableaux de bord - Case à Chocs</h1>
      
      <div class="space-y-6">
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
          <SalesChart :show-cumulative="showCumulative" :show-hourly="showHourly" />
        </div>
        
        <!-- Localisation géographique -->
        <GeographicMap />
        
        <!-- Panier moyen -->
        <AverageBasket />
        
        <!-- Comparaison mensuelle -->
        <MonthlyComparison />
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref } from "vue";
import SalesChart from "../components/SalesChart.vue";
import GeographicMap from "../components/GeographicMap.vue";
import AverageBasket from "../components/AverageBasket.vue";
import MonthlyComparison from "../components/MonthlyComparison.vue";

// Par défaut, afficher les deux courbes
const showCumulative = ref(true);
const showHourly = ref(true);
</script>

<style scoped>
/* Styles globaux si nécessaire */
</style>

