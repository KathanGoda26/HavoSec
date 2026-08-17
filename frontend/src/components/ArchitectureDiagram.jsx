import React, { useState, useRef, useEffect } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { gsap } from 'gsap'

const colors = {
  'web-service': 0x667eea,
  database: 0x10b981,
  api: 0xf59e0b,
  external: 0xef4444,
  infrastructure: 0x8b5cf6,
}

const defaultNodes = [
  { id: 'web1', name: 'Web Server', type: 'web-service', technology: 'Nginx', version: '1.21.0', port: 80, position: { x: -4, y: 2, z: 0 }, vulnerabilities: 2, vulnerabilityDetails: [{ id: 'vuln1', title: 'Outdated Nginx version', severity: 'medium' }, { id: 'vuln2', title: 'Missing security headers', severity: 'low' }] },
  { id: 'app1', name: 'Application Server', type: 'web-service', technology: 'Node.js', version: '16.14.0', port: 3000, position: { x: 0, y: 2, z: 0 }, vulnerabilities: 1, vulnerabilityDetails: [{ id: 'vuln3', title: 'Prototype pollution', severity: 'high' }] },
  { id: 'db1', name: 'Database', type: 'database', technology: 'MongoDB', version: '5.0.6', port: 27017, position: { x: 4, y: 2, z: 0 }, vulnerabilities: 0, vulnerabilityDetails: [] },
  { id: 'api1', name: 'REST API', type: 'api', technology: 'Express', version: '4.17.1', port: 8000, position: { x: -2, y: -1, z: 2 }, vulnerabilities: 3, vulnerabilityDetails: [{ id: 'vuln4', title: 'SQL Injection', severity: 'critical' }, { id: 'vuln5', title: 'Broken authentication', severity: 'high' }, { id: 'vuln6', title: 'CORS misconfiguration', severity: 'medium' }] },
  { id: 'cache1', name: 'Cache Server', type: 'infrastructure', technology: 'Redis', version: '6.2.0', port: 6379, position: { x: 2, y: -1, z: 2 }, vulnerabilities: 0, vulnerabilityDetails: [] },
  { id: 'ext1', name: 'External API', type: 'external', technology: 'Third-party', position: { x: -4, y: -1, z: -2 }, vulnerabilities: 0, vulnerabilityDetails: [] },
  { id: 'cdn1', name: 'CDN', type: 'infrastructure', technology: 'Cloudflare', position: { x: 0, y: -1, z: -2 }, vulnerabilities: 0, vulnerabilityDetails: [] },
  { id: 'storage1', name: 'Object Storage', type: 'infrastructure', technology: 'AWS S3', position: { x: 4, y: -1, z: -2 }, vulnerabilities: 1, vulnerabilityDetails: [{ id: 'vuln7', title: 'Public bucket exposure', severity: 'critical' }] },
]

const defaultConnections = [
  { from: 'web1', to: 'app1', vulnerable: false },
  { from: 'app1', to: 'db1', vulnerable: false },
  { from: 'app1', to: 'api1', vulnerable: true },
  { from: 'api1', to: 'cache1', vulnerable: false },
  { from: 'api1', to: 'ext1', vulnerable: false },
  { from: 'web1', to: 'cdn1', vulnerable: false },
  { from: 'app1', to: 'storage1', vulnerable: true },
]

