<template>
  <main class="page">
    <header class="page-header">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="page-title">Centre de contrôle</h1>
          <p class="page-subtitle">État du système — environnement, Firestore, webhooks.</p>
        </div>

        <div class="flex items-center gap-3">
          <div
            class="badge px-4 py-2 font-extrabold tracking-wide"
            :class="isEmulator ? 'badge-dark' : 'badge-outline'"
            :title="isEmulator ? 'Connecté à l\'émulateur Firestore' : 'Connecté à Firestore Cloud'"
          >
            <span class="block text-[11px] font-semibold opacity-80">ENV</span>
            <span class="block leading-tight">{{ isEmulator ? 'LOCAL (Emulator)' : 'PROD (Cloud)' }}</span>
          </div>

          <a
            v-if="isDev"
            class="btn-secondary"
            href="http://127.0.0.1:4000"
            target="_blank"
            rel="noreferrer"
          >
            Ouvrir la console Emulator
          </a>

          <button
            v-if="isDev"
            type="button"
            class="btn-secondary"
            @click="clearLocalStorageCache"
            title="Supprime tout le localStorage puis recharge la page"
          >
            Vider le cache (local)
          </button>
        </div>
      </div>
    </header>

    <div class="space-y-6">
      <section class="panel p-6">
        <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Application</div>
        <div class="mt-1 text-xl font-bold text-zinc-900">Ticketing Dashboard</div>
        <div class="mt-2 text-sm text-zinc-600 space-y-3">
          <p>
            Ticketing Dashboard est une application de supervision et d’analyse des ventes de billets.
          </p>
          <p>
            Elle s’appuie sur des webhooks Petzi pour recevoir les événements (créations/ventes, mises à jour, etc.),
            les normaliser côté backend Firebase (Functions), puis les persister dans Firestore.
          </p>

          <div>
            <div class="text-sm font-semibold text-zinc-800">Ce que le frontend apporte</div>
            <ul class="mt-1 list-disc pl-5 space-y-1">
              <li>État de l’environnement (LOCAL/PROD) et santé du pipeline webhook → Firestore</li>
              <li>Vérification d’accès Firestore (connexion + permissions) et présence de données</li>
              <li>Accès aux vues de travail pour analyser, explorer et investiguer les ventes</li>
            </ul>
          </div>

          <p>
            L’objectif est double : garantir que le système “ingestion → stockage → visualisation” fonctionne en continu,
            et offrir une lecture rapide des tendances/volumes (overview, dashboard) ainsi qu’une vue opérationnelle (tickets)
            pour valider et corriger rapidement en cas d’anomalie.
          </p>
        </div>

        <div class="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
          <router-link to="/overview" class="link-card">
            <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Overview</div>
            <div class="mt-1 text-base font-bold text-zinc-900">Indicateurs & tendances</div>
            <p class="mt-1 text-sm text-zinc-600">KPIs, top événements, dernières ventes.</p>
          </router-link>

          <router-link to="/dashboard" class="link-card">
            <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Dashboard</div>
            <div class="mt-1 text-base font-bold text-zinc-900">Graphiques en temps réel</div>
            <p class="mt-1 text-sm text-zinc-600">Courbes, répartition, carte, panier moyen, comparaison mensuelle.</p>
          </router-link>

          <router-link to="/tickets" class="link-card">
            <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Tickets</div>
            <div class="mt-1 text-base font-bold text-zinc-900">Liste & recherche</div>
            <p class="mt-1 text-sm text-zinc-600">Filtrer, trier et explorer les ventes.</p>
          </router-link>
        </div>
      </section>

      <section class="panel p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Health / Status</div>
            <div class="mt-1 text-xl font-bold text-zinc-900">État du système</div>
          </div>

          <div v-if="anyLoading" class="text-sm text-zinc-500">Vérification en cours…</div>
        </div>

        <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="rounded-xl border border-zinc-200 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-zinc-900">Vérifications</div>
                <div class="mt-1 text-sm text-zinc-600">
                  <span v-if="anyLoading">Vérification en cours…</span>
                  <span v-else>
                    <span v-if="healthCheckAgeMinutes !== null">Dernière vérification il y a {{ healthCheckAgeMinutes }} min</span>
                    <span v-else>Jamais vérifié</span>
                  </span>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="btn-secondary"
                  :disabled="anyLoading"
                  @click="runHealthChecks"
                  title="Relance les vérifications Firestore + tickets"
                >
                  Rafraîchir
                </button>

                <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(firestore.connectionOk && firestore.permissionsOk, anyLoading)">
                  {{ anyLoading ? '…' : (firestore.connectionOk && firestore.permissionsOk) ? 'OK' : 'KO' }}
                </span>
              </div>
            </div>
          </div>

          <div class="rounded-xl border border-zinc-200 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-zinc-900">Firestore</div>
                <div class="mt-1 text-sm text-zinc-600">
                  <span v-if="firestore.loading">Lecture test…</span>
                  <span v-else-if="firestore.error">{{ firestore.error }}</span>
                  <span v-else>
                    Connexion {{ firestore.connectionOk ? 'OK' : 'KO' }} — Permissions {{ firestore.permissionsOk ? 'OK' : 'KO' }}
                  </span>
                </div>
              </div>

              <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(firestore.connectionOk && firestore.permissionsOk, firestore.loading)">
                {{ firestore.loading ? '…' : (firestore.connectionOk && firestore.permissionsOk) ? 'OK' : 'KO' }}
              </span>
            </div>
          </div>

          <div class="rounded-xl border border-zinc-200 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-zinc-900">Données (tickets)</div>
                <div class="mt-1 text-sm text-zinc-600">
                  <span v-if="tickets.loading">Vérification…</span>
                  <span v-else-if="tickets.error">{{ tickets.error }}</span>
                  <span v-else>
                    <span v-if="tickets.hasData">
                      Au moins 1 document présent
                      <span v-if="tickets.lastCreatedAtMs" class="text-zinc-500">— dernier il y a {{ ticketAgeMinutes }} min</span>
                    </span>
                    <span v-else>Aucun document trouvé</span>
                  </span>
                </div>
              </div>

              <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(tickets.hasData, tickets.loading)">
                {{ tickets.loading ? '…' : tickets.hasData ? 'OK' : 'KO' }}
              </span>
            </div>
          </div>

          <div class="rounded-xl border border-zinc-200 p-4">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-zinc-900">.env.local frontend</div>
                <div class="mt-1 text-sm text-zinc-600">
                  <span v-if="envOk">Variables Vite Firebase détectées (API key + projectId)</span>
                  <span v-else>
                    Variables manquantes. Crée/complète <span class="font-semibold">frontend/.env.local</span> puis redémarre le serveur.
                  </span>
                  <div class="mt-1 text-zinc-500">
                    Cible Firestore : <span class="font-semibold">{{ isEmulator ? 'LOCAL (Emulator)' : 'PROD (Cloud)' }}</span>
                  </div>
                </div>
              </div>

              <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(envOk, false)">
                {{ envOk ? 'OK' : 'KO' }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { db } from "../firebase";
import {
  collection,
  getDocs,
  limit,
  orderBy,
  query,
} from "firebase/firestore";

const isDev = import.meta.env.DEV;

function clearLocalStorageCache() {
  try {
    window.localStorage.clear();
  } catch {
    // ignore
  }
  window.location.reload();
}

const envOk = computed(() => {
  const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;
  const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID;

  const hasApiKey = !!apiKey && apiKey !== "undefined";
  const hasProjectId = !!projectId && projectId !== "undefined";

  return hasApiKey && hasProjectId;
});

function isPermissionDenied(error) {
  return error?.code === "permission-denied" || /permission[- ]denied/i.test(String(error?.message ?? ""));
}

function isConnectionUnavailable(error) {
  return (
    error?.code === "unavailable" ||
    error?.code === "failed-precondition" ||
    /unavailable|failed[- ]precondition|network/i.test(String(error?.message ?? ""))
  );
}

function getFirestoreHost(database) {
  try {
    const settings = database?._settings ?? database?._delegate?._settings;
    return settings?.host ?? null;
  } catch {
    return null;
  }
}

const isEmulator = computed(() => {
  const host = getFirestoreHost(db);
  if (!host) return false;
  return host.includes("127.0.0.1") || host.includes("localhost");
});

function statusPillClass(ok, loading) {
  if (loading) return "bg-zinc-100 text-zinc-700";
  return ok ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800";
}

const nowMs = ref(Date.now());
let nowIntervalId;

const lastHealthCheckAtMs = ref(null);

const firestore = ref({
  loading: true,
  connectionOk: false,
  permissionsOk: false,
  error: "",
});

const tickets = ref({
  loading: true,
  hasData: false,
  lastCreatedAtMs: null,
  error: "",
});

const anyLoading = computed(() => firestore.value.loading || tickets.value.loading);

const healthCheckAgeMinutes = computed(() => {
  if (!lastHealthCheckAtMs.value) return null;
  const diffMs = Math.max(0, nowMs.value - lastHealthCheckAtMs.value);
  return Math.floor(diffMs / 60000);
});

const ticketAgeMinutes = computed(() => {
  if (!tickets.value.lastCreatedAtMs) return null;
  const diffMs = Math.max(0, nowMs.value - tickets.value.lastCreatedAtMs);
  return Math.floor(diffMs / 60000);
});


function toMillis(value) {
  if (!value) return null;
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = Date.parse(value);
    return Number.isNaN(parsed) ? null : parsed;
  }
  if (typeof value?.toDate === "function") {
    return value.toDate().getTime();
  }
  if (typeof value?.seconds === "number") {
    return value.seconds * 1000;
  }
  return null;
}

