<template>
  <main class="page">
    <header class="page-header">
      <h1 class="page-title">Ticketing Dashboard</h1>
      <p class="page-subtitle">Une vue claire des ventes — style Case à Chocs, navigation horizontale.</p>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <router-link to="/overview" class="panel p-6 hover:shadow-md transition">
        <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Overview</div>
        <div class="mt-2 text-xl font-bold text-zinc-900">Indicateurs & tendances</div>
        <p class="mt-2 text-sm text-zinc-600">KPIs, top événements, dernières ventes.</p>
      </router-link>

      <router-link to="/dashboard" class="panel p-6 hover:shadow-md transition">
        <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Dashboard</div>
        <div class="mt-2 text-xl font-bold text-zinc-900">Graphiques en temps réel</div>
        <p class="mt-2 text-sm text-zinc-600">Courbes, répartition, carte, panier moyen, comparaison mensuelle.</p>
      </router-link>

      <router-link to="/tickets" class="panel p-6 hover:shadow-md transition">
        <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Tickets</div>
        <div class="mt-2 text-xl font-bold text-zinc-900">Liste & recherche</div>
        <p class="mt-2 text-sm text-zinc-600">Filtrer, trier et explorer les ventes.</p>
      </router-link>
    </div>
  </main>
</template>

<script setup>
// pas de logique pour l’instant
</script>
