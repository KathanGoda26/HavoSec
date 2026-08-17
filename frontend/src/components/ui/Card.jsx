import React from 'react'

function Card({
  title = '',
  icon: Icon = null,
  variant = 'default',
  hover = false,
  clickable = false,
  onClick,
  header,
  footer,
  children,
}) {
  const classNames = [
    'ui-card',
    `card-${variant}`,
    hover ? 'card-hover' : '',
    clickable ? 'card-clickable' : '',
  ].filter(Boolean).join(' ')

  const handleClick = () => {
    if (clickable && onClick) onClick()
  }

  return (
    <div className={classNames} onClick={handleClick}>
      {(header || title) && (
        <div className="card-header">
          {title && (
            <div className="card-title">
              {Icon && <Icon className="card-title-icon" />}
              <span>{title}</span>
            </div>
          )}
          {header && <div className="card-header-content">{header}</div>}
        </div>
      )}

      <div className="card-body">
        {children}
      </div>

      {footer && (
        <div className="card-footer">
          {footer}
        </div>
      )}
    </div>
  )
}

export default Card
