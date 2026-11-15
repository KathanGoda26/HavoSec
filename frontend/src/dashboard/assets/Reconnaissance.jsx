import React from 'react'

export default function Reconnaissance({ data }) {
  if (!data) return <section className="recon-section"><h2>Reconnaissance</h2><p>No reconnaissance observations are available for this asset.</p></section>
  return (
    <section className="recon-section">
      <h2>Reconnaissance (demo)</h2>
      <p className="page-subtitle">Source run: {data.sourceRun} · Observed: {data.observedAt}. Illustrative observations only.</p>
      <div className="recon-grid">
        <div className="recon-card"><h4>Open Ports</h4><div className="port-list">{data.ports.map(port => <span className="port-badge" key={port}>{port}</span>)}</div></div>
        <div className="recon-card"><h4>Services Detected</h4><ul className="service-list">{data.services.map(service => <li key={service}>{service}</li>)}</ul></div>
        <div className="recon-card"><h4>Technologies</h4><div className="tech-list">{data.technologies.map(tech => <span className="tech-badge" key={tech}>{tech}</span>)}</div></div>
      </div>
    </section>
  )
}
