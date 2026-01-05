<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { collection, getDocs, query, orderBy } from "firebase/firestore";
import { db } from "../firebase";
import SkeletonBlock from "../components/SkeletonBlock.vue";

const FILTER_PRESETS_STORAGE_KEY = "ticketing-dashboard:ticketsView:filterPresets:v1";

function getDefaultFilters() {
  return {
    dateStart: "",
    dateEnd: "",
    ticketNumber: "",
    eventName: "",
    buyer: "",
    ticketCategory: [],
    priceMin: null,
    priceMax: null,
  };
}

function normalizeFilters(input) {
  const base = getDefaultFilters();
  const obj = (input && typeof input === "object") ? input : {};
  const normalized = {
    ...base,
    ...obj,
  };

  normalized.dateStart = typeof normalized.dateStart === "string" ? normalized.dateStart : "";
  normalized.dateEnd = typeof normalized.dateEnd === "string" ? normalized.dateEnd : "";
  normalized.ticketNumber = typeof normalized.ticketNumber === "string" ? normalized.ticketNumber : "";
  normalized.eventName = typeof normalized.eventName === "string" ? normalized.eventName : "";
  normalized.buyer = typeof normalized.buyer === "string" ? normalized.buyer : "";

  normalized.ticketCategory = Array.isArray(normalized.ticketCategory)
    ? normalized.ticketCategory.filter(Boolean)
    : [];

  normalized.priceMin = normalized.priceMin === null || normalized.priceMin === ""
    ? null
    : Number(normalized.priceMin);
  normalized.priceMax = normalized.priceMax === null || normalized.priceMax === ""
    ? null
    : Number(normalized.priceMax);

  if (Number.isNaN(normalized.priceMin)) normalized.priceMin = null;
  if (Number.isNaN(normalized.priceMax)) normalized.priceMax = null;

  return normalized;
}

function safeJsonParse(str, fallback) {
  try {
    return JSON.parse(str);
  } catch {
    return fallback;
  }
}

function loadFilterPresets() {
  const raw = localStorage.getItem(FILTER_PRESETS_STORAGE_KEY);
  if (!raw) return [];
  const parsed = safeJsonParse(raw, null);
  if (!parsed) return [];

  // Supporte deux formats: { presets: [...] } ou directement [...]
  const presets = Array.isArray(parsed) ? parsed : (Array.isArray(parsed.presets) ? parsed.presets : []);
  return presets
    .filter(p => p && typeof p === "object")
    .map(p => ({
      id: String(p.id ?? ""),
      name: String(p.name ?? ""),
      filters: normalizeFilters(p.filters),
      createdAt: typeof p.createdAt === "number" ? p.createdAt : Date.now(),
      updatedAt: typeof p.updatedAt === "number" ? p.updatedAt : (typeof p.createdAt === "number" ? p.createdAt : Date.now()),
    }))
    .filter(p => p.id && p.name);
}

function persistFilterPresets(presets) {
  localStorage.setItem(FILTER_PRESETS_STORAGE_KEY, JSON.stringify({
    version: 1,
    presets,
  }));
}

