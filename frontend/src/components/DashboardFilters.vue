<template>
  <div class="filter-panel space-y-4">
    <div class="flex justify-between items-center">
      <h2 class="text-base font-semibold text-zinc-900">Filtres</h2>
      <button 
        @click="resetFilters"
        class="btn-ghost text-xs"
      >
        Réinitialiser
      </button>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Event Filter with Date -->
      <div class="relative" ref="eventsDropdownRef">
        <label class="filter-label">Événements</label>
        
        <div class="relative">
          <button 
            @click="showEventsDropdown = !showEventsDropdown" 
            class="select-trigger"
            :class="{ 'ring-2 ring-zinc-900/10 border-zinc-400': showEventsDropdown }"
          >
            <span class="block truncate text-left">
              {{ selectedEvents.length ? `${selectedEvents.length} sélectionné(s)` : 'Sélectionner des événements' }}
            </span>
            <svg class="h-4 w-4 text-zinc-400 shrink-0" :class="{ 'rotate-180': showEventsDropdown }" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
            </svg>
          </button>

          <transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div v-if="showEventsDropdown" class="dropdown-menu custom-scrollbar">
              <!-- Search Input -->
              <div class="p-2 border-b border-zinc-100 sticky top-0 bg-white z-10">
                <input 
                  type="text" 
                  v-model="searchQuery" 
                  placeholder="Rechercher un événement..." 
                  class="input"
                  @click.stop
                />
              </div>

              <!-- Select All Option -->
              <div 
                class="dropdown-item border-b border-zinc-100 font-medium text-zinc-900"
                @click="toggleAllEvents"
              >
                <input 
                  type="checkbox" 
                  :checked="areAllEventsSelected"
                  class="checkbox"
                  @click.stop
                />
                <span>
                  {{ areAllEventsSelected ? 'Tout désélectionner' : 'Tout sélectionner' }}
                </span>
              </div>

              <div 
                v-for="event in filteredEvents" 
                :key="event.name" 
                class="dropdown-item"
                :class="{ 'dropdown-item-active': selectedEvents.includes(event.name) }"
                @click="toggleEvent(event.name)"
              >
                <input 
                  type="checkbox" 
                  :checked="selectedEvents.includes(event.name)"
                  class="checkbox"
                  @click.stop
                />
                <span class="truncate flex-1">
                  {{ event.name }}
                </span>
                <span class="text-xs text-zinc-400 shrink-0">{{ event.date }}</span>
              </div>

              <div v-if="filteredEvents.length === 0" class="px-3 py-4 text-sm text-zinc-500 text-center">
                Aucun événement trouvé
              </div>
            </div>
          </transition>
        </div>
      </div>

      <!-- Category Filter -->
      <div class="relative" ref="categoriesDropdownRef">
        <label class="filter-label">Catégories</label>
        <div class="relative">
          <button 
            @click="showCategoriesDropdown = !showCategoriesDropdown" 
            class="select-trigger"
            :class="{ 'ring-2 ring-zinc-900/10 border-zinc-400': showCategoriesDropdown }"
          >
            <span class="block truncate text-left">
              {{ selectedCategories.length ? `${selectedCategories.length} sélectionné(s)` : 'Sélectionner des catégories' }}
            </span>
            <svg class="h-4 w-4 text-zinc-400 shrink-0" :class="{ 'rotate-180': showCategoriesDropdown }" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
            </svg>
          </button>

          <transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div v-if="showCategoriesDropdown" class="dropdown-menu custom-scrollbar">
              <div 
                v-for="category in categories" 
                :key="category" 
                class="dropdown-item"
                :class="{ 'dropdown-item-active': selectedCategories.includes(category) }"
                @click="toggleCategory(category)"
              >
                <input 
                  type="checkbox" 
                  :checked="selectedCategories.includes(category)"
                  class="checkbox"
                  @click.stop
                />
                <span class="truncate">
                  {{ category }}
                </span>
              </div>

              <div v-if="categories.length === 0" class="px-3 py-4 text-sm text-zinc-500 text-center">
                Aucune catégorie disponible
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';

