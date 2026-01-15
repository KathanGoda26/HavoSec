<template>
  <footer class="footer-container">
    <div class="footer-content">
      <!-- Top Section -->
      <div class="footer-top">
        <!-- Company Info -->
        <div class="footer-section company-section">
          <div class="footer-logo">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 7V12C2 17 6 21 12 22C18 21 22 17 22 12V7L12 2Z"/>
              </svg>
            </div>
            <h3 class="logo-text">HavoSec</h3>
          </div>
          <!-- <p class="footer-description">
            Advanced cybersecurity analytics and threat detection platform 
            designed for modern organizations. Protecting your digital assets 
            with AI-powered security solutions.
          </p> -->
          <div class="social-links">
            <a href="#" class="social-link" data-testid="linkedin-link">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
              </svg>
            </a>
            <a href="#" class="social-link" data-testid="twitter-link">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
              </svg>
            </a>
            <a href="#" class="social-link" data-testid="github-link">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
          </div>
        </div>

        <!-- Quick Links -->
        <div class="footer-section">
          <h4 class="footer-title">Product</h4>
          <ul class="footer-links">
            <li><router-link to="/" class="footer-link">Features</router-link></li>
            <li><router-link to="/about" class="footer-link">Security</router-link></li>
            <li><a href="#" class="footer-link">Integrations</a></li>
            <li><a href="#" class="footer-link">Pricing</a></li>
            <li><a href="#" class="footer-link">API</a></li>
          </ul>
        </div>

        <!-- Solutions -->
        <div class="footer-section">
          <h4 class="footer-title">Solutions</h4>
          <ul class="footer-links">
            <li><a href="#" class="footer-link">Enterprise</a></li>
            <li><a href="#" class="footer-link">Small Business</a></li>
            <li><a href="#" class="footer-link">Government</a></li>
            <li><a href="#" class="footer-link">Healthcare</a></li>
            <li><a href="#" class="footer-link">Finance</a></li>
          </ul>
        </div>

        <!-- Resources -->
        <div class="footer-section">
          <h4 class="footer-title">Resources</h4>
          <ul class="footer-links">
            <li><router-link to="/blog" class="footer-link">Blog</router-link></li>
            <li><a href="#" class="footer-link">Documentation</a></li>
            <li><a href="#" class="footer-link">Help Center</a></li>
            <li><a href="#" class="footer-link">Case Studies</a></li>
            <li><a href="#" class="footer-link">Webinars</a></li>
          </ul>
        </div>

        <!-- Company -->
        <div class="footer-section">
          <h4 class="footer-title">Company</h4>
          <ul class="footer-links">
            <li><router-link to="/about" class="footer-link">About Us</router-link></li>
            <li><a href="#" class="footer-link">Careers</a></li>
            <li><a href="#" class="footer-link">News</a></li>
            <li><a href="#" class="footer-link">Contact</a></li>
            <li><a href="#" class="footer-link">Partners</a></li>
          </ul>
        </div>
      </div>

      <!-- Security Badges -->
      <div class="security-badges">
        <div class="badges-container">
          <div class="security-badge">
            <ShieldCheckIcon class="badge-icon" />
            <div class="badge-content">
              <span class="badge-title">SOC 2 Type II</span>
              <span class="badge-subtitle">Certified</span>
            </div>
          </div>
          <div class="security-badge">
            <LockClosedIcon class="badge-icon" />
            <div class="badge-content">
              <span class="badge-title">ISO 27001</span>
              <span class="badge-subtitle">Compliant</span>
            </div>
          </div>
          <div class="security-badge">
            <EyeIcon class="badge-icon" />
            <div class="badge-content">
              <span class="badge-title">GDPR</span>
              <span class="badge-subtitle">Ready</span>
            </div>
          </div>
          <div class="security-badge">
            <KeyIcon class="badge-icon" />
            <div class="badge-content">
              <span class="badge-title">256-bit</span>
              <span class="badge-subtitle">Encryption</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Section -->
      <div class="footer-bottom">
        <div class="footer-bottom-left">
          <p class="copyright">
            © {{ currentYear }} HavoSec. All rights reserved.
          </p>
          <div class="legal-links">
            <a href="#" class="legal-link">Privacy Policy</a>
            <span class="legal-separator">•</span>
            <a href="#" class="legal-link">Terms of Service</a>
            <span class="legal-separator">•</span>
            <a href="#" class="legal-link">Cookie Policy</a>
            <span class="legal-separator">•</span>
            <a href="#" class="legal-link">Security</a>
          </div>
        </div>
        <div class="footer-bottom-right">
          <div class="region-selector">
            <GlobeAltIcon class="region-icon" />
            <select class="region-select" data-testid="region-select">
              <option value="in">India</option>
              <option value="us">United States</option>
              <option value="eu">Europe</option>
              <option value="uk">United Kingdom</option>
              <option value="ca">Canada</option>
              <option value="au">Australia</option>
            </select>
          </div>
        </div>
      </div>
    </div>

  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { 
  ShieldCheckIcon, 
  LockClosedIcon, 
  EyeIcon, 
  KeyIcon,
  GlobeAltIcon
} from '@heroicons/vue/24/outline'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped>
.footer-container {
  @apply relative mt-20;
  background: #080808;
  border-top: 1px solid rgba(126, 99, 119, 0.2);
}

