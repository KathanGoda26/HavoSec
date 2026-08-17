import React, { useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { gsap } from 'gsap'
import { usePageLoaderStore } from '@/hooks/usePageLoader'

function PageLoader() {
  const setPageLoaded = usePageLoaderStore(state => state.setPageLoaded)
  const preloaderRef = useRef(null)
  const topRef = useRef(null)
  const bottomRef = useRef(null)
  const seamRef = useRef(null)
  const counterRef = useRef(null)
  const numberRef = useRef(null)

  useEffect(() => {
    // Ensure scroll is reset to the top immediately
    window.scrollTo(0, 0)

    const count = { value: 0 }
    const tl = gsap.timeline({ defaults: { ease: 'power4.inOut' } })

    // 1 — Count 0 → 100
    tl.to(count, {
      value: 100,
      duration: 2.4,
      ease: 'power2.out',
      onUpdate() {
        if (numberRef.current) {
          numberRef.current.textContent = Math.round(count.value)
        }
      },
    })
    // 2 — Fade counter out
    .to(counterRef.current, {
      opacity: 0,
      scale: 0.95,
      duration: 0.3,
      ease: 'power2.inOut',
    }, '-=0.1')
    // 3 — Scale out / fade the seam line
    .to(seamRef.current, {
      scaleX: 0,
      opacity: 0,
      duration: 0.4,
      ease: 'power3.inOut',
    }, '<')
    // 4 — Slide panels away
    .to(topRef.current, {
      yPercent: -100,
      duration: 1.25,
      ease: 'power4.inOut',
    }, '-=0.2')
    .to(bottomRef.current, {
      yPercent: 100,
      duration: 1.25,
      ease: 'power4.inOut',
    }, '<')
    // 5 — Hide preloader
    .set(preloaderRef.current, { display: 'none' })
    // 6 — Signal the rest of the app
    .call(() => {
      setPageLoaded(true)
    })
  }, [])

  return createPortal(
    <div className="preloader" ref={preloaderRef}>
      <div className="preloader__panel preloader__panel--top" ref={topRef}></div>
      <div className="preloader__panel preloader__panel--bottom" ref={bottomRef}></div>
      <div className="preloader__seam" ref={seamRef}></div>
      <div className="preloader__counter" ref={counterRef}>
        <span className="preloader__number" ref={numberRef}>0</span>
        <span className="preloader__symbol">%</span>
      </div>
    </div>,
    document.body
  )
}

export default PageLoader
