/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0F1E",
        surface: "#101731",
        "surface-2": "#161F3D",
        border: "#232D4D",
        fg: "#E6EAF4",
        muted: "#8C97B4",
        primary: {
          DEFAULT: "#6366F1",
          hover: "#818CF8",
        },
        accent: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Menlo", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.3), 0 8px 24px -12px rgba(0,0,0,0.5)",
        pop: "0 12px 40px -12px rgba(0,0,0,0.6)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
        blink: "blink 1.1s step-end infinite",
      },
    },
  },
  plugins: [],
};
