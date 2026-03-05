import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Harmony maritime theme — navy + teak + silver
        bg: {
          primary:   "#0D1B2A",   // ocean base — below navy
          secondary: "#1A2C42",   // navy — panels, sidebars
          elevated:  "#243347",   // cards, modals — lighter navy
          border:    "#1E3050",   // barely-there borders
        },
        brand: {
          primary:   "#A67C52",   // teak — prestige CTAs
          secondary: "#94A3B8",   // silver — secondary actions
          glow:      "#C4945C",   // teak light — hover / active
          gold:      "#A67C52",   // alias: teak = new gold
        },
        muted:          "#94A3B8",  // silver
        "text-primary": "#F1F4F8",  // ice
        navy:    "#1A2C42",
        teak:    "#A67C52",
        silver:  "#94A3B8",
        ice:     "#F1F4F8",
        slate:   "#718096",
        success: "#5A8279",
        error:   "#9C6B6B",
        warning: "#A68D6A",
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
          "0%, 100%": { boxShadow: "0 0 8px rgba(166, 124, 82, 0.2)" },
          "50%":      { boxShadow: "0 0 20px rgba(166, 124, 82, 0.4)" },
        },
      },
      backgroundImage: {
        "ocean-gradient": "radial-gradient(ellipse at top, #1A2C42 0%, #0D1B2A 70%)",
        "card-gradient":  "linear-gradient(135deg, #1A2C42 0%, #243347 100%)",
      },
      boxShadow: {
        "brand-glow": "0 0 16px rgba(166, 124, 82, 0.18)",
        "card":       "0 1px 3px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(30, 48, 80, 0.9)",
      },
    },
  },
  plugins: [],
};

export default config;