const props = defineProps({
  events: {
    type: Array,
    default: () => []
  },
  categories: {
    type: Array,
    default: () => []
  },
  initialFilters: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['update:filters']);

const selectedEvents = ref([]);
const selectedCategories = ref([]);
const searchQuery = ref('');

const showEventsDropdown = ref(false);
const showCategoriesDropdown = ref(false);
const eventsDropdownRef = ref(null);
const categoriesDropdownRef = ref(null);
const hasInitializedCategories = ref(false);

function asStringArray(value) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean);
  if (typeof value === 'string') return value ? [value] : [];
  return [];
}

// Apply initial filters from parent (e.g. URL restore)
watch(
  () => props.initialFilters,
  (next) => {
    if (!next || typeof next !== 'object') return;

    if (Object.prototype.hasOwnProperty.call(next, 'selectedEvents')) {
      selectedEvents.value = asStringArray(next.selectedEvents);
    }

    if (Object.prototype.hasOwnProperty.call(next, 'selectedCategories')) {
      selectedCategories.value = asStringArray(next.selectedCategories);
      hasInitializedCategories.value = true;
    }
  },
  { immediate: true, deep: true }
);

const filteredEvents = computed(() => {
  if (!searchQuery.value) return props.events;
  const query = searchQuery.value.toLowerCase();
  return props.events.filter(event => 
    event.name.toLowerCase().includes(query)
  );
});

// Initialize categories selection when data is available
watch(() => props.categories, (newVal) => {
  if (newVal.length > 0 && !hasInitializedCategories.value) {
    selectedCategories.value = [...newVal];
    hasInitializedCategories.value = true;
  } else if (newVal.length > 0 && hasInitializedCategories.value) {
    // Keep selection in sync with available categories
    const allowed = new Set(newVal);
    selectedCategories.value = selectedCategories.value.filter(c => allowed.has(c));
  }
}, { immediate: true });

const areAllEventsSelected = computed(() => {
  if (filteredEvents.value.length === 0) return false;
  return filteredEvents.value.every(e => selectedEvents.value.includes(e.name));
});

function toggleAllEvents() {
  if (areAllEventsSelected.value) {
    // Deselect all visible events
    const visibleNames = filteredEvents.value.map(e => e.name);
    selectedEvents.value = selectedEvents.value.filter(name => !visibleNames.includes(name));
  } else {
    // Select all visible events
    const visibleNames = filteredEvents.value.map(e => e.name);
    const newSelection = new Set([...selectedEvents.value, ...visibleNames]);
    selectedEvents.value = Array.from(newSelection);
  }
}

function toggleEvent(eventName) {
  if (selectedEvents.value.includes(eventName)) {
    selectedEvents.value = selectedEvents.value.filter(e => e !== eventName);
  } else {
    selectedEvents.value.push(eventName);
  }
}

function toggleCategory(category) {
  if (selectedCategories.value.includes(category)) {
    selectedCategories.value = selectedCategories.value.filter(c => c !== category);
  } else {
    selectedCategories.value.push(category);
  }
}

function resetFilters() {
  selectedEvents.value = [];
  selectedCategories.value = [...props.categories];
  searchQuery.value = '';
}

function emitFilters() {
  emit('update:filters', {
    selectedEvents: selectedEvents.value,
    selectedCategories: selectedCategories.value
  });
}

// Watch for changes and emit
watch([selectedEvents, selectedCategories], () => {
  emitFilters();
}, { deep: true });

// Close dropdowns when clicking outside
function handleClickOutside(event) {
  if (eventsDropdownRef.value && !eventsDropdownRef.value.contains(event.target)) {
    showEventsDropdown.value = false;
  }
  if (categoriesDropdownRef.value && !categoriesDropdownRef.value.contains(event.target)) {
    showCategoriesDropdown.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>
