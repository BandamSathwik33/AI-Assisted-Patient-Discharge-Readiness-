/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        clinical: {
          ready: '#10b981',
          'ready-bg': '#ecfdf5',
          near: '#f59e0b',
          'near-bg': '#fffbeb',
          blocked: '#e11d48',
          'blocked-bg': '#fff1f2',
          navy: '#0f172a',
          slate: '#1e293b',
          teal: '#0d9488',
        }
      }
    },
  },
  plugins: [],
}
