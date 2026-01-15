<template>
  <div class="layout-container">
    <Navigation v-if="showNavigation" />
    
    <main 
      class="main-content"
      :class="{
        'with-nav': showNavigation,
        'full-page': !showNavigation
      }"
    >
      <router-view v-slot="{ Component }">
        <transition
          name="page"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <Footer v-if="showNavigation" />

    <!-- Global Toast/Notification Container -->
    <div id="toast-container" class="toast-container">
      <!-- Toasts will be dynamically added here -->
    </div>

    <!-- Global Loading Overlay -->
    <div v-if="globalLoading" class="global-loading">
      <div class="loading-content">
        <div class="loading-spinner-large"></div>
        <p class="loading-text">{{ loadingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const globalLoading = ref(false)
const loadingMessage = ref('Loading...')

const showNavigation = computed(() => {
  // Hide navigation on auth pages and dashboard
  const hideNavRoutes = ['/auth/login', '/auth/register']
  const isDashboard = route.path.startsWith('/dashboard')
  
  return !hideNavRoutes.includes(route.path) && !isDashboard
})

// Global loading methods
function showGlobalLoading(message = 'Loading...') {
  loadingMessage.value = message
  globalLoading.value = true
}

function hideGlobalLoading() {
  globalLoading.value = false
}

// Expose methods to be used by other components
defineExpose({
  showGlobalLoading,
  hideGlobalLoading
})
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  background-color: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1a202c);
  transition: background-color 0.3s ease, color 0.3s ease;
}

.dark .layout-container {
  background-color: var(--bg-primary, #000000);
  color: var(--text-primary, #f7fafc);
}

.main-content {
  min-height: 100vh;
}

.main-content.with-nav {
  padding-top: 120px; /* Space for floating header */
}

.main-content.full-page {
  padding-top: 0;
}

/* Page Transitions */
.page-enter-active,
.page-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.95);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-30px) scale(0.95);
}

/* Toast Container */
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  pointer-events: none;
}

/* Global Loading Overlay */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-spinner-large {
  @apply w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto mb-4;
}

.loading-text {
  @apply text-lg font-medium;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .main-content.with-nav {
    padding-top: 300px;
  }
  
  .toast-container {
    top: 0.5rem;
    right: 0.5rem;
    left: 0.5rem;
  }
}

/* Scrollbar for main content */
.main-content {
  scrollbar-width: thin;
  scrollbar-color: rgba(139, 92, 246, 0.5) transparent;
}

.main-content::-webkit-scrollbar {
  width: 6px;
}

.main-content::-webkit-scrollbar-track {
  background: transparent;
}

.main-content::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #7c3aed, #059669);
}
</style>