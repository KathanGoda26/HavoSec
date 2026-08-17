import React, { useState, useMemo } from 'react'
import SEO from '@/components/SEO'
import LuxuryButton from '@/components/LuxuryButton'
import { ClockIcon, UserGroupIcon, ShieldCheckIcon, CheckCircleIcon, EyeIcon, ChartBarIcon, CogIcon } from '@heroicons/react/24/outline'

const expectations = [
  { id: 1, icon: EyeIcon, title: 'Platform Overview', description: 'Complete walkthrough of the HavoSec interface and core features' },
  { id: 2, icon: ChartBarIcon, title: 'Live Dashboard', description: 'Real-time security monitoring and threat detection in action' },
  { id: 3, icon: CogIcon, title: 'Custom Configuration', description: 'See how the platform can be tailored to your specific environment' },
]

function BookDemo() {
  const [form, setForm] = useState({ firstName: '', lastName: '', email: '', phone: '', company: '', companySize: '', preferredDate: '', message: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const minDate = useMemo(() => {
    const t = new Date(); t.setDate(t.getDate() + 1)
    return t.toISOString().split('T')[0]
  }, [])

  const isFormValid = form.firstName && form.lastName && form.email && form.company && Object.keys(errors).length === 0

  const updateField = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const validateForm = () => {
    const e = {}
    if (!form.firstName.trim()) e.firstName = 'First name is required'
    if (!form.lastName.trim()) e.lastName = 'Last name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Please enter a valid email address'
    if (!form.company.trim()) e.company = 'Company name is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const submitDemo = (e) => {
    e.preventDefault()
    if (!validateForm()) return
    setSubmitting(true)
    setTimeout(() => {
      setSubmitted(true)
      setForm({ firstName: '', lastName: '', email: '', phone: '', company: '', companySize: '', preferredDate: '', message: '' })
      setSubmitting(false)
    }, 1500)
  }

  return (
    <div className="book-demo-page">
      <SEO title="Book Your Demo" description="Schedule a personalized demonstration of HavoSec's security platform." />
      <div className="container">
        <section className="demo-hero" data-testid="demo-hero">
          <h1 className="heading-luxury">Book Your Demo</h1>
          <p className="hero-subtitle">See HavoSec in action. Get a personalized demonstration tailored to your organization's security needs.</p>
        </section>

        <section className="demo-info" data-testid="demo-info">
          <div className="info-grid">
            <div className="info-card"><ClockIcon className="info-icon" /><h3 className="info-title">30-Minute Session</h3><p className="info-description">Quick but comprehensive overview of our platform</p></div>
            <div className="info-card"><UserGroupIcon className="info-icon" /><h3 className="info-title">Personalized</h3><p className="info-description">Tailored to your specific security requirements</p></div>
            <div className="info-card"><ShieldCheckIcon className="info-icon" /><h3 className="info-title">Live Environment</h3><p className="info-description">Real-time demonstration with actual threat data</p></div>
          </div>
        </section>

        <section className="demo-form-section" data-testid="demo-form-section">
          <div className="form-container">
            <h2 className="form-title">Schedule Your Demo</h2>
            <form onSubmit={submitDemo} className="demo-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="firstName" className="form-label">First Name *</label>
                  <input id="firstName" value={form.firstName} onChange={e => updateField('firstName', e.target.value)} type="text" required className={`form-input ${errors.firstName ? 'error' : ''}`} data-testid="first-name-input" />
                  {errors.firstName && <span className="error-message">{errors.firstName}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="lastName" className="form-label">Last Name *</label>
                  <input id="lastName" value={form.lastName} onChange={e => updateField('lastName', e.target.value)} type="text" required className={`form-input ${errors.lastName ? 'error' : ''}`} data-testid="last-name-input" />
                  {errors.lastName && <span className="error-message">{errors.lastName}</span>}
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="email" className="form-label">Email Address *</label>
                  <input id="email" value={form.email} onChange={e => updateField('email', e.target.value)} type="email" required className={`form-input ${errors.email ? 'error' : ''}`} data-testid="email-input" />
                  {errors.email && <span className="error-message">{errors.email}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="phone" className="form-label">Phone Number</label>
                  <input id="phone" value={form.phone} onChange={e => updateField('phone', e.target.value)} type="tel" className="form-input" data-testid="phone-input" />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="company" className="form-label">Company *</label>
                  <input id="company" value={form.company} onChange={e => updateField('company', e.target.value)} type="text" required className={`form-input ${errors.company ? 'error' : ''}`} data-testid="company-input" />
                  {errors.company && <span className="error-message">{errors.company}</span>}
                </div>
                <div className="form-group">
                  <label htmlFor="companySize" className="form-label">Company Size</label>
                  <select id="companySize" value={form.companySize} onChange={e => updateField('companySize', e.target.value)} className="form-input" data-testid="company-size-select">
                    <option value="">Select company size</option>
                    <option value="1-10">1-10 employees</option>
                    <option value="11-50">11-50 employees</option>
                    <option value="51-200">51-200 employees</option>
                    <option value="201-1000">201-1000 employees</option>
                    <option value="1000+">1000+ employees</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="preferredDate" className="form-label">Preferred Date</label>
                <input id="preferredDate" value={form.preferredDate} onChange={e => updateField('preferredDate', e.target.value)} type="date" min={minDate} className="form-input" data-testid="preferred-date-input" />
              </div>
              <div className="form-group">
                <label htmlFor="message" className="form-label">Additional Information</label>
                <textarea id="message" value={form.message} onChange={e => updateField('message', e.target.value)} rows="4" placeholder="Tell us about your specific security needs or questions..." className="form-input" data-testid="message-textarea"></textarea>
              </div>
              <div className="form-actions">
                <LuxuryButton type="submit" size="lg" loading={submitting} disabled={!isFormValid} data-testid="submit-demo-button">Schedule Demo</LuxuryButton>
              </div>
            </form>
            {submitted && (
              <div className="success-message" data-testid="success-message">
                <CheckCircleIcon className="success-icon" />
                <h3 className="success-title">Demo Request Submitted!</h3>
                <p className="success-description">Thank you for your interest. Our team will contact you within 24 hours to schedule your personalized demonstration.</p>
              </div>
            )}
          </div>
        </section>

        <section className="expectations-section" data-testid="expectations-section">
          <h2 className="section-title">What to Expect in Your Demo</h2>
          <div className="expectations-grid">
            {expectations.map(exp => (
              <div key={exp.id} className="expectation-card" data-testid={`expectation-${exp.id}`}>
                <exp.icon className="expectation-icon" />
                <h3 className="expectation-title">{exp.title}</h3>
                <p className="expectation-description">{exp.description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default BookDemo
