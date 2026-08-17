import React, { useState } from 'react'
import SEO from '@/components/SEO'
import { useContentStore } from '@/stores/contentStore'
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/solid'

function ComparisonCell({ value }) {
  if (value === 'true') return <CheckIcon className="check-icon" />
  if (value === 'false') return <XMarkIcon className="x-icon" />
  return <>{value}</>
}

function Pricing() {
  const contentStore = useContentStore()
  const [isAnnual, setIsAnnual] = useState(false)

  const hero = contentStore.pricing?.hero || { title: 'Simple, Transparent Pricing', subtitle: "Choose the perfect plan for your organization's security needs", savingsPercent: 20 }
  const plans = contentStore.pricing?.plans || []
  const comparison = contentStore.pricing?.comparison || []
  const faq = contentStore.pricing?.faq || []
  const cta = contentStore.pricing?.cta || { title: 'Ready to secure your digital assets?', subtitle: 'Start your 14-day free trial today. No credit card required.', primaryButton: 'Start Free Trial', secondaryButton: 'Contact Sales' }

  return (
    <div className="pricing-page">
      <SEO title="Pricing Plans" description="Simple, transparent pricing for HavoSec cybersecurity solutions." />

      <section className="pricing-hero">
        <div className="hero-content">
          <h1 className="hero-title">{hero.title}</h1>
          <p className="hero-subtitle">{hero.subtitle}</p>
          <div className="billing-toggle">
            <span className={!isAnnual ? 'active' : ''}>Monthly</span>
            <button onClick={() => setIsAnnual(!isAnnual)} className="toggle-switch">
              <span className={`toggle-slider ${isAnnual ? 'annual' : ''}`}></span>
            </button>
            <span className={isAnnual ? 'active' : ''}>Annual <span className="save-badge">Save {hero.savingsPercent}%</span></span>
          </div>
        </div>
      </section>

      <section className="pricing-cards">
        <div className="container">
          <div className="cards-grid">
            {plans.map((plan, index) => (
              <div key={index} className={`pricing-card ${plan.isPopular ? 'popular' : ''}`}>
                {plan.isPopular && <div className="popular-badge">Most Popular</div>}
                <div className="card-header">
                  <h3 className="plan-name">{plan.name}</h3>
                  <p className="plan-description">{plan.description}</p>
                </div>
                <div className="card-price">
                  {!plan.isCustom ? (
                    <><span className="currency">$</span><span className="amount">{isAnnual ? plan.annualPrice : plan.monthlyPrice}</span><span className="period">/month</span></>
                  ) : (
                    <span className="amount custom">Custom</span>
                  )}
                </div>
                <ul className="features-list">
                  {plan.features.map((feature, fIndex) => (
                    <li key={fIndex}><CheckIcon className="check-icon" /> {feature}</li>
                  ))}
                </ul>
                <button className={`cta-button ${plan.isPopular ? 'primary' : 'secondary'}`}>{plan.ctaText}</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="features-comparison">
        <div className="container">
          <h2 className="section-title">Compare Plans</h2>
          <div className="comparison-table">
            <table>
              <thead><tr><th className="feature-column">Features</th><th>Starter</th><th className="popular-column">Professional</th><th>Enterprise</th></tr></thead>
              <tbody>
                {comparison.map((row, index) => (
                  <tr key={index}>
                    <td className="feature-name">{row.feature}</td>
                    <td><ComparisonCell value={row.starter} /></td>
                    <td><ComparisonCell value={row.professional} /></td>
                    <td><ComparisonCell value={row.enterprise} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="faq-section">
        <div className="container">
          <h2 className="section-title">Frequently Asked Questions</h2>
          <div className="faq-grid">
            {faq.map((item, index) => (
              <div key={index} className="faq-item">
                <h3 className="faq-question">{item.question}</h3>
                <p className="faq-answer">{item.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-content">
          <h2 className="cta-title">{cta.title}</h2>
          <p className="cta-subtitle">{cta.subtitle}</p>
          <div className="cta-buttons">
            <button className="cta-button primary large">{cta.primaryButton}</button>
            <button className="cta-button secondary large">{cta.secondaryButton}</button>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Pricing
