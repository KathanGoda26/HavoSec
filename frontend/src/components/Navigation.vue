<template>
  <header
    ref="headerRef"
    class="header-container"
    :class="{
      scrolled: isScrolled,
      reduced: isReduced,
    }"
  >
    <nav class="nav-content">
      <!-- Left Side - Logo + Name -->
      <div class="nav-left">
        <router-link to="/" class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12 2L2 7V12C2 17 6 21 12 22C18 21 22 17 22 12V7L12 2Z"
              />
            </svg>
          </div>
          <span class="logo-text">HavoSec</span>
        </router-link>
      </div>

      <!-- Center - Navigation Links (Hidden when reduced) -->
      <div v-if="!isReduced" class="nav-center">
        <router-link
          v-for="link in navLinks"
          :key="link.name"
          :to="link.path"
          class="nav-link"
          :data-testid="`nav-${link.name.toLowerCase()}`"
        >
          {{ link.name }}
        </router-link>
      </div>

      <!-- Right Side -->
      <div class="nav-right">
        <!-- Theme Toggle (Always Visible) -->
        <button
          @click="toggleTheme"
          class="theme-toggle"
          :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
          data-testid="theme-toggle"
        >
          <component :is="isDark ? SunIcon : MoonIcon" class="w-5 h-5" />
        </button>

        <!-- Book Demo (Hidden when reduced) -->
        <router-link
          v-if="!isReduced"
          to="/book-demo"
          class="book-demo-btn nav-link"
          data-testid="book-demo-button"
        >
          Book Demo
        </router-link>

        <!-- Auth Section (Hidden when reduced) -->
        <div v-if="!isReduced" class="auth-section">
          <div v-if="!isAuthenticated" class="auth-buttons">
            <router-link
              to="/auth/login"
              class="auth-btn login-btn nav-link"
              data-testid="login-button "
            >
              Login
            </router-link>
          </div>

          <div v-else class="user-menu relative" ref="userMenuRef">
            <button
              @click="toggleUserMenu"
              class="user-avatar"
              data-testid="user-menu-button"
            >
              <span class="avatar-text">{{ userInitials }}</span>
            </button>

            <div v-if="showUserMenu" class="user-dropdown">
              <div class="user-info">
                <p class="user-name">
                  {{ user?.firstName }} {{ user?.lastName }}
                </p>
                <p class="user-role">{{ user?.role }}</p>
              </div>
              <div class="menu-divider"></div>
              <router-link
                to="/dashboard"
                class="menu-item"
                @click="showUserMenu = false"
                data-testid="dashboard-link"
              >
                Dashboard
              </router-link>
              <router-link
                to="/dashboard/settings"
                class="menu-item"
                @click="showUserMenu = false"
                data-testid="settings-link"
              >
                Settings
              </router-link>
              <div class="menu-divider"></div>
              <button
                @click="handleLogout"
                class="menu-item logout-item"
                data-testid="logout-button"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useThemeStore } from "@/stores/theme";
import { useAuthStore } from "@/stores/auth";
import { SunIcon, MoonIcon } from "@heroicons/vue/24/outline";
import LuxuryButton from "@/components/LuxuryButton.vue";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();

const headerRef = ref(null);
const userMenuRef = ref(null);
const isScrolled = ref(false);
const isReduced = ref(false);
const showUserMenu = ref(false);

const isDark = computed(() => themeStore.isDark);
const isAuthenticated = computed(() => authStore.isAuthenticated());
const user = computed(() => authStore.user);

const userInitials = computed(() => {
  if (!user.value) return "U";
  return `${user.value.firstName?.[0] || ""}${user.value.lastName?.[0] || ""}`.toUpperCase();
});

const navLinks = [
  { name: "Home", path: "/" },
  { name: "About", path: "/about" },
  { name: "Blog", path: "/blog" },
];

function handleScroll() {
  const scrollY = window.scrollY;
  const maxScroll = 300;
  const scrollProgress = Math.min(scrollY / maxScroll, 1);

  isScrolled.value = scrollY > 50;
  isReduced.value = scrollY > 200;

  if (headerRef.value) {
    const minWidth = 40;
    const maxWidth = 100;
    const width = maxWidth - scrollProgress * (maxWidth - minWidth);

    const minOpacity = 0.7;
    const maxOpacity = 0.95;
    const opacity = maxOpacity - scrollProgress * (maxOpacity - minOpacity);

    headerRef.value.style.setProperty("--header-width", `${width}%`);
    headerRef.value.style.setProperty("--header-opacity", opacity);
  }
}

function toggleTheme() {
  themeStore.toggleTheme();
}

function toggleUserMenu() {
  showUserMenu.value = !showUserMenu.value;
}

async function handleLogout() {
  authStore.logout();
  showUserMenu.value = false;
  await router.push("/");
}

function handleClickOutside(event) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showUserMenu.value = false;
  }
}

