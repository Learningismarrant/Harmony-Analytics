import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Maritime dark theme — desaturated, refined
        bg: {
          primary:   "#07090F",
          secondary: "#0B1018",
          elevated:  "#101720",
          border:    "#1A2634",
        },
        brand: {
          primary:   "#4A90B8",   // maritime steel blue
          secondary: "#50528A",   // muted slate-indigo
          glow:      "#6AAFCC",   // lighter steel for hover
          gold:      "#A8864A",   // champagne bronze
        },
        muted:         "#5A7890",
        "text-primary": "#C8D8E4",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Courier New", "monospace"],
      },
      animation: {
        "fade-in":   "fadeIn 0.3s ease-in-out",
        "slide-up":  "slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "spin-slow": "spin 8s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 8px rgba(74, 144, 184, 0.2)" },
          "50%":      { boxShadow: "0 0 20px rgba(74, 144, 184, 0.4)" },
        },
      },
      backgroundImage: {
        "ocean-gradient": "radial-gradient(ellipse at top, #0D1B2A 0%, #07090F 70%)",
        "card-gradient":  "linear-gradient(135deg, #0B1018 0%, #101720 100%)",
      },
      boxShadow: {
        "brand-glow": "0 0 16px rgba(74, 144, 184, 0.15)",
        "card":       "0 1px 3px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(26, 38, 52, 0.9)",
      },
    },
  },
  plugins: [],
};

export default config;
