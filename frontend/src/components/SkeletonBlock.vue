<template>
  <div
    aria-hidden="true"
    :class="['animate-pulse rounded-md bg-zinc-200', className]"
  />
</template>

<script setup>
defineProps({
  className: { type: String, default: '' },
});
</script>
