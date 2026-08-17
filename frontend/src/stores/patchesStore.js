import { create } from 'zustand'

const usePatchStore = create((set, get) => ({
  // Store for patched vulnerabilities
  patchedVulnerabilities: [],

  // Add a patched vulnerability
  addPatchedVulnerability: (vulnerability) => {
    const patchedVuln = {
      ...vulnerability,
      patchedAt: new Date().toISOString(),
      patchStatus: 'applied',
      patchVersion: vulnerability.patch.version,
      patchDescription: vulnerability.patch.description
    }

    set(state => {
      const updated = [patchedVuln, ...state.patchedVulnerabilities]
      // Keep only last 50 patches
      return { patchedVulnerabilities: updated.slice(0, 50) }
    })
  },

  // Get all patched vulnerabilities
  getPatchedVulnerabilities: () => {
    return get().patchedVulnerabilities
  },

  // Get patch count
  getPatchCount: () => {
    return get().patchedVulnerabilities.length
  },
}))

export { usePatchStore }
