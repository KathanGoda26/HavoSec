import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import axios from 'axios'
import DynamicSEO from '@/components/DynamicSEO'

const API_BASE = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
).replace(/\/$/, '')

function ResetPassword() {
  const location = useLocation()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [error, setError] = useState('')
  const [tokenError, setTokenError] = useState(false)
  const [token, setToken] = useState('')

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search)
    const tokenVal = queryParams.get('token')

    if (!tokenVal) {
      setTokenError(true)
      return
    }

    setToken(tokenVal)

    // Verify token is valid
    async function verifyToken() {
      try {
        await axios.post(`${API_BASE}/auth/verify-reset-token`, {
          token: tokenVal,
        })
      } catch (err) {
        setTokenError(true)
      }
    }

    verifyToken()
  }, [location.search])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setIsLoading(true)

    try {
      await axios.post(`${API_BASE}/auth/reset-password`, {
        token,
        newPassword: password,
      })
      setIsSuccess(true)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Failed to reset password. Please try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="reset-password-page">
      <DynamicSEO page="reset-password" />
      <div className="auth-container glass">
        <div className="auth-header">
          <h1 className="heading-luxury">Set New Password</h1>
          <p className="auth-subtitle">Enter your new password below</p>
        </div>

        {/* Invalid Token State */}
        {tokenError ? (
          <div className="error-state" data-testid="token-error">
            <div className="error-icon">✕</div>
            <h2>Invalid or Expired Link</h2>
            <p>This password reset link is invalid or has expired.</p>
            <Link to="/auth/forgot-password" className="action-link">
              Request New Link
            </Link>
          </div>
        ) : isSuccess ? (
          /* Success State */
          <div className="success-message" data-testid="success-message">
            <div className="success-icon">✓</div>
            <h2>Password Reset Successfully</h2>
            <p>
              Your password has been changed. You can now log in with your new
              password.
            </p>
            <Link to="/auth/login" className="action-link">
              Go to Login
            </Link>
          </div>
        ) : (
          /* Form State */
          <form
            onSubmit={handleSubmit}
            className="auth-form"
            data-testid="reset-password-form"
          >
            <div className="form-group">
              <label htmlFor="password">New Password</label>
              <input
                id="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                type="password"
                placeholder="Enter new password"
                required
                minLength={8}
                disabled={isLoading}
                data-testid="password-input"
              />
              <small className="field-hint">Minimum 8 characters</small>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                id="confirmPassword"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                type="password"
                placeholder="Confirm new password"
                required
                disabled={isLoading}
                data-testid="confirm-password-input"
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
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default ResetPassword
