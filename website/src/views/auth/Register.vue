<template>
  <div class="register-page">
    <div class="register-container">
      <!-- Logo and Header -->
      <div class="register-header" data-testid="register-header">
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7V12C2 17 6 21 12 22C18 21 22 17 22 12V7L12 2Z"/>
            </svg>
          </div>
          <h1 class="logo-text">HavoSec</h1>
        </div>
        <p class="register-subtitle">Request access to the security platform</p>
      </div>

      <!-- Registration Form -->
      <div class="register-form-container glass" data-testid="register-form">
        <form @submit.prevent="handleRegister" class="register-form">
          <h2 class="form-title">Request Company Access</h2>
          <p class="form-description">
            Please provide your details below. All registrations require approval 
            from our security team.
          </p>

          <!-- Error Display -->
          <div v-if="error" class="error-banner" data-testid="error-message">
            <ExclamationTriangleIcon class="error-icon" />
            <span>{{ error }}</span>
          </div>

          <!-- Success Message -->
          <div v-if="registered" class="success-banner" data-testid="success-message">
            <CheckCircleIcon class="success-icon" />
            <div class="success-content">
              <h3 class="success-title">Registration Submitted</h3>
              <p class="success-description">
                Your access request has been submitted successfully. Our security team 
                will review your application and contact you within 24-48 hours.
              </p>
            </div>
          </div>

          <div v-if="!registered" class="form-fields">
            <!-- Personal Information -->
            <div class="form-row">
              <div class="form-group">
                <label for="firstName" class="form-label">First Name *</label>
                <input 
                  id="firstName"
                  v-model="form.firstName"
                  type="text" 
                  required
                  class="form-input"
                  :class="{ 'error': errors.firstName }"
                  data-testid="first-name-input"
                  placeholder="Enter your first name"
                />
                <span v-if="errors.firstName" class="error-text">{{ errors.firstName }}</span>
              </div>
              
              <div class="form-group">
                <label for="lastName" class="form-label">Last Name *</label>
                <input 
                  id="lastName"
                  v-model="form.lastName"
                  type="text" 
                  required
                  class="form-input"
                  :class="{ 'error': errors.lastName }"
                  data-testid="last-name-input"
                  placeholder="Enter your last name"
                />
                <span v-if="errors.lastName" class="error-text">{{ errors.lastName }}</span>
              </div>
            </div>

            <!-- Contact Information -->
            <div class="form-group">
              <label for="email" class="form-label">Email Address *</label>
              <input 
                id="email"
                v-model="form.email"
                type="email" 
                required
                class="form-input"
                :class="{ 'error': errors.email }"
                data-testid="email-input"
                placeholder="Enter your company email"
              />
              <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
            </div>

            <!-- Company Information -->
            <div class="form-group">
              <label for="company" class="form-label">Company Name *</label>
              <input 
                id="company"
                v-model="form.company"
                type="text" 
                required
                class="form-input"
                :class="{ 'error': errors.company }"
                data-testid="company-input"
                placeholder="Enter your company name"
              />
              <span v-if="errors.company" class="error-text">{{ errors.company }}</span>
            </div>

            <!-- Role Selection -->
            <div class="form-group">
              <label for="role" class="form-label">Requested Role *</label>
              <select 
                id="role"
                v-model="form.role"
                required
                class="form-input"
                data-testid="role-select"
              >
                <option value="">Select your role</option>
                <option value="viewer">Viewer - Read-only access to dashboards</option>
                <option value="analyst">Analyst - Security analysis and reporting</option>
                <option value="admin">Admin - Full platform administration</option>
              </select>
              <span v-if="errors.role" class="error-text">{{ errors.role }}</span>
            </div>

            <!-- Password -->
            <div class="form-group">
              <label for="password" class="form-label">Password *</label>
              <div class="password-input-container">
                <input 
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  class="form-input"
                  :class="{ 'error': errors.password }"
                  data-testid="password-input"
                  placeholder="Create a secure password"
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
              <div class="password-requirements">
                <p class="requirements-title">Password must contain:</p>
                <ul class="requirements-list">
                  <li :class="{ 'valid': passwordChecks.length }">At least 8 characters</li>
                  <li :class="{ 'valid': passwordChecks.uppercase }">One uppercase letter</li>
                  <li :class="{ 'valid': passwordChecks.lowercase }">One lowercase letter</li>
                  <li :class="{ 'valid': passwordChecks.number }">One number</li>
                </ul>
              </div>
              <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
            </div>

            <!-- Confirm Password -->
            <div class="form-group">
              <label for="confirmPassword" class="form-label">Confirm Password *</label>
              <input 
                id="confirmPassword"
                v-model="form.confirmPassword"
                type="password"
                required
                class="form-input"
                :class="{ 'error': errors.confirmPassword }"
                data-testid="confirm-password-input"
                placeholder="Confirm your password"
              />
              <span v-if="errors.confirmPassword" class="error-text">{{ errors.confirmPassword }}</span>
            </div>

            <!-- Terms Acceptance -->
            <div class="form-group">
              <label class="checkbox-container">
                <input 
                  v-model="form.acceptTerms"
                  type="checkbox"
                  required
                  data-testid="accept-terms-checkbox"
                />
                <span class="checkmark"></span>
                I agree to the <button type="button" class="terms-link">Terms of Service</button> 
                and <button type="button" class="terms-link">Privacy Policy</button>
              </label>
              <span v-if="errors.acceptTerms" class="error-text">{{ errors.acceptTerms }}</span>
            </div>

            <LuxuryButton 
              type="submit"
              size="lg"
              :loading="loading"
              :disabled="!isFormValid"
              class="w-full"
              data-testid="register-submit-button"
            >
              Submit Access Request
            </LuxuryButton>
          </div>

          <!-- Login Link -->
          <div class="login-section">
            <p class="login-text">
              Already have an account? 
              <router-link 
                to="/auth/login" 
                class="login-link"
                data-testid="login-link"
              >
                Sign In
              </router-link>
            </p>
          </div>
        </form>
      </div>

      <!-- Security Notice -->
      <div class="security-notice glass">
        <ShieldCheckIcon class="notice-icon" />
        <div class="notice-content">
          <h3 class="notice-title">Secure Registration</h3>
          <p class="notice-description">
            All access requests are reviewed by our security team. Only authorized 
            personnel will be granted access to the LockShield Analytics platform.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LuxuryButton from '@/components/LuxuryButton.vue'
