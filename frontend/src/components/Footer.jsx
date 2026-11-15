import React, { useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const letters = "HAVOSEC".split("");

function Footer() {
  const currentYear = useMemo(() => new Date().getFullYear(), []);
  const footerRef = useRef(null);
  const letterRefs = useRef([]);
  const navRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    const footer = footerRef.current;
    const letterEls = letterRefs.current.filter(Boolean);
    const navEl = navRef.current;
    const bottomEl = bottomRef.current;
    if (!footer || !letterEls.length || !navEl || !bottomEl) return;

    const ctx = gsap.context(() => {
      const totalLetters = letterEls.length;
      const letterSpacing = 9.3;
      const totalWidth = (totalLetters - 1) * letterSpacing;

      // ── Initial (hidden) state for all three sections ──────────────────
      // NOTE: per-property function values (not a function for the whole
      // vars object) — this is what actually spaces each letter out.
      gsap.set(letterEls, {
        x: (index) => `${index * letterSpacing - totalWidth / 2}vw`,
        y: "4vh",
        xPercent: -50,
        yPercent: -50,
        opacity: 0,
      });
      gsap.set(navEl, { y: 20, opacity: 0 });
      gsap.set(bottomEl, { y: 16, opacity: 0 });

      // ── Sequenced reveal: title → links → legal ─────────────────────────
      // Each section fully fades in before the next begins, roughly a
      // second apart, and reverses cleanly when the user scrolls back up.
      const timeline = gsap.timeline({
        paused: true,
        defaults: { ease: "power3.out" },
      });

      timeline
        // 1. Title (the big HAVOSEC letters)
        .to(letterEls, {
          x: (index) => `${index * letterSpacing - totalWidth / 2}vw`,
          y: 0,
          xPercent: -50,
          yPercent: -50,
          opacity: 1,
          duration: 1,
          stagger: 0.3,
        })
        // 2. Nav links — starts ~1s after the title finishes
        .to(
          navEl,
          {
            y: 0,
            opacity: 1,
            duration: 0.6,
            ease: "power2.out",
          },
          "+=0.5",
        )
        // 3. Legal / copyright row — starts ~1s after the links finish
        .to(
          bottomEl,
          {
            y: 0,
            opacity: 1,
            duration: 0.3,
            ease: "power2.out",
          },
          "+=0.5",
        );

      ScrollTrigger.create({
        trigger: footer,
        start: "top 80%",
        end: "bottom bottom",
        invalidateOnRefresh: true,
        onEnter: () => timeline.play(),
        onLeaveBack: () => timeline.reverse(),
      });
    }, footer);

    // Public routes are lazy-loaded. On a hard refresh the footer can mount
    // while the page is still showing its short loading fallback, which makes
    // ScrollTrigger cache the wrong vertical position. Refresh whenever the
    // actual page height changes so the trigger stays correct.
    let refreshFrame = null;
    let disposed = false;
    const scheduleRefresh = () => {
      if (disposed) return;
      if (refreshFrame !== null) cancelAnimationFrame(refreshFrame);
      refreshFrame = requestAnimationFrame(() => {
        refreshFrame = null;
        ScrollTrigger.refresh();
      });
    };

    const mainContent = document.querySelector(".main-content");
    const resizeObserver = new ResizeObserver(scheduleRefresh);
    if (mainContent) resizeObserver.observe(mainContent);
    resizeObserver.observe(footer);
    window.addEventListener("load", scheduleRefresh);
    document.fonts?.ready.then(scheduleRefresh);
    scheduleRefresh();

    return () => {
      disposed = true;
      if (refreshFrame !== null) cancelAnimationFrame(refreshFrame);
      resizeObserver.disconnect();
      window.removeEventListener("load", scheduleRefresh);
      ctx.revert();
    };
  }, []);

  return (
    <footer className="footer-anim" ref={footerRef}>
      <div className="footer-anim__pin">
        <div className="footer-anim__content" ref={navRef}>
          <nav className="footer-anim__nav" aria-label="Footer navigation">
            <Link to="/about" className="footer-anim__link">
              About Us
            </Link>
            <Link to="/pricing" className="footer-anim__link">
              Pricing
            </Link>
            <Link to="/blog" className="footer-anim__link">
              Insights
            </Link>
            <Link to="/book-demo" className="footer-anim__link">
              Book a Demo
            </Link>
          </nav>
        </div>

        <div className="footer-anim__stage" aria-hidden="true">
          {letters.map((letter, index) => (
            <span
              key={`${letter}-${index}`}
              className="footer-anim__letter"
              ref={(element) => {
                letterRefs.current[index] = element;
              }}
            >
              {letter}
            </span>
          ))}
        </div>

        <div className="footer-anim__bottom" ref={bottomRef}>
          <div className="footer-anim__copyright">
            © {currentYear} HavoSec. All rights reserved.
          </div>
          <div className="footer-legal">
            <Link to="/about">Privacy</Link>
            <Link to="/about">Terms</Link>
            <Link to="/about">Security</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
