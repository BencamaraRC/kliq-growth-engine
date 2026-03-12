/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        kliq: {
          green: '#1C3838',
          'green-light': '#F3FAF8',
          'green-hover': '#0E2325',
        },
        tangerine: '#FF9F88',
        lime: '#DEFE9C',
        alpine: '#9CF0FF',
        ivory: '#FFFDF9',
        teal: {
          50: '#F3FAF8',
          100: '#D7F0ED',
          200: '#AEE1DA',
          300: '#7ECAC3',
          400: '#53AEA9',
          500: '#39938F',
          600: '#2C7574',
          700: '#265F5E',
          800: '#224D4D',
          900: '#1C3838',
          950: '#0E2325',
        },
        gray: {
          25: '#FCFCFD',
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D2D6DB',
          400: '#9DA4AE',
          500: '#6C737F',
          600: '#4D5761',
          700: '#384250',
          800: '#1F2A37',
          900: '#111927',
          950: '#0D121C',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
