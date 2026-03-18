/**
 * RadarChart — Visualisation multi-axes des scores psychométriques.
 *
 * Fonctionne pour n'importe quel ensemble de traits (≥ 3 axes) :
 *   - HBF-50 : 5 axes Big Five (pentagone)
 *   - HMR-24 : 3 axes cognitifs (triangle)
 *   - Combiné : jusqu'à N traits
 *
 * Couleurs inspirées du sociogram Harmony :
 *   Élevé (≥67)  → #2E8A5C  vert
 *   Moyen (40-66) → #9A7030  ambre
 *   Faible (<40)  → #883838  rouge
 */

import { View, Text, Dimensions } from "react-native";
import Svg, { Polygon, Line, Circle, Text as SvgText, G } from "react-native-svg";
import { colors } from "@harmony/ui";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RadarDataPoint {
  label: string;    // nom du trait, affiché en majuscules
  score: number;    // 0–100
  niveau?: string;  // "Faible" | "Moyen" | "Élevé"
}

interface RadarChartProps {
  data: RadarDataPoint[];
  /** Taille du SVG en pt. Défaut = 85% de la largeur écran. */
  size?: number;
}

// ── Constantes ────────────────────────────────────────────────────────────────

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const GRID_LEVELS = [25, 50, 75, 100] as const;
const LABEL_PAD = 30;     // espace entre le bord du radar et les labels
const RING_LABELS = [25, 50, 75] as const;

// ── Helpers ───────────────────────────────────────────────────────────────────

function scoreColor(score: number): string {
  if (score >= 67) return "#2E8A5C";
  if (score >= 40) return "#9A7030";
  return "#883838";
}

function formatLabel(raw: string): string[] {
  return raw.replace(/_/g, " ").toUpperCase().split(" ").filter(Boolean);
}

function textAnchor(cosA: number): "start" | "middle" | "end" {
  if (cosA > 0.1) return "start";
  if (cosA < -0.1) return "end";
  return "middle";
}

// ── Composant principal ───────────────────────────────────────────────────────

