import React from "react";
import { View, TouchableOpacity, Text } from "react-native";
import Svg, { Circle, Line, Defs, RadialGradient, Stop } from "react-native-svg";
import { Ionicons } from "@expo/vector-icons";

// ─── Layout constants ──────────────────────────────────────────────────────────
const SVG_SIZE = 340;
const CX = 170;
const CY = 170;
const ORBIT_RADIUS = 120;
const CENTER_RADIUS = 52;
const STAR_RADIUS = 26;

// ─── Star definitions ──────────────────────────────────────────────────────────
type StarKey = "tests" | "experience" | "documents";

interface StarDef {
  key: StarKey;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  angle: number;   // degrees
  label: string;
}

const STARS: StarDef[] = [
  { key: "tests",      icon: "flask-outline",            color: "#4A90B8", angle: -90,  label: "Tests" },
  { key: "experience", icon: "boat-outline",             color: "#A67C52", angle: 30,   label: "Expérience" },
  { key: "documents",  icon: "shield-checkmark-outline", color: "#2E8A5C", angle: 150,  label: "Documents" },
];

// ─── Helpers ───────────────────────────────────────────────────────────────────
function degToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function hexToRgb(hex: string): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `${r},${g},${b}`;
}

function starPosition(angle: number): { x: number; y: number } {
  const rad = degToRad(angle);
  return {
    x: CX + ORBIT_RADIUS * Math.cos(rad),
    y: CY + ORBIT_RADIUS * Math.sin(rad),
  };
}

// ─── Dot row (always 3 dots for the 3 profile stars) ──────────────────────────
function DotRow({
  progress,
  color,
  cx,
  cy,
}: {
  progress: number; // 0–1
  color: string;
  cx: number;
  cy: number;
}) {
  const TOTAL = 3;
  const completed = Math.round(progress * TOTAL);
  const dotSpacing = 8;
  const startX = cx - ((TOTAL - 1) * dotSpacing) / 2;
  const dotY = cy + STAR_RADIUS + 8;

  return (
    <>
      {Array.from({ length: TOTAL }).map((_, i) => (
        <Circle
          key={i}
          cx={startX + i * dotSpacing}
          cy={dotY}
          r={2.5}
          fill={i < completed ? color : "rgba(255,255,255,0.12)"}
        />
      ))}
    </>
  );
}

// ─── Props ─────────────────────────────────────────────────────────────────────
export interface ProfileMacroMapProps {
  initials: string;
  globalProgress: number;       // 0–1
  starProgress: {
    tests: number;              // 0–1
    experience: number;
    documents: number;
  };
  onStarPress: (key: StarKey) => void;
}

