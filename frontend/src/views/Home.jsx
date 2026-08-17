import React, { useRef, useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import LuxuryButton from '@/components/LuxuryButton'
import Lock3D from '@/components/Lock3D'
import MarqueeStrip from '@/components/MarqueeStrip'
import SEO from '@/components/SEO'
import { useContentStore } from '@/stores/contentStore'
import { usePageLoaderStore } from '@/hooks/usePageLoader'
import {
  ShieldCheckIcon,
  EyeIcon,
  BoltIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'

gsap.registerPlugin(ScrollTrigger)

const storyAchievements = [
  {
    id: 'threats',
    display: '50M+',
    label: 'Threats Blocked Daily',
    desc: 'AI-powered detection blocks millions of attacks across every vector, every day.',
    icon: ShieldCheckIcon,
  },
  {
    id: 'uptime',
    display: '99.9%',
    label: 'Uptime Guarantee',
    desc: 'Enterprise-grade availability so your security coverage never has a gap.',
    icon: ClockIcon,
  },
  {
    id: 'clients',
    display: '500+',
    label: 'Enterprise Clients',
    desc: 'Trusted by organisations across finance, healthcare, government and tech.',
    icon: ChartBarIcon,
  },
  {
    id: 'monitoring',
    display: '24/7',
    label: 'Security Monitoring',
    desc: 'Our SOC team monitors your infrastructure around the clock—zero blind spots.',
    icon: EyeIcon,
  },
]

const featureIcons = [
  ShieldCheckIcon,
  EyeIcon,
  BoltIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon,
]

function getFeatureIcon(i) {
  const Icon = featureIcons[i % featureIcons.length]
  return <Icon className="feat-icon-svg" />
}

function Home() {
  const navigate = useNavigate()
  const store = useContentStore()
  const pageLoaded = usePageLoaderStore(state => state.pageLoaded)

  const [featActiveIdx, setFeatActiveIdx] = useState(0)

  // Refs
  const lockFloatRef = useRef(null)
  const lockRef = useRef(null)
  const heroRef = useRef(null)
  const marqueeWrapRef = useRef(null)
  const achieveStoryRef = useRef(null)
  const featuresSectionRef = useRef(null)
  const featHeadlineRef = useRef(null)
  const featContentRef = useRef(null)
  const headlineRef = useRef(null)
  const panelRefs = useRef([])

  const setLockRot = (y, z = 0) => {
    if (lockRef.current) {
      lockRef.current.setScrollRotation(y, z)
    }
  }

  // Computed values derived from contentStore
  const heroTitle = useMemo(() => {
    const t = store.hero?.title || 'Secure Your Digital Assets with'
    return t.replace(/\s*(HavoSec|with HavoSec)\s*$/i, '').trim() + ' '
  }, [store.hero?.title])

  const animationSettings = useMemo(() => ({
    modelPath: store.hero?.animation?.modelPath || '/lock.glb',
    primaryColor: store.hero?.animation?.primaryColor || '#673ee6',
    secondaryColor: store.hero?.animation?.secondaryColor || '#00b090',
    scale: store.hero?.animation?.scale || 3,
    autoRotate: true,
    rotationSpeed: store.hero?.animation?.rotationSpeed || 0.005,
  }), [store.hero?.animation])

  const displayFeatures = useMemo(() => {
    return store.features?.items?.length ? store.features.items : [
      {
        title: 'Real-Time Threat Detection',
        description: 'AI-powered detection identifies attacks in milliseconds.',
        benefit: 'Stay ahead of emerging threats',
      },
      {
        title: 'Advanced Monitoring',
        description: 'Comprehensive visibility across your entire digital infrastructure.',
        benefit: 'Complete oversight of your security landscape',
      },
      {
        title: 'Automated Response',
        description: 'Instant automated responses to security threats.',
        benefit: 'Minimize damage immediately',
      },
      {
        title: 'Analytics Dashboard',
        description: 'Rich analytics and reporting for security insights.',
        benefit: 'Data-driven security decisions',
      },
    ]
  }, [store.features?.items])

  const demoTitle = useMemo(() => store.hero?.demoTitle || 'Ready to Protect Your', [store.hero?.demoTitle])
  const demoTitle2 = useMemo(() => store.hero?.demoTitle2 || 'Organization?', [store.hero?.demoTitle2])
  const demoDescription = useMemo(() => store.hero?.demoDescription || 'Get a personalized demonstration of HavoSec.', [store.hero?.demoDescription])
  const demoButtonText = useMemo(() => store.hero?.demoButtonText || 'Schedule Your Demo Today', [store.hero?.demoButtonText])
  const demoButtonLink = useMemo(() => store.hero?.demoButtonLink || '/book-demo', [store.hero?.demoButtonLink])

  const scrollDown = () => {
    window.scrollBy({ top: window.innerHeight, behavior: 'smooth' })
  }

  // Hero Entry Animation
  useEffect(() => {
    if (!pageLoaded) return

    gsap.set(['.hero-left', '.hero-right'], { opacity: 0 })
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } })
    tl.fromTo(
      '.hero-left',
      { x: -80, opacity: 0 },
      { x: 0, opacity: 1, duration: 1.2 }
    )
      .fromTo(
        '.hero-right',
        { x: 80, opacity: 0 },
        { x: 0, opacity: 1, duration: 1.2 },
        '-=1.0'
      )
  }, [pageLoaded])

  // Scroll Animations
  useEffect(() => {
    const lockFloat = lockFloatRef.current
    const marqueeWrap = marqueeWrapRef.current
    const hero = heroRef.current
    const achieveStory = achieveStoryRef.current
    const featuresSection = featuresSectionRef.current
    const featHeadline = featHeadlineRef.current
    const featContent = featContentRef.current

    if (!lockFloat || !marqueeWrap || !hero || !achieveStory || !featuresSection) return

    // Clear transforms left by a hot reload or an earlier animation version.
    // Only the complete heading groups are allowed to own a heading transform.
    const achieveHeading = headlineRef.current?.querySelector('.achieve-heading')
    const featureHeading = featHeadline?.querySelector('.feature-heading')
    const titleLines = [
      headlineRef.current?.querySelector('.achieve-headline'),
      featHeadline?.querySelector('.feat-headline'),
    ].filter(Boolean)
    gsap.set(titleLines, { clearProps: 'transform,opacity' })
    gsap.set([achieveHeading, featureHeading].filter(Boolean), { x: '110vw', autoAlpha: 0 })

    // Lock stays centered and does not participate in scroll-driven motion.
    gsap.set(lockFloat, { xPercent: -50, yPercent: -50 })

    // Phase 1->2: keep steady center
    const stMarquee = ScrollTrigger.create({
      trigger: marqueeWrap,
      start: 'top 80%',
      end: 'bottom 20%',
      scrub: true,
      onUpdate() {
        gsap.set(lockFloat, { yPercent: -50 })
      },
    })

    // HERO -> ACHIEVEMENTS
    const HEADING_PHASE = 0.2

    // ACHIEVEMENTS CYCLE
    const stAchieve = ScrollTrigger.create({
      trigger: achieveStory,
      start: 'top top',
      end: 'bottom bottom',
      scrub: 1.2,
      onUpdate(self) {
        const p = self.progress
        const heading = headlineRef.current?.querySelector('.achieve-heading')

        if (p < HEADING_PHASE) {
          const hp = p / HEADING_PHASE
          const xVW = 100 - hp * 310
          if (heading) {
            gsap.set(heading, { x: `${xVW}vw`, autoAlpha: 1 })
          }
          // Hide all panels
          panelRefs.current.forEach(el => {
            if (el) gsap.set(el, { opacity: 0, y: 40 })
          })
        } else {
          if (heading) gsap.set(heading, { x: '-120vw', autoAlpha: 0 })

          const pp = (p - HEADING_PHASE) / (1 - HEADING_PHASE)
          const num = storyAchievements.length

          panelRefs.current.forEach((el, i) => {
            if (!el) return
            const s0 = i / num
            const s1 = (i + 1) / num
            let op = 0
            let y = 40
            if (pp >= s0 && pp < s1) {
              const loc = (pp - s0) / (s1 - s0)
              if (loc < 0.2) {
                op = loc / 0.2
                y = 40 * (1 - op)
              } else if (loc > 0.8) {
                op = (1 - loc) / 0.2
                y = 0
              } else {
                op = 1
                y = 0
              }
            }
            const direction = i % 2 === 0 ? -1 : 1
            gsap.set(el, {
              opacity: op,
              x: direction * 48 * (1 - op),
              y,
              rotationY: direction * 18 * (1 - op),
              scale: 0.93 + op * 0.07,
            })
          })

        }
      },
    })

    // FEATURES DETAIL CYCLE
    let lastActiveIdx = -1
    const stFeaturesCycle = ScrollTrigger.create({
      trigger: featuresSection,
      start: 'top top',
      end: 'bottom bottom',
      scrub: 1.2,
      onUpdate(self) {
        const p = self.progress
        const totalFeatures = displayFeatures.length
        const headingPhase = 1 / (totalFeatures + 1)
        const heading = featHeadline?.querySelector('.feature-heading')

        if (p < headingPhase) {
          const hp = p / headingPhase
          const xVW = 100 - hp * 310
          if (heading) gsap.set(heading, { x: `${xVW}vw`, autoAlpha: 1 })
          if (featContent) gsap.set(featContent, { opacity: 0, y: 150 })
        } else {
          if (heading) gsap.set(heading, { x: '-120vw', autoAlpha: 0 })

          const pp = (p - headingPhase) / (1 - headingPhase)
          const entryFraction = 0.08

          if (pp < entryFraction) {
            const entryP = pp / entryFraction
            if (featContent) {
              gsap.set(featContent, {
                opacity: Math.pow(entryP, 1.5),
                y: 150 * (1 - entryP),
              })
            }
          } else {
            if (featContent) gsap.set(featContent, { opacity: 1, y: 0 })
          }

          const idx = Math.min(Math.floor(pp * totalFeatures), totalFeatures - 1)
          if (idx !== lastActiveIdx) {
            lastActiveIdx = idx
            setFeatActiveIdx(idx)
          }
        }
      },
    })

    return () => {
      stMarquee.kill()
      stAchieve.kill()
      stFeaturesCycle.kill()
    }
  }, [displayFeatures.length])

  return (
    <div className="home-page">
      <SEO
        title="A Autonomous Cybersecurity Platform"
        description="Protect your organization with HavoSec's comprehensive cybersecurity solutions."
      />

      <div className="lock-float" ref={lockFloatRef}>
        <Lock3D
          ref={lockRef}
          modelPath={animationSettings.modelPath}
          primaryColor={animationSettings.primaryColor}
          secondaryColor={animationSettings.secondaryColor}
          scale={animationSettings.scale}
          autoRotate={false}
          rotationSpeed={animationSettings.rotationSpeed}
        />
      </div>

      <section className="hero-section" ref={heroRef} data-testid="hero-section">
        <div className="hero-col hero-left hero-animate">
          <span className="hero-tagline">AUTONOMOUS CYBERSECURITY PLATFORM</span>
          <h1 className="hero-heading-left">
            Break Before<br /><span className="hero-accent-green">Hackers</span> Do
          </h1>
          <p className="hero-desc-left">
            HavoSec autonomously simulates attacks, detects vulnerabilities, and
            protects your systems in real time
          </p>
        </div>

        <div className="hero-col hero-center-col">
          <div className="hero-bg-visuals">
            <div className="bg-ring ring-1"></div>
            <div className="bg-ring ring-2"></div>
            <div className="bg-ring ring-3"></div>
            <div className="bg-glow"></div>
          </div>
        </div>

        <div className="hero-col hero-right hero-animate">
          <span className="hero-tagline">PROACTIVE. AUTONOMOUS. RELENTLESS</span>
          <h2 className="hero-heading-right">
            Security That<br />Thinks Like an<br />
            <span className="hero-accent-purple">Attacker</span>
          </h2>
          <p className="hero-desc-right">
            Offensive AI meets defensive intelligence to give you continuous
            protection without constant human intervention
          </p>
        </div>

        <div className="hero-scroll-hint">
          <button onClick={scrollDown} className="scroll-hint">
            SCROLL TO EXPLORE
            <span className="scroll-line"></span>
          </button>
        </div>
      </section>

      <div className="marquee-wrap" ref={marqueeWrapRef}>
        <MarqueeStrip />
      </div>

      <div className="achieve-story" ref={achieveStoryRef}>
        <div className="achieve-sticky">
          <div className="achieve-headline-wrap" ref={headlineRef}>
            <div className="story-heading achieve-heading">
              <span className="story-kicker">Proof, not promises</span>
              <span className="achieve-headline">Trusted by<br />Industry Leaders</span>
              <p>Security teams use HavoSec to turn continuous risk into decisive action.</p>
            </div>
          </div>
          {storyAchievements.map((a, i) => (
            <div
              key={a.id}
              className="achieve-panel"
              ref={el => {
                if (el) panelRefs.current[i] = el
              }}
            >
              <article className={`stat-wrap ${i % 2 === 0 ? 'stat-left' : 'stat-right'}`}>
                <span className="stat-index">0{i + 1}</span>
                <div className="stat-icon-wrap"><a.icon className="stat-svg" /></div>
                <div className="stat-num">{a.display}</div>
                <div className="stat-label">{a.label}</div>
                <p className="stat-desc">{a.desc}</p>
                <span className="stat-line" />
              </article>
            </div>
          ))}
        </div>
      </div>

      <div
        className="feat-story"
        ref={featuresSectionRef}
        data-testid="features-section"
        style={{ height: `calc((${displayFeatures.length} + 1) * 100vh)` }}
      >
        <div className="feat-sticky">
          <div className="feat-headline-wrap" ref={featHeadlineRef}>
            <div className="story-heading feature-heading">
              <span className="story-kicker">Always one move ahead</span>
              <span className="feat-headline">Advanced<br />Security Features</span>
              <p>A unified security layer that sees, decides and acts at machine speed.</p>
            </div>
          </div>

          <div className="feat-content" ref={featContentRef}>
            <div className="feat-left">
              <span className="feat-eyebrow">Security command centre</span>
              <ul className="feat-list">
                {displayFeatures.map((feature, i) => (
                  <li
                    key={i}
                    className={`feat-list-item ${featActiveIdx === i ? 'is-active' : ''}`}
                  >
                    {feature.title}
                  </li>
                ))}
              </ul>
              <div className="feat-counter">
                <span>{featActiveIdx + 1}</span>
                <span className="feat-counter-sep">&nbsp;—&nbsp;</span>
                <span>{displayFeatures.length}</span>
              </div>
            </div>

            <div className="feat-right">
              {displayFeatures.map((feature, i) => (
                <div
                  key={i}
                  className={`feat-detail ${featActiveIdx === i ? 'is-active' : ''}`}
                >
                  <div className="feat-card-no">0{i + 1}</div>
                  <div className="feat-detail-icon">
                    {getFeatureIcon(i)}
                  </div>
                  <h3 className="feat-detail-title">{feature.title}</h3>
                  <p className="feat-detail-desc">{feature.description}</p>
                  {feature.benefit && (
                    <div className="feat-detail-benefit">
                      {feature.benefit}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <section className="demo-section" data-testid="demo-section">
        <div className="container">
          <div className="demo-card">
            <div className="demo-content">
              <div className="demo-text">
                <div className="demo-title-group">
                  <h2 className="demo-title">{demoTitle}</h2>
                  <h2 className="demo-title2">{demoTitle2}</h2>
                </div>
                <p className="demo-description">{demoDescription}</p>
                <LuxuryButton
                  variant="sweep"
                  onClick={() => navigate(demoButtonLink)}
                  size="xl"
                  className="demo-cta-button"
                  data-testid="demo-cta-button"
                >
                  {demoButtonText}
                </LuxuryButton>
              </div>
              <div className="demo-image">
                <img
                  src="https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600&h=400&fit=crop"
                  alt="Security Operations Center"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home
