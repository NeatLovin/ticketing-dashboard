<template>
  <div>
    <nav class="bg-blue-600 text-white p-4 shadow-md">
      <div class="max-w-7xl mx-auto flex gap-4">
        <router-link 
          to="/" 
          class="px-4 py-2 rounded hover:bg-blue-700 transition"
          active-class="bg-blue-800"
        >
          Accueil
        </router-link>
        <router-link 
          to="/overview" 
          class="px-4 py-2 rounded hover:bg-blue-700 transition"
          active-class="bg-blue-800"
        >
          Vue d'ensemble
        </router-link>
        <router-link 
          to="/dashboard" 
          class="px-4 py-2 rounded hover:bg-blue-700 transition"
          active-class="bg-blue-800"
        >
          Tableaux de bord
        </router-link>
        <router-link 
          to="/tickets" 
          class="px-4 py-2 rounded hover:bg-blue-700 transition"
          active-class="bg-blue-800"
        >
          Liste des tickets
        </router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup></script>

<style scoped>
/* Styles pour la navigation */
</style>
