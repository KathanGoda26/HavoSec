import React, { useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import * as THREE from 'three'
import { gsap } from 'gsap'

const examples = [
  { id: '1', title: 'SQL Injection Detection & Prevention', description: 'AI-powered detection of SQL injection attempts with real-time query analysis and automatic blocking mechanisms.', color: '#673ee6' },
  { id: '2', title: 'Cross-Site Scripting (XSS) Protection', description: 'Multi-layered XSS detection using content analysis and browser-level protection mechanisms to prevent script injection.', color: '#00b090' },
  { id: '3', title: 'DDoS Attack Mitigation', description: 'Distributed denial-of-service protection with intelligent traffic analysis, rate limiting, and load balancing.', color: '#8b5cf6' },
  { id: '4', title: 'Zero-Day Exploit Detection', description: 'Machine learning-based detection of previously unknown vulnerabilities and attack patterns before patches are available.', color: '#34d399' },
  { id: '5', title: 'Ransomware Defense System', description: 'Multi-stage ransomware detection and prevention with automated backup protection and behavioral analysis.', color: '#f59e0b' },
  { id: '6', title: 'API Authentication Bypass Prevention', description: 'Advanced authentication and authorization monitoring for API endpoints with token validation and rate limiting.', color: '#ef4444' },
  { id: '7', title: 'Privilege Escalation Detection', description: 'Monitor and prevent unauthorized privilege elevation attempts across systems with real-time permission tracking.', color: '#10b981' },
  { id: '8', title: 'Phishing Detection & Response', description: 'AI-powered email and website analysis to identify and block phishing attempts including spear-phishing campaigns.', color: '#6366f1' },
  { id: '9', title: 'Man-in-the-Middle Attack Prevention', description: 'Secure communication monitoring and encryption verification to prevent MITM attacks and traffic interception.', color: '#ec4899' },
  { id: '10', title: 'Insider Threat Detection', description: 'Behavioral analytics to identify malicious or negligent insider activities before data breaches occur.', color: '#14b8a6' },
  { id: '11', title: 'Cryptojacking Prevention', description: 'Detect and block unauthorized cryptocurrency mining activities on systems and browsers through resource monitoring.', color: '#f97316' },
  { id: '12', title: 'Remote Code Execution (RCE) Defense', description: 'Prevent unauthorized code execution through input validation, sandboxing, and command injection detection.', color: '#8b5cf6' },
  { id: '13', title: 'Data Exfiltration Prevention', description: 'Monitor and block unauthorized data transfers and sensitive information leaks across all communication channels.', color: '#06b6d4' },
  { id: '14', title: 'Brute Force Attack Protection', description: 'Intelligent rate limiting and lockout mechanisms to prevent credential attacks with adaptive CAPTCHA challenges.', color: '#a855f7' },
  { id: '15', title: 'XML External Entity (XXE) Protection', description: 'Secure XML parsing to prevent XXE injection attacks and data exposure through entity validation.', color: '#f59e0b' },
  { id: '16', title: 'Server-Side Request Forgery (SSRF) Prevention', description: 'Validate and restrict server-side requests to prevent SSRF exploitation and internal resource access.', color: '#ef4444' },
  { id: '17', title: 'Session Hijacking Prevention', description: 'Secure session management with continuous validation and anomaly detection to prevent session theft.', color: '#10b981' },
  { id: '18', title: 'DNS Tunneling Detection', description: 'Identify and block data exfiltration and C&C communications via DNS protocol through query pattern analysis.', color: '#3b82f6' },
  { id: '19', title: 'Business Logic Flaw Detection', description: 'Identify and prevent exploitation of application business logic vulnerabilities through workflow monitoring.', color: '#8b5cf6' },
  { id: '20', title: 'Container Escape Prevention', description: 'Monitor and prevent container breakout attempts in containerized environments with syscall monitoring.', color: '#06b6d4' },
]

function getSeverity(id) {
  const criticalIds = ['1', '3', '4', '5', '12', '20']
  const highIds = ['2', '6', '7', '8', '9', '10', '13', '16', '17', '19']
  if (criticalIds.includes(id)) return 'Critical'
  if (highIds.includes(id)) return 'High'
  return Math.random() > 0.5 ? 'Medium' : 'Low'
}

function getThreatLevel(id) {
  const levels = { '1': 95, '2': 88, '3': 92, '4': 97, '5': 94, '6': 85, '7': 89, '8': 86, '9': 83, '10': 78, '11': 72, '12': 91, '13': 87, '14': 75, '15': 82, '16': 84, '17': 88, '18': 70, '19': 80, '20': 96 }
  return levels[id] || 80
}

function wrapText(ctx, text, maxWidth) {
  const words = text.split(' ')
  const lines = []
  let currentLine = ''
  words.forEach(word => {
    const testLine = currentLine ? `${currentLine} ${word}` : word
    if (ctx.measureText(testLine).width > maxWidth && currentLine) {
      lines.push(currentLine)
      currentLine = word
    } else {
      currentLine = testLine
    }
  })
  if (currentLine) lines.push(currentLine)
  return lines
}

function drawHexagon(ctx, x, y, size) {
  ctx.beginPath()
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i
    const hx = x + size * Math.cos(angle)
    const hy = y + size * Math.sin(angle)
    if (i === 0) ctx.moveTo(hx, hy)
    else ctx.lineTo(hx, hy)
  }
  ctx.closePath()
  ctx.stroke()
}

