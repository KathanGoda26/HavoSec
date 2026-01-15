<template>
  <aside
    class="sidebar"
    :class="{ 'collapsed': isCollapsed }"
  >
    <div class="sidebar-header">
      <div class="logo-wrapper">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L2 7V12C2 17 6 21 12 22C18 21 22 17 22 12V7L12 2Z"/>
          </svg>
        </div>
        <transition name="fade">
          <span v-if="!isCollapsed" class="logo-text">HavoSec</span>
        </transition>
      </div>
      <button
        @click="toggleCollapse"
        class="collapse-btn"
        :title="isCollapsed ? 'Expand' : 'Collapse'"
      >
        <Bars3Icon v-if="isCollapsed" class="w-5 h-5" />
        <XMarkIcon v-else class="w-5 h-5" />
      </button>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section">
        <div v-if="!isCollapsed" class="nav-section-title">Main</div>
        <ul class="nav-list">
          <li v-for="item in mainNavItems" :key="item.name">
            <router-link
              :to="item.path"
              class="nav-item"
              :class="{ 'active': $route.path === item.path }"
              :title="isCollapsed ? item.name : ''"
            >
              <component :is="item.icon" class="nav-icon" />
              <transition name="fade">
                <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
              </transition>
              <span v-if="item.badge && !isCollapsed" class="nav-badge">{{ item.badge }}</span>
            </router-link>
          </li>
        </ul>
      </div>

      <div class="nav-section">
        <div v-if="!isCollapsed" class="nav-section-title">Analytics</div>
        <ul class="nav-list">
          <li v-for="item in analyticsNavItems" :key="item.name">
            <router-link
              :to="item.path"
              class="nav-item"
              :class="{ 'active': $route.path === item.path }"
              :title="isCollapsed ? item.name : ''"
            >
              <component :is="item.icon" class="nav-icon" />
              <transition name="fade">
                <span v-if="!isCollapsed" class="nav-text">{{ item.name }}</span>
              </transition>
            </router-link>
          </li>
        </ul>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="user-profile">
        <div class="user-avatar">
          {{ userInitials }}
        </div>
        <transition name="fade">
          <div v-if="!isCollapsed" class="user-info">
            <div class="user-name">{{ user?.firstName }} {{ user?.lastName }}</div>
            <div class="user-role">{{ user?.role }}</div>
          </div>
        </transition>
      </div>

      <div class="sidebar-actions">
        <button
          @click="toggleTheme"
          class="action-btn"
          :title="isDark ? 'Light Mode' : 'Dark Mode'"
        >
          <component :is="isDark ? SunIcon : MoonIcon" class="w-5 h-5" />
        </button>
        <button
          @click="handleLogout"
          class="action-btn logout"
          title="Logout"
        >
          <ArrowRightOnRectangleIcon class="w-5 h-5" />
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import {
  HomeIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  HeartIcon,
  DocumentTextIcon,
  CogIcon,
  SunIcon,
  MoonIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const isCollapsed = ref(false)
const isDark = computed(() => themeStore.isDark)
const user = computed(() => authStore.user)

const userInitials = computed(() => {
  if (!user.value) return 'U'
  return `${user.value.firstName?.[0] || ''}${user.value.lastName?.[0] || ''}`.toUpperCase()
})

const mainNavItems = [
  { name: 'Overview', path: '/dashboard/overview', icon: HomeIcon },
  { name: 'Attack Insights', path: '/dashboard/attack-insights', icon: ShieldCheckIcon, badge: '12' },
  { name: 'Defense Metrics', path: '/dashboard/defense-metrics', icon: ChartBarIcon },
  { name: 'System Health', path: '/dashboard/system-health', icon: HeartIcon },
]

const analyticsNavItems = [
  { name: 'Activity Logs', path: '/dashboard/activity-logs', icon: DocumentTextIcon },
  { name: 'Settings', path: '/dashboard/settings', icon: CogIcon },
]

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function toggleTheme() {
  themeStore.toggleTheme()
}

async function handleLogout() {
  authStore.logout()
  await router.push('/')
}
</script>

<style scoped>
.sidebar {
  @apply fixed left-0 top-0 h-screen bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-all duration-300 z-50;
  width: 260px;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  @apply flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800;
  min-height: 70px;
}

.logo-wrapper {
  @apply flex items-center gap-3;
}

.logo-icon {
  @apply w-8 h-8 text-purple-600 dark:text-purple-400 flex-shrink-0;
}

.logo-text {
  @apply text-xl font-bold text-gray-900 dark:text-white;
}

.collapse-btn {
  @apply p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors;
}

.sidebar-nav {
  @apply flex-1 overflow-y-auto py-4;
}

.nav-section {
  @apply mb-6;
}

.nav-section-title {
  @apply px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider;
}

.nav-list {
  @apply space-y-1 px-2;
}

.nav-item {
  @apply flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-700 dark:text-gray-300 transition-all duration-200 relative;
  @apply hover:bg-gray-100 dark:hover:bg-gray-800;
}

.nav-item.active {
  @apply bg-gradient-to-r from-purple-500 to-green-500 text-white;
  @apply shadow-lg shadow-purple-500/20;
}

.nav-icon {
  @apply w-5 h-5 flex-shrink-0;
}

.nav-text {
  @apply flex-1 text-sm font-medium;
}

.nav-badge {
  @apply px-2 py-0.5 text-xs font-semibold rounded-full bg-red-500 text-white;
}

.sidebar-footer {
  @apply p-4 border-t border-gray-200 dark:border-gray-800 space-y-3;
}

.user-profile {
  @apply flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800;
}

.user-avatar {
  @apply w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-green-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0;
}

.user-info {
  @apply flex-1 min-w-0;
}

.user-name {
  @apply text-sm font-semibold text-gray-900 dark:text-white truncate;
}

.user-role {
  @apply text-xs text-gray-500 dark:text-gray-400 capitalize;
}

.sidebar-actions {
  @apply flex gap-2;
}

.action-btn {
  @apply flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-gray-700 dark:text-gray-300;
  @apply hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors;
}

.action-btn.logout {
  @apply text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20;
}

/* Collapsed state */
.sidebar.collapsed .logo-text,
.sidebar.collapsed .nav-text,
.sidebar.collapsed .nav-section-title,
.sidebar.collapsed .user-info,
.sidebar.collapsed .nav-badge {
  @apply hidden;
}

.sidebar.collapsed .nav-item {
  @apply justify-center;
}

.sidebar.collapsed .sidebar-actions {
  @apply flex-col;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Scrollbar */
.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-track {
  @apply bg-transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  @apply bg-gray-300 dark:bg-gray-700 rounded-full;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-400 dark:bg-gray-600;
}
</style>