function ArchitectureDiagram({ title = '3D Software Architecture Map', subtitle = 'Interactive 3D visualization of infrastructure', architectureData = { nodes: [], connections: [] }, onNodeSelected, onDownload }) {
  const canvasContainerRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [autoRotate, setAutoRotate] = useState(true)
  const [wireframeMode, setWireframeMode] = useState(false)
  const threeRef = useRef({ scene: null, camera: null, renderer: null, controls: null, nodeObjects: [], connectionLines: [], raycaster: null, mouse: null, animationFrameId: null })

  const getNodes = () => architectureData.nodes?.length > 0 ? architectureData.nodes : defaultNodes
  const getConnections = () => architectureData.connections?.length > 0 ? architectureData.connections : defaultConnections

  useEffect(() => {
    const $ = threeRef.current
    const el = canvasContainerRef.current
    if (!el) return

    const initTimeout = setTimeout(() => {
      $.scene = new THREE.Scene()
      $.scene.background = new THREE.Color(0x0a0a0a)
      $.scene.fog = new THREE.Fog(0x0a0a0a, 10, 50)

      $.camera = new THREE.PerspectiveCamera(60, el.clientWidth / el.clientHeight, 0.1, 1000)
      $.camera.position.set(8, 6, 8)
      $.camera.lookAt(0, 0, 0)

      $.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
      $.renderer.setSize(el.clientWidth, el.clientHeight)
      $.renderer.setPixelRatio(window.devicePixelRatio)
      $.renderer.shadowMap.enabled = true
      $.renderer.shadowMap.type = THREE.PCFShadowMap
      el.appendChild($.renderer.domElement)

      $.controls = new OrbitControls($.camera, $.renderer.domElement)
      $.controls.enableDamping = true
      $.controls.dampingFactor = 0.05
      $.controls.autoRotate = true
      $.controls.autoRotateSpeed = 0.5
      $.controls.minDistance = 5
      $.controls.maxDistance = 30

      $.raycaster = new THREE.Raycaster()
      $.mouse = new THREE.Vector2()

      $.scene.add(new THREE.AmbientLight(0xffffff, 0.4))
      const dirLight = new THREE.DirectionalLight(0xffffff, 0.8)
      dirLight.position.set(10, 10, 5)
      dirLight.castShadow = true
      $.scene.add(dirLight)
      const pl1 = new THREE.PointLight(0x667eea, 1, 20)
      pl1.position.set(-5, 5, 5)
      $.scene.add(pl1)
      const pl2 = new THREE.PointLight(0x8b5cf6, 1, 20)
      pl2.position.set(5, 5, -5)
      $.scene.add(pl2)

      const grid = new THREE.GridHelper(20, 20, 0x444444, 0x222222)
      grid.position.y = -3
      $.scene.add(grid)

      // Create nodes
      const nodes = getNodes()
      nodes.forEach(nodeData => {
        const group = new THREE.Group()
        group.userData = nodeData
        const geo = new THREE.BoxGeometry(1, 1, 1)
        const mat = new THREE.MeshStandardMaterial({ color: colors[nodeData.type] || colors['web-service'], metalness: 0.5, roughness: 0.3, emissive: colors[nodeData.type] || colors['web-service'], emissiveIntensity: 0.2 })
        const cube = new THREE.Mesh(geo, mat)
        cube.castShadow = true
        cube.receiveShadow = true
        group.add(cube)

        const wfGeo = new THREE.EdgesGeometry(geo)
        const wfMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.3 })
        group.add(new THREE.LineSegments(wfGeo, wfMat))

        if (nodeData.vulnerabilities > 0) {
          const sGeo = new THREE.SphereGeometry(0.15, 16, 16)
          const sMat = new THREE.MeshStandardMaterial({ color: 0xef4444, emissive: 0xef4444, emissiveIntensity: 0.5 })
          const sphere = new THREE.Mesh(sGeo, sMat)
          sphere.position.set(0.6, 0.6, 0.6)
          group.add(sphere)
          gsap.to(sphere.scale, { x: 1.3, y: 1.3, z: 1.3, duration: 1, repeat: -1, yoyo: true, ease: 'power1.inOut' })
        }

        const pos = nodeData.position || { x: 0, y: 0, z: 0 }
        group.position.set(pos.x, pos.y, pos.z)
        group.scale.set(0, 0, 0)
        gsap.to(group.scale, { x: 1, y: 1, z: 1, duration: 0.8, delay: Math.random() * 0.5, ease: 'back.out(1.7)' })
        gsap.to(group.position, { y: pos.y + 0.2, duration: 2 + Math.random(), repeat: -1, yoyo: true, ease: 'sine.inOut' })
        gsap.to(group.rotation, { y: Math.PI * 2, duration: 10 + Math.random() * 5, repeat: -1, ease: 'none' })

        $.scene.add(group)
        $.nodeObjects.push(group)
      })

      // Create connections
      const connections = getConnections()
      const nodeMap = {}
      nodes.forEach(n => nodeMap[n.id] = n)
      connections.forEach(conn => {
        const fromN = nodeMap[conn.from]
        const toN = nodeMap[conn.to]
        if (!fromN || !toN) return
        const fp = fromN.position || { x: 0, y: 0, z: 0 }
        const tp = toN.position || { x: 0, y: 0, z: 0 }
        const curve = new THREE.QuadraticBezierCurve3(
          new THREE.Vector3(fp.x, fp.y, fp.z),
          new THREE.Vector3((fp.x + tp.x) / 2, Math.max(fp.y, tp.y) + 1, (fp.z + tp.z) / 2),
          new THREE.Vector3(tp.x, tp.y, tp.z)
        )
        const points = curve.getPoints(50)
        const geo = new THREE.BufferGeometry().setFromPoints(points)
        const mat = new THREE.LineBasicMaterial({ color: conn.vulnerable ? 0xef4444 : 0x64748b, transparent: true, opacity: conn.vulnerable ? 0.8 : 0.4 })
        const line = new THREE.Line(geo, mat)
        $.scene.add(line)
        $.connectionLines.push(line)
      })

      // Canvas click handler
      const onClick = (event) => {
        const rect = $.renderer.domElement.getBoundingClientRect()
        $.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
        $.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
        $.raycaster.setFromCamera($.mouse, $.camera)
        const intersects = $.raycaster.intersectObjects($.nodeObjects, true)
        if (intersects.length > 0) {
          const clicked = intersects[0].object.parent
          if (clicked.userData) {
            setSelectedNode(clicked.userData)
            if (onNodeSelected) onNodeSelected(clicked.userData)
            gsap.to(clicked.scale, { x: 1.2, y: 1.2, z: 1.2, duration: 0.3, yoyo: true, repeat: 1 })
          }
        }
      }

      const onMouseMove = (event) => {
        const rect = $.renderer.domElement.getBoundingClientRect()
        $.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
        $.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
        $.raycaster.setFromCamera($.mouse, $.camera)
        const intersects = $.raycaster.intersectObjects($.nodeObjects, true)
        $.nodeObjects.forEach(obj => { if (obj.children[0]?.material) obj.children[0].material.emissiveIntensity = 0.2 })
        if (intersects.length > 0) {
          const hovered = intersects[0].object.parent
          if (hovered.children[0]?.material) hovered.children[0].material.emissiveIntensity = 0.5
          $.renderer.domElement.style.cursor = 'pointer'
        } else {
          $.renderer.domElement.style.cursor = 'default'
        }
      }

      const onResize = () => {
        if (!el) return
        $.camera.aspect = el.clientWidth / el.clientHeight
        $.camera.updateProjectionMatrix()
        $.renderer.setSize(el.clientWidth, el.clientHeight)
      }

      $.renderer.domElement.addEventListener('click', onClick)
      $.renderer.domElement.addEventListener('mousemove', onMouseMove)
      window.addEventListener('resize', onResize)

      function animate() {
        $.animationFrameId = requestAnimationFrame(animate)
        $.controls.update()
        $.renderer.render($.scene, $.camera)
      }
      animate()
      setLoading(false)

      // Store cleanup refs
      $.cleanup = { onClick, onMouseMove, onResize }
    }, 100)

    return () => {
      clearTimeout(initTimeout)
      if ($.animationFrameId) cancelAnimationFrame($.animationFrameId)
      if ($.cleanup) {
        window.removeEventListener('resize', $.cleanup.onResize)
        if ($.renderer) {
          $.renderer.domElement.removeEventListener('click', $.cleanup.onClick)
          $.renderer.domElement.removeEventListener('mousemove', $.cleanup.onMouseMove)
          $.renderer.dispose()
        }
      }
      if ($.scene) {
        $.scene.traverse(obj => {
          if (obj.geometry) obj.geometry.dispose()
          if (obj.material) {
            (Array.isArray(obj.material) ? obj.material : [obj.material]).forEach(m => m?.dispose())
          }
        })
      }
    }
  }, [])

  const resetCamera = () => {
    const $ = threeRef.current
    gsap.to($.camera.position, { x: 8, y: 6, z: 8, duration: 1, ease: 'power2.inOut', onUpdate: () => $.camera.lookAt(0, 0, 0) })
  }

  const toggleAutoRotate = () => {
    const $ = threeRef.current
    const newVal = !autoRotate
    setAutoRotate(newVal)
    if ($.controls) $.controls.autoRotate = newVal
  }

  const toggleWireframe = () => {
    const $ = threeRef.current
    const newVal = !wireframeMode
    setWireframeMode(newVal)
    $.nodeObjects.forEach(obj => { if (obj.children[0]?.material) obj.children[0].material.wireframe = newVal })
  }

  const downloadScreenshot = () => {
    const $ = threeRef.current
    $.renderer.render($.scene, $.camera)
    const dataURL = $.renderer.domElement.toDataURL('image/png')
    const link = document.createElement('a')
    link.href = dataURL
    link.download = '3d-architecture-diagram.png'
    link.click()
    if (onDownload) onDownload()
  }

  const toggleFullscreen = () => {
    const el = canvasContainerRef.current
    const newVal = !isFullscreen
    setIsFullscreen(newVal)
    if (newVal) el?.requestFullscreen?.()
    else document.exitFullscreen?.()
  }

  return (
    <div className="architecture-3d-container">
      <div className="diagram-header">
        <div>
          <h3>{title}</h3>
          <p className="subtitle">{subtitle}</p>
        </div>
        <div className="diagram-controls">
          <button onClick={resetCamera} className="control-btn" title="Reset View">🔄</button>
          <button onClick={toggleAutoRotate} className="control-btn" title="Auto Rotate">{autoRotate ? '⏸️' : '▶️'}</button>
          <button onClick={toggleWireframe} className="control-btn" title="Wireframe">🔲</button>
          <button onClick={downloadScreenshot} className="control-btn" title="Screenshot">📷</button>
          <button onClick={toggleFullscreen} className="control-btn" title="Fullscreen">⛶</button>
        </div>
      </div>

      <div className="diagram-legend">
        <div className="legend-item"><div className="legend-color" style={{ background: '#667eea' }}></div><span>Web Services</span></div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#10b981' }}></div><span>Databases</span></div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#f59e0b' }}></div><span>APIs</span></div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#ef4444' }}></div><span>External</span></div>
        <div className="legend-item"><div className="legend-color" style={{ background: '#8b5cf6' }}></div><span>Infrastructure</span></div>
      </div>

      <div ref={canvasContainerRef} className={`canvas-container ${isFullscreen ? 'fullscreen' : ''}`}></div>

      {selectedNode && (
        <div className="node-details-panel">
          <div className="panel-header">
            <h3>{selectedNode.name}</h3>
            <button onClick={() => setSelectedNode(null)} className="close-btn">×</button>
          </div>
          <div className="panel-content">
            <div className="detail-row"><span className="label">Type:</span><span className="value">{selectedNode.type}</span></div>
            {selectedNode.technology && <div className="detail-row"><span className="label">Technology:</span><span className="value">{selectedNode.technology}</span></div>}
            {selectedNode.version && <div className="detail-row"><span className="label">Version:</span><span className="value">{selectedNode.version}</span></div>}
            {selectedNode.port && <div className="detail-row"><span className="label">Port:</span><span className="value">{selectedNode.port}</span></div>}
            {selectedNode.vulnerabilities > 0 && (
              <div className="vulnerabilities-section">
                <h4>Vulnerabilities ({selectedNode.vulnerabilities})</h4>
                <div className="vulnerability-list">
                  {selectedNode.vulnerabilityDetails?.map(vuln => (
                    <div key={vuln.id} className="vulnerability-item">
                      <span className={`severity-badge ${vuln.severity}`}>{vuln.severity}</span>
                      <span>{vuln.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Initializing 3D Architecture...</p>
        </div>
      )}
    </div>
  )
}

export default ArchitectureDiagram