function makeId() {
  // Pas besoin de crypto.randomUUID pour rester compatible
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

// états
const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const slowLoad = ref(false);

// Tri
const sortColumn = ref('date'); // Tri par défaut sur la date
const sortDirection = ref('desc'); // Le plus récent en premier

// Filtres
const filters = ref(getDefaultFilters());

// Presets de filtres (localStorage)
const savedFilterPresets = ref([]);
const selectedPresetId = ref("");
const presetName = ref("");
const presetError = ref(null);
const pendingPresetId = ref(null);

function refreshPresets() {
  presetError.value = null;
  try {
    savedFilterPresets.value = loadFilterPresets();
  } catch (e) {
    console.error("Erreur chargement presets:", e);
    presetError.value = "Impossible de charger les sauvegardes.";
    savedFilterPresets.value = [];
  }
}

function applyPreset(preset) {
  if (!preset?.filters) return;

  const next = normalizeFilters(preset.filters);

  // Normaliser catégories par rapport aux catégories disponibles (si on a déjà chargé les tickets)
  if (uniqueCategories.value.length > 0 && Array.isArray(next.ticketCategory)) {
    const allowed = new Set(uniqueCategories.value);
    next.ticketCategory = next.ticketCategory.filter(c => allowed.has(c));
  }

  filters.value = {
    ...getDefaultFilters(),
    ...next,
  };
}

function loadSelectedPreset() {
  presetError.value = null;
  const id = selectedPresetId.value;
  if (!id) return;

  if (loading.value) {
    pendingPresetId.value = id;
    return;
  }

  const preset = savedFilterPresets.value.find(p => p.id === id);
  if (!preset) {
    presetError.value = "Sauvegarde introuvable.";
    return;
  }
  applyPreset(preset);
}

function saveCurrentFilters() {
  presetError.value = null;
  const name = presetName.value.trim();
  if (!name) {
    presetError.value = "Donne un nom à la sauvegarde.";
    return;
  }

  const now = Date.now();
  const current = normalizeFilters(filters.value);
  const presets = [...savedFilterPresets.value];

  const existingIndex = presets.findIndex(p => p.name.toLowerCase() === name.toLowerCase());
  if (existingIndex >= 0) {
    presets[existingIndex] = {
      ...presets[existingIndex],
      name,
      filters: current,
      updatedAt: now,
    };
    selectedPresetId.value = presets[existingIndex].id;
  } else {
    const id = makeId();
    presets.unshift({
      id,
      name,
      filters: current,
      createdAt: now,
      updatedAt: now,
    });
    selectedPresetId.value = id;
  }

  try {
    persistFilterPresets(presets);
    savedFilterPresets.value = presets;
    presetName.value = "";
  } catch (e) {
    console.error("Erreur sauvegarde presets:", e);
    presetError.value = "Impossible de sauvegarder (localStorage).";
  }
}

function deleteSelectedPreset() {
  presetError.value = null;
  const id = selectedPresetId.value;
  if (!id) return;

  const preset = savedFilterPresets.value.find(p => p.id === id);
  if (!preset) return;

  const ok = window.confirm(`Supprimer la sauvegarde "${preset.name}" ?`);
  if (!ok) return;

  const presets = savedFilterPresets.value.filter(p => p.id !== id);
  try {
    persistFilterPresets(presets);
    savedFilterPresets.value = presets;
    selectedPresetId.value = "";
  } catch (e) {
    console.error("Erreur suppression preset:", e);
    presetError.value = "Impossible de supprimer la sauvegarde.";
  }
}

function resetAllFilters() {
  presetError.value = null;
  showCategoryDropdown.value = false;

  // Base defaults
  filters.value = getDefaultFilters();

  // Si on a déjà les tickets, on remet les defaults "intelligents"
  if (tickets.value.length > 0) {
    const cats = new Set(tickets.value.map(t => t.ticketCategory).filter(Boolean));
    filters.value.ticketCategory = Array.from(cats).sort();

    const prices = tickets.value.map(t => t.priceAmount).filter(p => typeof p === 'number');
    if (prices.length > 0) {
      filters.value.priceMin = Math.min(...prices);
      filters.value.priceMax = Math.max(...prices);
    }
  }
}

const showCategoryDropdown = ref(false);

const uniqueCategories = computed(() => {
  const cats = new Set(tickets.value.map(t => t.ticketCategory).filter(Boolean));
  return Array.from(cats).sort();
});

const uniqueEvents = computed(() => {
  const events = new Set(tickets.value.map(t => t.eventName).filter(Boolean));
  return events.size;
});

const totalRevenue = computed(() => {
  return sortedTickets.value
    .filter(t => typeof t.priceAmount === 'number')
    .reduce((sum, t) => sum + t.priceAmount, 0);
});

const priceRange = computed(() => {
  const prices = tickets.value
    .map(t => t.priceAmount)
    .filter(p => typeof p === 'number');
  
  if (prices.length === 0) return { min: 0, max: 100 };
  return {
    min: Math.min(...prices),
    max: Math.max(...prices)
  };
});

const priceRangeStyle = computed(() => {
  const min = priceRange.value.min;
  const max = priceRange.value.max;
  const currentMin = filters.value.priceMin ?? min;
  const currentMax = filters.value.priceMax ?? max;
  
  if (max === min) return { left: '0%', width: '100%' };

  const left = ((currentMin - min) / (max - min)) * 100;
  const right = ((currentMax - min) / (max - min)) * 100;
  
  return {
    left: `${left}%`,
    width: `${right - left}%`
  };
});

function updatePriceMin() {
  const min = filters.value.priceMin;
  const max = filters.value.priceMax;
  if (min > max) {
    filters.value.priceMin = max;
  }
}

function updatePriceMax() {
  const min = filters.value.priceMin;
  const max = filters.value.priceMax;
  if (max < min) {
    filters.value.priceMax = min;
  }
}

// Pagination
const itemsPerPage = ref(10);
const currentPage = ref(1);

const sortedTickets = computed(() => {
  // 1. Filtrage
  let result = tickets.value.filter(t => {
    const f = filters.value;
    
    // Filtre Date (Plage)
    const ticketDateRaw = t.generatedAtRaw || t.createdAtRaw;
    if (f.dateStart || f.dateEnd) {
      if (!ticketDateRaw) return false;
      
      // Conversion en YYYY-MM-DD local pour comparaison
      const d = new Date(ticketDateRaw);
      const offset = d.getTimezoneOffset();
      const localDate = new Date(d.getTime() - (offset * 60 * 1000));
      const dateYMD = localDate.toISOString().split('T')[0];

      if (f.dateStart && dateYMD < f.dateStart) return false;
      if (f.dateEnd && dateYMD > f.dateEnd) return false;
    }
    if (f.ticketNumber && !(t.ticketNumber || '').toLowerCase().includes(f.ticketNumber.toLowerCase())) return false;
    if (f.eventName && !(t.eventName || '').toLowerCase().includes(f.eventName.toLowerCase())) return false;
    if (f.buyer) {
      const term = f.buyer.toLowerCase();
      const name = `${t.buyerFirstName || ''} ${t.buyerLastName || ''}`.toLowerCase();
      const email = (t.buyerEmail || '').toLowerCase();
      if (!name.includes(term) && !email.includes(term)) return false;
    }
    // Filtre catégorie (liste)
    if (f.ticketCategory.length > 0 && !f.ticketCategory.includes(t.ticketCategory)) return false;
    
    // Filtre Prix (Plage)
    if (typeof t.priceAmount === 'number') {
      if (f.priceMin !== null && t.priceAmount < f.priceMin) return false;
      if (f.priceMax !== null && t.priceAmount > f.priceMax) return false;
    }

    return true;
  });

  // 2. Tri
  if (sortColumn.value) {
    result.sort((a, b) => {
      let valA, valB;

      // Logique spécifique par colonne
      if (sortColumn.value === 'date') {
        valA = a.generatedAtRaw || a.createdAtRaw || '';
        valB = b.generatedAtRaw || b.createdAtRaw || '';
      } else if (sortColumn.value === 'buyer') {
        valA = (a.buyerLastName || '') + (a.buyerFirstName || '');
        valB = (b.buyerLastName || '') + (b.buyerFirstName || '');
      } else {
        valA = a[sortColumn.value];
        valB = b[sortColumn.value];
      }

      // Gestion des null/undefined
      if (valA == null) valA = "";
      if (valB == null) valB = "";

      // Comparaison numérique pour le prix
      if (sortColumn.value === 'priceAmount') {
        valA = Number(valA) || 0;
        valB = Number(valB) || 0;
      } 
      // Comparaison string insensible à la casse
      else if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }

      if (valA < valB) return sortDirection.value === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection.value === 'asc' ? 1 : -1;
      return 0;
    });
  }
  
  return result;
});

