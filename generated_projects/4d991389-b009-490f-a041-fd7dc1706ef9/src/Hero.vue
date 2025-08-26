<template>
  <div :class="['p-4 rounded-lg shadow-sm', className]">
    <h2 class="text-xl font-semibold mb-2">Hero</h2>
    <p class="text-gray-600 dark:text-gray-300">
      This is the Hero component.
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  className?: string
}

withDefaults(defineProps<Props>(), {
  className: ''
})
</script>

<style scoped>
</style>