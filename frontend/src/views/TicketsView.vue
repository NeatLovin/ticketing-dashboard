<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { collection, getDocs, query, orderBy } from "firebase/firestore";
import { db } from "../firebase";

// états
const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const slowLoad = ref(false);

// Tri
const sortColumn = ref('date'); // Tri par défaut sur la date
const sortDirection = ref('desc'); // Le plus récent en premier

// Filtres
const filters = ref({
  dateStart: '',
  dateEnd: '',
  ticketNumber: '',
  eventName: '',
  buyer: '',
  ticketCategory: [], // Array pour les checkboxes
  priceMin: null,
  priceMax: null
});

const showCategoryDropdown = ref(false);

const uniqueCategories = computed(() => {
  const cats = new Set(tickets.value.map(t => t.ticketCategory).filter(Boolean));
  return Array.from(cats).sort();
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

onMounted(async () => {
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
  <main class="p-4">
    <div class="flex justify-between items-end mb-4">
      <h1 class="text-2xl font-bold">Tickets</h1>

      <!-- Top Pagination Controls -->
      <div v-if="!loading && tickets.length > 0" class="flex items-center gap-4 text-sm">
        <div class="flex items-center gap-2">
          <select v-model.number="itemsPerPage" class="border rounded px-1 py-0.5">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
          <span class="text-xs text-gray-500">/ page</span>
        </div>

        <div class="flex items-center gap-2">
          <button 
            @click="currentPage--" 
            :disabled="currentPage === 1"
            class="px-2 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Précédent
          </button>
          <span>{{ currentPage }} / {{ totalPages || 1 }}</span>
          <button 
            @click="currentPage++" 
            :disabled="currentPage >= totalPages"
            class="px-2 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Suivant
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="mt-4">
      Chargement des tickets…
      <span v-if="slowLoad" class="ml-2 text-sm text-gray-500">c'est un peu long, merci de patienter</span>
    </div>

    <div v-else-if="error" class="mt-4 text-red-600">Erreur : {{ error }}</div>

    <table v-else class="mt-4 border-collapse w-full text-sm">
      <thead>
        <tr class="bg-gray-100">
          <th @click="handleSort('date')" class="border px-2 py-1 text-left cursor-pointer hover:bg-gray-200 select-none align-top">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Date d'achat</span>
                <span v-if="sortColumn === 'date'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <div class="flex flex-col gap-1" @click.stop>
                <input 
                  v-model="filters.dateStart" 
                  type="date" 
                  class="w-full px-1 py-0.5 text-xs border rounded font-normal"
                  title="Date de début"
                />
                <input 
                  v-model="filters.dateEnd" 
                  type="date" 
                  class="w-full px-1 py-0.5 text-xs border rounded font-normal"
                  title="Date de fin"
                />
              </div>
            </div>
          </th>
          <th @click="handleSort('ticketNumber')" class="border px-2 py-1 text-left cursor-pointer hover:bg-gray-200 select-none align-top">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Ticket #</span>
                <span v-if="sortColumn === 'ticketNumber'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <input 
                v-model="filters.ticketNumber" 
                @click.stop 
                type="text" 
                placeholder="Filtre..." 
                class="w-full px-1 py-0.5 text-xs border rounded font-normal"
              />
            </div>
          </th>
          <th @click="handleSort('eventName')" class="border px-2 py-1 text-left cursor-pointer hover:bg-gray-200 select-none align-top">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Événement</span>
                <span v-if="sortColumn === 'eventName'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <input 
                v-model="filters.eventName" 
                @click.stop 
                type="text" 
                placeholder="Filtre..." 
                class="w-full px-1 py-0.5 text-xs border rounded font-normal"
              />
            </div>
          </th>
          <th @click="handleSort('buyer')" class="border px-2 py-1 text-left cursor-pointer hover:bg-gray-200 select-none align-top">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Acheteur</span>
                <span v-if="sortColumn === 'buyer'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <input 
                v-model="filters.buyer" 
                @click.stop 
                type="text" 
                placeholder="Filtre..." 
                class="w-full px-1 py-0.5 text-xs border rounded font-normal"
              />
            </div>
          </th>
          <th @click="handleSort('ticketCategory')" class="border px-2 py-1 text-left cursor-pointer hover:bg-gray-200 select-none align-top">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Catégorie</span>
                <span v-if="sortColumn === 'ticketCategory'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              
              <div class="relative">
                <button 
                  @click.stop="showCategoryDropdown = !showCategoryDropdown"
                  class="w-full px-1 py-0.5 text-xs border rounded font-normal bg-white text-left flex justify-between items-center"
                >
                  <span class="truncate">
                    {{ filters.ticketCategory.length ? `${filters.ticketCategory.length} sélect.` : 'Tous' }}
                  </span>
                  <span class="text-[10px]">▼</span>
                </button>

                <!-- Overlay pour fermer -->
                <div 
                  v-if="showCategoryDropdown" 
                  @click.stop="showCategoryDropdown = false" 
                  class="fixed inset-0 z-40 cursor-default"
                ></div>

                <!-- Menu Dropdown -->
                <div 
                  v-if="showCategoryDropdown" 
                  @click.stop 
                  class="absolute top-full left-0 mt-1 w-48 bg-white border rounded shadow-xl z-50 max-h-60 overflow-y-auto p-2"
                >
                  <div class="flex justify-between mb-2 pb-1 border-b">
                    <span class="text-xs font-bold">Filtres</span>
                    <button @click="filters.ticketCategory = []" class="text-xs text-blue-600 hover:underline">Tout décocher</button>
                  </div>
                  <div v-for="cat in uniqueCategories" :key="cat" class="flex items-center gap-2 mb-1">
                    <input 
                      type="checkbox" 
                      :id="`cat-${cat}`" 
                      :value="cat" 
                      v-model="filters.ticketCategory"
                      class="cursor-pointer"
                    >
                    <label :for="`cat-${cat}`" class="text-xs cursor-pointer select-none flex-1 truncate" :title="cat">
                      {{ cat }}
                    </label>
                  </div>
                  <div v-if="uniqueCategories.length === 0" class="text-xs text-gray-500 italic">
                    Aucune catégorie
                  </div>
                </div>
              </div>
            </div>
          </th>
          <th @click="handleSort('priceAmount')" class="border px-2 py-1 text-left cursor-pointer hover:bg-gray-200 select-none align-top w-32">
            <div class="flex flex-col gap-1">
              <div class="flex justify-between items-center">
                <span>Prix</span>
                <span v-if="sortColumn === 'priceAmount'">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
              </div>
              <div class="flex flex-col gap-1" @click.stop>
                <div class="flex justify-between text-[10px] text-gray-500">
                  <span>{{ filters.priceMin }}</span>
                  <span>{{ filters.priceMax }}</span>
                </div>
                
                <div v-if="priceRange.max > priceRange.min" class="relative h-4 w-full">
                  <!-- Track background -->
                  <div class="absolute top-1/2 left-0 right-0 h-1 bg-gray-300 rounded -translate-y-1/2"></div>
                  <!-- Selected range -->
                  <div 
                    class="absolute top-1/2 h-1 bg-blue-500 rounded -translate-y-1/2 z-10"
                    :style="priceRangeStyle"
                  ></div>
                  
                  <!-- Input Min -->
                  <input 
                    type="range" 
                    v-model.number="filters.priceMin" 
                    :min="priceRange.min" 
                    :max="priceRange.max"
                    @input="updatePriceMin"
                    class="absolute top-0 left-0 w-full h-full appearance-none bg-transparent pointer-events-none z-20 slider-thumb"
                  />
                  <!-- Input Max -->
                  <input 
                    type="range" 
                    v-model.number="filters.priceMax" 
                    :min="priceRange.min" 
                    :max="priceRange.max"
                    @input="updatePriceMax"
                    class="absolute top-0 left-0 w-full h-full appearance-none bg-transparent pointer-events-none z-20 slider-thumb"
                  />
                </div>
                <div v-else class="text-xs text-gray-400 italic text-center">Fixe</div>
              </div>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in paginatedTickets" :key="t.id" class="hover:bg-gray-50">
          <td class="border px-2 py-1 text-xs">
            <span v-if="t.generatedAtRaw !== undefined">{{ formatDateTime(t.generatedAtRaw) }}</span>
            <span v-else-if="t.createdAtRaw !== undefined" class="text-gray-400" title="Date de réception (generatedAt manquant)">
              {{ formatDateTime(t.createdAtRaw) }}*
            </span>
            <span v-else>—</span>
          </td>
          <td class="border px-2 py-1 font-mono text-xs">
            {{ t.ticketNumber ?? "—" }}
            <div v-if="t.cancellationReason" class="text-red-600 font-bold text-xs mt-1">
              ANNULÉ: {{ t.cancellationReason }}
            </div>
          </td>
          <td class="border px-2 py-1">
            <div class="font-bold">{{ t.eventName ?? "—" }}</div>
            <div class="text-xs text-gray-500">
              {{ t.sessionDate ?? "—" }} <span v-if="t.sessionTime">à {{ t.sessionTime }}</span>
            </div>
          </td>
          <td class="border px-2 py-1">
            <div v-if="t.buyerFirstName || t.buyerLastName">
              {{ t.buyerFirstName }} {{ t.buyerLastName }}
              <div v-if="t.buyerEmail" class="text-xs text-blue-600">{{ t.buyerEmail }}</div>
              <div v-if="t.buyerPostcode" class="text-xs text-gray-500">{{ t.buyerPostcode }}</div>
            </div>
            <span v-else>—</span>
          </td>
          <td class="border px-2 py-1">{{ t.ticketCategory ?? "—" }}</td>
          <td class="border px-2 py-1 whitespace-nowrap">
            <span v-if="typeof t.priceAmount === 'number'">
              {{ formatPrice(t.priceAmount, t.priceCurrency) }}
            </span>
            <span v-else>—</span>
          </td>
        </tr>
        <tr v-if="tickets.length === 0 && !loading">
          <td class="border px-2 py-1 text-center py-4" colspan="6">Aucun ticket trouvé.</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination Controls -->
    <div v-if="!loading && tickets.length > 0" class="mt-4 flex justify-between items-center text-sm">
      <div class="flex items-center gap-2">
        <span>Afficher</span>
        <select v-model.number="itemsPerPage" class="border rounded px-1 py-0.5">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
        <span>tickets par page</span>
      </div>

      <div class="flex items-center gap-2">
        <button 
          @click="currentPage--" 
          :disabled="currentPage === 1"
          class="px-2 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Précédent
        </button>
        <span>Page {{ currentPage }} sur {{ totalPages || 1 }}</span>
        <button 
          @click="currentPage++" 
          :disabled="currentPage >= totalPages"
          class="px-2 py-1 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Suivant
        </button>
      </div>
      
      <div class="text-gray-500">
        Total: {{ sortedTickets.length }} ticket(s) filtré(s)
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
