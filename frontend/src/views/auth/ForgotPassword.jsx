import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import DynamicSEO from '@/components/DynamicSEO'

const API_BASE = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
).replace(/\/$/, '')

function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email) {
      setError('Please enter your email address')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      await axios.post(`${API_BASE}/auth/forgot-password`, { email })
      setIsSuccess(true)
    } catch (err) {
      // Always show success to prevent email enumeration
      setIsSuccess(true)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="forgot-password-page">
      <DynamicSEO page="forgot-password" />
      <div className="auth-container glass">
        <div className="auth-header">
          <h1 className="heading-luxury">Reset Password</h1>
          <p className="auth-subtitle">Enter your email to receive a reset link</p>
        </div>

        {/* Success State */}
        {isSuccess ? (
          <div className="success-message" data-testid="success-message">
            <div className="success-icon">✓</div>
            <h2>Check Your Email</h2>
            <p>
              If an account exists with {email}, we've sent a password reset
              link.
            </p>
            <p className="text-muted mt-2">The link will expire in 1 hour.</p>
            <Link to="/auth/login" className="back-link">
              Back to Login
            </Link>
          </div>
        ) : (
          /* Form State */
          <form
            onSubmit={handleSubmit}
            className="auth-form"
            data-testid="forgot-password-form"
          >
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                type="email"
                placeholder="Enter your email"
                required
                disabled={isLoading}
                data-testid="email-input"
              />
            </div>

            {error && (
              <div className="error-message" data-testid="error-message">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="submit-btn"
              disabled={isLoading}
              data-testid="submit-btn"
            >
              {isLoading && <span className="loading-spinner"></span>}
              {isLoading ? 'Sending...' : 'Send Reset Link'}
            </button>

            <div className="auth-links">
              <Link to="/auth/login">Back to Login</Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default ForgotPassword
