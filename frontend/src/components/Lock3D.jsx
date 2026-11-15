import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const Lock3D = forwardRef(function Lock3D({
  modelPath = '/lock.glb',
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
    let isDisposed = false

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
    $.renderer.domElement.setAttribute('aria-hidden', 'true')
    el.appendChild($.renderer.domElement)

    // Lighting
    $.scene.add(new THREE.AmbientLight(0xffffff, 1.2))
    const dir = new THREE.DirectionalLight(0xffffff, 1.5)
    dir.position.set(5, 10, 7)
    dir.castShadow = true
    $.scene.add(dir)

    const rim1 = new THREE.DirectionalLight(0xffffff, 0.9)
    rim1.position.set(-5, 3, -3)
    $.scene.add(rim1)

    const rim2 = new THREE.DirectionalLight(0xffffff, 0.8)
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
        if (isDisposed) {
          gltf.scene.traverse((child) => {
            if (!child.isMesh) return
            child.geometry?.dispose()
            const materials = Array.isArray(child.material) ? child.material : [child.material]
            materials.forEach(material => material?.dispose())
          })
          return
        }
        $.lockModel = gltf.scene
        $.lockModel.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true
            child.receiveShadow = true
            const materials = Array.isArray(child.material) ? child.material : [child.material]
            materials.forEach((material) => {
              if (!material) return
              material.side = THREE.DoubleSide
              material.needsUpdate = true
            })
          }
        })
        const box = new THREE.Box3().setFromObject($.lockModel)
        const center = box.getCenter(new THREE.Vector3())
        const size = box.getSize(new THREE.Vector3())
        const maxDim = Math.max(size.x, size.y, size.z)
        if (!Number.isFinite(maxDim) || maxDim <= 0) {
          console.error('Lock3D model has invalid dimensions')
          return
        }
        const sc = scale / maxDim
        $.lockModel.scale.multiplyScalar(sc)
        $.lockModel.position.set(-center.x * sc, -center.y * sc, -center.z * sc)
        $.scene.add($.lockModel)

        // Fit the camera to the normalized model rather than relying on the
        // source file's original units or export origin.
        const fittedBox = new THREE.Box3().setFromObject($.lockModel)
        const fittedSize = fittedBox.getSize(new THREE.Vector3())
        const fittedMaxDim = Math.max(fittedSize.x, fittedSize.y, fittedSize.z)
        const fovRadians = THREE.MathUtils.degToRad($.camera.fov)
        const cameraDistance = (fittedMaxDim / (2 * Math.tan(fovRadians / 2))) * 1.35
        $.camera.position.set(0, 0, Math.max(cameraDistance, 4.5))
        $.camera.lookAt(0, 0, 0)
        $.camera.updateProjectionMatrix()

        // Do not hide the visible fallback until a real model frame has been
        // drawn. This avoids a blank hero while the large GLB is decoding.
        $.renderer.render($.scene, $.camera)
        requestAnimationFrame(() => {
          if (!isDisposed) el.classList.add('is-loaded')
        })
      },
      undefined,
      (err) => console.error('Lock3D load error:', err)
    )

    // Animation
    function animate() {
      $.animationId = requestAnimationFrame(animate)
      if ($.lockModel) {
        if ($.pointerPending) {
          $.targetRotation.y = THREE.MathUtils.clamp($.rawPointer.x, -1, 1) * $.maxRotation
          $.targetRotation.x = THREE.MathUtils.clamp(-$.rawPointer.y, -1, 1) * $.maxRotation
          $.pointerPending = false
        }

        if (autoRotate) {
          $.lockModel.rotation.y += rotationSpeed
          $.lockModel.rotation.y += ($.targetRotation.y - $.lockModel.rotation.y) * $.rotationDamping
        } else {
          $.lockModel.rotation.y += ($.targetRotation.y + $.ext.y - $.lockModel.rotation.y) * $.rotationDamping
        }

        $.lockModel.rotation.x += ($.targetRotation.x - $.lockModel.rotation.x) * $.rotationDamping
        $.lockModel.rotation.z += ($.ext.z - $.lockModel.rotation.z) * $.rotationDamping
      }

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
    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(el)
    animate()

    return () => {
      isDisposed = true
      el.removeEventListener('pointermove', handlePointerMove)
      el.removeEventListener('pointerleave', handlePointerLeave)
      window.removeEventListener('resize', handleResize)
      resizeObserver.disconnect()
      if ($.animationId) cancelAnimationFrame($.animationId)
      if ($.renderer) {
        $.renderer.dispose()
        $.renderer.forceContextLoss()
        if ($.renderer.domElement.parentNode === el) {
          el.removeChild($.renderer.domElement)
        }
      }
      el.classList.remove('is-loaded')
      if ($.lockModel) {
        $.lockModel.traverse((child) => {
          if (child.isMesh) {
            child.geometry.dispose();
            (Array.isArray(child.material) ? child.material : [child.material]).forEach(m => m?.dispose())
          }
        })
        $.lockModel = null
      }
      $.animationId = null
      $.renderer = null
      $.camera = null
      $.scene = null
    }
  }, [])

  return <div className="lock-3d-container" ref={containerRef} />
})

export default Lock3D
