/**
 * Design tokens — Harmony dark maritime theme
 *
 * Palette philosophy: deep desaturated navy, weathered brass as prestige accent.
 * Color is reserved for data meaning — never decorative.
 * Contrast is calibrated to feel refined, not harsh.
 */

export const colors = {
  // ── Background ──────────────────────────────────────────
  bg: {
    primary:   "#07090F",    // ocean depth — near-black
    secondary: "#0B1018",    // panel backgrounds
    elevated:  "#101720",    // cards, modals, sidebars
    border:    "#1A2634",    // barely-there borders
  },

  // ── Brand ───────────────────────────────────────────────
  brand: {
    primary:   "#4A90B8",    // maritime steel blue (desaturated from #0EA5E9)
    secondary: "#50528A",    // muted slate-indigo
    glow:      "#6AAFCC",    // lighter steel for hover/active
    gold:      "#A8864A",    // champagne bronze — prestige accent
  },

  // ── Text ────────────────────────────────────────────────
  text: {
    primary:   "#C8D8E4",    // soft cool white (less stark than near-white)
    secondary: "#5A7890",    // recessed label text
    disabled:  "#2D4358",    // disabled state
    inverse:   "#07090F",    // on bright backgrounds
  },

  // ── Semantic — fully desaturated, convey meaning without screaming ────────
  success: "#2E7A52",        // deep muted emerald
  warning: "#9A7230",        // weathered brass
  danger:  "#884040",        // deep muted crimson
  info:    "#287890",        // deep muted teal

  // ── Sociogram node/edge colors ───────────────────────────
  sociogram: {
    excellent:  "#2E8A5C",   // muted emerald  (dyad ≥ 80)
    good:       "#5A8A30",   // muted sage      (dyad 65–80)
    moderate:   "#9A7030",   // weathered brass (dyad 45–65)
    weak:       "#883838",   // muted crimson   (dyad < 45)
    node:       "#1A3A60",   // deep navy node fill
    nodeGlow:   "#4A90B8",   // matches brand primary
    edge:       "#1A2634",   // low-compatibility edge (same as border)
    candidate:  "#7850A8",   // muted amethyst for simulated candidate
  },

  // ── Score level colors (slightly lighter for readability in UI) ──────────
  score: {
    high:   "#3D9A6A",       // readable muted emerald
    medium: "#A88540",       // readable brass
    low:    "#9A4848",       // readable muted crimson
  },
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  "2xl": 48,
  "3xl": 64,
} as const;

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
} as const;

export const typography = {
  fontFamily: {
    sans: "'Inter', system-ui, sans-serif",
    mono: "'JetBrains Mono', 'Courier New', monospace",
  },
  fontSize: {
    xs: 11,
    sm: 13,
    base: 15,
    lg: 17,
    xl: 20,
    "2xl": 24,
    "3xl": 30,
    "4xl": 36,
  },
  fontWeight: {
    regular: "400",
    medium: "500",
    semibold: "600",
    bold: "700",
  },
} as const;

/** Three.js hex integers — use with THREE.Color */
export const threeColors = {
  nodeFill:      0x1a3a60,   // deep navy
  nodeGlow:      0x4a90b8,   // maritime steel blue
  edgeExcellent: 0x2e8a5c,   // muted emerald
  edgeGood:      0x5a8a30,   // muted sage
  edgeModerate:  0x9a7030,   // weathered brass
  edgeWeak:      0x883838,   // muted crimson
  candidateNode: 0x7850a8,   // muted amethyst
  background:    0x07090f,
  fog:           0x0b1018,
  ambient:       0x1a2634,
} as const;

/** Dyad score → hex color for edge rendering */
export function dyadScoreToColor(score: number): number {
  if (score >= 80) return threeColors.edgeExcellent;
  if (score >= 65) return threeColors.edgeGood;
  if (score >= 45) return threeColors.edgeModerate;
  return threeColors.edgeWeak;
}

/** Dyad score → edge thickness (world units) */
export function dyadScoreToThickness(score: number): number {
  return 0.02 + (score / 100) * 0.08;
}