// Pagination calculée
const totalPages = computed(() => Math.ceil(sortedTickets.value.length / itemsPerPage.value));

const paginatedTickets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value;
  const end = start + itemsPerPage.value;
  return sortedTickets.value.slice(start, end);
});

// Reset page quand on filtre ou trie
watch([filters, sortColumn, sortDirection], () => {
  currentPage.value = 1;
}, { deep: true });

function handleSort(column) {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortColumn.value = column;
    sortDirection.value = 'asc'; // Par défaut ascendant au changement de colonne
    
    // Exception pour la date : on préfère souvent voir le plus récent en premier (desc)
    // Mais pour rester intuitif "flèche haut = croissant", on garde 'asc' par défaut
    // ou on force 'desc' si c'est la date ? 
    // Restons standard : click = asc.
  }
}

// helper format prix
function formatPrice(amount, currency) {
  // affiche comme "24.00 CHF"
  const fixed = Number(amount).toFixed(2);
  return currency ? `${fixed} ${currency}` : `${fixed}`;
}

// helper format date
function formatDateTime(isoString) {
  if (!isoString) return "—";
  try {
    // Format: "12/12/2025 14:30"
    return new Date(isoString).toLocaleString('fr-CH', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return isoString;
  }
}

function csvEscape(value) {
  if (value === null || value === undefined) return '""';
  const str = String(value);
  return `"${str.replace(/"/g, '""')}"`;
}

function getCategoryBadgeClasses(category) {
  if (!category) return 'bg-gray-100 text-gray-800';
  
  const cat = String(category).toLowerCase();
  
  // Prélocation : violet/purple
  if (cat.includes('préloc') || cat.includes('preloc') || cat.includes('pre-loc') || cat.includes('prévente')) {
    return 'bg-purple-100 text-purple-800';
  }
  
  // Sur place : orange
  if (cat.includes('sur place') || cat.includes('surplace') || cat.includes('caisse') || cat.includes('porte')) {
    return 'bg-orange-100 text-orange-800';
  }
  
  // Par défaut : bleu
  return 'bg-blue-100 text-blue-800';
}

function exportFilteredTicketsCsv() {
  // On exporte les lignes correspondant aux filtres (pas seulement la page courante)
  const rows = sortedTickets.value;
  if (!rows || rows.length === 0) return;

  const sep = ';';
  const headers = [
    'date_achat',
    'ticket_number',
    'event_name',
    'session_date',
    'session_time',
    'buyer_first_name',
    'buyer_last_name',
    'buyer_email',
    'buyer_postcode',
    'ticket_category',
    'price_amount',
    'price_currency',
    'cancellation_reason',
  ];

  const lines = [];
  lines.push(headers.map(csvEscape).join(sep));

  for (const t of rows) {
    const dateRaw = t.generatedAtRaw ?? t.createdAtRaw ?? '';
    lines.push([
      formatDateTime(dateRaw),
      t.ticketNumber ?? '',
      t.eventName ?? '',
      t.sessionDate ?? '',
      t.sessionTime ?? '',
      t.buyerFirstName ?? '',
      t.buyerLastName ?? '',
      t.buyerEmail ?? '',
      t.buyerPostcode ?? '',
      t.ticketCategory ?? '',
      (typeof t.priceAmount === 'number') ? t.priceAmount : '',
      t.priceCurrency ?? '',
      t.cancellationReason ?? '',
    ].map(csvEscape).join(sep));
  }

  // BOM UTF-8 pour Excel
  const csv = `\uFEFF${lines.join('\n')}`;
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const pad2 = (n) => String(n).padStart(2, '0');
  const d = new Date();
  const filename = `tickets_${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}_${pad2(d.getHours())}-${pad2(d.getMinutes())}.csv`;

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

onMounted(async () => {
  // Charger les presets dès le départ
  try {
    refreshPresets();
  } catch {
    // déjà géré
  }

  loading.value = true;
  error.value = null;

  // Indicateur "lent" ultra court sans interrompre la requête (1s)
  const TIMEOUT_MS = 1000;
  const TIMEOUT_SECONDS = Math.ceil(TIMEOUT_MS / 1000);
  const timeoutId = setTimeout(() => {
    if (loading.value) {
      console.warn(`⏱️ Chargement plus long que prévu (> ${TIMEOUT_SECONDS}s), on continue d'attendre…`);
      slowLoad.value = true; // on n'arrête PAS la requête et on n'affiche PAS d'erreur
    }
  }, TIMEOUT_MS);

  try {
    if (!db) {
      throw new Error("Firestore (db) non initialisé — vérifie frontend/src/firebase.js et .env.local");
    }

    console.log("🔍 Début de la récupération des tickets depuis Firestore...");
    console.log("📊 Collection: 'tickets'");
    console.log(`⏱️ Indicateur lenteur après: ${TIMEOUT_SECONDS} seconde(s)`);
    console.log("🔗 Configuration Firebase:", {
      projectId: db.app.options.projectId,
      databaseId: db._delegate?.databaseId || "default",
    });
    
    const startTime = Date.now();
    
    // Essayer d'abord une requête simple sans orderBy pour éviter les problèmes d'index
    let q;
    let snap;
    let docs;
    
    try {
      console.log("📝 Tentative 1: Requête simple sans orderBy...");
      q = query(collection(db, "tickets"));
      snap = await getDocs(q);
      docs = snap.docs;
      const elapsed = Date.now() - startTime;
      console.log(`✅ Requête réussie en ${elapsed}ms. ${docs.length} document(s) trouvé(s)`);
      
      // Si on a des résultats, essayer de les trier par createdAt si disponible
      if (docs.length > 0) {
        console.log("🔄 Tri manuel des résultats par createdAt...");
        docs = docs.sort((a, b) => {
          const dateA = a.data().createdAt;
          const dateB = b.data().createdAt;
          if (!dateA || !dateB) return 0;
          try {
            const timeA = dateA.toDate ? dateA.toDate().getTime() : new Date(dateA).getTime();
            const timeB = dateB.toDate ? dateB.toDate().getTime() : new Date(dateB).getTime();
            return timeB - timeA; // Plus récent en premier
          } catch {
            return 0;
          }
        });
        console.log("✅ Tri terminé");
      }
    } catch (simpleError) {
      const elapsed = Date.now() - startTime;
      console.error(`❌ Erreur avec requête simple après ${elapsed}ms:`, simpleError);
      console.error("Détails:", {
        code: simpleError?.code,
        message: simpleError?.message,
      });
      
      // Si la requête simple échoue, essayer avec orderBy (peut-être qu'un index existe)
      try {
        console.log("📝 Tentative 2: Requête avec orderBy('createdAt', 'desc')...");
        q = query(collection(db, "tickets"), orderBy("createdAt", "desc"));
        snap = await getDocs(q);
        docs = snap.docs;
        const elapsed2 = Date.now() - startTime;
        console.log(`✅ Requête avec orderBy réussie en ${elapsed2}ms. ${docs.length} document(s) trouvé(s)`);
      } catch (orderByError) {
        const elapsed2 = Date.now() - startTime;
        console.error(`❌ Erreur avec orderBy après ${elapsed2}ms:`, orderByError);
        throw orderByError; // Relancer l'erreur pour qu'elle soit gérée par le catch principal
      }
    }

    // transformer en objets JS simples
    tickets.value = docs.map((doc) => {
      const data = doc.data();

      // createdAt peut être un Timestamp Firestore, une ISO string, ou autre.
      let createdAtRaw = data.createdAt;
      let generatedAtRaw = data.generatedAt;

      try {
        // si c'est un objet avec toDate (Firestore Timestamp), convertir en ISO string pour affichage brut lisible
        if (createdAtRaw && typeof createdAtRaw.toDate === "function") {
          createdAtRaw = createdAtRaw.toDate().toISOString();
        } else if (typeof createdAtRaw === "object" && createdAtRaw !== null) {
          // si c'est un objet quelconque, stringify minimal
          createdAtRaw = JSON.stringify(createdAtRaw);
        }

        if (generatedAtRaw && typeof generatedAtRaw.toDate === "function") {
          generatedAtRaw = generatedAtRaw.toDate().toISOString();
        } else if (typeof generatedAtRaw === "object" && generatedAtRaw !== null) {
          generatedAtRaw = JSON.stringify(generatedAtRaw);
        }
      } catch (e) {
        // leave as-is si erreur
      }

      return {
        id: doc.id,
        eventName: data.eventName ?? null,
        sessionDate: data.sessionDate ?? null,
        sessionTime: data.sessionTime ?? null,
        sessionDoors: data.sessionDoors ?? null,
        ticketNumber: data.ticketNumber ?? null,
        priceAmount: typeof data.priceAmount === "number" ? data.priceAmount : (data.priceAmount ? Number(data.priceAmount) : undefined),
        priceCurrency: data.priceCurrency ?? null,
        createdAtRaw,
        generatedAtRaw,
        // New fields
        ticketType: data.ticketType ?? null,
        ticketCategory: data.ticketCategory ?? null,
        buyerFirstName: data.buyerFirstName ?? null,
        buyerLastName: data.buyerLastName ?? null,
        buyerEmail: data.buyerEmail ?? null,
        buyerPostcode: data.buyerPostcode ?? null,
        venueName: data.venueName ?? null,
        venueStreet: data.venueStreet ?? null,
        venueCity: data.venueCity ?? null,
        cancellationReason: data.cancellationReason ?? null,
      };
    });

    console.debug(`Tickets chargés: ${tickets.value.length}`);
    
    // Initialiser le filtre catégorie avec toutes les catégories cochées par défaut
    const cats = new Set(tickets.value.map(t => t.ticketCategory).filter(Boolean));
    filters.value.ticketCategory = Array.from(cats).sort();

    // Initialiser le filtre prix avec min/max
    const prices = tickets.value.map(t => t.priceAmount).filter(p => typeof p === 'number');
    if (prices.length > 0) {
      filters.value.priceMin = Math.min(...prices);
      filters.value.priceMax = Math.max(...prices);
    }

    // Appliquer un preset demandé pendant le chargement
    if (pendingPresetId.value) {
      const preset = savedFilterPresets.value.find(p => p.id === pendingPresetId.value);
      pendingPresetId.value = null;
      if (preset) {
        applyPreset(preset);
      }
    }

    if (tickets.value.length === 0) {
      console.warn("⚠️ Aucun ticket trouvé dans la collection 'tickets'");
      console.info("💡 Pour ajouter des tickets, utilisez le simulateur Petzi ou envoyez des webhooks");
      console.info("🔍 Vérifications à faire:");
      console.info("   1. Vérifiez que vous êtes connecté au bon projet Firebase (émulateur vs cloud)");
      console.info("   2. Ouvrez la console Firebase/émulateur et vérifiez que la collection 'tickets' contient des documents");
      console.info("   3. Si vous utilisez l'émulateur, ajoutez VITE_USE_FIREBASE_EMULATOR=true dans .env.local");
      console.info("   4. Vérifiez les règles de sécurité Firestore dans backend/firestore.rules");
    } else {
      console.log(`✅ ${tickets.value.length} ticket(s) chargé(s) avec succès!`);
    }
  } catch (err) {
    console.error("❌ Erreur lecture tickets:", err);
    console.error("Détails de l'erreur:", {
      code: err?.code,
      message: err?.message,
      stack: err?.stack,
    });
    
    // Messages d'erreur plus explicites
    let errorMessage = err?.message || String(err);
    if (err?.code === "unavailable" || err?.code === "deadline-exceeded") {
      errorMessage = "Impossible de se connecter à Firestore. Vérifiez votre connexion internet et que Firebase est accessible.";
      if (import.meta.env.DEV) {
        errorMessage += " Si vous utilisez l'émulateur, assurez-vous qu'il est démarré et ajoutez VITE_USE_FIREBASE_EMULATOR=true dans .env.local";
      }
    } else if (err?.code === "permission-denied") {
      errorMessage = "Permission refusée. Vérifiez les règles de sécurité Firestore.";
    } else if (err?.code === "failed-precondition") {
      errorMessage = "Index manquant. Créez l'index requis dans la console Firebase ou utilisez l'émulateur.";
    }
    
    error.value = errorMessage;
  } finally {
    clearTimeout(timeoutId);
    loading.value = false;
  }
});
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h1 class="page-title">Tickets</h1>
      <p class="page-subtitle">Recherche, filtres et tri sur l'ensemble des ventes.</p>
    </div>

    <!-- KPI Cards -->
    <div v-if="!loading && tickets.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="panel p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-zinc-500 uppercase font-semibold tracking-wide">Total tickets</p>
            <p class="text-2xl font-bold text-zinc-900">{{ sortedTickets.length }}</p>
          </div>
          <div class="p-3 bg-blue-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="panel p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-zinc-500 uppercase font-semibold tracking-wide">Événements</p>
            <p class="text-2xl font-bold text-zinc-900">{{ uniqueEvents }}</p>
          </div>
          <div class="p-3 bg-purple-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="panel p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-zinc-500 uppercase font-semibold tracking-wide">Catégories</p>
            <p class="text-2xl font-bold text-zinc-900">{{ uniqueCategories.length }}</p>
          </div>
          <div class="p-3 bg-green-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="panel p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-zinc-500 uppercase font-semibold tracking-wide">Revenu total</p>
            <p class="text-2xl font-bold text-zinc-900">{{ formatPrice(totalRevenue, 'CHF') }}</p>
          </div>
          <div class="p-3 bg-emerald-100 rounded-full">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters Panel -->
    <div v-if="!loading && tickets.length > 0" class="panel p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-zinc-900">Filtres</h2>
        <button
          @click="resetAllFilters"
          class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition"
        >
          Réinitialiser
        </button>
      </div>

      <!-- Sauvegardes de filtres -->
      <div class="mb-6 pb-6 border-b border-gray-200">
        <h3 class="text-sm font-semibold text-zinc-700 mb-3">Sauvegardes de filtres</h3>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="text-xs text-zinc-600 font-medium">Charger une sauvegarde</label>
            <div class="flex items-center gap-2">
              <select v-model="selectedPresetId" class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="">— Choisir une sauvegarde —</option>
                <option v-for="p in savedFilterPresets" :key="p.id" :value="p.id">
                  {{ p.name }}
                </option>
              </select>
              <button
                @click="loadSelectedPreset"
                :disabled="!selectedPresetId"
                class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600"
              >
                Charger
              </button>
              <button
                @click="deleteSelectedPreset"
                :disabled="!selectedPresetId"
                class="px-4 py-2 border border-red-300 text-red-600 text-sm font-medium rounded-lg hover:bg-red-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Supprimer
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-xs text-zinc-600 font-medium">Nouvelle sauvegarde</label>
            <div class="flex items-center gap-2">
              <input
                v-model="presetName"
                type="text"
                placeholder="Nom de la sauvegarde..."
                class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                @keydown.enter.prevent="saveCurrentFilters"
              />
              <button
                @click="saveCurrentFilters"
                class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition"
              >
                Sauvegarder
              </button>
            </div>
          </div>
        </div>

        <div v-if="presetError" class="mt-2 text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
          {{ presetError }}
        </div>
      </div>

      <!-- Search Filters -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Date début</label>
          <input 
            v-model="filters.dateStart" 
            type="date" 
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Date fin</label>
          <input 
            v-model="filters.dateEnd" 
            type="date" 
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">N° de ticket</label>
          <input 
            v-model="filters.ticketNumber" 
            type="text" 
            placeholder="Rechercher..."
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Événement</label>
          <input 
            v-model="filters.eventName" 
            type="text" 
            placeholder="Rechercher..."
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Acheteur</label>
          <input 
            v-model="filters.buyer" 
            type="text" 
            placeholder="Nom, email..."
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Catégories ({{ filters.ticketCategory.length }})</label>
          <div class="relative">
            <button 
              @click.stop="showCategoryDropdown = !showCategoryDropdown"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-left focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white flex justify-between items-center"
            >
              <span class="truncate text-zinc-700">
                {{ filters.ticketCategory.length ? `${filters.ticketCategory.length} sélect.` : 'Tous' }}
              </span>
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <div 
              v-if="showCategoryDropdown" 
              @click.stop="showCategoryDropdown = false" 
              class="fixed inset-0 z-40"
            ></div>

            <div 
              v-if="showCategoryDropdown" 
              @click.stop 
              class="absolute top-full left-0 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto"
            >
              <div class="p-2 border-b border-gray-100 sticky top-0 bg-white z-10">
                <button @click="filters.ticketCategory = []" class="text-xs text-blue-600 hover:underline font-medium">Tout décocher</button>
              </div>
              <div class="p-2 space-y-1">
                <label v-for="cat in uniqueCategories" :key="cat" class="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-50 rounded cursor-pointer">
                  <input 
                    type="checkbox" 
                    :value="cat" 
                    v-model="filters.ticketCategory"
                    class="rounded text-blue-600 focus:ring-blue-500"
                  >
                  <span class="text-sm text-zinc-700 flex-1 truncate">{{ cat }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Prix min</label>
          <input 
            type="number" 
            v-model.number="filters.priceMin" 
            :min="priceRange.min" 
            :max="priceRange.max"
            @input="updatePriceMin"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-zinc-600 font-medium">Prix max</label>
          <input 
            type="number" 
            v-model.number="filters.priceMax" 
            :min="priceRange.min" 
            :max="priceRange.max"
            @input="updatePriceMax"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>
    </div>

    <!-- Data Panel -->
    <div class="panel p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-bold text-zinc-900">Liste des tickets</h2>

        <div v-if="!loading && tickets.length > 0" class="flex items-center gap-3">
          <button
            @click="exportFilteredTicketsCsv"
            :disabled="sortedTickets.length === 0"
            class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Exporter CSV
          </button>

          <div class="flex items-center gap-2 text-sm">
            <select v-model.number="itemsPerPage" class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <span class="text-xs text-zinc-500">par page</span>
          </div>

          <div class="flex items-center gap-2">
            <button 
              @click="currentPage--" 
              :disabled="currentPage === 1"
              class="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition"
            >
              ← Préc.
            </button>
            <span class="text-sm text-zinc-700">{{ currentPage }} / {{ totalPages || 1 }}</span>
            <button 
              @click="currentPage++" 
              :disabled="currentPage >= totalPages"
              class="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition"
            >
              Suiv. →
            </button>
          </div>
        </div>
      </div>

    <div v-if="loading" class="mt-4">
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <SkeletonBlock class-name="h-4 w-40" />
          <SkeletonBlock class-name="h-4 w-24" />
        </div>

        <div class="border rounded overflow-hidden">
          <div class="bg-gray-100 px-2 py-2 flex gap-2">
            <SkeletonBlock class-name="h-4 w-32" />
            <SkeletonBlock class-name="h-4 w-20" />
            <SkeletonBlock class-name="h-4 w-44" />
            <SkeletonBlock class-name="h-4 w-40" />
            <SkeletonBlock class-name="h-4 w-24" />
          </div>
          <div class="divide-y">
            <div v-for="i in 10" :key="i" class="px-2 py-3 flex gap-2 items-center">
              <SkeletonBlock class-name="h-4 w-32" />
              <SkeletonBlock class-name="h-4 w-20" />
              <SkeletonBlock class-name="h-4 w-44" />
              <SkeletonBlock class-name="h-4 w-40" />
              <SkeletonBlock class-name="h-4 w-24" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="error" class="mt-4 text-red-600">Erreur : {{ error }}</div>

    <div v-else class="overflow-x-auto rounded-lg border border-gray-200">
    <table class="w-full text-sm">
      <thead>
        <tr class="bg-zinc-50 border-b border-gray-200">
          <th @click="handleSort('date')" class="px-4 py-3 text-left cursor-pointer hover:bg-zinc-100 select-none align-top transition border-r border-gray-200 last:border-r-0">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Date d'achat</span>
                <span v-if="sortColumn === 'date'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <div class="text-xs text-zinc-500 font-normal" @click.stop>
                Filtres dans le panneau ci-dessus
              </div>
            </div>
          </th>
          <th @click="handleSort('ticketNumber')" class="px-4 py-3 text-left cursor-pointer hover:bg-zinc-100 select-none align-top transition border-r border-gray-200">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Ticket #</span>
                <span v-if="sortColumn === 'ticketNumber'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <span class="text-xs text-zinc-500 font-normal" @click.stop>Cliquez pour trier</span>
            </div>
          </th>
          <th @click="handleSort('eventName')" class="px-4 py-3 text-left cursor-pointer hover:bg-zinc-100 select-none align-top transition border-r border-gray-200">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Événement</span>
                <span v-if="sortColumn === 'eventName'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <span class="text-xs text-zinc-500 font-normal" @click.stop>Cliquez pour trier</span>
            </div>
          </th>
          <th @click="handleSort('buyer')" class="px-4 py-3 text-left cursor-pointer hover:bg-zinc-100 select-none align-top transition border-r border-gray-200">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Acheteur</span>
                <span v-if="sortColumn === 'buyer'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <span class="text-xs text-zinc-500 font-normal" @click.stop>Cliquez pour trier</span>
            </div>
          </th>
          <th @click="handleSort('ticketCategory')" class="px-4 py-3 text-left cursor-pointer hover:bg-zinc-100 select-none align-top transition border-r border-gray-200">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Catégorie</span>
                <span v-if="sortColumn === 'ticketCategory'" class="text-blue-600">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <span class="text-xs text-zinc-500 font-normal" @click.stop>Cliquez pour trier</span>
            </div>
          </th>
          <th @click="handleSort('priceAmount')" class="px-4 py-3 text-left cursor-pointer hover:bg-zinc-100 select-none align-top transition">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Prix</span>
                <span v-if="sortColumn === 'priceAmount'" class="text-blue-600">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <span class="text-xs text-zinc-500 font-normal" @click.stop>Cliquez pour trier</span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-200">
        <tr v-for="t in paginatedTickets" :key="t.id" class="hover:bg-blue-50/30 transition">
          <td class="px-4 py-3 text-xs text-zinc-700 border-r border-gray-100">
            <span v-if="t.generatedAtRaw !== undefined">{{ formatDateTime(t.generatedAtRaw) }}</span>
            <span v-else-if="t.createdAtRaw !== undefined" class="text-gray-400" title="Date de réception (generatedAt manquant)">
              {{ formatDateTime(t.createdAtRaw) }}*
            </span>
            <span v-else>—</span>
          </td>
          <td class="px-4 py-3 font-mono text-xs text-zinc-700 border-r border-gray-100">
            {{ t.ticketNumber ?? "—" }}
            <div v-if="t.cancellationReason" class="text-red-600 font-bold text-xs mt-1">
              ANNULÉ: {{ t.cancellationReason }}
            </div>
          </td>
          <td class="px-4 py-3 border-r border-gray-100">
            <div class="font-semibold text-zinc-900">{{ t.eventName ?? "—" }}</div>
            <div class="text-xs text-zinc-500">
              {{ t.sessionDate ?? "—" }} <span v-if="t.sessionTime">à {{ t.sessionTime }}</span>
            </div>
          </td>
          <td class="px-4 py-3 border-r border-gray-100">
            <div v-if="t.buyerFirstName || t.buyerLastName" class="text-zinc-900">
              {{ t.buyerFirstName }} {{ t.buyerLastName }}
              <div v-if="t.buyerEmail" class="text-xs text-blue-600 font-medium">{{ t.buyerEmail }}</div>
              <div v-if="t.buyerPostcode" class="text-xs text-zinc-500">{{ t.buyerPostcode }}</div>
            </div>
            <span v-else class="text-zinc-400">—</span>
          </td>
          <td class="px-4 py-3 border-r border-gray-100">
            <span 
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              :class="getCategoryBadgeClasses(t.ticketCategory)"
            >
              {{ t.ticketCategory ?? "—" }}
            </span>
          </td>
          <td class="px-4 py-3 whitespace-nowrap font-semibold text-zinc-900">
            <span v-if="typeof t.priceAmount === 'number'">
              {{ formatPrice(t.priceAmount, t.priceCurrency) }}
            </span>
            <span v-else>—</span>
          </td>
        </tr>
        <tr v-if="sortedTickets.length === 0 && !loading">
          <td class="px-4 py-8 text-center text-zinc-500" colspan="6">
            <div class="flex flex-col items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p class="text-sm font-medium">Aucun ticket trouvé avec ces filtres</p>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <!-- Pagination Controls -->
    <div v-if="!loading && tickets.length > 0" class="mt-6 pt-4 border-t border-gray-200 flex flex-wrap justify-between items-center gap-4">
      <div class="flex items-center gap-2 text-sm">
        <span class="text-zinc-600">Afficher</span>
        <select v-model.number="itemsPerPage" class="border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
        <span class="text-zinc-600">tickets par page</span>
      </div>

      <div class="flex items-center gap-3">
        <button 
          @click="currentPage--" 
          :disabled="currentPage === 1"
          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition"
        >
          ← Précédent
        </button>
        <span class="text-sm font-medium text-zinc-700">Page {{ currentPage }} sur {{ totalPages || 1 }}</span>
        <button 
          @click="currentPage++" 
          :disabled="currentPage >= totalPages"
          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition"
        >
          Suivant →
        </button>
      </div>
      
      <div class="text-sm">
        <span class="text-zinc-600">Total:</span>
        <span class="font-semibold text-zinc-900 ml-1">{{ sortedTickets.length }}</span>
        <span class="text-zinc-600 ml-1">ticket(s)</span>
      </div>
    </div>
    </div>
  </main>
</template>

<style scoped>
/* Pas de CSS compliqué — utilitaires légers déjà fournis inline */
/* Custom styles for dual range slider */
.slider-thumb::-webkit-slider-thumb {
  pointer-events: auto;
  appearance: none;
  width: 12px;
  height: 12px;
  background: white;
  border: 2px solid #3b82f6; /* blue-500 */
  border-radius: 50%;
  cursor: pointer;
  margin-top: -4px; /* center vertically if needed, though absolute positioning handles it mostly */
  position: relative;
  z-index: 30;
}

.slider-thumb::-moz-range-thumb {
  pointer-events: auto;
  width: 12px;
  height: 12px;
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  z-index: 30;
}
</style>
