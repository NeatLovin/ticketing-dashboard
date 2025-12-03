<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Localisation géographique des clients</h2>
    
    <div class="mb-4">
      <label class="block text-sm font-medium mb-2">Filtrer par date de session :</label>
      <input 
        type="date" 
        v-model="selectedDate" 
        @change="onDateChange"
        class="border rounded px-3 py-2"
      />
      <button 
        @click="clearFilter"
        class="ml-2 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
      >
        Afficher tout
      </button>
    </div>

    <div v-if="loading" class="text-center py-8">Chargement des données...</div>
    <div v-else-if="error" class="text-red-600 py-8">Erreur : {{ error }}</div>
    <div v-else>
      <div ref="mapContainer" id="map" class="w-full" style="height: 500px"></div>
      <div class="mt-4 text-sm text-gray-600">
        <p>Total de clients localisés : {{ localizedTickets.length }}</p>
        <p v-if="selectedDate">Pour la date : {{ selectedDate }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { TicketsService } from "../services/ticketsService";

// Fix pour les icônes Leaflet avec Vite
import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: iconUrl,
  iconRetinaUrl: iconRetinaUrl,
  shadowUrl: shadowUrl,
});

const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const selectedDate = ref("");
const unsubscribe = ref(null);
const mapContainer = ref(null);
let map = null;
let markers = [];

// Filtrer les tickets avec localisation (utiliser buyerPostcode du code postal de l'acheteur)
const localizedTickets = computed(() => {
  let filtered = tickets.value.filter(
    (ticket) => ticket.buyerPostcode && ticket.buyerPostcode.trim() !== ""
  );

  if (selectedDate.value) {
    filtered = filtered.filter((ticket) => ticket.sessionDate === selectedDate.value);
  }

  return filtered;
});

// Grouper par code postal de l'acheteur (buyerPostcode) pour éviter trop de marqueurs
const groupedByPostcode = computed(() => {
  const grouped = {};
  localizedTickets.value.forEach((ticket) => {
    const postcode = ticket.buyerPostcode.trim();
    if (!grouped[postcode]) {
      grouped[postcode] = {
        postcode,
        count: 0,
        tickets: [],
        // Note: on n'a pas de city pour l'acheteur, on utilisera le code postal
      };
    }
    grouped[postcode].count++;
    grouped[postcode].tickets.push(ticket);
  });
  return grouped;
});

async function geocodePostcode(postcode) {
  // Utilisation de l'API Nominatim (OpenStreetMap) pour géocoder les codes postaux
  // Note: En production, utilisez une API payante ou un service dédié
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?postalcode=${postcode}&country=ch&format=json&limit=1`,
      {
        headers: {
          "User-Agent": "CaseAChocs-Dashboard/1.0",
        },
      }
    );
    const data = await response.json();
    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
      };
    }
  } catch (err) {
    console.error(`Erreur géocodage pour ${postcode}:`, err);
  }
  return null;
}

async function updateMap() {
  if (!map) return;

  // Supprimer les anciens marqueurs
  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];

  const grouped = groupedByPostcode.value;
  const coordinates = [];

  // Géocoder et ajouter les marqueurs
  for (const [postcode, data] of Object.entries(grouped)) {
    const coords = await geocodePostcode(postcode);
    if (coords) {
      coordinates.push(coords);
      const marker = L.marker([coords.lat, coords.lon])
        .addTo(map)
        .bindPopup(
          `<strong>Code postal: ${postcode}</strong><br>` +
            `Nombre de clients: ${data.count}<br>` +
            `Nombre de tickets: ${data.tickets.length}`
        );
      markers.push(marker);
    }

    // Limiter le nombre de requêtes pour éviter le rate limiting
    if (markers.length >= 50) break;
  }

  // Ajuster la vue de la carte
  if (coordinates.length > 0) {
    const bounds = L.latLngBounds(coordinates);
    map.fitBounds(bounds, { padding: [50, 50] });
  } else {
    // Vue par défaut sur Neuchâtel
    map.setView([46.9928, 6.9319], 10);
  }
}

function onDateChange() {
  nextTick(() => {
    updateMap();
  });
}

function clearFilter() {
  selectedDate.value = "";
  nextTick(() => {
    updateMap();
  });
}

function setupSubscription() {
  if (unsubscribe.value) {
    unsubscribe.value();
  }

  loading.value = true;
  error.value = null;

  if (selectedDate.value) {
    unsubscribe.value = TicketsService.subscribeToSessionTickets(
      selectedDate.value,
      (newTickets, err) => {
        if (err) {
          error.value = err.message;
          loading.value = false;
        } else {
          tickets.value = newTickets;
          loading.value = false;
          nextTick(() => {
            updateMap();
          });
        }
      }
    );
  } else {
    unsubscribe.value = TicketsService.subscribeToAllTickets(
      (newTickets, err) => {
        if (err) {
          error.value = err.message;
          loading.value = false;
        } else {
          tickets.value = newTickets;
          loading.value = false;
          nextTick(() => {
            updateMap();
          });
        }
      }
    );
  }
}

watch(selectedDate, () => {
  setupSubscription();
});

function initializeMap() {
  if (!mapContainer.value || map) return;
  
  // Initialiser la carte Leaflet
  map = L.map(mapContainer.value).setView([46.9928, 6.9319], 10); // Neuchâtel par défaut

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);
}

// Watcher pour initialiser la carte quand l'élément est disponible
watch([loading, mapContainer], () => {
  if (!loading.value && mapContainer.value && !map) {
    nextTick(() => {
      // Vérifier que l'élément est bien dans le DOM
      if (mapContainer.value && mapContainer.value.offsetParent !== null) {
        initializeMap();
        if (map) {
          updateMap();
        }
      }
    });
  }
}, { immediate: true, flush: 'post' });

onMounted(async () => {
  await nextTick();
  setupSubscription();
  
  // Tentative supplémentaire d'initialisation après un court délai
  setTimeout(() => {
    if (!map && mapContainer.value && !loading.value) {
      initializeMap();
      if (map) {
        updateMap();
      }
    }
  }, 100);
});

onUnmounted(() => {
  if (unsubscribe.value) {
    unsubscribe.value();
  }
  if (map) {
    map.remove();
  }
});
</script>

<style scoped>
/* Styles pour la carte */
</style>

