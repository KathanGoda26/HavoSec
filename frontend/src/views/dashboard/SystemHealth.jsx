import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useContentStore } from '@/stores/contentStore'

const logPool = [
  { severity: 'INFO', message: 'Polled CPU and memory thresholds: all systems stable' },
  { severity: 'SUCCESS', message: 'WAF successfully blocked packet from unauthorized agent' },
  { severity: 'INFO', message: 'Flushed expired session tokens from local memory caches' },
  { severity: 'WARN', message: 'Sandbox detonation latency spike detected: 105ms' },
  { severity: 'INFO', message: 'Synced threat signatures database with primary cloud repository' },
  { severity: 'INFO', message: 'Running standard health assessment on reverse proxy cluster' },
  { severity: 'SUCCESS', message: 'All backend uvicorn servers responding on port 8000' }
]

const STROKE_DASHARRAY = 2 * Math.PI * 50

function getStrokeDashoffset(percentage) {
  return STROKE_DASHARRAY - (STROKE_DASHARRAY * percentage) / 100
}

function SystemHealth() {
  const contentStore = useContentStore()
  const terminalBodyRef = useRef(null)

  // Live updating usage states
  const [cpuUsage, setCpuUsage] = useState(42)
  const [ramUsage, setRamUsage] = useState(61)
  const [diskUsage, setDiskUsage] = useState(74)
  const [netUsage, setNetUsage] = useState(18)

  // Nodes
  const [nodes, setNodes] = useState([
    { name: 'auth-node-01', role: 'Authentication', status: 'online', ping: 12 },
    { name: 'db-replica-01', role: 'Database Primary', status: 'online', ping: 8 },
    { name: 'api-gateway-01', role: 'Reverse Proxy', status: 'online', ping: 15 },
    { name: 'waf-shield-01', role: 'Firewall / IDS', status: 'online', ping: 4 },
    { name: 'scan-agent-01', role: 'Vulnerability scanner', status: 'online', ping: 22 },
    { name: 'sandbox-01', role: 'Detonation cell', status: 'alert', ping: 105 }
  ])

  // Logs stream
  const [logs, setLogs] = useState([
    { time: '11:50:01', severity: 'INFO', message: 'HavoSec Client Daemon v2.4.1 initialized' },
    { time: '11:50:03', severity: 'SUCCESS', message: 'Established connection to database clusters' },
    { time: '11:50:08', severity: 'INFO', message: 'WAF active on port 443; syncing policy rules...' },
    { time: '11:50:12', severity: 'SUCCESS', message: 'Synchronized 142 firewall rule definitions successfully' },
    { time: '11:50:24', severity: 'INFO', message: 'Initiated background audit scan for core modules' }
  ])

  // Page titles and description
  const pageTitle = useMemo(() => {
    return contentStore.clientDashboard?.systemHealth?.title || 'System Health'
  }, [contentStore.clientDashboard?.systemHealth?.title])

  const pageDescription = useMemo(() => {
    return contentStore.clientDashboard?.systemHealth?.description || 'Monitor system performance and health metrics'
  }, [contentStore.clientDashboard?.systemHealth?.description])

  // Load content and start intervals
  useEffect(() => {
    async function loadContent() {
      try {
        if (contentStore.fetchClientDashboard) {
          await contentStore.fetchClientDashboard()
        }
      } catch (error) {
        console.warn('Could not load client dashboard content, using defaults:', error)
      }
    }
    loadContent()

    // Metrics interval
    const metricsInterval = setInterval(() => {
      setCpuUsage(prev => Math.min(Math.max(prev + Math.floor(Math.random() * 9) - 4, 10), 95))
      setRamUsage(prev => Math.min(Math.max(prev + Math.floor(Math.random() * 3) - 1, 55), 85))
      setNetUsage(prev => Math.min(Math.max(prev + Math.floor(Math.random() * 11) - 5, 5), 90))

      setNodes(prevNodes =>
        prevNodes.map(node => ({
          ...node,
          ping: Math.max(node.ping + Math.floor(Math.random() * 5) - 2, 2)
        }))
      )
    }, 2500)

    // Logs interval
    const logsInterval = setInterval(() => {
      const randomLog = logPool[Math.floor(Math.random() * logPool.length)]
      const now = new Date()
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

      setLogs(prevLogs => {
        const nextLogs = [
          ...prevLogs,
          {
            time: timeStr,
            severity: randomLog.severity,
            message: randomLog.message
          }
        ]
        if (nextLogs.length > 25) {
          nextLogs.shift()
        }
        return nextLogs
      })

      // Scroll to bottom
      setTimeout(() => {
        if (terminalBodyRef.current) {
          terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight
        }
      }, 50)
    }, 3500)

    return () => {
      clearInterval(metricsInterval)
      clearInterval(logsInterval)
    }
  }, [])

  return (
    <div className="system-health-page">
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="system-health-title">{pageTitle}</h1>
          <p className="page-subtitle">{pageDescription}</p>
        </div>
      </div>

      <div className="health-content">
        {/* Circular Progress Metrics Grid */}
        <div className="health-metrics-grid">
          {/* CPU Card */}
          <div className="health-card">
            <div className="gauge-container">
              <svg className="gauge-svg">
                <circle className="gauge-bg" cx="60" cy="60" r="50"></circle>
                <circle
                  className="gauge-fill"
                  cx="60"
                  cy="60"
                  r="50"
                  stroke="#673ee6"
                  strokeDasharray={STROKE_DASHARRAY}
                  strokeDashoffset={getStrokeDashoffset(cpuUsage)}
                ></circle>
              </svg>
              <div className="gauge-value">{cpuUsage}%</div>
            </div>
            <h4>CPU Core Usage</h4>
            <span className="health-status text-green-500">Normal Load</span>
          </div>

          {/* Memory Card */}
          <div className="health-card">
            <div className="gauge-container">
              <svg className="gauge-svg">
                <circle className="gauge-bg" cx="60" cy="60" r="50"></circle>
                <circle
                  className="gauge-fill"
                  cx="60"
                  cy="60"
                  r="50"
                  stroke="#8b5cf6"
                  strokeDasharray={STROKE_DASHARRAY}
                  strokeDashoffset={getStrokeDashoffset(ramUsage)}
                ></circle>
              </svg>
              <div className="gauge-value">{ramUsage}%</div>
            </div>
            <h4>RAM Utilization</h4>
            <span className="health-status text-green-500">Stable</span>
          </div>

          {/* Disk Card */}
          <div className="health-card">
            <div className="gauge-container">
              <svg className="gauge-svg">
                <circle className="gauge-bg" cx="60" cy="60" r="50"></circle>
                <circle
                  className="gauge-fill"
                  cx="60"
                  cy="60"
                  r="50"
                  stroke="#00b090"
                  strokeDasharray={STROKE_DASHARRAY}
                  strokeDashoffset={getStrokeDashoffset(diskUsage)}
                ></circle>
              </svg>
              <div className="gauge-value">{diskUsage}%</div>
            </div>
            <h4>Disk Capacity</h4>
            <span className="health-status text-green-500">240GB Free</span>
          </div>

          {/* Network Card */}
          <div className="health-card">
            <div className="gauge-container">
              <svg className="gauge-svg">
                <circle className="gauge-bg" cx="60" cy="60" r="50"></circle>
                <circle
                  className="gauge-fill"
                  cx="60"
                  cy="60"
                  r="50"
                  stroke="#ec4899"
                  strokeDasharray={STROKE_DASHARRAY}
                  strokeDashoffset={getStrokeDashoffset(netUsage)}
                ></circle>
              </svg>
              <div className="gauge-value">{netUsage}%</div>
            </div>
            <h4>Network Traffic</h4>
            <span className="health-status text-green-500">1.2 Gbps</span>
          </div>
        </div>

        {/* Server Nodes Cluster Section */}
        <div className="cluster-section ui-card">
          <div className="card-header">
            <div className="card-title">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="card-title-icon"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a3 3 0 003 3m13.5-3a3 3 0 003 3m-9.75-3h1.5"
                />
              </svg>
              <span>HavoSec Infrastructure Clusters</span>
            </div>
          </div>

          <div className="cluster-nodes-grid">
            {nodes.map(node => (
              <div key={node.name} className="node-card">
                <div className={`node-status-dot ${node.status}`}></div>
                <div className="node-name">{node.name}</div>
                <div className="node-role">{node.role}</div>
                <div className="node-ping">{node.ping}ms</div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Terminal Logs */}
        <div className="terminal-card ui-card">
          <div className="terminal-header">
            <div className="terminal-controls">
              <div className="control-dot red"></div>
              <div className="control-dot yellow"></div>
              <div className="control-dot green"></div>
            </div>
            <div className="terminal-title">system_orchestrator@havosec-node01:~</div>
          </div>
          <div className="terminal-body" ref={terminalBodyRef}>
            {logs.map((line, idx) => (
              <div key={idx} className="terminal-line">
                <span className="terminal-timestamp">[{line.time}]</span>
                <span className={`terminal-severity ${line.severity}`}>{line.severity}</span>
                <span className="terminal-message">{line.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemHealth
