<template>
  <button
    :class="[
      'luxury-button',
      variantClasses,
      sizeClasses,
      {
        'loading': loading,
        'disabled': disabled
      }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <div class="button-content">
      <div v-if="loading" class="loading-spinner"></div>
      
      <component 
        v-if="iconLeft && !loading" 
        :is="iconLeft" 
        class="button-icon icon-left" 
      />
      
      <span class="button-text">
        <slot>{{ text }}</slot>
      </span>
      
      <component 
        v-if="iconRight && !loading" 
        :is="iconRight" 
        class="button-icon icon-right" 
      />
    </div>
    
    <!-- Ripple effect -->
    <div class="button-ripple"></div>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: value => ['primary', 'secondary', 'outline', 'ghost', 'danger'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: value => ['sm', 'md', 'lg', 'xl'].includes(value)
  },
  text: {
    type: String,
    default: ''
  },
  iconLeft: {
    type: Object,
    default: null
  },
  iconRight: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  fullWidth: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const variantClasses = computed(() => {
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary', 
    outline: 'btn-outline',
    ghost: 'btn-ghost',
    danger: 'btn-danger'
  }
  return variants[props.variant]
})

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg',
    xl: 'btn-xl'
  }
  return `${sizes[props.size]} ${props.fullWidth ? 'btn-full' : ''}`
})

function handleClick(event) {
  if (props.disabled || props.loading) return
  
  // Create ripple effect
  createRipple(event)
  
  emit('click', event)
}

function createRipple(event) {
  const button = event.currentTarget
  const ripple = button.querySelector('.button-ripple')
  
  const rect = button.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2
  
  ripple.style.width = ripple.style.height = `${size}px`
  ripple.style.left = `${x}px`
  ripple.style.top = `${y}px`
  ripple.classList.add('animate-ripple')
  
  setTimeout(() => {
    ripple.classList.remove('animate-ripple')
  }, 600)
}
</script>

<style scoped>
.luxury-button {
  @apply relative inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-300 transform focus:outline-none focus:ring-4 focus:ring-opacity-50 overflow-hidden;
  position: relative;
  cursor: pointer;
  border: none;
  font-family: 'Inter', sans-serif;
}

.luxury-button:not(.disabled):not(.loading):hover {
  @apply scale-105 shadow-2xl;
}

.luxury-button:not(.disabled):not(.loading):active {
  @apply scale-95;
}

.luxury-button.disabled,
.luxury-button.loading {
  @apply opacity-60 cursor-not-allowed;
  transform: none !important;
}

/* Variant Styles */
.btn-primary {
  background: linear-gradient(135deg, #673ee6, #00b090);
  @apply text-white;
}

.btn-primary:focus {
  @apply ring-purple-500;
}

.btn-secondary {
  @apply bg-gray-100 text-gray-900 shadow-md;
}

.dark .btn-secondary {
  @apply bg-gray-800 text-gray-100;
}

.btn-secondary:focus {
  @apply ring-gray-500;
}

.btn-outline {
  @apply bg-transparent border-2;
  border-image: linear-gradient(135deg, #673ee6, #00b090) 1;
  color: transparent;
  background: linear-gradient(135deg, #673ee6, #00b090);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.btn-outline:focus {
  @apply ring-purple-500;
}

.btn-ghost {
  @apply bg-transparent text-gray-700;
}

.dark .btn-ghost {
  @apply text-gray-300;
}

.btn-ghost:not(.disabled):not(.loading):hover {
  background: rgba(103, 62, 230, 0.1);
}

.btn-danger {
  @apply bg-red-600 text-white shadow-lg;
}

.btn-danger:focus {
  @apply ring-red-500;
}

/* Size Styles */
.btn-sm {
  @apply px-3 py-1.5 text-sm;
}

.btn-md {
  @apply px-6 py-3 text-base;
}

.btn-lg {
  @apply px-8 py-4 text-lg;
}

.btn-xl {
  @apply px-10 py-5 text-xl;
}

.btn-full {
  @apply w-full;
}

/* Button Content */
.button-content {
  @apply flex items-center justify-center gap-2 relative z-10;
}

.button-icon {
  @apply w-5 h-5;
}

.btn-sm .button-icon {
  @apply w-4 h-4;
}

.btn-lg .button-icon {
  @apply w-6 h-6;
}

.btn-xl .button-icon {
  @apply w-7 h-7;
}

.button-text {
  @apply font-medium;
}

/* Loading Spinner */
.loading-spinner {
  @apply w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin;
}

.btn-sm .loading-spinner {
  @apply w-4 h-4;
}

.btn-lg .loading-spinner {
  @apply w-6 h-6;
}

.btn-xl .loading-spinner {
  @apply w-7 h-7;
}

/* Ripple Effect */
.button-ripple {
  @apply absolute rounded-full opacity-0 pointer-events-none;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0);
}

.button-ripple.animate-ripple {
  @apply opacity-100;
  animation: ripple 0.6s ease-out;
}

@keyframes ripple {
  to {
    transform: scale(2);
    opacity: 0;
  }
}

/* Accessibility */
.luxury-button:focus-visible {
  @apply ring-4 ring-opacity-50;
}

/* Dark mode adjustments */
.dark .btn-outline {
  border-image: linear-gradient(135deg, #673ee6, #00b090) 1;
}
</style>