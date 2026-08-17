import React, { useState, useEffect, useMemo } from 'react'
import { useSecurityStore } from '@/stores/securityStore'
import ArchitectureDiagram from '@/components/ArchitectureDiagram'
import {
  ArrowPathIcon,
  MagnifyingGlassIcon,
  ServerIcon,
  CircleStackIcon,
  CloudIcon,
  CpuChipIcon,
  GlobeAltIcon,
  ChevronRightIcon,
  ArrowLongRightIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getComponentIcon(type) {
  const icons = {
    'web-service': ServerIcon,
    database: CircleStackIcon,
    api: CpuChipIcon,
    external: CloudIcon,
    infrastructure: GlobeAltIcon,
  }
  return icons[type] || ServerIcon
}

function ArchitectureMap() {
  const securityStore = useSecurityStore()

  // State
  const [loading, setLoading] = useState(false)
  const [selectedScan, setSelectedScan] = useState(null)
  const [showScanSelector, setShowScanSelector] = useState(false)
  const [selectedComponent, setSelectedComponent] = useState(null)
  const [availableScans, setAvailableScans] = useState([])
  const [mockArchitectureData, setMockArchitectureData] = useState({
    nodes: [],
    connections: [],
  })

  // Computed / Memos
  const architectureTitle = useMemo(() => {
    return selectedScan
      ? `Architecture Map: ${selectedScan.target}`
      : 'Software Architecture Map'
  }, [selectedScan])

  const architectureSubtitle = useMemo(() => {
    return selectedScan
      ? `Discovered on ${formatDate(selectedScan.createdAt)}`
      : 'Interactive visualization of discovered infrastructure'
  }, [selectedScan])

  const componentsList = useMemo(() => {
    return mockArchitectureData.nodes || []
  }, [mockArchitectureData.nodes])

  const connectionsList = useMemo(() => {
    const connections = mockArchitectureData.connections || []
    const nodeMap = {}

    componentsList.forEach(node => {
      nodeMap[node.id] = node
    })

    return connections.map(conn => {
      const fromNode = nodeMap[conn.from]
      const toNode = nodeMap[conn.to]

      return {
        ...conn,
        fromName: fromNode?.name || conn.from,
        toName: toNode?.name || conn.to,
        fromType: fromNode?.type || 'web-service',
        toType: toNode?.type || 'web-service',
      }
    })
  }, [mockArchitectureData.connections, componentsList])

  const totalComponents = useMemo(() => componentsList.length, [componentsList])
  const totalConnections = useMemo(() => connectionsList.length, [connectionsList])

  const vulnerableComponents = useMemo(() => {
    return componentsList.filter(c => c.vulnerabilities > 0).length
  }, [componentsList])

  // Load available scans on mount
  useEffect(() => {
    async function loadScans() {
      setLoading(true)
      try {
        setAvailableScans([
          {
            executionId: 'exec_001',
            target: 'example.com',
            status: 'completed',
            createdAt: new Date(Date.now() - 86400000), // 1 day ago
            agentsExecuted: ['recon', 'scanner', 'analyzer'],
          },
          {
            executionId: 'exec_002',
            target: 'api.example.com',
            status: 'completed',
            createdAt: new Date(Date.now() - 172800000), // 2 days ago
            agentsExecuted: ['recon', 'scanner'],
          },
          {
            executionId: 'exec_003',
            target: 'app.example.com',
            status: 'completed',
            createdAt: new Date(Date.now() - 259200000), // 3 days ago
            agentsExecuted: ['recon', 'scanner', 'analyzer', 'validator'],
          },
        ])
      } catch (error) {
        console.error('Failed to load scans:', error)
      } finally {
        setLoading(false)
      }
    }
    loadScans()
  }, [])

  // Methods
  const refreshData = async () => {
    if (!selectedScan) return

    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error('Failed to refresh architecture data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadArchitectureData = async (executionId) => {
    setLoading(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 800))
      setMockArchitectureData({
        nodes: [
          {
            id: 'web1',
            name: 'Web Server',
            type: 'web-service',
            technology: 'Nginx',
            version: '1.21.0',
            port: 80,
            x: 100,
            y: 50,
            vulnerabilities: 2,
            description: 'Main web server handling HTTP requests',
            vulnerabilityDetails: [
              {
                id: 'vuln1',
                title: 'Outdated Nginx version',
                severity: 'medium',
                description: 'Running an outdated version of Nginx',
              },
              {
                id: 'vuln2',
                title: 'Missing security headers',
                severity: 'low',
                description: 'CSP and HSTS headers not configured',
              },
            ],
          },
          {
            id: 'app1',
            name: 'Application Server',
            type: 'web-service',
            technology: 'Node.js',
            version: '16.14.0',
            port: 3000,
            x: 350,
            y: 50,
            vulnerabilities: 1,
            description: 'Main application server',
            vulnerabilityDetails: [
              {
                id: 'vuln3',
                title: 'Prototype pollution',
                severity: 'high',
                description: 'Vulnerable to prototype pollution attacks',
              },
            ],
          },
          {
            id: 'db1',
            name: 'Database',
            type: 'database',
            technology: 'MongoDB',
            version: '5.0.6',
            port: 27017,
            x: 600,
            y: 50,
            vulnerabilities: 0,
            description: 'Primary database for application data',
            vulnerabilityDetails: [],
          },
          {
            id: 'api1',
            name: 'REST API',
            type: 'api',
            technology: 'Express',
            version: '4.17.1',
            port: 8000,
            x: 225,
            y: 250,
            vulnerabilities: 3,
            description: 'RESTful API endpoints',
            vulnerabilityDetails: [
              {
                id: 'vuln4',
                title: 'SQL Injection',
                severity: 'critical',
                description: 'Vulnerable to SQL injection attacks',
              },
              {
                id: 'vuln5',
                title: 'Broken authentication',
                severity: 'high',
                description: 'Weak authentication mechanism',
              },
              {
                id: 'vuln6',
                title: 'CORS misconfiguration',
                severity: 'medium',
                description: 'CORS headers improperly configured',
              },
            ],
          },
          {
            id: 'cache1',
            name: 'Cache Server',
            type: 'infrastructure',
            technology: 'Redis',
            version: '6.2.0',
            port: 6379,
            x: 475,
            y: 250,
            vulnerabilities: 0,
            description: 'In-memory cache for performance',
            vulnerabilityDetails: [],
          },
          {
            id: 'ext1',
            name: 'External API',
            type: 'external',
            technology: 'Third-party',
            x: 100,
            y: 450,
            vulnerabilities: 0,
            description: 'External third-party service',
            vulnerabilityDetails: [],
          },
          {
            id: 'cdn1',
            name: 'CDN',
            type: 'infrastructure',
            technology: 'Cloudflare',
            x: 350,
            y: 450,
            vulnerabilities: 0,
            description: 'Content delivery network',
            vulnerabilityDetails: [],
          },
          {
            id: 'storage1',
            name: 'Object Storage',
            type: 'infrastructure',
            technology: 'AWS S3',
            x: 600,
            y: 450,
            vulnerabilities: 1,
            description: 'Cloud storage for static assets',
            vulnerabilityDetails: [
              {
                id: 'vuln7',
                title: 'Public bucket exposure',
                severity: 'critical',
                description: 'S3 bucket is publicly accessible',
              },
            ],
          },
        ],
        connections: [
          {
            from: 'web1',
            to: 'app1',
            protocol: 'HTTP',
            port: 3000,
            vulnerable: false,
          },
          {
            from: 'app1',
            to: 'db1',
            protocol: 'MongoDB',
            port: 27017,
            vulnerable: false,
          },
          {
            from: 'app1',
            to: 'api1',
            protocol: 'REST',
            port: 8000,
            vulnerable: true,
          },
          {
            from: 'api1',
            to: 'cache1',
            protocol: 'Redis',
            port: 6379,
            vulnerable: false,
          },
          { from: 'api1', to: 'ext1', protocol: 'HTTPS', vulnerable: false },
          { from: 'web1', to: 'cdn1', protocol: 'HTTP', vulnerable: false },
          { from: 'app1', to: 'storage1', protocol: 'S3', vulnerable: true },
        ],
      })
    } catch (error) {
      console.error('Failed to load architecture data:', error)
    } finally {
      setLoading(false)
    }
  }

  const selectScan = (scan) => {
    setSelectedScan(scan)
    setShowScanSelector(false)
    loadArchitectureData(scan.executionId)
  }

  const handleNodeSelected = (node) => {
    console.log('Node selected:', node)
  }

  const handleDownload = () => {
    console.log('Download requested')
  }

  return (
    <div className="architecture-map-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Architecture Maps</h1>
          <p className="subtitle">
            Visualize discovered infrastructure and software architecture
          </p>
        </div>
        <div className="header-actions">
          <button onClick={refreshData} className="btn-secondary" disabled={loading}>
            <ArrowPathIcon className={`icon-xs ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button onClick={() => setShowScanSelector(true)} className="btn-primary">
            <MagnifyingGlassIcon className="icon-xs" />
            Select Scan
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && !selectedScan ? (
        <div className="loading-container">
          <div className="loading-spinner-large"></div>
          <p>Loading architecture data...</p>
        </div>
      ) : !selectedScan ? (
        /* Empty State */
        <div className="empty-state">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="empty-icon"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
            />
          </svg>
          <h2>No Scan Selected</h2>
          <p>Select a scan to view the discovered architecture map</p>
          <button onClick={() => setShowScanSelector(true)} className="btn-primary">
            Select a Scan
          </button>
        </div>
      ) : (
        /* Main Content */
        <div className="architecture-content">
          {/* Scan Info Card */}
          <div className="scan-info-card">
            <div className="scan-info-content">
              <div>
                <h3>{selectedScan.target}</h3>
                <p className="scan-meta">
                  Scanned on {formatDate(selectedScan.createdAt)} •{' '}
                  {selectedScan.agentsExecuted?.length || 0} agents •{' '}
                  {totalComponents} components discovered
                </p>
              </div>
              <div className="scan-stats">
                <div className="stat-item">
                  <span className="stat-value">{totalComponents}</span>
                  <span className="stat-label">Components</span>
                </div>
                <div className="stat-item">
                  <span className="stat-value">{totalConnections}</span>
                  <span className="stat-label">Connections</span>
                </div>
                <div className="stat-item">
                  <span className={`stat-value ${vulnerableComponents > 0 ? 'text-red' : 'text-green'}`}>
                    {vulnerableComponents}
                  </span>
                  <span className="stat-label">Vulnerable</span>
                </div>
              </div>
            </div>
          </div>

          {/* Architecture Diagram */}
          <ArchitectureDiagram
            title={architectureTitle}
            subtitle={architectureSubtitle}
            architectureData={mockArchitectureData}
            onNodeSelected={handleNodeSelected}
            onDownload={handleDownload}
          />

          {/* Components List */}
          <div className="components-section">
            <h2>Discovered Components</h2>
            <div className="components-grid">
              {componentsList.map(component => {
                const ComponentIcon = getComponentIcon(component.type)
                return (
                  <div
                    key={component.id}
                    className={`component-card ${component.vulnerabilities > 0 ? 'has-vulnerabilities' : ''}`}
                    onClick={() => setSelectedComponent(component)}
                  >
                    <div className="component-header">
                      <div className={`component-icon icon-${component.type}`}>
                        <ComponentIcon className="icon-md" />
                      </div>
                      <div className="component-info">
                        <h4>{component.name}</h4>
                        <p>{component.technology} {component.version}</p>
                      </div>
                      {component.vulnerabilities > 0 && (
                        <div className="vuln-badge">{component.vulnerabilities}</div>
                      )}
                    </div>
                    <div className="component-details">
                      <div className="detail-item">
                        <span className="label">Type:</span>
                        <span className="value">{component.type}</span>
                      </div>
                      {component.port && (
                        <div className="detail-item">
                          <span className="label">Port:</span>
                          <span className="value">{component.port}</span>
                        </div>
                      )}
                      {component.description && (
                        <div className="detail-item full-width">
                          <span className="label">Description:</span>
                          <span className="value">{component.description}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Network Connections */}
          <div className="connections-section">
            <h2>Network Connections</h2>
            <div className="connections-list">
              {connectionsList.map((connection, index) => {
                const FromIcon = getComponentIcon(connection.fromType)
                const ToIcon = getComponentIcon(connection.toType)
                return (
                  <div
                    key={`conn-${index}`}
                    className={`connection-item ${connection.vulnerable ? 'vulnerable' : ''}`}
                  >
                    <div className="connection-flow">
                      <div className="connection-node from">
                        <FromIcon className="icon-xs" />
                        <span>{connection.fromName}</span>
                      </div>
                      <div className="connection-arrow">
                        <ArrowLongRightIcon className="icon-md" />
                        <div className="connection-protocol">
                          {connection.protocol || 'HTTP'}
                          {connection.port ? `:${connection.port}` : ''}
                        </div>
                      </div>
                      <div className="connection-node to">
                        <span>{connection.toName}</span>
                        <ToIcon className="icon-xs" />
                      </div>
                    </div>
                    {connection.vulnerable && (
                      <div className="connection-warning">
                        <ExclamationTriangleIcon className="icon-xs" />
                        <span>Vulnerable connection detected</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Scan Selector Modal */}
      {showScanSelector && (
        <div className="modal-overlay" onClick={() => setShowScanSelector(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Select a Scan</h3>
              <button onClick={() => setShowScanSelector(false)} className="close-btn">×</button>
            </div>
            <div className="modal-body">
              <div className="scans-list">
                {availableScans.map(scan => (
                  <div
                    key={scan.executionId}
                    className={`scan-item ${selectedScan?.executionId === scan.executionId ? 'active' : ''}`}
                    onClick={() => selectScan(scan)}
                  >
                    <div className="scan-item-content">
                      <h4>{scan.target}</h4>
                      <p className="scan-date">{formatDate(scan.createdAt)}</p>
                      <div className="scan-badges">
                        <span className="badge">{scan.agentsExecuted?.length || 0} agents</span>
                        <span className={`badge status ${scan.status}`}>{scan.status}</span>
                      </div>
                    </div>
                    <div className="scan-arrow">
                      <ChevronRightIcon className="icon-sm" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Component Details Modal */}
      {selectedComponent && (
        <div className="modal-overlay" onClick={() => setSelectedComponent(null)}>
          <div className="modal-content large" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedComponent.name}</h3>
              <button onClick={() => setSelectedComponent(null)} className="close-btn">×</button>
            </div>
            <div className="modal-body">
              <div className="component-full-details">
                <div className="details-grid">
                  <div className="detail-row">
                    <span className="label">Type:</span>
                    <span className="value">{selectedComponent.type}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Technology:</span>
                    <span className="value">{selectedComponent.technology}</span>
                  </div>
                  {selectedComponent.version && (
                    <div className="detail-row">
                      <span className="label">Version:</span>
                      <span className="value">{selectedComponent.version}</span>
                    </div>
                  )}
                  {selectedComponent.port && (
                    <div className="detail-row">
                      <span className="label">Port:</span>
                      <span className="value">{selectedComponent.port}</span>
                    </div>
                  )}
                </div>

                {selectedComponent.description && (
                  <div className="description-section">
                    <h4>Description</h4>
                    <p>{selectedComponent.description}</p>
                  </div>
                )}

                {selectedComponent.vulnerabilities > 0 && (
                  <div className="vulnerabilities-section">
                    <h4>
                      Vulnerabilities ({selectedComponent.vulnerabilityDetails?.length || 0})
                    </h4>
                    <div className="vulnerability-list">
                      {selectedComponent.vulnerabilityDetails?.map(vuln => (
                        <div key={vuln.id} className="vulnerability-item">
                          <span className={`severity-badge ${vuln.severity}`}>{vuln.severity}</span>
                          <div className="vuln-info">
                            <p className="vuln-title">{vuln.title}</p>
                            {vuln.description && <p className="vuln-desc">{vuln.description}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ArchitectureMap
