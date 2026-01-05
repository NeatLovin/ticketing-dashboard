<template>
  <div class="app-shell">
    <header class="app-nav">
      <div class="app-nav-inner">
        <div class="app-brand">
          <img src="/cac-logo-white.svg" alt="Case à Chocs" class="h-9 w-auto" />
          <div class="min-w-0">
            <div class="app-brand-title">Ticketing Dashboard</div>
            <div class="text-[11px] text-zinc-400 truncate">Case à Chocs — ventes & billetterie</div>
          </div>
        </div>

        <div class="flex-1" />

        <nav class="app-links" aria-label="Navigation principale">
          <router-link to="/" class="app-link" active-class="app-link-active">Accueil</router-link>
          <router-link to="/overview" class="app-link" active-class="app-link-active">Overview</router-link>
          <router-link to="/dashboard" class="app-link" active-class="app-link-active">Dashboard</router-link>
          <router-link to="/tickets" class="app-link" active-class="app-link-active">Tickets</router-link>
          <a
            href="https://case-a-chocs.ch/"
            class="app-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            Site officiel
          </a>
        </nav>
      </div>
    </header>

    <router-view />
  </div>
</template>

<script setup></script>

<style scoped>
</style>
