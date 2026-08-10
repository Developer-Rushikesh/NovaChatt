/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.html',
    './static/**/*.js'
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F0EDFF',
          100: '#D9D2FE',
          500: '#6C5CE7',
          600: '#5849D6',
          700: '#4535B5',
        },
        online: '#00B894',
        darkbg: '#0B0F19',
        darkcard: '#1A2233',
        lightbg: '#F5F7FA'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        outfit: ['Outfit', 'sans-serif']
      }
    },
  },
  plugins: [],
}
