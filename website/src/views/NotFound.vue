<template>
  <div class="not-found-page">
    <div class="container">
      <div class="not-found-content" data-testid="not-found-content">
        <div class="error-icon">
          <ShieldExclamationIcon class="w-24 h-24 text-purple-500" />
        </div>
        
        <h1 class="error-title">404 - Page Not Found</h1>
        <p class="error-description">
          The page you're looking for seems to have been moved, deleted, or doesn't exist.
        </p>
        
        <div class="error-actions">
          <LuxuryButton 
            @click="goHome"
            size="lg"
            data-testid="go-home-button"
          >
            Return Home
          </LuxuryButton>
          
          <LuxuryButton 
            @click="goBack"
            variant="outline"
            size="lg"
            data-testid="go-back-button"
          >
            Go Back
          </LuxuryButton>
        </div>
        
        <div class="helpful-links">
          <h3 class="links-title">You might be looking for:</h3>
          <div class="links-grid">
            <router-link 
              v-for="link in helpfulLinks" 
              :key="link.name"
              :to="link.path" 
              class="helpful-link"
              :data-testid="`link-${link.name.toLowerCase().replace(/\s+/g, '-')}`"
            >
              <component :is="link.icon" class="link-icon" />
              <span>{{ link.name }}</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import LuxuryButton from '@/components/LuxuryButton.vue'
import { 
  ShieldExclamationIcon,
  HomeIcon,
  InformationCircleIcon,
  ChatBubbleLeftRightIcon,
  CalendarDaysIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()

const helpfulLinks = [
  { name: 'Home', path: '/', icon: HomeIcon },
  { name: 'About Us', path: '/about', icon: InformationCircleIcon },
  { name: 'Blog', path: '/blog', icon: ChatBubbleLeftRightIcon },
  { name: 'Book Demo', path: '/book-demo', icon: CalendarDaysIcon }
]

function goHome() {
  router.push('/')
}

function goBack() {
  router.go(-1)
}
</script>

<style scoped>
.not-found-page {
  @apply min-h-screen flex items-center justify-center py-20;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(16, 185, 129, 0.05));
}

.dark .not-found-page {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(16, 185, 129, 0.1));
}

.container {
  @apply max-w-4xl mx-auto px-6;
}

.not-found-content {
  @apply text-center;
}

.error-icon {
  @apply mb-8;
}

.error-title {
  @apply text-4xl md:text-6xl font-bold mb-6;
  font-family: 'Playfair Display', serif;
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.error-description {
  @apply text-xl text-gray-600 mb-12 max-w-2xl mx-auto leading-relaxed;
}

.dark .error-description {
  @apply text-gray-300;
}

.error-actions {
  @apply flex flex-col sm:flex-row justify-center gap-4 mb-16;
}

.helpful-links {
  @apply mt-16;
}

.links-title {
  @apply text-2xl font-bold mb-8;
  color: #1a202c;
}

.dark .links-title {
  color: #f7fafc;
}

.links-grid {
  @apply grid grid-cols-2 md:grid-cols-4 gap-4;
}

.helpful-link {
  @apply flex flex-col items-center gap-3 p-6 rounded-xl no-underline transition-all duration-300 hover:scale-105;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #6b7280;
}

.dark .helpful-link {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  color: #9ca3af;
}

.helpful-link:hover {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
  border-color: rgba(139, 92, 246, 0.3);
}

.dark .helpful-link:hover {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.link-icon {
  @apply w-8 h-8;
}

/* Responsive Design */
@media (max-width: 640px) {
  .error-actions {
    @apply flex-col gap-3;
  }
  
  .links-grid {
    @apply grid-cols-1 gap-3;
  }
}
</style>