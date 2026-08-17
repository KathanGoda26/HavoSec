import React from 'react'
import SEO from '@/components/SEO'
import { useContentStore } from '@/stores/contentStore'
import { ShieldCheckIcon, LightBulbIcon, EyeIcon, HeartIcon } from '@heroicons/react/24/outline'

const iconMap = { ShieldCheckIcon, LightBulbIcon, EyeIcon, HeartIcon }

const defaultValues = [
  { id: 1, icon: 'ShieldCheckIcon', title: 'Security First', description: 'Everything we do is designed with security as the foundation, never as an afterthought.' },
  { id: 2, icon: 'LightBulbIcon', title: 'Innovation', description: "We continuously push the boundaries of what's possible in cybersecurity technology." },
  { id: 3, icon: 'EyeIcon', title: 'Transparency', description: 'Clear communication and honest practices build trust with our clients and partners.' },
  { id: 4, icon: 'HeartIcon', title: 'Customer Success', description: 'Our success is measured by the security and peace of mind we provide our clients.' },
]

function About() {
  const contentStore = useContentStore()

  const aboutTitle = contentStore.about?.title || 'About HavoSec'
  const aboutDescription = contentStore.about?.description || 'Protecting organizations with cutting-edge cybersecurity analytics and threat detection since 2020'
  const missionText = contentStore.about?.mission || 'To empower organizations with advanced cybersecurity analytics that transform how they detect, respond to, and prevent cyber threats. We believe that proactive security should be accessible, intelligent, and automated.'
  const visionText = contentStore.about?.vision || missionText
  const companyInfo = contentStore.about?.companyInfo?.length ? contentStore.about.companyInfo : [
    { title: 'Founded', value: '2020' },
    { title: 'Team Size', value: '50-100 employees' },
    { title: 'Global Offices', value: 'San Francisco, New York, London' },
  ]
  const displayValues = contentStore.about?.values?.length ? contentStore.about.values : defaultValues

  function getValueIcon(iconName) {
    const Icon = iconMap[iconName] || ShieldCheckIcon
    return <Icon className="value-icon" />
  }

  return (
    <div className="about-page">
      <SEO title="About Us" description="Learn about HavoSec's mission to protect organizations with cutting-edge cybersecurity." />
      <div className="container">
        <section className="about-hero" data-testid="about-hero">
          <h1 className="heading-luxury">{aboutTitle}</h1>
          <p className="hero-subtitle">{aboutDescription}</p>
        </section>

        <section className="mission-section" data-testid="mission-section">
          <h2 className="section-title">Our Mission</h2>
          <p className="mission-text">{missionText}</p>
        </section>

        <section className="vision-section" data-testid="vision-section">
          <h2 className="section-title">Our Vision</h2>
          <p className="vision-text">{visionText}</p>
        </section>

        <section className="company-info" data-testid="company-info">
          <div className="info-grid">
            {companyInfo.map(info => (
              <div key={info.title} className="info-card">
                <h3 className="info-title">{info.title}</h3>
                <p className="info-value">{info.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="values-section" data-testid="values-section">
          <h2 className="section-title">Our Values</h2>
          <div className="values-grid">
            {displayValues.map(value => (
              <div key={value.id} className="value-card" data-testid={`value-${value.id}`}>
                {getValueIcon(value.icon)}
                <h3 className="value-title">{value.title}</h3>
                <p className="value-description">{value.description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default About