import { 
  EyeIcon, 
  EyeSlashIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ShieldCheckIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  firstName: '',
  lastName: '',
  email: '',
  company: '',
  role: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false
})

const errors = ref({})
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const registered = ref(false)

const passwordChecks = computed(() => ({
  length: form.value.password.length >= 8,
  uppercase: /[A-Z]/.test(form.value.password),
  lowercase: /[a-z]/.test(form.value.password),
  number: /\d/.test(form.value.password)
}))

const isPasswordValid = computed(() => {
  return Object.values(passwordChecks.value).every(check => check === true)
})

const isFormValid = computed(() => {
  return form.value.firstName && 
         form.value.lastName && 
         form.value.email && 
         form.value.company &&
         form.value.role &&
         isPasswordValid.value &&
         form.value.password === form.value.confirmPassword &&
         form.value.acceptTerms &&
         !Object.keys(errors.value).length
})

function validateForm() {
  errors.value = {}
  
  if (!form.value.firstName.trim()) {
    errors.value.firstName = 'First name is required'
  }
  
  if (!form.value.lastName.trim()) {
    errors.value.lastName = 'Last name is required'
  }
  
  if (!form.value.email.trim()) {
    errors.value.email = 'Email is required'
  } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
    errors.value.email = 'Please enter a valid email address'
  }
  
  if (!form.value.company.trim()) {
    errors.value.company = 'Company name is required'
  }
  
  if (!form.value.role) {
    errors.value.role = 'Please select a role'
  }
  
  if (!isPasswordValid.value) {
    errors.value.password = 'Password does not meet requirements'
  }
  
  if (form.value.password !== form.value.confirmPassword) {
    errors.value.confirmPassword = 'Passwords do not match'
  }
  
  if (!form.value.acceptTerms) {
    errors.value.acceptTerms = 'You must accept the terms and conditions'
  }
  
  return Object.keys(errors.value).length === 0
}

