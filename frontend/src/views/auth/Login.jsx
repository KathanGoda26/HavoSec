import React, { useState, useMemo } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import DynamicSEO from '@/components/DynamicSEO'
import LuxuryButton from '@/components/LuxuryButton'
import {
  EyeIcon,
  EyeSlashIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const authStore = useAuthStore()

  const [form, setForm] = useState({
    email: '',
    password: '',
    rememberMe: false,
  })

  const [errors, setErrors] = useState({})
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const isFormValid = useMemo(() => {
    return form.email && form.password && Object.keys(errors).length === 0
  }, [form.email, form.password, errors])

  const validateForm = () => {
    const errs = {}

    if (!form.email.trim()) {
      errs.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      errs.email = 'Please enter a valid email address'
    }

    if (!form.password) {
      errs.password = 'Password is required'
    } else if (form.password.length < 8) {
      errs.password = 'Password must be at least 8 characters'
    }

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleChange = (field, value) => {
    setForm(prev => {
      const next = { ...prev, [field]: value }
      return next
    })
    // Clear field-specific error as they type
    if (errors[field]) {
      setErrors(prev => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    setLoading(true)
    setError('')

    try {
      const result = await authStore.login({
        email: form.email,
        password: form.password,
      })

      if (result.success) {
        const queryParams = new URLSearchParams(location.search)
        const redirect = queryParams.get('redirect') || '/dashboard/overview'
        navigate(redirect)
      } else {
        setError(result.error || 'Login failed')
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.')
      console.error('Login error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <DynamicSEO page="login" />

      {/* Animated Ambient Glowing Blobs */}
      <div className="ambient-glow glow-1"></div>
      <div className="ambient-glow glow-2"></div>
      <div className="ambient-glow glow-3"></div>

      <div className="login-visual" aria-hidden="true">
        <div className="login-grid"></div>
        <div className="login-orbit orbit-a"></div>
        <div className="login-orbit orbit-b"></div>
        <div className="login-signal signal-a"></div>
        <div className="login-signal signal-b"></div>
        <div className="login-visual-copy">
          <span>HAVOSEC / SECURE CORE</span>
          <strong>Defend<br />with intent.</strong>
          <p>Autonomous intelligence for the threats you cannot see.</p>
        </div>
        <div className="login-status-pill"><i /> SYSTEMS OPERATIONAL</div>
      </div>

      <div className="login-container">
        <div className="login-form-container glass-card animate-slide-up" data-testid="login-form">
          <form onSubmit={handleLogin} className="login-form">
            <h2 className="form-title">Company Portal</h2>
            <p className="form-description">
              Restricted access system for authorized company personnel only.
            </p>

            {/* Error Display */}
            {error && (
              <div className="error-banner" data-testid="error-message">
                <ExclamationTriangleIcon className="error-icon" />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <div className="input-wrapper">
                <input
                  id="email"
                  value={form.email}
                  onChange={e => handleChange('email', e.target.value)}
                  type="email"
                  required
                  autoComplete="email"
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  data-testid="email-input"
                  placeholder="Enter your company email"
                />
              </div>
              {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <div className="password-input-container">
                <input
                  id="password"
                  value={form.password}
                  onChange={e => handleChange('password', e.target.value)}
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  data-testid="password-input"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(prev => !prev)}
                  className="password-toggle"
                  data-testid="password-toggle"
                  tabIndex="-1"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="icon-sm" />
                  ) : (
                    <EyeIcon className="icon-sm" />
                  )}
                </button>
              </div>
              {errors.password && <span className="error-text">{errors.password}</span>}
            </div>

            <div className="form-options">
              <label className="checkbox-container">
                <input
                  type="checkbox"
                  checked={form.rememberMe}
                  onChange={e => handleChange('rememberMe', e.target.checked)}
                  data-testid="remember-me-checkbox"
                />
                <span className="checkmark"></span>
                Remember me
              </label>

              <Link
                to="/auth/forgot-password"
                className="forgot-password-link"
                data-testid="forgot-password-link"
              >
                Forgot password?
              </Link>
            </div>

            <LuxuryButton
              variant="sweep"
              type="submit"
              size="lg"
              loading={loading}
              disabled={!isFormValid}
              className="btn-full submit-button"
              data-testid="login-submit-button"
            >
              Sign In
            </LuxuryButton>
          </form>
        </div>

      </div>
    </div>
  )
}

export default Login
