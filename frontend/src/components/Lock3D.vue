<template>
  <div class="lock-3d-container" ref="container"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const container = ref(null);
let scene, camera, renderer, lockModel;
let animationId = null;
const maxRotation = Math.PI / 2;
const rotationDamping = 0.08;
const targetRotation = { x: 0, y: 0 };

function initScene() {
  if (!container.value) return;

  // Scene setup
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);

  // Camera setup
  const width = container.value.clientWidth;
  const height = container.value.clientHeight;
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(0, 0, 5);

  // Renderer setup
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(width, height);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.value.appendChild(renderer.domElement);

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
  scene.add(ambientLight);

  const directionalLight1 = new THREE.DirectionalLight(0xffffff, 1.5);
  directionalLight1.position.set(5, 10, 7);
  directionalLight1.castShadow = true;
  scene.add(directionalLight1);

  // Rim lights for edge highlighting
  const rimLight1 = new THREE.DirectionalLight(0x673ee6, 0.9);
  rimLight1.position.set(-5, 3, -3);
  scene.add(rimLight1);

  const rimLight2 = new THREE.DirectionalLight(0x00b090, 0.8);
  rimLight2.position.set(5, -2, -5);
  scene.add(rimLight2);

  // Point light for highlights
  const pointLight = new THREE.PointLight(0xffffff, 1.5, 25);
  pointLight.position.set(0, 3, 3);
  scene.add(pointLight);

  // Soft fill light to brighten shadowed areas
  const fillLight = new THREE.PointLight(0xffffff, 0.5);
  fillLight.position.set(-2, -1, 4);
  scene.add(fillLight);

  // Load the GLB model
  loadModel();
}

function loadModel() {
  const loader = new GLTFLoader();

  loader.load(
    "/lock.glb",
    (gltf) => {
      lockModel = gltf.scene;

      // Enable shadows
      lockModel.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
        }
      });

      // Center and scale the model
      const box = new THREE.Box3().setFromObject(lockModel);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());

      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 3 / maxDim;
      lockModel.scale.multiplyScalar(scale);

      lockModel.position.x = -center.x * scale;
      lockModel.position.y = -center.y * scale;
      lockModel.position.z = -center.z * scale;

      scene.add(lockModel);
    },
    (progress) => {
      // Loading progress (optional)
      console.log(
        "Loading progress:",
        (progress.loaded / progress.total) * 100 + "%"
      );
    },
    (error) => {
      console.error("Error loading model:", error);
    }
  );
}

function animate() {
  animationId = requestAnimationFrame(animate);
  if (lockModel) {
    lockModel.rotation.x +=
      (targetRotation.x - lockModel.rotation.x) * rotationDamping;
    lockModel.rotation.y +=
      (targetRotation.y - lockModel.rotation.y) * rotationDamping;
  }
  renderer.render(scene, camera);
}

function handleResize() {
  if (!container.value) return;

  const width = container.value.clientWidth;
  const height = container.value.clientHeight;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function handlePointerMove(event) {
  if (!container.value) return;

  const rect = container.value.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  const y = ((event.clientY - rect.top) / rect.height) * 2 - 1;

  targetRotation.y = THREE.MathUtils.clamp(x, -1, 1) * maxRotation;
  targetRotation.x = THREE.MathUtils.clamp(-y, -1, 1) * maxRotation;
}

function handlePointerLeave() {
  targetRotation.x = 0;
  targetRotation.y = 0;
}

function setupInteraction() {
  if (!container.value) return;

  container.value.addEventListener("pointermove", handlePointerMove);
  container.value.addEventListener("pointerleave", handlePointerLeave);
}

function cleanupInteraction() {
  if (!container.value) return;

  container.value.removeEventListener("pointermove", handlePointerMove);
  container.value.removeEventListener("pointerleave", handlePointerLeave);
}

onMounted(() => {
  initScene();
  setupInteraction();
  window.addEventListener("resize", handleResize);
  animate();
});

onBeforeUnmount(() => {
  cleanupInteraction();
  window.removeEventListener("resize", handleResize);

  if (animationId) {
    cancelAnimationFrame(animationId);
  }

  if (renderer) {
    renderer.dispose();
  }

  // Clean up model
  if (lockModel) {
    lockModel.traverse((child) => {
      if (child.isMesh) {
        child.geometry.dispose();
        if (child.material) {
          if (Array.isArray(child.material)) {
            child.material.forEach((material) => material.dispose());
          } else {
            child.material.dispose();
          }
        }
      }
    });
  }
});
</script>

<style scoped>
.lock-3d-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  position: relative;
}
</style>