function drawShieldIcon(ctx, x, y, size, color) {
  ctx.save()
  ctx.fillStyle = color + '40'
  ctx.strokeStyle = color
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(x, y)
  ctx.lineTo(x - size/2, y + size/4)
  ctx.lineTo(x - size/2, y + size/1.5)
  ctx.quadraticCurveTo(x - size/2, y + size, x, y + size * 1.2)
  ctx.quadraticCurveTo(x + size/2, y + size, x + size/2, y + size/1.5)
  ctx.lineTo(x + size/2, y + size/4)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(x - size/4, y + size/2)
  ctx.lineTo(x - size/8, y + size/1.5)
  ctx.lineTo(x + size/3, y + size/3)
  ctx.stroke()
  ctx.restore()
}

function drawSeverityBadge(ctx, x, y, severity) {
  const cs = { Critical: '#ef4444', High: '#f97316', Medium: '#eab308', Low: '#10b981' }
  ctx.save()
  ctx.fillStyle = cs[severity] || '#6b7280'
  ctx.font = 'bold 28px Arial, sans-serif'
  const text = severity.toUpperCase()
  const m = ctx.measureText(text)
  const p = 20
  ctx.globalAlpha = 0.9
  ctx.fillRect(x - p, y - 30, m.width + p * 2, 50)
  ctx.globalAlpha = 1
  ctx.fillStyle = '#ffffff'
  ctx.fillText(text, x, y)
  ctx.restore()
}

function drawStatBox(ctx, x, y, label, value, color) {
  ctx.save()
  ctx.fillStyle = 'rgba(0,0,0,0.4)'
  ctx.fillRect(x, y, 280, 100)
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.strokeRect(x, y, 280, 100)
  ctx.fillStyle = '#a0a0a0'
  ctx.font = '22px Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(label, x + 20, y + 35)
  ctx.fillStyle = color
  ctx.font = 'bold 32px monospace'
  ctx.fillText(value, x + 20, y + 75)
  ctx.restore()
}

function drawThreatLevel(ctx, x, y, width, level, color) {
  ctx.save()
  ctx.fillStyle = '#ffffff'
  ctx.font = '26px Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('Threat Level Detected:', x, y - 10)
  ctx.fillStyle = 'rgba(255,255,255,0.1)'
  ctx.fillRect(x, y + 10, width, 30)
  const pw = (width * level) / 100
  const bg = ctx.createLinearGradient(x, 0, x + pw, 0)
  bg.addColorStop(0, color)
  bg.addColorStop(1, '#00b090')
  ctx.fillStyle = bg
  ctx.fillRect(x, y + 10, pw, 30)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 24px Arial, sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText(level + '%', x + width + 80, y + 35)
  ctx.restore()
}

