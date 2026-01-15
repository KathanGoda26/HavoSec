/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          purple: '#673ee6',
          green: '#00b090',
          'purple-light': '#8b5cf6',
          'green-light': '#34d399',
        },
        dark: {
          bg: '#000000',
          card: '#111111',
          text: '#f9fafb',
        }
      },
      fontFamily: {
        'heading': ['Playfair Display', 'serif'],
        'body': ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #673ee6, #00b090)',
      },
      boxShadow: {
        'luxury': '0 10px 40px rgba(0, 0, 0, 0.1)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'slide-in': 'slideIn 0.5s ease-out',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}