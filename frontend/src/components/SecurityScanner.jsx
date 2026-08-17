import React, { useState, useMemo, useEffect } from 'react'
import { useSecurityStore } from '@/stores/securityStore'

function SecurityScanner() {
  const securityStore = useSecurityStore()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedWorkflow, setSelectedWorkflow] = useState('')
  const [target, setTarget] = useState('')

  const workflows = securityStore.workflows
  const isScanning = securityStore.isScanning
  const currentScan = securityStore.currentScan
  const error = securityStore.error

  const selectedWorkflowDetails = useMemo(() => {
    if (!selectedWorkflow) return null
    return workflows.find(w => w.id === selectedWorkflow)
  }, [selectedWorkflow, workflows])

  const canStartScan = selectedWorkflow && target && !isScanning

  const openModal = async () => {
    setIsModalOpen(true)
    if (workflows.length === 0) {
      securityStore.fetchWorkflows()
    }
  }

  const closeModal = () => setIsModalOpen(false)

  const startScan = async () => {
    if (!canStartScan) return
    try {
      await securityStore.startScan(selectedWorkflow, target)
      closeModal()
      window.location.href = '/dashboard/attack-insights'
    } catch (err) {
      console.error('Scan failed:', err)
    }
  }

  useEffect(() => {
    if (!isModalOpen) return
    const handleEscape = (e) => {
      if (e.key === 'Escape') closeModal()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isModalOpen])

  return (
    <div className="security-scanner-modal">
      <button onClick={openModal} className="scan-trigger-btn">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="icon">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
        </svg>
        Run Security Scan
      </button>

      {isModalOpen && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-container" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Security Scanner</h2>
              <button onClick={closeModal} className="close-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="modal-body">
              <p className="modal-description">Run comprehensive security assessments on your infrastructure</p>

              <div className="scan-form">
                <div className="form-group">
                  <label htmlFor="workflow">Scan Type</label>
                  <select id="workflow" value={selectedWorkflow} onChange={e => setSelectedWorkflow(e.target.value)} disabled={isScanning} className="form-control">
                    <option value="">Select a scan type...</option>
                    {workflows.map(workflow => (
                      <option key={workflow.id} value={workflow.id}>{workflow.name}</option>
                    ))}
                  </select>
                  {selectedWorkflowDetails && <small className="form-text">{selectedWorkflowDetails.description}</small>}
                </div>

                <div className="form-group">
                  <label htmlFor="target">Target (Domain or IP)</label>
                  <input id="target" value={target} onChange={e => setTarget(e.target.value)} type="text" placeholder="example.com or 192.168.1.1" disabled={isScanning} className="form-control" />
                </div>

                <button onClick={startScan} disabled={!canStartScan} className="btn-primary">
                  {!isScanning ? <span>🚀 Start Scan</span> : <span>⏳ Scanning...</span>}
                </button>
              </div>

              {currentScan && (
                <div className="scan-status">
                  <h3>Current Scan</h3>
                  <div className="status-card">
                    <div className="status-item">
                      <span className="label">Workflow:</span>
                      <span className="value">{currentScan.workflow}</span>
                    </div>
                    <div className="status-item">
                      <span className="label">Target:</span>
                      <span className="value">{currentScan.target}</span>
                    </div>
                    <div className="status-item">
                      <span className="label">Status:</span>
                      <span className={`value status-badge ${currentScan.status}`}>{currentScan.status}</span>
                    </div>
                  </div>
                </div>
              )}

              {error && <div className="error-message">⚠️ {error}</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SecurityScanner
