import { create } from 'zustand'

function updateDOM(isDark) {
  if (isDark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

const useThemeStore = create((set, get) => ({
  isDark: false,

  toggleTheme: () => {
    const newDark = !get().isDark
    set({ isDark: newDark })
    updateDOM(newDark)
    localStorage.setItem('theme', newDark ? 'dark' : 'light')
  },

  initializeTheme: () => {
    const saved = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const isDark = saved ? saved === 'dark' : prefersDark
    set({ isDark })
    updateDOM(isDark)
  },
}))

export { useThemeStore }
