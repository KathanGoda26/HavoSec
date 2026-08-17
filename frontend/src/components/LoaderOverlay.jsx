import React from 'react'

function LoaderOverlay() {
  return (
    <div className="loader-overlay" role="status" aria-live="polite">
      <div className="spinner"></div>
      <div className="loader-text">Loading...</div>
    </div>
  )
}

export default LoaderOverlay
