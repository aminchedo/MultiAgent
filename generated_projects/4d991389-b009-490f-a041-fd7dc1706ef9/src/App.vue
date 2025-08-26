<template>
  <div class="light min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="container mx-auto px-4">
    <Features />
    <Footer />
    <CTA />
    <Hero />
    </div>
  </div>
</template>

<script setup lang="ts">
import Features from './components/Features.vue'
import Footer from './components/Footer.vue'
import CTA from './components/CTA.vue'
import Hero from './components/Hero.vue'
</script>

<style scoped>
</style>