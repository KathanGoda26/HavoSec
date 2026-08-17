import React, { useMemo } from 'react'
import Card from '@/components/ui/Card'

function Widget({
  title = '',
  subtitle = '',
  value = 0,
  icon: Icon = null,
  variant = 'default',
  hover = false,
  trend = null,
  format = null,
  children,
  footer,
}) {
  const formattedValue = useMemo(() => {
    if (format === 'percentage') return `${value}%`
    if (typeof value === 'number') return value.toLocaleString()
    return value
  }, [value, format])

  const trendClass = trend >= 0 ? 'text-red-500' : 'text-green-500'
  const trendText = trend != null ? `${trend}%` : ''

  const headerContent = (
    <div className="widget-header">
      <div className="widget-left">
        {Icon && <Icon className="widget-icon" />}
        <div className="widget-texts">
          <div className="widget-title">{title}</div>
          {subtitle && <div className="widget-subtitle">{subtitle}</div>}
        </div>
      </div>
      <div className="widget-right">
        <div className="widget-value">{formattedValue}</div>
        {trend != null && <div className={`widget-trend ${trendClass}`}>{trendText}</div>}
      </div>
    </div>
  )

  return (
    <Card variant={variant} hover={hover} header={headerContent} footer={footer}>
      <div className="widget-body">
        {children}
      </div>
    </Card>
  )
}

export default Widget
