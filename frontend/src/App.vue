<template>
  <div id="app" :class="{ 'dark': isDark }">
    <LoaderOverlay v-if="ui.isLoading" />
    <Layout />
  </div>
</template>

<script setup>
import { ref, onMounted, provide } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { useUiStore } from '@/stores/ui'
import Layout from '@/components/Layout.vue'
import LoaderOverlay from '@/components/LoaderOverlay.vue'

const themeStore = useThemeStore()
const ui = useUiStore()

// Provide theme reactivity to all components
const isDark = ref(themeStore.isDark)
provide('isDark', isDark)

// Initialize theme
onMounted(() => {
  themeStore.initializeTheme()
  // brief initial loading fade-in to avoid flash of unstyled content
  ui.startLoading()
  setTimeout(() => ui.stopLoading(), 400)
})

// Watch for theme changes
themeStore.$subscribe(() => {
  isDark.value = themeStore.isDark
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
  line-height: 1.6;
  transition: all 0.3s ease;
}

#app {
  background-color: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1a202c);
  min-height: 100vh;
  transition: background-color 0.3s ease, color 0.3s ease;
}

#app.dark {
  background-color: var(--bg-primary, #000000);
  color: var(--text-primary, #f7fafc);
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #7c3aed, #059669);
}
</style>