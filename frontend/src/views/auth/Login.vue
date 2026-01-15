<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo and Header -->
      <div class="login-header" data-testid="login-header">
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7V12C2 17 6 21 12 22C18 21 22 17 22 12V7L12 2Z"/>
            </svg>
          </div>
          <h1 class="logo-text">HavoSec</h1>
        </div>
        <p class="login-subtitle">Access your security dashboard</p>
      </div>

      <!-- Login Form -->
      <div class="login-form-container glass" data-testid="login-form">
        <form @submit.prevent="handleLogin" class="login-form">
          <h2 class="form-title">Company Login</h2>
          <p class="form-description">
            This is a restricted access portal for authorized company personnel only.
          </p>

          <!-- Error Display -->
          <div v-if="error" class="error-banner" data-testid="error-message">
            <ExclamationTriangleIcon class="error-icon" />
            <span>{{ error }}</span>
          </div>

          <div class="form-group">
            <label for="email" class="form-label">Email Address</label>
            <input 
              id="email"
              v-model="form.email"
              type="email" 
              required
              autocomplete="email"
              class="form-input"
              :class="{ 'error': errors.email }"
              data-testid="email-input"
              placeholder="Enter your company email"
            />
            <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Password</label>
            <div class="password-input-container">
              <input 
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                class="form-input"
                :class="{ 'error': errors.password }"
                data-testid="password-input"
                placeholder="Enter your password"
              />
              <button 
                type="button"
                @click="showPassword = !showPassword"
                class="password-toggle"
                data-testid="password-toggle"
              >
                <component :is="showPassword ? EyeSlashIcon : EyeIcon" class="w-5 h-5" />
              </button>
            </div>
            <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
          </div>

          <div class="form-options">
            <label class="checkbox-container">
              <input 
                v-model="form.rememberMe"
                type="checkbox"
                data-testid="remember-me-checkbox"
              />
              <span class="checkmark"></span>
              Remember me
            </label>
            
            <button 
              type="button" 
              class="forgot-password-link"
              data-testid="forgot-password-link"
            >
              Forgot password?
            </button>
          </div>

          <LuxuryButton 
            type="submit"
            size="lg"
            :loading="loading"
            :disabled="!isFormValid"
            class="w-full"
            data-testid="login-submit-button"
          >
            Sign In
          </LuxuryButton>

          <!-- Registration Link -->
          <div class="register-section">
            <p class="register-text">
              Don't have an account? 
              <router-link 
                to="/auth/register" 
                class="register-link"
                data-testid="register-link"
              >
                Request Access
              </router-link>
            </p>
          </div>
        </form>
      </div>

      <!-- Security Notice -->
      <div class="security-notice glass">
        <ShieldCheckIcon class="notice-icon" />
        <div class="notice-content">
          <h3 class="notice-title">Secure Access</h3>
          <p class="notice-description">
            All login attempts are monitored and logged. Unauthorized access attempts 
            will be reported to security personnel.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LuxuryButton from '@/components/LuxuryButton.vue'
import { 
  EyeIcon, 
  EyeSlashIcon, 
  ExclamationTriangleIcon,
  ShieldCheckIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: '',
  rememberMe: false
})

const errors = ref({})
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const isFormValid = computed(() => {
  return form.value.email && form.value.password && !Object.keys(errors.value).length
})

function validateForm() {
  errors.value = {}
  
  if (!form.value.email.trim()) {
    errors.value.email = 'Email is required'
  } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
    errors.value.email = 'Please enter a valid email address'
  }
  
  if (!form.value.password) {
    errors.value.password = 'Password is required'
  } else if (form.value.password.length < 8) {
    errors.value.password = 'Password must be at least 8 characters'
  }
  
  return Object.keys(errors.value).length === 0
}

