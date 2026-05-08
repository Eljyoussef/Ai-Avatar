import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          700: '#1d4ed8',
          900: '#1e3a5f',
        },
        dark: {
          800: '#1e1e2e',
          900: '#11111b',
          950: '#0a0a14',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'avatar-speak': 'avatarSpeak 0.3s ease-in-out infinite',
      },
      keyframes: {
        avatarSpeak: {
          '0%, 100%': { transform: 'scaleY(1)' },
          '50%': { transform: 'scaleY(0.3)' },
        },
      },
    },
  },
  plugins: [],
}
export default config