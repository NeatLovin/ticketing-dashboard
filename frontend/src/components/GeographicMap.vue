<template>
  <div class="panel p-6">
    <h2 class="text-xl font-bold mb-4">Localisation géographique des clients</h2>
    
    <div>
      <div ref="mapContainer" id="map" class="w-full" style="height: 500px"></div>
      <div class="mt-4 text-sm text-zinc-600">
        <p>Total de clients localisés : {{ localizedTickets.length }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

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

const props = defineProps({
  tickets: { type: Array, default: () => [] }
});

const mapContainer = ref(null);
let map = null;
let markerClusterLayer = null;
let hasAutoFitted = false;
let updateRunId = 0;

// Permet un "drill-down" : on n'affiche pas tous les sous-groupes d'un coup.
// L'utilisateur clique sur une zone pour zoomer et charger une granularité plus fine.
const focusPrefix = ref("");

const GEOCODE_CACHE_STORAGE_KEY = "ticketing_dashboard_geocode_ch_v1";
const geocodeCache = new Map();
let lastGeocodeRequestAtMs = 0;
const geocodeInFlight = new Map();
let persistCacheTimeoutId = null;

const MAX_BACKGROUND_GEOCODES_PER_RENDER = 3;

// Centroids approximatifs par grande région (1er chiffre du code postal CH)
const APPROX_REGION_CENTROIDS = {
  "1": { lat: 46.52, lon: 6.63 },  // Lausanne / Vaud
  "2": { lat: 46.99, lon: 6.93 },  // Neuchâtel / Jura
  "3": { lat: 46.95, lon: 7.44 },  // Berne
  "4": { lat: 47.56, lon: 7.59 },  // Bâle
  "5": { lat: 47.39, lon: 8.05 },  // Argovie
  "6": { lat: 47.05, lon: 8.31 },  // Lucerne
  "7": { lat: 47.42, lon: 9.38 },  // St-Gall / Grisons
  "8": { lat: 47.38, lon: 8.54 },  // Zurich
  "9": { lat: 47.42, lon: 9.37 },  // Appenzell (proche)
  "0": { lat: 46.80, lon: 8.23 },  // fallback CH centre
};

function loadGeocodeCache() {
  try {
    const raw = localStorage.getItem(GEOCODE_CACHE_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return;
    Object.entries(parsed).forEach(([postcode, coords]) => {
      if (!coords || typeof coords !== "object") return;
      const lat = Number(coords.lat);
      const lon = Number(coords.lon);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      geocodeCache.set(postcode, { lat, lon });
    });
  } catch {
    // ignore
  }
}

function persistGeocodeCache() {
  if (persistCacheTimeoutId) clearTimeout(persistCacheTimeoutId);
  persistCacheTimeoutId = setTimeout(() => {
    persistCacheTimeoutId = null;
    try {
      const obj = {};
      geocodeCache.forEach((coords, postcode) => {
        obj[postcode] = coords;
      });
      localStorage.setItem(GEOCODE_CACHE_STORAGE_KEY, JSON.stringify(obj));
    } catch {
      // ignore
    }
  }, 500);
}

function persistGeocodeCacheImmediate() {
  try {
    const obj = {};
    geocodeCache.forEach((coords, postcode) => {
      obj[postcode] = coords;
    });
    localStorage.setItem(GEOCODE_CACHE_STORAGE_KEY, JSON.stringify(obj));
  } catch {
    // ignore
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizePostcode(value) {
  if (value == null) return "";
  return String(value).trim().replace(/\s+/g, "");
}

function digitsOnly(value) {
  return String(value).replace(/\D+/g, "");
}

function hashStringToUnitInterval(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  // 0..1
  return (hash >>> 0) / 0xFFFFFFFF;
}

function approximateCoordsForPrefix(prefixDigits) {
  const first = prefixDigits?.[0] ?? "0";
  const base = APPROX_REGION_CENTROIDS[first] ?? APPROX_REGION_CENTROIDS["0"];

  // Petit offset déterministe pour écarter les marqueurs (évite le chevauchement)
  const u = hashStringToUnitInterval(prefixDigits);
  const v = hashStringToUnitInterval(`${prefixDigits}_b`);
  const scale = Math.min(0.35, 0.08 + (prefixDigits.length - 1) * 0.06);
  const dLat = (u - 0.5) * scale;
  const dLon = (v - 0.5) * scale;

  return { lat: base.lat + dLat, lon: base.lon + dLon };
}

function getDesiredDigitsForZoom(zoom) {
  if (zoom <= 8) return 1;
  if (zoom <= 11) return 2;
  if (zoom <= 13) return 3;
  return 4;
}

function zoomForNextDigits(digits) {
  if (digits <= 1) return 8;
  if (digits === 2) return 10;
  if (digits === 3) return 12;
  return 14;
}

function makeZoneKey(prefixDigits, digits) {
  const xCount = Math.max(0, 4 - digits);
  return `${prefixDigits}${"x".repeat(xCount)}`;
}

function getZoneFromPostcode(postcodeDigits, zoom, focusPrefixDigits) {
  const p = postcodeDigits;
  if (!p) return null;

  const desiredDigits = getDesiredDigitsForZoom(zoom);
  const focus = focusPrefixDigits || "";

  // Limite volontaire: on ne descend qu'un niveau plus fin que le focus.
  // Sans focus, on reste au niveau 1 (chargement rapide même avec des milliers de clients).
  const maxDigitsAllowed = Math.max(1, focus.length + 1);
  const effectiveDigits = Math.min(desiredDigits, maxDigitsAllowed, Math.min(4, p.length));

  // Si focus défini, filtrer strictement le dataset sur ce prefix.
  if (focus && !p.startsWith(focus)) return null;

  const prefixDigits = p.slice(0, effectiveDigits);
  return {
    key: makeZoneKey(prefixDigits, effectiveDigits),
    prefixDigits,
    digits: effectiveDigits,
  };
}

// Filtrer les tickets avec localisation (utiliser buyerPostcode du code postal de l'acheteur)
const localizedTickets = computed(() => {
  return props.tickets.filter(
    (ticket) => ticket.buyerPostcode && ticket.buyerPostcode.trim() !== ""
  );
});

// Résumé stable (postcodeDigits -> nombre de tickets) pour éviter de rescanner des milliers
// de tickets à chaque update.
const postcodesSummary = computed(() => {
  const summary = new Map();
  localizedTickets.value.forEach((ticket) => {
    const digits = digitsOnly(normalizePostcode(ticket.buyerPostcode));
    if (!digits) return;
    summary.set(digits, (summary.get(digits) ?? 0) + 1);
  });
  return summary;
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
  const cacheKey = normalizePostcode(postcode);
  if (geocodeCache.has(cacheKey)) return geocodeCache.get(cacheKey);
  if (geocodeInFlight.has(cacheKey)) return geocodeInFlight.get(cacheKey);

  // Utilisation de l'API Nominatim (OpenStreetMap) pour géocoder les codes postaux
  // Note: En production, utilisez une API payante ou un service dédié
  try {
    // Nominatim rate limiting: keep requests spaced out.
    const minIntervalMs = 1100;
    const now = Date.now();
    const waitMs = Math.max(0, lastGeocodeRequestAtMs + minIntervalMs - now);
    if (waitMs > 0) await sleep(waitMs);

    const promise = (async () => {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?postalcode=${postcode}&country=ch&format=json&limit=1`,
        {
          headers: {
            "User-Agent": "CaseAChocs-Dashboard/1.0",
          },
        }
      );
      lastGeocodeRequestAtMs = Date.now();

      const data = await response.json();
      if (data && data.length > 0) {
        const coords = {
          lat: parseFloat(data[0].lat),
          lon: parseFloat(data[0].lon),
        };

        if (Number.isFinite(coords.lat) && Number.isFinite(coords.lon)) {
          geocodeCache.set(cacheKey, coords);
          persistGeocodeCache();
          return coords;
        }
      }
      return null;
    })();

    geocodeInFlight.set(cacheKey, promise);
    const result = await promise;
    return result;
  } catch (err) {
    console.error(`Erreur géocodage pour ${postcode}:`, err);
  }
  finally {
    geocodeInFlight.delete(cacheKey);
  }
  return null;
}

function debounce(fn, delayMs) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delayMs);
  };
}

function buildZonesForZoom(zoom) {
  const zones = new Map();
  const focus = focusPrefix.value;

  postcodesSummary.value.forEach((count, digits) => {
    const zoneInfo = getZoneFromPostcode(digits, zoom, focus);
    if (!zoneInfo) return;

    let zone = zones.get(zoneInfo.key);
    if (!zone) {
      zone = {
        key: zoneInfo.key,
        prefixDigits: zoneInfo.prefixDigits,
        digits: zoneInfo.digits,
        uniquePostcodesCount: 0,
        ticketsCount: 0,
        representativePostcode: digits,
      };
      zones.set(zoneInfo.key, zone);
    }

    zone.uniquePostcodesCount += 1;
    zone.ticketsCount += count;
  });

  return Array.from(zones.values()).sort((a, b) => b.ticketsCount - a.ticketsCount);
}

async function updateMap() {
  if (!map) return;
  const runId = ++updateRunId;

  if (!markerClusterLayer) return;
  markerClusterLayer.clearLayers();

  const zoom = map.getZoom();
  const zones = buildZonesForZoom(zoom);
  const coordinates = [];
  let scheduledGeocodes = 0;

  // Géocoder et ajouter des marqueurs de "zone" (niveau dépendant du zoom).
  for (const zone of zones) {
    if (runId !== updateRunId) return;

    // 1) Utiliser le cache si disponible
    const cacheKey = normalizePostcode(zone.representativePostcode);
    let coords = geocodeCache.get(cacheKey);

    // 2) Sinon, afficher immédiatement une position approximative
    if (!coords) {
      coords = approximateCoordsForPrefix(zone.prefixDigits);
    }

    // 3) Raffiner en arrière-plan (sans bloquer le rendu)
    if (!geocodeCache.has(cacheKey) && scheduledGeocodes < MAX_BACKGROUND_GEOCODES_PER_RENDER) {
      scheduledGeocodes += 1;
      geocodePostcode(zone.representativePostcode).then((real) => {
        if (!real) return;
        if (runId !== updateRunId) return;
        // Relancer un update léger pour repositionner les marqueurs.
        // (simple et fiable, évite de garder une map zoneKey->marker)
        updateMap();
      });
    }

    coordinates.push([coords.lat, coords.lon]);

    const popup =
      `<strong>Zone: ${zone.key}</strong><br>` +
      `Codes postaux: ${zone.uniquePostcodesCount}<br>` +
      `Tickets: ${zone.ticketsCount}<br>` +
      `<em style="color: #666; font-size: 0.85em;">Double-cliquez pour zoomer</em>`;

    const marker = L.marker([coords.lat, coords.lon]).bindPopup(popup);

    // Drill-down: double-clic pour zoomer et autoriser un niveau plus fin.
    // Le simple clic ouvre le popup (comportement par défaut de Leaflet).
    marker.on("dblclick", (e) => {
      L.DomEvent.stopPropagation(e);
      if (!map) return;
      // Fermer le popup avant de zoomer
      marker.closePopup();
      focusPrefix.value = zone.prefixDigits;
      const nextDigits = Math.min(4, zone.digits + 1);
      const targetZoom = Math.max(map.getZoom(), zoomForNextDigits(nextDigits));
      map.flyTo([coords.lat, coords.lon], targetZoom, { animate: true, duration: 0.5 });
    });

    markerClusterLayer.addLayer(marker);
  }

  // Ajuster la vue uniquement lors du premier rendu (évite de "lutter" contre le zoom/pan utilisateur).
  if (!hasAutoFitted) {
    if (coordinates.length > 0) {
      const bounds = L.latLngBounds(coordinates);
      map.fitBounds(bounds, { padding: [50, 50] });
    } else {
      // Vue par défaut sur Neuchâtel
      map.setView([46.9928, 6.9319], 10);
    }
    hasAutoFitted = true;
  }
}

function initializeMap() {
  if (!mapContainer.value || map) return;
  
  // Initialiser la carte Leaflet
  map = L.map(mapContainer.value).setView([46.9928, 6.9319], 10); // Neuchâtel par défaut

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map);

  markerClusterLayer = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
  });
  markerClusterLayer.addTo(map);

  const scheduleUpdate = debounce(() => {
    if (map) updateMap();
  }, 200);

  map.on("zoomend", scheduleUpdate);

  // Ne pas recalculer lors du pan (moveend) : trop coûteux, et inutile.

  map.on("zoomend", () => {
    // Si on revient à la vue "globale", on reset le focus.
    if (!map) return;
    if (map.getZoom() <= 8 && focusPrefix.value) {
      focusPrefix.value = "";
    }
  });
}

// Watcher pour initialiser la carte quand l'élément est disponible
watch(mapContainer, () => {
  if (mapContainer.value && !map) {
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

// Watcher pour mettre à jour la carte quand les tickets changent
watch(() => props.tickets, () => {
  if (map) {
    hasAutoFitted = false;
    focusPrefix.value = "";
    updateMap();
  }
}, { deep: true });

onMounted(async () => {
  loadGeocodeCache();
  await nextTick();
  
  // Tentative supplémentaire d'initialisation après un court délai
  setTimeout(() => {
    if (!map && mapContainer.value) {
      initializeMap();
      if (map) {
        updateMap();
      }
    }
  }, 100);
});

onUnmounted(() => {
  persistGeocodeCacheImmediate();
  if (map) {
    map.remove();
  }
});
</script>

<style scoped>
/* Styles pour la carte */
</style>