function initScrollTrigger() {
  if (typeof window === "undefined" || !headerRef.value) return;

  gsap.timeline({
    scrollTrigger: {
      trigger: "body",
      start: "top top",
      end: "+=300",
      scrub: true,
      onUpdate: (self) => {
        const progress = self.progress;
        isScrolled.value = progress > 0.1;
        isReduced.value = progress > 0.5;

        if (headerRef.value) {
          const minWidth = 40;
          const maxWidth = 100;
          const width = maxWidth - progress * (maxWidth - minWidth);

          const minOpacity = 0.7;
          const maxOpacity = 0.95;
          const opacity = maxOpacity - progress * (maxOpacity - minOpacity);

          headerRef.value.style.setProperty("--header-width", `${width}%`);
          headerRef.value.style.setProperty("--header-opacity", opacity);
        }
      },
    },
  });
}

onMounted(() => {
  window.addEventListener("scroll", handleScroll);
  document.addEventListener("click", handleClickOutside);
  handleScroll();
  setTimeout(() => initScrollTrigger(), 100);
});

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll);
  document.removeEventListener("click", handleClickOutside);
  if (typeof ScrollTrigger !== "undefined") {
    ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
  }
});
</script>

<style scoped>
.header-container {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: var(--header-width, 100%);
  height: 80px;
  z-index: 1000;
  background: rgba(255, 255, 255, var(--header-opacity, 0.95));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(103, 62, 230, 0.15);
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition: all 0.4s ease;
}

.dark .header-container {
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(126, 99, 119, 0.3);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 2rem;
}

.nav-left,
.nav-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  font-weight: 700;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: #673ee6;
}

.logo-text {
  /* inherit Ubuntu */
  font-size: 2rem;
  color: #374151;
}

.dark .logo-text {
  color: #f9fafb;
}

.nav-center {
  display: flex;
  gap: 2rem;
  flex: 1;
  justify-content: center;
}

.nav-link {
  color: #6b7280;
  text-decoration: none;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: #673ee6;
  /* background: rgba(103, 62, 230, 0.1); */
}

.dark .nav-link {
  color: #ffffff;
}

.dark .nav-link:hover,
.dark .nav-link.router-link-active {
  color: #00b090;
}

.theme-toggle {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 0.5rem;
  background: rgba(103, 62, 230, 0.1);
  border: 1px solid rgba(103, 62, 230, 0.2);
  cursor: pointer;
  color: #673ee6;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.theme-toggle:hover {
  background: rgba(103, 62, 230, 0.2);
  border-color: rgba(103, 62, 230, 0.4);
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(103, 62, 230, 0.2);
}

.theme-toggle:active {
  transform: scale(0.95);
}

.dark .theme-toggle {
  color: #00b090;
  background: rgba(0, 176, 144, 0.15);
  border-color: rgba(0, 176, 144, 0.3);
}

.dark .theme-toggle:hover {
  background: rgba(0, 176, 144, 0.25);
  border-color: rgba(0, 176, 144, 0.5);
  box-shadow: 0 2px 8px rgba(0, 176, 144, 0.3);
}

.auth-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.auth-buttons {
  display: flex;
  gap: 0.5rem;
}

.auth-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
}

.login-btn {
  color: #673ee6;
  /* border: 1px solid rgba(103, 62, 230, 0.3); */
}

/* .login-btn:hover {
  background: rgba(103, 62, 230, 0.1);
} */

.user-menu {
  position: relative;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #673ee6, #00b090);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(103, 62, 230, 0.3);
}

.user-dropdown {
  position: absolute;
  top: 55px;
  right: 0;
  min-width: 200px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(103, 62, 230, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 0.5rem;
  z-index: 1001;
}

.dark .user-dropdown {
  background: rgba(0, 0, 0, 0.95);
  border-color: rgba(103, 62, 230, 0.3);
}

.user-info {
  padding: 0.75rem;
}

.user-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.25rem;
}

.dark .user-name {
  color: #f9fafb;
}

.user-role {
  font-size: 0.875rem;
  color: #6b7280;
}

.dark .user-role {
  color: #9ca3af;
}

.menu-divider {
  height: 1px;
  background: rgba(103, 62, 230, 0.1);
  margin: 0.5rem 0;
}

.menu-item {
  display: block;
  width: 100%;
  padding: 0.75rem;
  text-align: left;
  color: #374151;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
}

.menu-item:hover {
  background: rgba(103, 62, 230, 0.1);
  color: #673ee6;
}

.dark .menu-item {
  color: #f9fafb;
}

.dark .menu-item:hover {
  background: rgba(0, 176, 144, 0.1);
  color: #00b090;
}

.logout-item {
  color: #ef4444;
}

.logout-item:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* Responsive */
@media (max-width: 768px) {
  .header-container {
    width: 95% !important;
  }

  .nav-center {
    display: none;
  }

  .book-demo-btn {
    display: none;
  }
}
</style>
