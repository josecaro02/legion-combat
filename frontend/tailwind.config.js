/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0A0A0A',
        card: '#1A1A1A',
        border: '#2A2A2A',
        gold: '#C9A646',
        goldLight: "#f1c754",
        goldSoft: '#8B6F2A',
        text: '#E5E7EB',
        muted: '#9CA3AF',
        bgInput: "#121212"
      }
    },
    fontFamily: {
      legion: ["Cinzel", "serif"],
    },
    boxShadow: {
      soft: "0 0 20px rgba(0,0,0,0.6)",
    }
  },
  plugins: [],
}