async function handleRegister() {
  if (!validateForm()) return
  
  loading.value = true
  error.value = ''
  
  try {
    const result = await authStore.register({
      firstName: form.value.firstName,
      lastName: form.value.lastName,
      email: form.value.email,
      company: form.value.company,
      role: form.value.role,
      password: form.value.password
    })
    
    if (result.success) {
      registered.value = true
    } else {
      error.value = result.error || 'Registration failed'
    }
  } catch (err) {
    error.value = 'An unexpected error occurred. Please try again.'
    console.error('Registration error:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  @apply min-h-screen flex items-center justify-center py-12;
  background: linear-gradient(135deg, #0f0f23, #1a1b2e);
  position: relative;
}

.register-page::before {
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

.register-container {
  @apply max-w-lg w-full mx-auto px-6 relative z-10 space-y-8;
}

/* Header */
.register-header {
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

.register-subtitle {
  @apply text-lg text-gray-300;
}

/* Form Container */
.register-form-container {
  @apply p-8 rounded-2xl;
}

.register-form {
  @apply space-y-6;
}

.form-title {
  @apply text-2xl font-bold text-center mb-2;
  color: #f7fafc;
}

.form-description {
  @apply text-center text-gray-400 text-sm mb-6;
}

/* Messages */
.error-banner,
.success-banner {
  @apply flex items-start gap-3 p-4 rounded-lg mb-6;
}

.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.success-banner {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.error-icon,
.success-icon {
  @apply w-5 h-5 flex-shrink-0 mt-0.5;
}

.success-content {
  @apply flex-1;
}

.success-title {
  @apply font-bold mb-2;
}

.success-description {
  @apply text-sm opacity-90;
}

/* Form Elements */
.form-fields {
  @apply space-y-6;
}

.form-row {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

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

/* Password Requirements */
.password-requirements {
  @apply mt-2 p-3 rounded-lg;
  background: rgba(255, 255, 255, 0.05);
}

.requirements-title {
  @apply text-xs font-medium text-gray-400 mb-2;
}

.requirements-list {
  @apply space-y-1;
}

.requirements-list li {
  @apply text-xs text-gray-500 flex items-center gap-2;
}

.requirements-list li.valid {
  @apply text-green-400;
}

.requirements-list li.valid::before {
  content: '✓';
  @apply text-green-400 font-bold;
}

.requirements-list li:not(.valid)::before {
  content: '○';
  @apply text-gray-500;
}

/* Checkbox */
.checkbox-container {
  @apply flex items-start gap-3 text-sm text-gray-300 cursor-pointer;
}

.checkbox-container input[type="checkbox"] {
  @apply sr-only;
}

.checkmark {
  @apply w-4 h-4 rounded border border-gray-500 relative flex-shrink-0 mt-0.5;
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

.terms-link {
  @apply text-purple-400 hover:text-purple-300 transition-colors underline;
  background: none;
  border: none;
  cursor: pointer;
}

/* Login Section */
.login-section {
  @apply text-center pt-4 border-t border-gray-700;
}

.login-text {
  @apply text-gray-400;
}

.login-link {
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
@media (max-width: 640px) {
  .register-container {
    @apply px-4;
  }
  
  .register-form-container {
    @apply p-6;
  }
  
  .form-row {
    @apply grid-cols-1;
  }
}
</style>