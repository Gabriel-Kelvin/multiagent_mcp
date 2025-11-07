/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Project brand palette
        brand: {
          primary: '#5C3E94', // royal purple
          deep: '#412B6B',    // deep purple
          ink: '#211832',     // nearly-black
          accent: '#F25912',  // orange
        },
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'mesh-gradient': 'radial-gradient(at 0% 0%, rgb(14, 165, 233) 0px, transparent 50%), radial-gradient(at 100% 0%, rgb(217, 70, 239) 0px, transparent 50%), radial-gradient(at 100% 100%, rgb(14, 165, 233) 0px, transparent 50%), radial-gradient(at 0% 100%, rgb(217, 70, 239) 0px, transparent 50%)',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.25), 0 10px 20px -2px rgba(0, 0, 0, 0.2)',
        'glow': '0 0 24px rgba(92, 62, 148, 0.35)',
        'glow-accent': '0 0 24px rgba(242, 89, 18, 0.35)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
