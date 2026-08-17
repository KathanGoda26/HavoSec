import React, { useRef, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const letters = 'HAVOSEC'.split('')

function Footer() {
  const currentYear = useMemo(() => new Date().getFullYear(), [])
  const footerRef = useRef(null)
  const pinRef = useRef(null)
  const letterRefs = useRef([])

  useEffect(() => {
    const els = letterRefs.current.filter(Boolean)
    if (!els.length) return

    const ctx = gsap.context(() => {
      const totalLetters = els.length

      // Set initial positions
      els.forEach((el, i) => {
        const letterSpacing = 12
        const totalWidth = (totalLetters - 1) * letterSpacing
        const startX = i * letterSpacing - totalWidth / 2

        gsap.set(el, {
          x: `${startX}vw`,
          y: '80vh',
          rotation: 0,
        })
      })

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: footerRef.current,
          start: 'top top',
          end: '+=150%',
          pin: pinRef.current,
          scrub: 1.5,
          anticipatePin: 1,
        },
      })

      // All letters move straight up together
      els.forEach((el, i) => {
        const letterSpacing = 12
        const totalWidth = (totalLetters - 1) * letterSpacing
        const finalX = i * letterSpacing - totalWidth / 2

        tl.to(el, {
          x: `${finalX}vw`,
          y: '10vh',
          rotation: 0,
          ease: 'power2.out',
          duration: 1,
        }, 0)
      })

      // Reveal nav first
      tl.fromTo('.footer-anim__nav', { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.4 }, 0.5)

      // Reveal bottom bar
      tl.fromTo('.footer-anim__bottom', { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0.6)
    }, footerRef.current)

    return () => ctx.revert()
  }, [])

  return (
    <footer className="footer-anim" ref={footerRef}>
      <div className="footer-anim__pin" ref={pinRef}>
        {/* Footer content revealed as letters leave */}
        <div className="footer-anim__content">
          <nav className="footer-anim__nav">
            <Link to="/about" className="footer-anim__link">About Us</Link>
            <Link to="/pricing" className="footer-anim__link">Pricing</Link>
            <a href="#" className="footer-anim__link">Careers</a>
            <a href="#" className="footer-anim__link">Contact</a>
            <a href="#" className="footer-anim__link">Help Center</a>
          </nav>
        </div>

        {/* Big HAVOSEC letters */}
        <div className="footer-anim__stage">
          {letters.map((letter, i) => (
            <span
              key={i}
              className="footer-anim__letter"
              ref={el => letterRefs.current[i] = el}
            >
              {letter}
            </span>
          ))}
        </div>

        <div className="footer-anim__bottom">
          <div className="footer-anim__copyright">
            © {currentYear} HavoSec. All rights reserved.
          </div>
          <div className="footer-legal">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Cookie Policy</a>
            <a href="#">Security</a>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
