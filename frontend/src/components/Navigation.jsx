import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { usePageLoaderStore } from '@/hooks/usePageLoader'
import { useContentStore } from '@/stores/contentStore'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

const SCRAMBLE_CHARS = '01'

function useScramble(ref) {
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const original = el.textContent.trim()
    let rafId = null
    let startTime = null
    const DURATION = 600

    function scrambleFrame(ts) {
      if (!startTime) startTime = ts
      const elapsed = ts - startTime
      const progress = Math.min(elapsed / DURATION, 1)
      const revealedCount = Math.floor(progress * original.length)

      el.textContent = original
        .split('')
        .map((char, i) => {
          if (char === ' ') return ' '
          if (i < revealedCount) return original[i]
          return SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)]
        })
        .join('')

      if (progress < 1) {
        rafId = requestAnimationFrame(scrambleFrame)
      } else {
        el.textContent = original
      }
    }

    function startScramble() {
      if (rafId) cancelAnimationFrame(rafId)
      startTime = null
      rafId = requestAnimationFrame(scrambleFrame)
    }

    function stopScramble() {
      if (rafId) cancelAnimationFrame(rafId)
      rafId = null
      el.textContent = original
    }

    el.addEventListener('mouseenter', startScramble)
    el.addEventListener('mouseleave', stopScramble)

    return () => {
      el.removeEventListener('mouseenter', startScramble)
      el.removeEventListener('mouseleave', stopScramble)
      if (rafId) cancelAnimationFrame(rafId)
    }
  }, [ref])
}

function ScrambleText({ children }) {
  const ref = useRef(null)
  useScramble(ref)
  return <span ref={ref}>{children}</span>
}

function Navigation() {
  const contentStore = useContentStore()
  const pageLoaded = usePageLoaderStore(state => state.pageLoaded)
  const headerRef = useRef(null)
  const [isScrolled, setIsScrolled] = useState(false)
  const [isReduced, setIsReduced] = useState(false)

  const navLinks = contentStore.header?.navLinks || [
    { name: 'About', path: '/about' },
    { name: 'Pricing', path: '/pricing' },
    { name: 'Blog', path: '/blog' },
  ]

  const handleScroll = useCallback(() => {
    const scrollY = window.scrollY
    setIsScrolled(scrollY > 50)
    setIsReduced(scrollY > 200)
  }, [])

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()

    gsap.set(headerRef.current, { y: -120, opacity: 0 })

    function animateNavIn() {
      gsap.to(headerRef.current, {
        y: 0,
        opacity: 1,
        duration: 1.3,
        ease: 'power3.out',
        delay: 0.25,
      })
    }

    if (pageLoaded) {
      animateNavIn()
    }

    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [pageLoaded])

  return (
    <header
      ref={headerRef}
      className={`site-header ${isReduced ? 'is-reduced' : ''} ${isScrolled ? 'is-scrolled' : ''}`}
    >
      <nav className={`site-nav ${isReduced ? 'nav-centered' : 'nav-spread'}`}>
        <div className="nav-brand">
          <Link to="/" className="brand-link">
            <span className="brand-name">HavoSec</span>
          </Link>
        </div>

        {!isReduced && (
          <div className="nav-links">
            {navLinks.map(link => (
              <Link
                key={link.name}
                to={link.path}
                className="nav-link"
                data-testid={`nav-${link.name.toLowerCase()}`}
              >
                {link.name}
              </Link>
            ))}
          </div>
        )}

        <div className={`nav-actions ${isReduced ? 'nav-actions-reduced' : ''}`}>
          {!isReduced && (
            <Link to="/book-demo" className="nav-link" data-testid="book-demo-button">
              Book Demo
            </Link>
          )}

          {!isReduced && (
            <div className="nav-auth">
              <div className="nav-auth-guest">
                <Link to="/auth/login" className="nav-login" data-testid="login-button">
                  <span>Login</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>
    </header>
  )
}

export default Navigation
