<template>
  <main class="p-6 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-4">Ticketing Dashboard</h1>
    <p class="mb-6 text-lg">
      Bienvenue sur le dashboard de billetterie de la Case à Chocs.
    </p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <router-link 
        to="/overview" 
        class="bg-indigo-600 text-white p-6 rounded-lg shadow-md hover:bg-indigo-700 transition"
      >
        <h2 class="text-xl font-bold mb-2">🔍 Vue d'ensemble</h2>
        <p class="text-sm">
          Indicateurs clés de performance (KPI), événements populaires et ventes récentes.
        </p>
      </router-link>

      <router-link 
        to="/dashboard" 
        class="bg-blue-500 text-white p-6 rounded-lg shadow-md hover:bg-blue-600 transition"
      >
        <h2 class="text-xl font-bold mb-2">📊 Tableaux de bord</h2>
        <p class="text-sm">
          Visualisez les statistiques en temps réel : courbes de vente, localisation géographique, panier moyen et comparaisons mensuelles.
        </p>
      </router-link>

      <router-link 
        to="/tickets" 
        class="bg-green-500 text-white p-6 rounded-lg shadow-md hover:bg-green-600 transition"
      >
        <h2 class="text-xl font-bold mb-2">🎫 Liste des tickets</h2>
        <p class="text-sm">
          Consultez la liste détaillée de tous les tickets vendus.
        </p>
      </router-link>
    </div>
  </main>
</template>

<script setup>
// pas de logique pour l’instant
</script>
