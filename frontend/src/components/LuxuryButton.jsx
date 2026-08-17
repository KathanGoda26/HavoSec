import React, { useMemo, useCallback } from 'react'

function LuxuryButton({
  variant = 'primary',
  size = 'md',
  text = '',
  iconLeft: IconLeft = null,
  iconRight: IconRight = null,
  loading = false,
  disabled = false,
  fullWidth = false,
  onClick,
  children,
  className = '',
  ...rest
}) {
  const variantClasses = useMemo(() => {
    const variants = {
      primary: 'btn-primary',
      secondary: 'btn-secondary',
      outline: 'btn-outline',
      ghost: 'btn-ghost',
      danger: 'btn-danger'
      ,sweep: 'btn-sweep'
    }
    return variants[variant] || 'btn-primary'
  }, [variant])

  const sizeClasses = useMemo(() => {
    const sizes = {
      sm: 'btn-sm',
      md: 'btn-md',
      lg: 'btn-lg',
      xl: 'btn-xl'
    }
    return `${sizes[size] || 'btn-md'} ${fullWidth ? 'btn-full' : ''}`
  }, [size, fullWidth])

  const handleClick = useCallback((event) => {
    if (disabled || loading) return

    // Create ripple effect
    const button = event.currentTarget
    const ripple = button.querySelector('.button-ripple')

    if (ripple) {
      const rect = button.getBoundingClientRect()
      const rippleSize = Math.max(rect.width, rect.height)
      const x = event.clientX - rect.left - rippleSize / 2
      const y = event.clientY - rect.top - rippleSize / 2

      ripple.style.width = ripple.style.height = `${rippleSize}px`
      ripple.style.left = `${x}px`
      ripple.style.top = `${y}px`
      ripple.classList.add('animate-ripple')

      setTimeout(() => {
        ripple.classList.remove('animate-ripple')
      }, 600)
    }

    if (onClick) onClick(event)
  }, [disabled, loading, onClick])

  const classNames = [
    'luxury-button',
    variantClasses,
    sizeClasses,
    loading ? 'loading' : '',
    disabled ? 'disabled' : '',
    className
  ].filter(Boolean).join(' ')

  return (
    <button
      className={classNames}
      disabled={disabled || loading}
      onClick={handleClick}
      {...rest}
    >
      <div className="button-content">
        {loading && <div className="loading-spinner"></div>}
        {IconLeft && !loading && <IconLeft className="button-icon icon-left" />}
        <span className="button-text">
          {children || text}
        </span>
        {IconRight && !loading && <IconRight className="button-icon icon-right" />}
      </div>
      <div className="button-ripple"></div>
    </button>
  )
}

export default LuxuryButton
