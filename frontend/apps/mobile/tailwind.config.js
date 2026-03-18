/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
    "../../packages/ui/src/**/*.{ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // ── Fonds — navy profond ──────────────────────────────
        bg: {
          primary:   "#0D1B2A",   // base la plus sombre (sous le navy)
          secondary: "#1A2C42",   // navy — panneaux, sidebars
          elevated:  "#243347",   // cartes, modales — navy plus clair
          border:    "#1E3050",   // bordures quasi-invisibles
        },
        // ── Textes ───────────────────────────────────────────
        text: {
          primary:   "#F1F4F8",   // ice — texte principal
          secondary: "#CBD5E1",   // silverLight — texte secondaire
        },
        // ── Brand ────────────────────────────────────────────
        brand: {
          primary:   "#A67C52",   // teak — CTA prestige, actions primaires (aligne avec @harmony/ui tokens.ts)
          secondary: "#94A3B8",   // silver — icônes, éléments UI neutres
          glow:      "#C4945C",   // teak clair — hover / glow
        },
        // ── Utilitaires ──────────────────────────────────────
        muted:   "#94A3B8",       // silver
        slate:   "#718096",       // slate fumée
        navy:    "#1A2C42",       // accès direct à navy
        teak:    "#A67C52",       // accès direct à teak
        silver:  "#94A3B8",       // accès direct à silver
        ice:     "#F1F4F8",       // accès direct à ice
        // ── Statuts ──────────────────────────────────────────
        success: "#5A8279",       // vert eucalyptus
        error:   "#9C6B6B",       // terre d'ombre rouge
        warning: "#A68D6A",       // ocre doré
      },
      fontFamily: {
        sans: ["Inter"],
      },
    },
  },
  plugins: [],
};
