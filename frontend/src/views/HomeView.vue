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
            class="px-4 py-2 rounded-xl border text-sm font-extrabold tracking-wide"
            :class="isEmulator ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-white text-zinc-900 border-zinc-200'"
            :title="isEmulator ? 'Connecté à l\'émulateur Firestore' : 'Connecté à Firestore Cloud'"
          >
            <span class="block text-[11px] font-semibold opacity-80">ENV</span>
            <span class="block leading-tight">{{ isEmulator ? 'LOCAL (Emulator)' : 'PROD (Cloud)' }}</span>
          </div>

          <a
            v-if="isDev"
            class="inline-flex items-center justify-center px-4 py-2 rounded-xl border border-zinc-200 bg-white text-sm font-medium text-zinc-900 hover:bg-zinc-50"
            href="http://127.0.0.1:4000"
            target="_blank"
            rel="noreferrer"
          >
            Ouvrir la console Emulator
          </a>
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
          <router-link to="/overview" class="rounded-xl border border-zinc-200 p-4 bg-white hover:bg-zinc-50">
            <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Overview</div>
            <div class="mt-1 text-base font-bold text-zinc-900">Indicateurs & tendances</div>
            <p class="mt-1 text-sm text-zinc-600">KPIs, top événements, dernières ventes.</p>
          </router-link>

          <router-link to="/dashboard" class="rounded-xl border border-zinc-200 p-4 bg-white hover:bg-zinc-50">
            <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Dashboard</div>
            <div class="mt-1 text-base font-bold text-zinc-900">Graphiques en temps réel</div>
            <p class="mt-1 text-sm text-zinc-600">Courbes, répartition, carte, panier moyen, comparaison mensuelle.</p>
          </router-link>

          <router-link to="/tickets" class="rounded-xl border border-zinc-200 p-4 bg-white hover:bg-zinc-50">
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
                <div class="text-sm font-semibold text-zinc-900">Webhook</div>
                <div class="mt-1 text-sm text-zinc-600">
                  <span v-if="webhook.loading">Lecture Firestore…</span>
                  <span v-else-if="webhook.error">{{ webhook.error }}</span>
                  <span v-else>
                    <span v-if="webhook.lastReceivedAtMs">Dernier webhook reçu il y a {{ webhookAgeMinutes }} min</span>
                    <span v-else>Aucun webhook reçu</span>
                    <span v-if="webhook.lastHttpStatus" class="text-zinc-500"> — HTTP {{ webhook.lastHttpStatus }}</span>
                  </span>
                </div>
              </div>

              <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(webhook.ok, webhook.loading)">
                {{ webhook.loading ? '…' : webhook.ok ? 'OK' : 'KO' }}
              </span>
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
                    {{ tickets.hasData ? 'Au moins 1 document présent' : 'Aucun document trouvé' }}
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
                <div class="text-sm font-semibold text-zinc-900">Navigation</div>
                <div class="mt-1 text-sm text-zinc-600">Accès rapide aux vues de travail</div>
              </div>

              <div class="flex gap-2">
                <router-link to="/tickets" class="px-3 py-1.5 rounded-lg border border-zinc-200 bg-white text-sm font-medium text-zinc-900 hover:bg-zinc-50">
                  Tickets
                </router-link>
                <router-link to="/dashboard" class="px-3 py-1.5 rounded-lg border border-zinc-200 bg-white text-sm font-medium text-zinc-900 hover:bg-zinc-50">
                  Dashboard
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="!checklistComplete" class="panel p-6">
        <div class="text-xs font-semibold uppercase tracking-wide text-zinc-500">Setup checklist</div>
        <div class="mt-1 text-xl font-bold text-zinc-900">Onboarding technique</div>

        <div class="mt-4 space-y-2">
          <div class="flex items-start justify-between gap-4 rounded-xl border border-zinc-200 p-4">
            <div>
              <div class="text-sm font-semibold text-zinc-900">.env.local frontend présent</div>
              <div class="mt-1 text-sm text-zinc-600">Variables Vite Firebase détectées (API key + projectId)</div>
            </div>
            <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(envOk, false)">
              {{ envOk ? 'OK' : 'KO' }}
            </span>
          </div>

          <div class="flex items-start justify-between gap-4 rounded-xl border border-zinc-200 p-4">
            <div>
              <div class="text-sm font-semibold text-zinc-900">Accès Firestore fonctionnel</div>
              <div class="mt-1 text-sm text-zinc-600">Lecture test sur la collection tickets</div>
            </div>
            <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(firestore.connectionOk && firestore.permissionsOk, firestore.loading)">
              {{ firestore.loading ? '…' : (firestore.connectionOk && firestore.permissionsOk) ? 'OK' : 'KO' }}
            </span>
          </div>

          <div class="flex items-start justify-between gap-4 rounded-xl border border-zinc-200 p-4">
            <div>
              <div class="text-sm font-semibold text-zinc-900">Données présentes</div>
              <div class="mt-1 text-sm text-zinc-600">Au moins 1 document dans tickets</div>
            </div>
            <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(tickets.hasData, tickets.loading)">
              {{ tickets.loading ? '…' : tickets.hasData ? 'OK' : 'KO' }}
            </span>
          </div>

          <div class="flex items-start justify-between gap-4 rounded-xl border border-zinc-200 p-4">
            <div>
              <div class="text-sm font-semibold text-zinc-900">Statut webhook (optionnel)</div>
              <div class="mt-1 text-sm text-zinc-600">
                <span v-if="webhook.loading">Lecture…</span>
                <span v-else-if="webhook.lastReceivedAtMs">Dernier webhook il y a {{ webhookAgeMinutes }} min</span>
                <span v-else>Aucun webhook reçu</span>
              </div>
            </div>
            <span class="px-2.5 py-1 rounded-lg text-xs font-bold" :class="statusPillClass(webhook.ok, webhook.loading)">
              {{ webhook.loading ? '…' : webhook.ok ? 'OK' : 'KO' }}
            </span>
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
  doc,
  getDoc,
  getDocs,
  limit,
  orderBy,
  query,
} from "firebase/firestore";

