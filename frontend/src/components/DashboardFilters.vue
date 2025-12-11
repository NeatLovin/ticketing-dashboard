<template>
  <div class="bg-white p-4 rounded-lg shadow mb-6 space-y-4">
    <div class="flex justify-between items-center mb-2">
      <h2 class="text-lg font-semibold text-gray-700">Filtres</h2>
      <button 
        @click="resetFilters"
        class="text-sm text-blue-600 hover:text-blue-800 underline"
      >
        Réinitialiser
      </button>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Event Filter with Date -->
      <div class="relative" ref="eventsDropdownRef">
        <label class="block text-sm font-medium text-gray-700 mb-1">Événements</label>
        
        <div class="relative">
          <button 
            @click="showEventsDropdown = !showEventsDropdown" 
            class="w-full bg-white border border-gray-300 rounded-md py-2 px-3 text-left cursor-default focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm flex justify-between items-center"
          >
            <span class="block truncate">
              {{ selectedEvents.length ? `${selectedEvents.length} sélectionné(s)` : 'Sélectionner des événements' }}
            </span>
            <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
              <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 011.414 0L10 14.586l2.293-2.293a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </span>
          </button>
          <div v-if="showEventsDropdown" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
            <div 
              v-for="event in events" 
              :key="event.name" 
              class="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-blue-50"
              @click="toggleEvent(event.name)"
            >
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  :checked="selectedEvents.includes(event.name)"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span class="ml-3 block truncate font-normal">
                  {{ event.name }}
                  <span class="text-xs text-gray-500 ml-2">({{ event.date }})</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Category Filter -->
      <div class="relative" ref="categoriesDropdownRef">
        <label class="block text-sm font-medium text-gray-700 mb-1">Catégories</label>
        <div class="relative">
          <button 
            @click="showCategoriesDropdown = !showCategoriesDropdown" 
            class="w-full bg-white border border-gray-300 rounded-md py-2 px-3 text-left cursor-default focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm flex justify-between items-center"
          >
            <span class="block truncate">
              {{ selectedCategories.length ? `${selectedCategories.length} sélectionné(s)` : 'Sélectionner des catégories' }}
            </span>
            <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
              <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fill-rule="evenodd" d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 011.414 0L10 14.586l2.293-2.293a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </span>
          </button>
          <div v-if="showCategoriesDropdown" class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
            <div 
              v-for="category in categories" 
              :key="category" 
              class="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-blue-50"
              @click="toggleCategory(category)"
            >
              <div class="flex items-center">
                <input 
                  type="checkbox" 
                  :checked="selectedCategories.includes(category)"
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span class="ml-3 block truncate font-normal">
                  {{ category }}
                </span>
              </div>
            </div>
          </div>
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
  }
});

const emit = defineEmits(['update:filters']);

const selectedEvents = ref([]);
const selectedCategories = ref([]);

const showEventsDropdown = ref(false);
const showCategoriesDropdown = ref(false);
const eventsDropdownRef = ref(null);
const categoriesDropdownRef = ref(null);

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
  selectedCategories.value = [];
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