// ─── Component ─────────────────────────────────────────────────────────────────
export function ProfileMacroMap({
  initials,
  globalProgress,
  starProgress,
  onStarPress,
}: ProfileMacroMapProps) {
  // Progress ring geometry
  const ringCircumference = 2 * Math.PI * (CENTER_RADIUS - 4);
  const ringDash = ringCircumference * globalProgress;
  const ringGap = ringCircumference - ringDash;

  // Per-star derived style helpers
  function lineStroke(star: StarDef): string {
    const p = starProgress[star.key];
    if (p <= 0) return "rgba(255,255,255,0.06)";
    if (p >= 1) return `rgba(${hexToRgb(star.color)},0.85)`;
    return `rgba(${hexToRgb(star.color)},0.4)`;
  }

  function starFill(star: StarDef): string {
    const p = starProgress[star.key];
    if (p <= 0) return "#1A2C42";
    const alpha = p >= 1 ? "0.28" : "0.16";
    return `rgba(${hexToRgb(star.color)},${alpha})`;
  }

  function starBorder(star: StarDef): string {
    const p = starProgress[star.key];
    if (p <= 0) return "rgba(255,255,255,0.12)";
    return p >= 1
      ? `rgba(${hexToRgb(star.color)},0.9)`
      : `rgba(${hexToRgb(star.color)},0.55)`;
  }

  function iconColor(star: StarDef): string {
    const p = starProgress[star.key];
    if (p <= 0) return "rgba(255,255,255,0.25)";
    return p >= 1 ? star.color : `rgba(${hexToRgb(star.color)},0.75)`;
  }

  return (
    <View style={{ width: SVG_SIZE, height: SVG_SIZE }}>
      {/* ── SVG layer: connections + circles ──────────────────────────────────── */}
      <Svg
        width={SVG_SIZE}
        height={SVG_SIZE}
        style={{ position: "absolute" }}
        viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`}
      >
        <Defs>
          <RadialGradient
            id="centerGlow"
            cx="50%"
            cy="50%"
            r="50%"
            fx="50%"
            fy="50%"
          >
            <Stop offset="0%" stopColor="#A67C52" stopOpacity="0.2" />
            <Stop offset="100%" stopColor="#A67C52" stopOpacity="0" />
          </RadialGradient>
        </Defs>

        {/* Connection lines */}
        {STARS.map((star) => {
          const pos = starPosition(star.angle);
          return (
            <Line
              key={`line-${star.key}`}
              x1={CX}
              y1={CY}
              x2={pos.x}
              y2={pos.y}
              stroke={lineStroke(star)}
              strokeWidth={1}
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Central ambient glow */}
        <Circle
          cx={CX}
          cy={CY}
          r={CENTER_RADIUS + 14}
          fill="url(#centerGlow)"
        />

        {/* Central circle */}
        <Circle
          cx={CX}
          cy={CY}
          r={CENTER_RADIUS}
          fill="#0D1B2A"
          stroke="rgba(166,124,82,0.4)"
          strokeWidth={1.5}
        />

        {/* Progress ring track */}
        <Circle
          cx={CX}
          cy={CY}
          r={CENTER_RADIUS - 4}
          fill="none"
          stroke="rgba(166,124,82,0.12)"
          strokeWidth={3}
        />

        {/* Progress ring fill */}
        {globalProgress > 0 && (
          <Circle
            cx={CX}
            cy={CY}
            r={CENTER_RADIUS - 4}
            fill="none"
            stroke="#A67C52"
            strokeWidth={3}
            strokeDasharray={`${ringDash} ${ringGap}`}
            strokeLinecap="round"
            transform={`rotate(-90, ${CX}, ${CY})`}
          />
        )}

        {/* Orbital stars */}
        {STARS.map((star) => {
          const pos = starPosition(star.angle);
          const p = starProgress[star.key];
          return (
            <React.Fragment key={`star-${star.key}`}>
              {/* Glow halo (only when any progress) */}
              {p > 0 && (
                <Circle
                  cx={pos.x}
                  cy={pos.y}
                  r={STAR_RADIUS + 10}
                  fill={`rgba(${hexToRgb(star.color)},0.08)`}
                />
              )}

              {/* Main circle */}
              <Circle
                cx={pos.x}
                cy={pos.y}
                r={STAR_RADIUS}
                fill={starFill(star)}
                stroke={starBorder(star)}
                strokeWidth={1.5}
              />

              {/* Dot progress indicators */}
              <DotRow
                progress={p}
                color={star.color}
                cx={pos.x}
                cy={pos.y}
              />
            </React.Fragment>
          );
        })}
      </Svg>

      {/* ── Center initials overlay ────────────────────────────────────────────── */}
      <View
        style={{
          position: "absolute",
          left: CX - 32,
          top: CY - 16,
          width: 64,
          alignItems: "center",
        }}
        pointerEvents="none"
      >
        <Text
          style={{
            color: "#A67C52",
            fontSize: 18,
            fontWeight: "800",
            textAlign: "center",
            letterSpacing: 2,
          }}
        >
          {initials.substring(0, 2).toUpperCase()}
        </Text>
      </View>

      {/* ── Star icons + tap zones ─────────────────────────────────────────────── */}
      {STARS.map((star) => {
        const pos = starPosition(star.angle);
        const color = iconColor(star);

        // Label positioning: below the dot row
        const labelY = pos.y + STAR_RADIUS + 20;
        const labelWidth = 60;

        return (
          <React.Fragment key={`overlay-${star.key}`}>
            {/* Tap zone with icon */}
            <TouchableOpacity
              style={{
                position: "absolute",
                left: pos.x - STAR_RADIUS,
                top: pos.y - STAR_RADIUS,
                width: STAR_RADIUS * 2,
                height: STAR_RADIUS * 2,
                alignItems: "center",
                justifyContent: "center",
              }}
              onPress={() => onStarPress(star.key)}
              activeOpacity={0.7}
            >
              <Ionicons name={star.icon} size={18} color={color} />
            </TouchableOpacity>

            {/* Label below dot row */}
            <View
              style={{
                position: "absolute",
                left: pos.x - labelWidth / 2,
                top: labelY,
                width: labelWidth,
                alignItems: "center",
              }}
              pointerEvents="none"
            >
              <Text
                style={{
                  color: color,
                  fontSize: 9,
                  fontWeight: "600",
                  letterSpacing: 0.8,
                  textAlign: "center",
                }}
              >
                {star.label.toUpperCase()}
              </Text>
            </View>
          </React.Fragment>
        );
      })}
    </View>
  );
}