.dark .footer-container {
  background: #050505;
  border-top: 1px solid rgba(126, 99, 119, 0.25);
}

.footer-content {
  @apply relative z-10 max-w-7xl mx-auto px-6 py-16;
}

/* Top Section */
.footer-top {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-12;
}

/* .company-section {
  @apply lg:col-span-2;
} */

.footer-section {
  @apply space-y-4;
}

.footer-logo {
  @apply flex items-center gap-3 mb-4;
}

.logo-icon {
  @apply w-8 h-8;
  color: #673ee6;
}

.logo-text {
  @apply text-xl font-bold;
  color: #374151;
  font-size: 2.5rem;
}

.dark .logo-text {
  color: #f9fafb;
}

.footer-description {
  @apply text-gray-300 leading-relaxed mb-6;
}

.social-links {
  @apply flex gap-4;
}

.social-link {
  @apply p-2 rounded-lg transition-all duration-300;
  background: rgba(103, 62, 230, 0.1);
  color: #6b7280;
}

.social-link:hover {
  background: rgba(103, 62, 230, 0.2);
  color: #673ee6;
  transform: translateY(-2px);
}

.dark .social-link {
  background: rgba(103, 62, 230, 0.2);
  color: #ffffff;
}

.footer-title {
  @apply text-lg font-semibold mb-4;
  color: #374151;
}

.dark .footer-title {
  color: #00b090;
}

.footer-links {
  @apply space-y-3;
}

.footer-link {
  @apply text-white hover:text-gray-200 transition-colors duration-300 no-underline block;
}

/* Security Badges */
.security-badges {
  @apply py-8 border-t border-b;
  border-color: rgba(126, 99, 119, 0.15);
}

.badges-container {
  @apply flex flex-wrap justify-center gap-6;
}

.security-badge {
  @apply flex items-center gap-3 px-4 py-3 rounded-lg;
  background: rgba(103, 62, 230, 0.2);
  border: 1px solid rgba(126, 99, 119, 0.18);
}

.badge-icon {
  @apply w-8 h-8;
  color: #000000;
}

.badge-content {
  @apply flex flex-col;
}

.badge-title {
  @apply text-sm font-semibold;
  color: #f9fafb;
}

.badge-subtitle {
  @apply text-xs;
  color: #ffffff;
}

/* Bottom Section */
.footer-bottom {
  @apply flex flex-col lg:flex-row justify-between items-center pt-8 gap-4;
}

.footer-bottom-left {
  @apply text-center lg:text-left;
}

.copyright {
  @apply text-sm text-gray-500 mb-2;
}

.legal-links {
  @apply flex flex-wrap justify-center lg:justify-start gap-2 text-sm;
}

.legal-link {
  @apply text-gray-500 hover:text-gray-300 no-underline transition-colors;
}

.legal-separator {
  @apply text-gray-400;
}

.footer-bottom-right {
  @apply flex items-center gap-4;
}

.region-selector {
  @apply flex items-center gap-2;
}

.region-icon {
  @apply w-4 h-4;
  color: #9ca3af;
}

.region-select {
  @apply bg-transparent border-0 text-sm cursor-pointer;
  color: #9ca3af;
}

.region-select:focus {
  @apply outline-none;
}

/* Responsive Design */
@media (max-width: 768px) {
  .footer-top {
    @apply grid-cols-1 gap-6;
  }
  
  .footer-bottom {
    @apply flex-col gap-4;
  }
  
  .legal-links {
    @apply justify-center;
  }
  
  .badges-container {
    @apply grid grid-cols-2 gap-4;
  }
}

@media (max-width: 480px) {
  .badges-container {
    @apply grid-cols-1;
  }
}
</style>