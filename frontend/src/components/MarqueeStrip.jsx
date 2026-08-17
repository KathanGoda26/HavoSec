import React, { useState } from 'react'
import {
  ShieldCheckIcon,
  LockClosedIcon,
  EyeIcon,
  BoltIcon,
  ServerStackIcon,
  FingerPrintIcon,
  BugAntIcon,
  CloudIcon,
  CpuChipIcon,
  KeyIcon,
} from '@heroicons/react/24/solid'

const items = [
  { label: 'Zero-Trust Security', icon: ShieldCheckIcon },
  { label: 'End-to-End Encryption', icon: LockClosedIcon },
  { label: 'Threat Intelligence', icon: EyeIcon },
  { label: 'Real-Time Detection', icon: BoltIcon },
  { label: 'SOC Automation', icon: ServerStackIcon },
  { label: 'Identity & Access', icon: FingerPrintIcon },
  { label: 'Malware Analysis', icon: BugAntIcon },
  { label: 'Cloud Security', icon: CloudIcon },
  { label: 'AI-Powered Defense', icon: CpuChipIcon },
  { label: 'Key Management', icon: KeyIcon },
]

function MarqueeStrip() {
  const [paused, setPaused] = useState(false)

  return (
    <section className="marquee-section">
      <div
        className="marquee-wrapper"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <div className={`marquee-track ${paused ? 'is-paused' : ''}`}>
          {[1, 2].map(n => (
            <div className="marquee-inner" key={n}>
              {items.map(item => (
                <React.Fragment key={item.label + n}>
                  <div className="marquee-item">
                    <item.icon className="marquee-icon" aria-hidden="true" />
                    <span className="marquee-label">{item.label}</span>
                  </div>
                  <div className="marquee-dot"></div>
                </React.Fragment>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default MarqueeStrip
