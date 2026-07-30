/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: '#0A0F1A',
          sidebar: '#0D1526',
          card: '#111827',
          'card-hover': '#1a2332',
          border: '#1e293b',
          primary: '#3B82F6',
          'primary-hover': '#2563EB',
          accent: '#FA8C16',
          success: '#10B981',
          danger: '#EF4444',
          warning: '#F59E0B',
          info: '#06B6D4',
          text: '#E2E8F0',
          'text-secondary': '#94A3B8',
          'text-muted': '#64748B',
        },
      },
      fontFamily: {
        sans: ['PingFang SC', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'typing': 'blink 1s step-end infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.6)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
  ],
}
