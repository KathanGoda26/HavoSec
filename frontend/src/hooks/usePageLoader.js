import { create } from 'zustand'

// Shared singleton state — true once the intro loader finishes
const usePageLoaderStore = create((set) => ({
  pageLoaded: false,
  setPageLoaded: (value) => set({ pageLoaded: value }),
}))

export { usePageLoaderStore }