function createCardTexture(example) {
  const c = document.createElement('canvas')
  c.width = 1600
  c.height = 1000
  const ctx = c.getContext('2d')
  ctx.fillStyle = 'rgba(0,0,0,0.75)'
  ctx.fillRect(0, 0, c.width, c.height)
  const gradient = ctx.createLinearGradient(0, 0, 0, c.height)
  gradient.addColorStop(0, example.color + '30')
  gradient.addColorStop(0.6, 'rgba(15,15,25,0.4)')
  gradient.addColorStop(1, 'rgba(5,5,10,0.7)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, c.width, c.height)
  ctx.strokeStyle = example.color
  ctx.lineWidth = 8
  ctx.strokeRect(20, 20, c.width - 40, c.height - 40)
  ctx.strokeStyle = 'rgba(255,255,255,0.03)'
  ctx.lineWidth = 1
  for (let y = 0; y < c.height; y += 80) { for (let x = 0; x < c.width; x += 140) { drawHexagon(ctx, x, y, 35) } }
  drawShieldIcon(ctx, 80, 80, 60, example.color)
  drawSeverityBadge(ctx, c.width - 250, 70, getSeverity(example.id))
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 64px Arial, sans-serif'
  ctx.textAlign = 'left'
  ctx.shadowColor = 'rgba(0,0,0,0.9)'
  ctx.shadowBlur = 20
  ctx.shadowOffsetX = 4
  ctx.shadowOffsetY = 4
  const titleLines = wrapText(ctx, example.title, c.width - 180)
  let currentY = 200
  titleLines.forEach((line, i) => ctx.fillText(line, 80, currentY + i * 80))
  ctx.shadowColor = 'transparent'
  ctx.shadowBlur = 0
  ctx.shadowOffsetX = 0
  ctx.shadowOffsetY = 0
  ctx.fillStyle = '#e0e0e0'
  ctx.font = '38px Arial, sans-serif'
  ctx.shadowColor = 'rgba(0,0,0,0.7)'
  ctx.shadowBlur = 10
  ctx.shadowOffsetX = 2
  ctx.shadowOffsetY = 2
  const descLines = wrapText(ctx, example.description, c.width - 180)
  const startY = currentY + titleLines.length * 80 + 50
  descLines.slice(0, 4).forEach((line, i) => ctx.fillText(line, 80, startY + i * 55))
  ctx.shadowColor = 'transparent'
  ctx.shadowBlur = 0
  const statsY = startY + 250
  drawStatBox(ctx, 80, statsY, 'Detection Time', '< 50ms', example.color)
  drawStatBox(ctx, 420, statsY, 'Blocked', '250K+', '#00b090')
  drawStatBox(ctx, 760, statsY, 'Success Rate', '99.5%', '#10b981')
  drawThreatLevel(ctx, 80, statsY + 140, c.width - 160, getThreatLevel(example.id), example.color)
  ctx.fillStyle = '#00b090'
  ctx.font = 'bold 36px Arial, sans-serif'
  ctx.textAlign = 'center'
  ctx.shadowColor = 'rgba(0,0,0,0.8)'
  ctx.shadowBlur = 12
  ctx.fillText('Click to learn more →', c.width / 2, c.height - 70)
  const texture = new THREE.CanvasTexture(c)
  texture.minFilter = THREE.LinearFilter
  texture.magFilter = THREE.LinearFilter
  return texture
}

function ExamplesGallery3D() {
  const navigate = useNavigate()
  const galleryContainerRef = useRef(null)
  const canvasRef = useRef(null)
  const threeRef = useRef({ scene: null, camera: null, renderer: null, raycaster: null, mouse: null, cardMeshes: [], animationId: null, hoveredCardMesh: null })

  useEffect(() => {
    const el = galleryContainerRef.current
    const canvasEl = canvasRef.current
    if (!el || !canvasEl) return

    const $ = threeRef.current
    const initTimeout = setTimeout(() => {
      $.scene = new THREE.Scene()
      $.camera = new THREE.PerspectiveCamera(50, el.offsetWidth / el.offsetHeight, 0.1, 1000)
      $.camera.position.set(0, 1, 12)
      $.camera.lookAt(0, 0, 0)

      $.renderer = new THREE.WebGLRenderer({ canvas: canvasEl, antialias: true, alpha: true })
      $.renderer.setSize(el.offsetWidth, el.offsetHeight)
      $.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
      $.renderer.shadowMap.enabled = true
      $.renderer.shadowMap.type = THREE.PCFShadowMap

      $.scene.add(new THREE.AmbientLight(0xffffff, 0.8))
      const dl1 = new THREE.DirectionalLight(0xffffff, 0.6)
      dl1.position.set(10, 10, 10)
      dl1.castShadow = true
      $.scene.add(dl1)
      const dl2 = new THREE.DirectionalLight(0xffffff, 0.4)
      dl2.position.set(-10, -10, 10)
      $.scene.add(dl2)

      $.raycaster = new THREE.Raycaster()
      $.mouse = new THREE.Vector2()

      // Create cards
      const cardWidth = 8, cardHeight = 5
      const totalCards = examples.length
      examples.forEach((example, index) => {
        const geo = new THREE.PlaneGeometry(cardWidth, cardHeight)
        const tex = createCardTexture(example)
        const mat = new THREE.MeshLambertMaterial({ map: tex, transparent: true, opacity: 0.95, side: THREE.DoubleSide })
        const mesh = new THREE.Mesh(geo, mat)
        const centerOffset = (index - totalCards / 2) * 0.3
        const x = centerOffset
        const y = -index * 0.15
        const z = -index * 0.8 - 2
        const rotY = -0.25 + index * 0.01
        const rotX = -0.2 - index * 0.02
        mesh.position.set(x, y, z)
        mesh.rotation.set(rotX, rotY, 0)
        mesh.userData = { index, example, originalPosition: { x, y, z }, originalRotation: { x: rotX, y: rotY, z: 0 }, isHovered: false }
        mesh.castShadow = true
        mesh.receiveShadow = true
        $.scene.add(mesh)
        $.cardMeshes.push(mesh)
      })

      // Event handlers
      const onMouseMove = (event) => {
        const rect = el.getBoundingClientRect()
        $.mouse.x = ((event.clientX - rect.left) / el.offsetWidth) * 2 - 1
        $.mouse.y = -((event.clientY - rect.top) / el.offsetHeight) * 2 + 1
        $.raycaster.setFromCamera($.mouse, $.camera)
        const intersects = $.raycaster.intersectObjects($.cardMeshes)
        if ($.hoveredCardMesh?.userData.isHovered) {
          $.hoveredCardMesh.userData.isHovered = false
          const m = $.hoveredCardMesh
          gsap.to(m.position, { z: m.userData.originalPosition.z, duration: 0.4, ease: 'power2.out' })
          gsap.to(m.scale, { x: 1, y: 1, z: 1, duration: 0.4, ease: 'power2.out' })
          gsap.to(m.rotation, { x: m.userData.originalRotation.x, duration: 0.4, ease: 'power2.out' })
          $.hoveredCardMesh = null
        }
        if (intersects.length > 0) {
          const card = intersects[0].object
          if (!card.userData.isHovered) {
            card.userData.isHovered = true
            $.hoveredCardMesh = card
            gsap.to(card.position, { z: card.userData.originalPosition.z + 2.5, duration: 0.4, ease: 'power2.out' })
            gsap.to(card.scale, { x: 1.1, y: 1.1, z: 1.1, duration: 0.4, ease: 'power2.out' })
            gsap.to(card.rotation, { x: card.userData.originalRotation.x + 0.05, duration: 0.4, ease: 'power2.out' })
          }
        }
        $.camera.position.x = $.mouse.x * 2.5
        $.camera.position.y = 1 + $.mouse.y * 1.5
        $.camera.lookAt(0, -2, 0)
      }

      const onClick = () => {
        const intersects = $.raycaster.intersectObjects($.cardMeshes)
        if (intersects.length > 0) {
          const vulnId = intersects[0].object.userData.example.id
          navigate(`/vulnerability/${vulnId}`)
        }
      }

      const onMouseLeave = () => {
        $.cardMeshes.forEach(m => {
          if (m.userData.isHovered) {
            m.userData.isHovered = false
            gsap.to(m.position, { z: m.userData.originalPosition.z, duration: 0.4, ease: 'power2.out' })
            gsap.to(m.scale, { x: 1, y: 1, z: 1, duration: 0.4, ease: 'power2.out' })
            gsap.to(m.rotation, { x: m.userData.originalRotation.x, duration: 0.4, ease: 'power2.out' })
          }
        })
      }

      const onResize = () => {
        if (!el) return
        $.camera.aspect = el.offsetWidth / el.offsetHeight
        $.camera.updateProjectionMatrix()
        $.renderer.setSize(el.offsetWidth, el.offsetHeight)
      }

      el.addEventListener('mousemove', onMouseMove)
      el.addEventListener('click', onClick)
      el.addEventListener('mouseleave', onMouseLeave)
      window.addEventListener('resize', onResize)

      function animate() {
        $.animationId = requestAnimationFrame(animate)
        const time = Date.now() * 0.001
        $.cardMeshes.forEach((mesh, index) => {
          mesh.position.y = Math.sin(time + index * 0.5) * 0.1
        })
        $.renderer.render($.scene, $.camera)
      }
      animate()

      $.cleanup = { onMouseMove, onClick, onMouseLeave, onResize }
    }, 100)

    return () => {
      clearTimeout(initTimeout)
      if ($.animationId) cancelAnimationFrame($.animationId)
      if ($.cleanup) {
        el.removeEventListener('mousemove', $.cleanup.onMouseMove)
        el.removeEventListener('click', $.cleanup.onClick)
        el.removeEventListener('mouseleave', $.cleanup.onMouseLeave)
        window.removeEventListener('resize', $.cleanup.onResize)
      }
      if ($.renderer) $.renderer.dispose()
    }
  }, [])

  return (
    <div className="examples-gallery-3d">
      <div className="gallery-container" ref={galleryContainerRef}>
        <canvas ref={canvasRef} className="gallery-canvas"></canvas>
      </div>
    </div>
  )
}

export default ExamplesGallery3D
