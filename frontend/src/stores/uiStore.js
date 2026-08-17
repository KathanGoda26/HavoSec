import { create } from 'zustand'

const useUiStore = create((set) => ({
  isLoading: false,

  startLoading: () => set({ isLoading: true }),
  stopLoading: () => set({ isLoading: false }),
}))

export { useUiStore }
