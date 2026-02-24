/**
 * Design tokens — Harmony dark maritime theme
 *
 * Shared between web (Tailwind CSS variables) and mobile (NativeWind).
 * All color values: hex strings suitable for both CSS and Three.js.
 */

export const colors = {
  // ── Background ──────────────────────────────────────────
  bg: {
    primary: "#07090F",    // near-black ocean depth
    secondary: "#0D1117",  // card backgrounds
    elevated: "#13191F",   // modals, sidebars
    border: "#1E2733",     // subtle borders
  },

  // ── Brand ───────────────────────────────────────────────
  brand: {
    primary: "#0EA5E9",    // sky-500 — ocean surface blue
    secondary: "#6366F1",  // indigo-500 — psychometric accent
    glow: "#38BDF8",       // sky-400 — hover/active glow
  },

  // ── Text ────────────────────────────────────────────────
  text: {
    primary: "#E8EFF7",    // near-white
    secondary: "#8FA3B8",  // muted
    disabled: "#3D5169",   // disabled state
    inverse: "#07090F",    // on bright backgrounds
  },

  // ── Semantic ─────────────────────────────────────────────
  success: "#22C55E",      // green-500
  warning: "#F59E0B",      // amber-500
  danger: "#EF4444",       // red-500
  info: "#06B6D4",         // cyan-500

  // ── Sociogram node colors (by score range) ───────────────
  sociogram: {
    excellent: "#22C55E",  // > 80 dyad score
    good: "#84CC16",       // 65–80
    moderate: "#F59E0B",   // 45–65
    weak: "#EF4444",       // < 45
    node: "#1E40AF",       // default node fill
    nodeGlow: "#3B82F6",   // node hover
    edge: "#1E2733",       // low-compatibility edge
    candidate: "#A855F7",  // simulated candidate (purple)
  },

  // ── Score level colors ───────────────────────────────────
  score: {
    high: "#22C55E",
    medium: "#F59E0B",
    low: "#EF4444",
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
  nodeFill: 0x1e40af,
  nodeGlow: 0x3b82f6,
  edgeExcellent: 0x22c55e,
  edgeGood: 0x84cc16,
  edgeModerate: 0xf59e0b,
  edgeWeak: 0xef4444,
  candidateNode: 0xa855f7,
  background: 0x07090f,
  fog: 0x0d1117,
  ambient: 0x1e2733,
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
