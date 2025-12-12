<template>
  <main class="min-h-screen bg-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">Vue d'ensemble</h1>

      <div v-if="loading" class="text-center py-10">
        <p class="text-gray-500">Chargement des données...</p>
      </div>

      <div v-else class="space-y-6">
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Total Revenue -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Chiffre d'affaires</p>
                <p class="text-2xl font-bold text-gray-800">{{ formatCurrency(totalRevenue) }}</p>
              </div>
              <div class="p-3 bg-green-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Total Tickets -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Billets vendus</p>
                <p class="text-2xl font-bold text-gray-800">{{ totalTickets }}</p>
              </div>
              <div class="p-3 bg-blue-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Total Events -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-purple-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Événements</p>
                <p class="text-2xl font-bold text-gray-800">{{ totalEvents }}</p>
              </div>
              <div class="p-3 bg-purple-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Avg Ticket Price -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-orange-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Prix moyen billet</p>
                <p class="text-2xl font-bold text-gray-800">{{ formatCurrency(averageTicketPrice) }}</p>
              </div>
              <div class="p-3 bg-orange-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Peak Sales Time -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-pink-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Pic de ventes</p>
                <p class="text-2xl font-bold text-gray-800">{{ peakSalesTime }}</p>
              </div>
              <div class="p-3 bg-pink-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-pink-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Avg Lead Time -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-teal-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Délai moyen d'achat</p>
                <p class="text-2xl font-bold text-gray-800">{{ avgLeadTime }} jours</p>
              </div>
              <div class="p-3 bg-teal-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Presale Percentage -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-indigo-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm text-gray-500 uppercase font-semibold">Prélocations</p>
                <p class="text-2xl font-bold text-gray-800">{{ presalePercentage }}%</p>
              </div>
              <div class="p-3 bg-indigo-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Top Locations -->
          <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-yellow-500">
            <div class="flex items-center justify-between mb-2">
              <p class="text-sm text-gray-500 uppercase font-semibold">Top Localités</p>
              <div class="p-2 bg-yellow-100 rounded-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
            </div>
            <ul class="space-y-1">
              <li v-for="loc in topLocations" :key="loc.zip" class="flex justify-between text-sm">
                <span class="text-gray-600 font-medium">{{ loc.zip }}</span>
                <span class="text-gray-800 font-bold">{{ loc.count }}</span>
              </li>
              <li v-if="topLocations.length === 0" class="text-sm text-gray-500">N/A</li>
            </ul>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Top Events -->
          <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="p-6 border-b border-gray-100">
              <h2 class="text-xl font-bold text-gray-800">Top Événements (Chiffre d'affaires)</h2>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-sm text-gray-600">
                <thead class="bg-gray-50 text-gray-700 uppercase font-semibold">
                  <tr>
                    <th class="px-6 py-3">Événement</th>
                    <th class="px-6 py-3 text-right">Billets</th>
                    <th class="px-6 py-3 text-right">CA</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="event in topEvents" :key="event.name" class="hover:bg-gray-50 transition">
                    <td class="px-6 py-4 font-medium text-gray-900 truncate max-w-xs" :title="event.name">
                      {{ event.name }}
                    </td>
                    <td class="px-6 py-4 text-right">{{ event.count }}</td>
                    <td class="px-6 py-4 text-right font-semibold text-green-600">
                      {{ formatCurrency(event.revenue) }}
                    </td>
                  </tr>
                  <tr v-if="topEvents.length === 0">
                    <td colspan="3" class="px-6 py-4 text-center text-gray-500">Aucun événement</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Recent Sales -->
          <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="p-6 border-b border-gray-100">
              <h2 class="text-xl font-bold text-gray-800">Dernières ventes</h2>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-left text-sm text-gray-600">
                <thead class="bg-gray-50 text-gray-700 uppercase font-semibold">
                  <tr>
                    <th class="px-6 py-3">Acheteur</th>
                    <th class="px-6 py-3">Événement</th>
                    <th class="px-6 py-3 text-right">Montant</th>
                    <th class="px-6 py-3 text-right">Date</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                  <tr v-for="ticket in recentTickets" :key="ticket.id" class="hover:bg-gray-50 transition">
                    <td class="px-6 py-4">
                      <div class="font-medium text-gray-900">
                        {{ ticket.buyerFirstName }} {{ ticket.buyerLastName }}
                      </div>
                      <div class="text-xs text-gray-500">{{ ticket.category }}</div>
                    </td>
                    <td class="px-6 py-4 truncate max-w-xs" :title="ticket.eventName">
                      {{ ticket.eventName }}
                    </td>
                    <td class="px-6 py-4 text-right font-semibold">
                      {{ formatCurrency(ticket.priceAmount) }}
                    </td>
                    <td class="px-6 py-4 text-right text-xs text-gray-500">
                      {{ formatDate(ticket.createdAt) }}
                    </td>
                  </tr>
                  <tr v-if="recentTickets.length === 0">
                    <td colspan="4" class="px-6 py-4 text-center text-gray-500">Aucune vente récente</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { TicketsService } from '../services/ticketsService';

const tickets = ref([]);
const loading = ref(true);
let unsubscribe = null;

onMounted(() => {
  unsubscribe = TicketsService.subscribeToAllTickets((data) => {
    tickets.value = data;
    loading.value = false;
  });
});

onUnmounted(() => {
  if (unsubscribe) unsubscribe();
});

// Helpers
const formatCurrency = (value) => {
  const num = parseFloat(value);
  if (isNaN(num)) return '0.00 CHF';
  return new Intl.NumberFormat('fr-CH', { style: 'currency', currency: 'CHF' }).format(num);
};

const formatDate = (timestamp) => {
  if (!timestamp) return '';
  // Handle Firestore Timestamp or string/number
  const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
  return new Intl.DateTimeFormat('fr-CH', { 
    day: '2-digit', 
    month: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  }).format(date);
};

// KPIs
const totalTickets = computed(() => tickets.value.length);

const totalRevenue = computed(() => {
  return tickets.value.reduce((sum, t) => sum + (parseFloat(t.priceAmount) || 0), 0);
});

const totalEvents = computed(() => {
  const events = new Set(tickets.value.map(t => t.eventName).filter(Boolean));
  return events.size;
});

const averageTicketPrice = computed(() => {
  if (totalTickets.value === 0) return 0;
  return totalRevenue.value / totalTickets.value;
});

const peakSalesTime = computed(() => {
  if (tickets.value.length === 0) return 'N/A';

  const slots = {};

  tickets.value.forEach(t => {
    const timestamp = t.createdAt;
    if (!timestamp) return;
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
    
    // Day of week (0-6, 0=Sunday)
    const day = date.getDay(); 
    // Hour (0-23)
    const hour = date.getHours();
    
    const key = `${day}-${hour}`;
    slots[key] = (slots[key] || 0) + 1;
  });

  let maxKey = null;
  let maxCount = 0;

  for (const [key, count] of Object.entries(slots)) {
    if (count > maxCount) {
      maxCount = count;
      maxKey = key;
    }
  }

  if (!maxKey) return 'N/A';

  const [dayStr, hourStr] = maxKey.split('-');
  const dayIndex = parseInt(dayStr);
  const hour = parseInt(hourStr);

  const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
  
  return `${days[dayIndex]} ${hour}h`;
});

const avgLeadTime = computed(() => {
  if (tickets.value.length === 0) return 0;
  
  let totalDays = 0;
  let count = 0;
  
  tickets.value.forEach(t => {
    if (t.generatedAt && t.sessionDate) {
      const purchaseDate = new Date(t.generatedAt);
      const eventDate = new Date(t.sessionDate);
      
      // Difference in milliseconds
      const diffTime = eventDate - purchaseDate;
      // Difference in days
      const diffDays = diffTime / (1000 * 60 * 60 * 24);
      
      if (!isNaN(diffDays)) {
        totalDays += diffDays;
        count++;
      }
    }
  });
  
  return count > 0 ? Math.round(totalDays / count) : 0;
});

const presalePercentage = computed(() => {
  if (tickets.value.length === 0) return 0;
  
  // Check both ticketCategory (backend) and category (potential frontend legacy)
  const presaleCount = tickets.value.filter(t => {
    const cat = t.ticketCategory || t.category;
    return cat === 'Prélocation';
  }).length;
  
  return Math.round((presaleCount / tickets.value.length) * 100);
});

const topLocations = computed(() => {
  const counts = {};
  tickets.value.forEach(t => {
    const zip = t.buyerPostcode;
    if (zip) {
      counts[zip] = (counts[zip] || 0) + 1;
    }
  });
  
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([zip, count]) => ({ zip, count }));
});

// Top Events
const topEvents = computed(() => {
  const eventsMap = {};
  
  tickets.value.forEach(t => {
    const name = t.eventName || 'Inconnu';
    if (!eventsMap[name]) {
      eventsMap[name] = { name, count: 0, revenue: 0 };
    }
    eventsMap[name].count++;
    eventsMap[name].revenue += (parseFloat(t.priceAmount) || 0);
  });

  return Object.values(eventsMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 5);
});

// Recent Sales
const recentTickets = computed(() => {
  // Assuming tickets are already sorted by createdAt desc from the service
  return tickets.value.slice(0, 10);
});
</script>
