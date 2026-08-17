import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const Lock3D = forwardRef(function Lock3D({
  modelPath = '/lock.glb',
  primaryColor = '#673ee6',
  secondaryColor = '#00b090',
  scale = 3,
  autoRotate = false,
  rotationSpeed = 0.005,
}, ref) {
  const containerRef = useRef(null)
  const internals = useRef({
    scene: null,
    camera: null,
    renderer: null,
    lockModel: null,
    animationId: null,
    ext: { y: 0, z: 0 },
    maxRotation: Math.PI / 2,
    rotationDamping: 0.06,
    targetRotation: { x: 0, y: 0 },
    pointerPending: false,
    rawPointer: { x: 0, y: 0 },
  })

  // Expose setScrollRotation to parent via ref
  useImperativeHandle(ref, () => ({
    setScrollRotation: (y, z = 0) => {
      internals.current.ext.y = y
      internals.current.ext.z = z
    }
  }))

  useEffect(() => {
    const $ = internals.current
    const el = containerRef.current
    if (!el) return

    // Init scene
    $.scene = new THREE.Scene()
    const w = el.clientWidth
    const h = el.clientHeight

    $.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000)
    $.camera.position.set(0, 0, 5)

    $.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
    $.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    $.renderer.setSize(w, h)
    $.renderer.shadowMap.enabled = true
    $.renderer.shadowMap.type = THREE.PCFShadowMap
    $.renderer.outputColorSpace = THREE.SRGBColorSpace
    el.appendChild($.renderer.domElement)

    // Lighting
    $.scene.add(new THREE.AmbientLight(0xffffff, 1.2))
    const dir = new THREE.DirectionalLight(0xffffff, 1.5)
    dir.position.set(5, 10, 7)
    dir.castShadow = true
    $.scene.add(dir)

    const rim1 = new THREE.DirectionalLight(primaryColor, 0.9)
    rim1.position.set(-5, 3, -3)
    $.scene.add(rim1)

    const rim2 = new THREE.DirectionalLight(secondaryColor, 0.8)
    rim2.position.set(5, -2, -5)
    $.scene.add(rim2)

    const pt1 = new THREE.PointLight(0xffffff, 1.5, 25)
    pt1.position.set(0, 3, 3)
    $.scene.add(pt1)

    const fill = new THREE.PointLight(0xffffff, 0.5)
    fill.position.set(-2, -1, 4)
    $.scene.add(fill)

    // Load model
    const loader = new GLTFLoader()
    loader.load(
      modelPath,
      (gltf) => {
        $.lockModel = gltf.scene
        el.classList.add('is-loaded')
        $.lockModel.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true
            child.receiveShadow = true
          }
        })
        const box = new THREE.Box3().setFromObject($.lockModel)
        const center = box.getCenter(new THREE.Vector3())
        const size = box.getSize(new THREE.Vector3())
        const maxDim = Math.max(size.x, size.y, size.z)
        const sc = scale / maxDim
        $.lockModel.scale.multiplyScalar(sc)
        $.lockModel.position.set(-center.x * sc, -center.y * sc, -center.z * sc)
        $.scene.add($.lockModel)
      },
      undefined,
      (err) => console.error('Lock3D load error:', err)
    )

    // Animation
    function animate() {
      $.animationId = requestAnimationFrame(animate)
      if (!$.lockModel) return

      if ($.pointerPending) {
        $.targetRotation.y = THREE.MathUtils.clamp($.rawPointer.x, -1, 1) * $.maxRotation
        $.targetRotation.x = THREE.MathUtils.clamp(-$.rawPointer.y, -1, 1) * $.maxRotation
        $.pointerPending = false
      }

      if (autoRotate) {
        $.lockModel.rotation.y += rotationSpeed
        $.lockModel.rotation.y += ($.targetRotation.y - $.lockModel.rotation.y) * $.rotationDamping
      } else {
        // Keep the lock still by default; pointer movement provides the only
        // rotation and smoothly returns it to center when the pointer leaves.
        $.lockModel.rotation.y += ($.targetRotation.y + $.ext.y - $.lockModel.rotation.y) * $.rotationDamping
      }

      $.lockModel.rotation.x += ($.targetRotation.x - $.lockModel.rotation.x) * $.rotationDamping
      $.lockModel.rotation.z += ($.ext.z - $.lockModel.rotation.z) * $.rotationDamping

      $.renderer.render($.scene, $.camera)
    }

    function handleResize() {
      if (!el || !$.camera || !$.renderer) return
      const w = el.clientWidth
      const h = el.clientHeight
      $.camera.aspect = w / h
      $.camera.updateProjectionMatrix()
      $.renderer.setSize(w, h)
    }

    function handlePointerMove(e) {
      const rect = el.getBoundingClientRect()
      $.rawPointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      $.rawPointer.y = ((e.clientY - rect.top) / rect.height) * 2 - 1
      $.pointerPending = true
    }

    function handlePointerLeave() {
      $.rawPointer = { x: 0, y: 0 }
      $.pointerPending = true
    }

    el.addEventListener('pointermove', handlePointerMove, { passive: true })
    el.addEventListener('pointerleave', handlePointerLeave, { passive: true })
    window.addEventListener('resize', handleResize, { passive: true })
    animate()

    return () => {
      el.removeEventListener('pointermove', handlePointerMove)
      el.removeEventListener('pointerleave', handlePointerLeave)
      window.removeEventListener('resize', handleResize)
      if ($.animationId) cancelAnimationFrame($.animationId)
      if ($.renderer) $.renderer.dispose()
      if ($.lockModel) {
        $.lockModel.traverse((child) => {
          if (child.isMesh) {
            child.geometry.dispose();
            (Array.isArray(child.material) ? child.material : [child.material]).forEach(m => m?.dispose())
          }
        })
      }
    }
  }, [])

  return (
    <div className="lock-3d-container" ref={containerRef}>
      <div className="lock-3d-fallback" aria-hidden="true">
        <span className="fallback-shackle" />
        <span className="fallback-body"><i /></span>
      </div>
    </div>
  )
})

export default Lock3D
