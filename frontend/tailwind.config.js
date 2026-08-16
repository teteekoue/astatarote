/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          base: "#05070f",
          deep: "#070b18",
          panel: "#0a101f",
          panel2: "#0d1526",
          line: "#1c2740",
          line2: "#283650",
        },
        asta: {
          green: "#10b981",
          mint: "#34d399",
          cyan: "#22d3ee",
          violet: "#8b5cf6",
          amber: "#f59e0b",
          red: "#ef4444",
        },
      },
      fontFamily: {
        sans: ["Sora", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "Consolas", "monospace"],
        display: ["Sora", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(16, 185, 129, 0.18)",
        "glow-sm": "0 0 12px rgba(16, 185, 129, 0.14)",
        card: "0 8px 32px rgba(0, 0, 0, 0.45)",
      },
      backgroundImage: {
        "grid-cyber":
          "linear-gradient(rgba(34, 211, 238, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(34, 211, 238, 0.04) 1px, transparent 1px)",
        "grad-radial":
          "radial-gradient(ellipse at 30% 0%, rgba(16, 185, 129, 0.10), transparent 60%), radial-gradient(ellipse at 80% 100%, rgba(139, 92, 246, 0.08), transparent 60%)",
      },
      backgroundSize: {
        "grid-size": "32px 32px",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
        "scan": {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out both",
        "pulse-glow": "pulse-glow 2.4s ease-in-out infinite",
        scan: "scan 5s linear infinite",
      },
    },
  },
  plugins: [],
}
