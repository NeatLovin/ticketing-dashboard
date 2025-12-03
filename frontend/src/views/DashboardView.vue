<template>
  <main class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Tableaux de bord - Case à Chocs</h1>
      
      <div class="space-y-6">
        <!-- Courbes de vente en temps réel -->
        <SalesChart />
        
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
import SalesChart from "../components/SalesChart.vue";
import GeographicMap from "../components/GeographicMap.vue";
import AverageBasket from "../components/AverageBasket.vue";
import MonthlyComparison from "../components/MonthlyComparison.vue";
</script>

<style scoped>
/* Styles globaux si nécessaire */
</style>

