<template>
  <div class="home-page">
    <!-- Hero Section with 3D Animation -->
    <section class="hero-section" data-testid="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title" data-testid="hero-title">
            {{ heroTitle }}
            <span class="text-gradient">HavoSec</span>
          </h1>
          <p class="hero-description" data-testid="hero-description">
            {{ heroSubtitle }}
          </p>
        </div>
        
        <!-- 3D Lock Model -->
        <div class="hero-animation" data-testid="3d-animation">
          <Lock3D />
        </div>
      </div>
    </section>

    <!-- Achievements Section -->
    <section class="achievements-section glass" data-testid="achievements-section">
      <div class="container">
        <h2 class="section-title">Trusted by Industry Leaders</h2>
        <div class="achievements-grid">
          <div 
            v-for="achievement in achievements" 
            :key="achievement.id"
            class="achievement-card"
            :data-testid="`achievement-${achievement.id}`"
          >
            <div class="achievement-number">{{ achievement.number }}</div>
            <div class="achievement-label">{{ achievement.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features and Benefits -->
    <section class="features-section" ref="featuresSection" data-testid="features-section">
      <div class="container">
        <h2 class="section-title">{{ featuresTitle }}</h2>
        <div class="features-grid">
          <div 
            v-for="(feature, index) in displayFeatures" 
            :key="index"
            class="feature-card glass"
            :data-testid="`feature-${index}`"
          >
            <div class="feature-icon">
              <component :is="getFeatureIcon(index)" class="w-8 h-8" />
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-description">{{ feature.description }}</p>
            <div v-if="feature.benefit" class="feature-benefit">
              <strong>Benefit:</strong> {{ feature.benefit }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 3D Examples Gallery -->
    <!-- <section class="examples-section-3d" data-testid="examples-section">
      <div class="container">
        <h2 class="section-title">See HavoSec in Action</h2>
        <p class="section-subtitle">
          Explore our advanced cybersecurity solutions through interactive demonstrations
        </p>
        <ExamplesGallery3D />
      </div>
    </section> -->

    <!-- Schedule Demo Component -->
    <section class="demo-section glass" data-testid="demo-section">
      <div class="container">
        <div class="demo-content">
          <div class="demo-text">
            <h2 class="demo-title">Ready to Protect Your</h2>
            <h2 class="demo-title2">Organization?</h2>
            <p class="demo-description">
              Get a personalized demonstration of HavoSec 
              and see how we can strengthen your cybersecurity posture.
            </p>
            <LuxuryButton 
              @click="$router.push('/book-demo')"
              size="xl"
              data-testid="demo-cta-button"
            >
              Schedule Your Demo Today
            </LuxuryButton>
          </div>
          <div class="demo-image">
            <img 
              src="https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600&h=400&fit=crop&crop=center" 
              alt="Security Operations Center"
            />
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import LuxuryButton from '@/components/LuxuryButton.vue'
import ExamplesGallery3D from '@/components/ExamplesGallery3D.vue'
import Lock3D from '@/components/Lock3D.vue'
import { useContentStore } from '@/stores/content'
import { 
  ShieldCheckIcon, 
  EyeIcon, 
  BoltIcon, 
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

gsap.registerPlugin(ScrollTrigger)

const contentStore = useContentStore()
const featuresSection = ref(null)

// Icon mapping for features
const featureIcons = [ShieldCheckIcon, EyeIcon, BoltIcon, ChartBarIcon, ExclamationTriangleIcon, ClockIcon]

function getFeatureIcon(index) {
  return featureIcons[index % featureIcons.length]
}

// Dynamic content with fallbacks
const heroTitle = computed(() => {
  const title = contentStore.hero?.title || 'Secure Your Digital Assets with'
  // Remove "HavoSec" from API title if present to avoid duplication
  return title.replace(/\s*(HavoSec|with HavoSec)\s*$/i, '').trim() + ' '
})

const heroSubtitle = computed(() => 
  contentStore.hero?.subtitle || 'Advanced cybersecurity analytics and threat detection platform designed for modern organizations. Real-time monitoring, AI-powered insights, and automated defense mechanisms.'
)

const featuresTitle = computed(() => 
  contentStore.features?.title || 'Advanced Security Features'
)

const displayFeatures = computed(() => {
  if (contentStore.features?.items?.length) {
    return contentStore.features.items
  }
  // Fallback features
  return defaultFeatures
})

const achievements = [
  { id: 1, number: '50M+', label: 'Threats Blocked Daily' },
  { id: 2, number: '99.9%', label: 'Uptime Guarantee' },  
  { id: 3, number: '500+', label: 'Enterprise Clients' },
  { id: 4, number: '24/7', label: 'Security Monitoring' }
]

const defaultFeatures = [
  {
    title: 'Real-Time Threat Detection',
    description: 'AI-powered threat detection that identifies and blocks attacks in milliseconds.',
    benefit: 'Reduce security incidents by 95% with proactive threat prevention.'
  },
  {
    title: 'Advanced Monitoring',
    description: 'Comprehensive visibility across your entire digital infrastructure.',
    benefit: 'Complete security oversight with zero blind spots in your network.'
  },
  {
    title: 'Automated Response',
    description: 'Instant automated responses to security threats and incidents.',
    benefit: 'Minimize damage with response times under 10 seconds.'
  },
  {
    title: 'Analytics Dashboard',
    description: 'Rich analytics and reporting for security insights and compliance.',
    benefit: 'Make data-driven security decisions with comprehensive insights.'
  },
  {
    title: 'Incident Management',
    description: 'Streamlined incident response and investigation workflows.',
    benefit: 'Reduce incident resolution time by 80% with automated workflows.'
  },
  {
    title: '24/7 Monitoring',
    description: 'Round-the-clock security monitoring and threat hunting.',
    benefit: 'Never miss a threat with continuous security surveillance.'
  }
]

// Examples data removed - now using ExamplesGallery3D component

function scrollToFeatures() {
  featuresSection.value?.scrollIntoView({ behavior: 'smooth' })
}

function initScrollAnimations() {
  // Hero section animation
  gsap.fromTo('.hero-title', 
    { y: 100, opacity: 0 },
    { y: 0, opacity: 1, duration: 1, ease: 'power3.out' }
  )

  gsap.fromTo('.hero-description', 
    { y: 50, opacity: 0 },
    { y: 0, opacity: 1, duration: 1, delay: 0.3, ease: 'power3.out' }
  )

  gsap.fromTo('.hero-actions', 
    { y: 30, opacity: 0 },
    { y: 0, opacity: 1, duration: 1, delay: 0.6, ease: 'power3.out' }
  )

  // Achievements animation
  gsap.fromTo('.achievement-card',
    { y: 50, opacity: 0 },
    {
      y: 0,
      opacity: 1,
      duration: 0.8,
      stagger: 0.2,
      scrollTrigger: {
        trigger: '.achievements-section',
        start: 'top 80%'
      }
    }
  )

  // Features animation
  gsap.fromTo('.feature-card',
    { y: 50, opacity: 0, scale: 0.9 },
    {
      y: 0,
      opacity: 1,
      scale: 1,
      duration: 0.8,
      stagger: 0.15,
      scrollTrigger: {
        trigger: '.features-section',
        start: 'top 80%'
      }
    }
  )

  // 3D Examples Gallery animation
  gsap.fromTo('.examples-section-3d',
    { y: 50, opacity: 0 },
    {
      y: 0,
      opacity: 1,
      duration: 0.8,
      scrollTrigger: {
        trigger: '.examples-section-3d',
        start: 'top 80%'
      }
    }
  )
}

onMounted(() => {
  // Fetch dynamic content
  contentStore.fetchHero()
  contentStore.fetchFeatures()
  
  initScrollAnimations()
})

onUnmounted(() => {
  ScrollTrigger.killAll()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

/* Hero Section */
.hero-section {
  min-height: calc(100vh - 80px);
  @apply relative flex items-center justify-center;
  background: var(--bg-secondary, #f8f9fa);
  overflow: hidden;
  transition: background-color 0.3s ease;
}

.dark .hero-section {
  background: var(--bg-primary, #000000);
}

.hero-content {
  @apply container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center;
  max-width: 1200px;
}

.hero-text {
  @apply space-y-6;
}

.hero-title {
  @apply text-4xl md:text-6xl font-bold leading-tight;
  color: #1a202c;
}

.dark .hero-title {
  color: #f7fafc;
}

.hero-description {
  @apply text-xl text-gray-600 leading-relaxed;
}

.dark .hero-description {
  @apply text-gray-300;
}

.hero-actions {
  @apply flex flex-col sm:flex-row gap-4;
}

.hero-animation {
  @apply flex justify-center items-center;
  min-height: 520px;
  width: 100%;
}

/* Achievements Section */
.achievements-section {
  @apply py-20 my-20;
}

.achievements-grid {
  @apply grid grid-cols-2 md:grid-cols-4 gap-6 mt-12;
}

.achievement-card {
  @apply text-center p-6 rounded-xl;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.dark .achievement-card {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(126, 99, 119, 0.2);
}

.achievement-number {
  @apply text-3xl md:text-4xl font-bold mb-2;
  color: #00b090;
}

.achievement-label {
  @apply text-gray-600 font-medium;
}

.dark .achievement-label {
  @apply text-gray-300;
}

/* Features Section */
.features-section {
  @apply py-20;
}

.features-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12;
}

.feature-card {
  @apply p-8 rounded-xl transition-all duration-300 hover:scale-105;
}

.feature-icon {
  @apply mb-6 p-3 rounded-lg w-fit;
  background: #00b090;
  color: white;
}

.feature-title {
  @apply text-xl font-bold mb-4;
  color: #1a202c;
}

.dark .feature-title {
  color: #f7fafc;
}

.feature-description {
  @apply text-gray-600 mb-4 leading-relaxed;
}

.dark .feature-description {
  @apply text-gray-300;
}

.feature-benefit {
  @apply text-sm p-3 rounded-lg;
  background: rgba(126, 99, 119, 0.1);
  color: #ffffff;
}

.dark .feature-benefit {
  background: rgba(103, 62, 230, 0.2);
  color: #ffffff;
}

/* 3D Examples Gallery Section */
.examples-section-3d {
  @apply py-20;
}

.section-subtitle {
  @apply text-lg text-gray-600 text-center mb-12 max-w-3xl mx-auto;
}

.dark .section-subtitle {
  @apply text-gray-300;
}

/* Old example styles removed - now using ExamplesGallery3D component */

/* Demo Section */
.demo-section {
  @apply py-20 my-20;
}

.demo-content {
  @apply grid grid-cols-1 lg:grid-cols-2 gap-12 items-center;
}

.demo-title {
  @apply text-3xl md:text-4xl font-bold mb-6;
  color: #1a202c;
}

.dark .demo-title {
  color: #f7fafc;
}

.demo-title2 {
  @apply text-3xl md:text-4xl font-bold mb-6;
  color: #1a202c;
}

.dark .demo-title2 {
  color: #00b090;
}

.demo-description {
  @apply text-lg text-gray-600 mb-8 leading-relaxed;
}

.dark .demo-description {
  @apply text-gray-300;
}

.demo-image {
  @apply rounded-xl overflow-hidden;
}

.demo-image img {
  @apply w-full h-auto object-cover;
}

/* Common Styles */
.container {
  @apply max-w-7xl mx-auto px-6;
}

.section-title {
  @apply text-3xl md:text-4xl font-bold text-center mb-4;
  color: #1a202c;
}

.dark .section-title {
  color: #f7fafc;
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero-content {
    @apply grid-cols-1 text-center;
  }
  
  .hero-animation {
    @apply order-first;
    min-height: 360px;
  }
  
  .achievements-grid {
    @apply grid-cols-2;
  }
  
  .features-grid {
    @apply grid-cols-1;
  }
}
</style>