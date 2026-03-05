/**
 * Design tokens — Harmony maritime theme
 *
 * Palette philosophy: deep navy as the ocean floor, teak as a prestige anchor,
 * silver as a cool titanium accent. Color is reserved for data meaning — never decorative.
 * Contrast is calibrated to feel refined, not harsh.
 *
 * Primary:   Navy  #1A2C42  +  White / Ice #F1F4F8
 * Secondary: Silver #94A3B8
 * Third:     Teak  #A67C52
 */

export const colors = {
  // ── Background — navy depths ─────────────────────────────
  bg: {
    primary:   "#0D1B2A",    // ocean base — below navy
    secondary: "#1A2C42",    // navy — panels, sidebars
    elevated:  "#243347",    // cards, modals — lighter navy
    border:    "#1E3050",    // barely-there borders
  },

  // ── Brand ────────────────────────────────────────────────
  brand: {
    primary:   "#A67C52",    // teak wood — prestige CTAs
    secondary: "#94A3B8",    // silver titanium — secondary actions
    glow:      "#C4945C",    // teak light — hover / active glow
    gold:      "#A67C52",    // alias: teak = new gold
  },

  // ── Text ─────────────────────────────────────────────────
  text: {
    primary:   "#F1F4F8",    // ice — main readable text
    secondary: "#CBD5E1",    // silverLight — recessed labels
    disabled:  "#4A6070",    // disabled state
    inverse:   "#0D1B2A",    // on bright backgrounds (ice / white)
  },

  // ── Semantic — desaturated, convey meaning precisely ─────
  success: "#5A8279",        // eucalyptus green
  warning: "#A68D6A",        // warm ocre
  danger:  "#9C6B6B",        // muted terracotta
  info:    "#4A789A",        // muted maritime blue

  // ── Sociogram node/edge colors ───────────────────────────
  sociogram: {
    excellent:  "#2E8A5C",   // muted emerald  (dyad ≥ 80)
    good:       "#5A8A30",   // muted sage      (dyad 65–80)
    moderate:   "#9A7030",   // weathered brass (dyad 45–65)
    weak:       "#883838",   // muted crimson   (dyad < 45)
    node:       "#1A2C42",   // navy node fill
    nodeGlow:   "#A67C52",   // teak glow — nodes stand out on navy bg
    edge:       "#1E3050",   // low-compatibility edge (border)
    candidate:  "#7850A8",   // muted amethyst for simulated candidate
  },

  // ── Score level colors ───────────────────────────────────
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
  nodeFill:      0x1a2c42,   // navy node fill
  nodeGlow:      0xa67c52,   // teak glow — warm prestige on navy
  edgeExcellent: 0x2e8a5c,   // muted emerald
  edgeGood:      0x5a8a30,   // muted sage
  edgeModerate:  0x9a7030,   // weathered brass
  edgeWeak:      0x883838,   // muted crimson
  candidateNode: 0x7850a8,   // muted amethyst
  background:    0x0d1b2a,   // ocean base
  fog:           0x1a2c42,   // navy fog
  ambient:       0x1e3050,   // subtle ambient
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
