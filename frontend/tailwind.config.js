/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0a0a0f',
          800: '#12121a',
          700: '#1a1a2e',
          600: '#222240',
        },
        accent: {
          green: '#00e676',
          red: '#ff5252',
          blue: '#448aff',
          purple: '#7c4dff',
          cyan: '#18ffff',
          yellow: '#ffea00',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
