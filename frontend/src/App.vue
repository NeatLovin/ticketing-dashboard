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

    <!-- Notification globale (reste visible quelle que soit la page) -->
    <div class="fixed bottom-4 right-4 z-50 pointer-events-none">
      <transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-[6px]"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-[6px]"
      >
        <div
          v-if="saleToast.visible"
          class="pointer-events-auto w-[min(90vw,340px)] overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm"
          role="status"
          aria-live="polite"
        >
          <div class="p-3">
            <div class="flex items-start gap-3">
              <div class="relative mt-0.5 h-9 w-9 shrink-0">
                <div class="absolute inset-0 rounded-full bg-green-600/15" />
                <div class="absolute inset-0 rounded-full ring-1 ring-green-600/30" />
                <div class="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-green-600" />
                <div class="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-green-600 animate-ping opacity-40" />
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <div class="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Billet vendu</div>
                  <span class="inline-flex items-center rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-[10px] font-semibold text-zinc-600">
                    +1 vente
                  </span>
                </div>

                <div class="mt-0.5 text-sm font-semibold text-zinc-900 truncate" :title="saleToast.title">{{ saleToast.title }}</div>
                <div class="mt-0.5 text-xs text-zinc-600">
                  <span class="font-semibold text-green-600">{{ saleToast.amount }}</span>
                  <span v-if="saleToast.when" class="text-zinc-400"> · {{ saleToast.when }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="h-1 bg-zinc-100">
            <div class="toast-progress h-full bg-green-600/70" :style="{ animationDuration: toastDurationMs + 'ms' }" />
          </div>
        </div>
      </transition>
    </div>

    <router-view />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { TicketsService } from "./services/ticketsService";

const TOAST_DURATION_MS = 3200;

const toastDurationMs = TOAST_DURATION_MS;

const saleToast = ref({
  visible: false,
  title: "",
  amount: "",
  when: "",
});

let hideTimer = null;
let unsubscribeSales = null;

function formatCurrency(value) {
  const num = typeof value === "number" ? value : parseFloat(value);
  if (Number.isNaN(num)) return "0.00 CHF";
  return new Intl.NumberFormat("fr-CH", { style: "currency", currency: "CHF" }).format(num);
}

function formatTime(timestamp) {
  const date = TicketsService.toDate(timestamp);
  if (!date) return "";
  return new Intl.DateTimeFormat("fr-CH", { hour: "2-digit", minute: "2-digit" }).format(date);
}

function showSaleToast(ticket) {
  const buyer = `${ticket?.buyerFirstName || ""} ${ticket?.buyerLastName || ""}`.trim();
  const eventName = ticket?.eventName || "Événement";
  const title = buyer ? `${buyer} — ${eventName}` : eventName;

  saleToast.value = {
    visible: true,
    title,
    amount: formatCurrency(ticket?.priceAmount),
    when: formatTime(ticket?.createdAt),
  };

  if (hideTimer) window.clearTimeout(hideTimer);
  hideTimer = window.setTimeout(() => {
    saleToast.value.visible = false;
  }, TOAST_DURATION_MS);
}

onMounted(() => {
  unsubscribeSales = TicketsService.subscribeToNewTicketSales((ticket) => {
    showSaleToast(ticket);
  });
});

onUnmounted(() => {
  if (unsubscribeSales) unsubscribeSales();
  if (hideTimer) window.clearTimeout(hideTimer);
});
</script>

<style scoped>
@keyframes toast-progress {
  from {
    transform: scaleX(1);
  }
  to {
    transform: scaleX(0);
  }
}

.toast-progress {
  transform-origin: left;
  animation-name: toast-progress;
  animation-timing-function: linear;
  animation-fill-mode: forwards;
}
</style>
