import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import LuxuryButton from '@/components/LuxuryButton'
import {
  ShieldExclamationIcon,
  HomeIcon,
  InformationCircleIcon,
  ChatBubbleLeftRightIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline'

const helpfulLinks = [
  { name: 'Home', path: '/', icon: HomeIcon },
  { name: 'About Us', path: '/about', icon: InformationCircleIcon },
  { name: 'Blog', path: '/blog', icon: ChatBubbleLeftRightIcon },
  { name: 'Book Demo', path: '/book-demo', icon: CalendarDaysIcon },
]

function NotFound() {
  const navigate = useNavigate()

  return (
    <div className="not-found-page">
      <div className="container">
        <div className="not-found-content" data-testid="not-found-content">
          <div className="error-icon">
            <ShieldExclamationIcon className="icon-2xl nf-icon" />
          </div>
          <h1 className="error-title">404 - Page Not Found</h1>
          <p className="error-description">
            The page you're looking for seems to have been moved, deleted, or doesn't exist.
          </p>
          <div className="error-actions">
            <LuxuryButton onClick={() => navigate('/')} size="lg" data-testid="go-home-button">Return Home</LuxuryButton>
            <LuxuryButton onClick={() => navigate(-1)} variant="outline" size="lg" data-testid="go-back-button">Go Back</LuxuryButton>
          </div>
          <div className="helpful-links">
            <h3 className="links-title">You might be looking for:</h3>
            <div className="links-grid">
              {helpfulLinks.map(link => (
                <Link key={link.name} to={link.path} className="helpful-link" data-testid={`link-${link.name.toLowerCase().replace(/\s+/g, '-')}`}>
                  <link.icon className="icon-lg link-icon" />
                  <span>{link.name}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotFound
