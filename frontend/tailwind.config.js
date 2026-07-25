/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0B0F19",
          dark: "#070A13",
          card: "#111827",
          border: "#1F2937",
          green: "#10B981",
          neonGreen: "#34D399",
          glowGreen: "#059669",
          red: "#EF4444",
          blue: "#3B82F6",
          purple: "#8B5CF6",
          yellow: "#F59E0B"
        }
      },
      fontFamily: {
        mono: ["Courier New", "Courier", "monospace", "JetBrains Mono"]
      }
    },
  },
  plugins: [],
}
