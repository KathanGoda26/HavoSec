import React from 'react'
import { useNavigate } from 'react-router-dom'
import LuxuryButton from '@/components/LuxuryButton'
import {
  ArrowLeftIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline'

function NotFound() {
  const navigate = useNavigate()

  return (
    <div className="not-found-page">
      <div className="nf-grid" aria-hidden="true" />
      <div className="nf-glow nf-glow-purple" aria-hidden="true" />
      <div className="nf-glow nf-glow-green" aria-hidden="true" />
      <div className="container nf-container">
        <div className="not-found-content" data-testid="not-found-content">
          <div className="nf-status"><span /> Route unavailable</div>
          <div className="nf-code" aria-label="Error 404">
            <span className="nf-digit nf-digit-left">4</span>
            <span className="nf-digit nf-zero">0</span>
            <span className="nf-digit nf-digit-right">4</span>
          </div>
          <p className="nf-eyebrow">HAVOSEC / LOST SIGNAL</p>
          <h1 className="error-title">This page slipped off the network.</h1>
          <p className="error-description">
            The address may have changed, or the page is no longer available. Your connection is secure—choose a route below to continue.
          </p>
          <div className="error-actions">
            <LuxuryButton onClick={() => navigate('/')} size="lg" iconRight={ArrowRightIcon} data-testid="go-home-button">Return Home</LuxuryButton>
            <LuxuryButton onClick={() => navigate(-1)} variant="outline" size="lg" iconLeft={ArrowLeftIcon} data-testid="go-back-button">Go Back</LuxuryButton>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotFound
