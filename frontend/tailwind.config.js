/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        desk:          '#C8A97A',
        paper:         '#FAF7EE',
        'paper-card':  '#FEFBF0',
        'tab-bar':     '#EDD9A8',
        'tab-hover':   '#E2CC90',
        ink: {
          DEFAULT: '#2C1810',
          muted:   '#7A5530',
          light:   '#5C4033',
        },
        gold: {
          DEFAULT: '#8B6914',
          light:   '#C8A951',
          border:  '#A08040',
        },
        leather:   '#3D2B1F',
        burgundy: {
          DEFAULT: '#6B2D3E',
          light:   '#8B3D52',
        },
      },
      fontFamily: {
        serif:   ['"EB Garamond"', 'Georgia', '"Times New Roman"', 'serif'],
        display: ['"Playfair Display"', 'Georgia', 'serif'],
      },
      boxShadow: {
        paper: '-12px 0 28px rgba(80,40,10,0.22), 12px 0 28px rgba(80,40,10,0.22), 0 4px 18px rgba(80,40,10,0.15), inset 6px 0 12px rgba(80,40,10,0.05), inset -6px 0 12px rgba(80,40,10,0.05)',
      },
    },
  },
  plugins: [],
}