export function RadarChart({ data, size = SCREEN_WIDTH * 0.85 }: RadarChartProps) {
  if (!data || data.length < 3) {
    return (
      <View testID="radar-no-data" style={{ padding: 16 }}>
        <Text style={{ color: colors.text.secondary, textAlign: "center", fontSize: 12 }}>
          Données insuffisantes pour afficher le radar.
        </Text>
      </View>
    );
  }

  const center = size / 2;
  const radius = center - LABEL_PAD - 22;
  const n = data.length;
  const LINE_H = 11;

  function angle(i: number): number {
    return (2 * Math.PI * i) / n - Math.PI / 2;
  }

  function pointAt(r: number, i: number): { x: number; y: number } {
    const a = angle(i);
    return { x: center + r * Math.cos(a), y: center + r * Math.sin(a) };
  }

  function polygonString(r: (d: RadarDataPoint) => number): string {
    return data
      .map((d, i) => {
        const p = pointAt(r(d), i);
        return `${p.x},${p.y}`;
      })
      .join(" ");
  }

  const avgScore = data.reduce((s, d) => s + d.score, 0) / data.length;
  const polyColor = scoreColor(avgScore);

  const scorePoints = polygonString(
    (d) => (Math.min(d.score, 100) / 100) * radius
  );

  return (
    <View testID="radar-chart" style={{ alignItems: "center" }}>
      <Svg width={size} height={size}>
        <G>
          {/* ── Grille polygonale ──────────────────────────────────────────── */}
          {GRID_LEVELS.map((lvl) => {
            const r = (lvl / 100) * radius;
            const pts = Array.from({ length: n }, (_, i) => {
              const p = pointAt(r, i);
              return `${p.x},${p.y}`;
            }).join(" ");
            return (
              <Polygon
                key={`grid-${lvl}`}
                points={pts}
                fill="none"
                stroke={`${colors.brand.primary}28`}
                strokeWidth={lvl === 100 ? 1.5 : 0.8}
                strokeDasharray={lvl === 100 ? undefined : "3,3"}
              />
            );
          })}

          {/* ── Valeurs de la grille (axe du haut) ────────────────────────── */}
          {RING_LABELS.map((lvl) => {
            const r = (lvl / 100) * radius;
            const p = pointAt(r, 0);
            return (
              <SvgText
                key={`rl-${lvl}`}
                x={p.x + 4}
                y={p.y}
                fontSize="8"
                fill={`${colors.text.secondary}60`}
                textAnchor="start"
                alignmentBaseline="middle"
              >
                {lvl}
              </SvgText>
            );
          })}

          {/* ── Axes rayonnants ────────────────────────────────────────────── */}
          {data.map((_, i) => {
            const end = pointAt(radius, i);
            return (
              <Line
                key={`axis-${i}`}
                x1={center}
                y1={center}
                x2={end.x}
                y2={end.y}
                stroke={`${colors.brand.primary}20`}
                strokeWidth={1}
              />
            );
          })}

          {/* ── Polygone du candidat ───────────────────────────────────────── */}
          <Polygon
            points={scorePoints}
            fill={`${polyColor}28`}
            stroke={polyColor}
            strokeWidth={2}
          />

          {/* ── Points vertex (colorés par score) ─────────────────────────── */}
          {data.map((d, i) => {
            const r = (Math.min(d.score, 100) / 100) * radius;
            const p = pointAt(r, i);
            const c = scoreColor(d.score);
            return (
              <Circle
                key={`dot-${i}`}
                cx={p.x}
                cy={p.y}
                r={5}
                fill={c}
                stroke={colors.bg.primary}
                strokeWidth={1.5}
              />
            );
          })}

          {/* ── Labels + score par axe ─────────────────────────────────────── */}
          {data.map((d, i) => {
            const a = angle(i);
            const cosA = Math.cos(a);
            const sinA = Math.sin(a);
            const lx = center + (radius + LABEL_PAD) * cosA;
            const ly = center + (radius + LABEL_PAD) * sinA;
            const anchor = textAnchor(cosA);
            const words = formatLabel(d.label);
            const totalLines = words.length + 1; // +1 pour le score
            // Décalage vertical : centrer le bloc sur ly
            const blockH = totalLines * LINE_H;
            const startY = sinA < -0.05 ? ly - blockH : sinA > 0.05 ? ly : ly - blockH / 2;

            return (
              <G key={`label-${i}`}>
                {words.map((word, wi) => (
                  <SvgText
                    key={`w-${wi}`}
                    x={lx}
                    y={startY + wi * LINE_H}
                    fontSize="9"
                    fontWeight="700"
                    fill={colors.text.secondary}
                    textAnchor={anchor}
                    alignmentBaseline="hanging"
                    letterSpacing={0.4}
                  >
                    {word}
                  </SvgText>
                ))}
                <SvgText
                  x={lx}
                  y={startY + words.length * LINE_H}
                  fontSize="11"
                  fontWeight="800"
                  fill={scoreColor(d.score)}
                  textAnchor={anchor}
                  alignmentBaseline="hanging"
                >
                  {Math.round(d.score)}
                </SvgText>
              </G>
            );
          })}
        </G>
      </Svg>

      {/* ── Légende ───────────────────────────────────────────────────────── */}
      <View style={{ flexDirection: "row", gap: 14, marginTop: 10 }}>
        {(
          [
            { color: "#2E8A5C", label: "Élevé (≥67)" },
            { color: "#9A7030", label: "Moyen (40–66)" },
            { color: "#883838", label: "Faible (<40)" },
          ] as const
        ).map(({ color: c, label }) => (
          <View key={label} style={{ flexDirection: "row", alignItems: "center", gap: 5 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: c }} />
            <Text style={{ color: colors.text.secondary, fontSize: 9, fontWeight: "600" }}>
              {label}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}