async function checkFirestoreAndTickets() {
  firestore.value = { loading: true, connectionOk: false, permissionsOk: false, error: "" };
  tickets.value = { loading: true, hasData: false, lastCreatedAtMs: null, error: "" };

  if (!db) {
    firestore.value = { loading: false, connectionOk: false, permissionsOk: false, error: "Firestore non initialisé" };
    tickets.value = { loading: false, hasData: false, error: "Firestore non initialisé" };
    return;
  }

  try {
    const ticketsRef = collection(db, "tickets");
    const q = query(ticketsRef, orderBy("createdAt", "desc"), limit(1));
    const snap = await getDocs(q);

    const lastCreatedAtMs = !snap.empty ? toMillis(snap.docs[0]?.data()?.createdAt) : null;

    firestore.value = { loading: false, connectionOk: true, permissionsOk: true, error: "" };
    tickets.value = { loading: false, hasData: !snap.empty, lastCreatedAtMs, error: "" };
  } catch (error) {
    const permissionDenied = isPermissionDenied(error);
    const unavailable = isConnectionUnavailable(error);

    firestore.value = {
      loading: false,
      connectionOk: !unavailable,
      permissionsOk: !permissionDenied && !unavailable,
      error: permissionDenied
        ? "Permissions insuffisantes (permission-denied)"
        : unavailable
          ? "Connexion indisponible (unavailable)"
          : "Erreur lors de la lecture test",
    };

    tickets.value = {
      loading: false,
      hasData: false,
      lastCreatedAtMs: null,
      error: permissionDenied ? "Lecture tickets refusée" : "Impossible de lire tickets",
    };
  }
}

async function runHealthChecks() {
  await checkFirestoreAndTickets();
  lastHealthCheckAtMs.value = Date.now();
}

onMounted(async () => {
  nowIntervalId = window.setInterval(() => {
    nowMs.value = Date.now();
  }, 30_000);

  await runHealthChecks();
});

onUnmounted(() => {
  if (nowIntervalId) window.clearInterval(nowIntervalId);
});
</script>
