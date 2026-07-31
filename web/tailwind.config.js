/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: 'rgb(var(--industrial-bg) / <alpha-value>)',
          sidebar: 'rgb(var(--industrial-sidebar) / <alpha-value>)',
          card: 'rgb(var(--industrial-card) / <alpha-value>)',
          'card-hover': 'rgb(var(--industrial-card-hover) / <alpha-value>)',
          border: 'rgb(var(--industrial-border) / <alpha-value>)',
          primary: 'rgb(var(--industrial-primary) / <alpha-value>)',
          'primary-hover': 'rgb(var(--industrial-primary-hover) / <alpha-value>)',
          accent: 'rgb(var(--industrial-accent) / <alpha-value>)',
          'accent-hover': 'rgb(var(--industrial-accent-hover) / <alpha-value>)',
          success: 'rgb(var(--industrial-success) / <alpha-value>)',
          danger: 'rgb(var(--industrial-danger) / <alpha-value>)',
          warning: 'rgb(var(--industrial-warning) / <alpha-value>)',
          info: 'rgb(var(--industrial-info) / <alpha-value>)',
          text: 'rgb(var(--industrial-text) / <alpha-value>)',
          'text-secondary': 'rgb(var(--industrial-text-secondary) / <alpha-value>)',
          'text-muted': 'rgb(var(--industrial-text-muted) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['PingFang SC', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'typing': 'blink 1s step-end infinite',
        'float': 'float 4s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(var(--industrial-accent), 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(var(--industrial-accent), 0.4)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
  ],
}