const isDev = import.meta.env.DEV;

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

const firestore = ref({
  loading: true,
  connectionOk: false,
  permissionsOk: false,
  error: "",
});

const tickets = ref({
  loading: true,
  hasData: false,
  error: "",
});

const webhook = ref({
  loading: true,
  ok: false,
  lastReceivedAtMs: null,
  lastHttpStatus: null,
  error: "",
});

const anyLoading = computed(() => firestore.value.loading || tickets.value.loading || webhook.value.loading);

const webhookAgeMinutes = computed(() => {
  if (!webhook.value.lastReceivedAtMs) return null;
  const diffMs = Math.max(0, nowMs.value - webhook.value.lastReceivedAtMs);
  return Math.floor(diffMs / 60000);
});

const checklistComplete = computed(() => {
  const firestoreOk = firestore.value.connectionOk && firestore.value.permissionsOk;
  return envOk.value && firestoreOk && tickets.value.hasData;
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
  tickets.value = { loading: true, hasData: false, error: "" };

  if (!db) {
    firestore.value = { loading: false, connectionOk: false, permissionsOk: false, error: "Firestore non initialisé" };
    tickets.value = { loading: false, hasData: false, error: "Firestore non initialisé" };
    return;
  }

  try {
    const ticketsRef = collection(db, "tickets");
    const q = query(ticketsRef, orderBy("createdAt", "desc"), limit(1));
    const snap = await getDocs(q);

    firestore.value = { loading: false, connectionOk: true, permissionsOk: true, error: "" };
    tickets.value = { loading: false, hasData: !snap.empty, error: "" };
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
      error: permissionDenied ? "Lecture tickets refusée" : "Impossible de lire tickets",
    };
  }
}

async function checkWebhookStatus() {
  webhook.value = { loading: true, ok: false, lastReceivedAtMs: null, lastHttpStatus: null, error: "" };

  if (!db) {
    webhook.value = { loading: false, ok: false, lastReceivedAtMs: null, lastHttpStatus: null, error: "Firestore non initialisé" };
    return;
  }

  try {
    const statusRef = doc(db, "system", "webhookStatus");
    const snap = await getDoc(statusRef);

    if (!snap.exists()) {
      webhook.value = { loading: false, ok: false, lastReceivedAtMs: null, lastHttpStatus: null, error: "Document system/webhookStatus introuvable" };
      return;
    }

    const data = snap.data() ?? {};
    const lastReceivedAtMs =
      toMillis(data.lastReceivedAt) ??
      toMillis(data.lastReceivedAtMs) ??
      toMillis(data.lastReceivedAtMillis) ??
      toMillis(data.last_received_at) ??
      toMillis(data.lastWebhookReceivedAt) ??
      toMillis(data.updatedAt) ??
      null;

    const lastHttpStatus =
      (typeof data.lastHttpStatus === "number" ? data.lastHttpStatus : null) ??
      (typeof data.lastStatusCode === "number" ? data.lastStatusCode : null) ??
      (typeof data.last_http_status === "number" ? data.last_http_status : null) ??
      (typeof data.last_status_code === "number" ? data.last_status_code : null) ??
      null;

    const explicitOk = typeof data.ok === "boolean" ? data.ok : null;
    const statusString = typeof data.status === "string" ? data.status.toLowerCase() : null;

    const ok =
      explicitOk ??
      (statusString ? ["ok", "healthy", "up"].includes(statusString) : null) ??
      (typeof lastHttpStatus === "number" ? lastHttpStatus >= 200 && lastHttpStatus < 300 : null) ??
      !!lastReceivedAtMs;

    webhook.value = {
      loading: false,
      ok,
      lastReceivedAtMs,
      lastHttpStatus,
      error: "",
    };
  } catch (error) {
    webhook.value = {
      loading: false,
      ok: false,
      lastReceivedAtMs: null,
      lastHttpStatus: null,
      error: isPermissionDenied(error) ? "Permissions insuffisantes (webhookStatus)" : "Erreur de lecture webhookStatus",
    };
  }
}

onMounted(async () => {
  nowIntervalId = window.setInterval(() => {
    nowMs.value = Date.now();
  }, 30_000);

  await Promise.all([checkFirestoreAndTickets(), checkWebhookStatus()]);
});

onUnmounted(() => {
  if (nowIntervalId) window.clearInterval(nowIntervalId);
});
</script>