async function handleLogin() {
  if (!validateForm()) return
  
  loading.value = true
  error.value = ''
  
  try {
    const result = await authStore.login({
      email: form.value.email,
      password: form.value.password
    })
    
    if (result.success) {
      // Redirect to intended page or dashboard
      const redirect = route.query.redirect || '/dashboard'
      await router.push(redirect)
    } else {
      error.value = result.error || 'Login failed'
    }
  } catch (err) {
    error.value = 'An unexpected error occurred. Please try again.'
    console.error('Login error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  @apply min-h-screen flex items-center justify-center py-12;
  background: linear-gradient(135deg, #0f0f23, #1a1b2e);
  position: relative;
}

.login-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1920&h=1080&fit=crop');
  background-size: cover;
  background-position: center;
  opacity: 0.1;
  z-index: 0;
}

.login-container {
  @apply max-w-md w-full mx-auto px-6 relative z-10 space-y-8;
}

/* Header */
.login-header {
  @apply text-center;
}

.logo-container {
  @apply flex items-center justify-center gap-3 mb-4;
}

.logo-icon {
  @apply w-12 h-12;
  color: #8b5cf6;
}

.logo-text {
  @apply text-2xl font-bold;
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  @apply text-lg text-gray-300;
}

/* Form Container */
.login-form-container {
  @apply p-8 rounded-2xl;
}

.login-form {
  @apply space-y-6;
}

.form-title {
  @apply text-2xl font-bold text-center mb-2;
  color: #f7fafc;
}

.form-description {
  @apply text-center text-gray-400 text-sm mb-6;
}

/* Error Banner */
.error-banner {
  @apply flex items-center gap-3 p-4 rounded-lg mb-6;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.error-icon {
  @apply w-5 h-5;
}

/* Form Elements */
.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-semibold text-gray-300;
}

.form-input {
  @apply w-full px-4 py-3 rounded-lg border-0 transition-all duration-300;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
}

.form-input::placeholder {
  @apply text-gray-400;
}

.form-input:focus {
  @apply outline-none;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.5);
  border-color: #8b5cf6;
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.3);
}

.error-text {
  @apply text-red-400 text-sm;
}

.password-input-container {
  @apply relative;
}

.password-toggle {
  @apply absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300 transition-colors;
  background: none;
  border: none;
  cursor: pointer;
}

/* Form Options */
.form-options {
  @apply flex items-center justify-between;
}

.checkbox-container {
  @apply flex items-center gap-2 text-sm text-gray-300 cursor-pointer;
}

.checkbox-container input[type="checkbox"] {
  @apply sr-only;
}

.checkmark {
  @apply w-4 h-4 rounded border border-gray-500 relative;
  background: rgba(255, 255, 255, 0.1);
}

.checkbox-container input[type="checkbox"]:checked + .checkmark {
  background: linear-gradient(135deg, #8b5cf6, #10b981);
  border-color: #8b5cf6;
}

.checkbox-container input[type="checkbox"]:checked + .checkmark::after {
  content: '';
  @apply absolute top-0 left-1 w-1.5 h-3 border-r-2 border-b-2 border-white;
  transform: rotate(45deg);
}

.forgot-password-link {
  @apply text-sm text-purple-400 hover:text-purple-300 transition-colors;
  background: none;
  border: none;
  cursor: pointer;
}

/* Registration Section */
.register-section {
  @apply text-center pt-4 border-t border-gray-700;
}

.register-text {
  @apply text-gray-400;
}

.register-link {
  @apply text-purple-400 hover:text-purple-300 transition-colors no-underline font-medium;
}

/* Security Notice */
.security-notice {
  @apply flex items-start gap-4 p-6 rounded-xl;
}

.notice-icon {
  @apply w-8 h-8 text-green-400 flex-shrink-0;
}

.notice-content {
  @apply flex-1;
}

.notice-title {
  @apply font-bold text-green-400 mb-2;
}

.notice-description {
  @apply text-sm text-gray-400 leading-relaxed;
}

/* Responsive Design */
@media (max-width: 480px) {
  .login-container {
    @apply px-4;
  }
  
  .login-form-container {
    @apply p-6;
  }
}
</style>