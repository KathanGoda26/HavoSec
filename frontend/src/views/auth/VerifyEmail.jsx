import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import DynamicSEO from '@/components/DynamicSEO'

const API_BASE = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
).replace(/\/$/, '')

function VerifyEmail() {
  const location = useLocation()
  const user = useAuthStore(state => state.user)

  const [isLoading, setIsLoading] = useState(true)
  const [isSuccess, setIsSuccess] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search)
    const token = queryParams.get('token')

    if (!token) {
      setError('No verification token provided')
      setIsLoading(false)
      return
    }

    async function verify() {
      try {
        await axios.post(`${API_BASE}/auth/verify-email`, { token })
        setIsSuccess(true)

        // Update auth store if user is logged in
        if (user) {
          useAuthStore.setState({ user: { ...user, emailVerified: true } })
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Verification failed')
      } finally {
        setIsLoading(false)
      }
    }

    verify()
  }, [location.search, user])

  const resendVerification = async () => {
    if (!user?.email) {
      setError('Please log in to resend verification email')
      return
    }

    setIsResending(true)

    try {
      await axios.post(`${API_BASE}/auth/send-verification`, {
        email: user.email,
      })
      alert('Verification email sent! Please check your inbox.')
    } catch (err) {
      alert('Failed to send verification email. Please try again.')
    } finally {
      setIsResending(false)
    }
  }

  return (
    <div className="verify-email-page">
      <DynamicSEO page="verify-email" />
      <div className="auth-container glass">
        {/* Loading State */}
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner-large"></div>
            <p>Verifying your email...</p>
          </div>
        ) : isSuccess ? (
          /* Success State */
          <div className="success-message" data-testid="success-message">
            <div className="success-icon">✓</div>
            <h2>Email Verified!</h2>
            <p>
              Your email has been successfully verified. You now have full access to
              all features.
            </p>
            <Link to="/dashboard/overview" className="action-link">
              Go to Dashboard
            </Link>
          </div>
        ) : (
          /* Error State */
          <div className="error-state" data-testid="error-state">
            <div className="error-icon">✕</div>
            <h2>Verification Failed</h2>
            <p>
              {error || 'This verification link is invalid or has expired.'}
            </p>
            <div className="action-buttons">
              <button
                onClick={resendVerification}
                className="action-link"
                disabled={isResending}
              >
                {isResending ? 'Sending...' : 'Resend Verification Email'}
              </button>
              <Link to="/auth/login" className="secondary-link">
                Back to Login
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default VerifyEmail
