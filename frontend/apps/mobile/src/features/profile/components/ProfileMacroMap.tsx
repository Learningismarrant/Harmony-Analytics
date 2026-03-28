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
  angle: number; // degrees
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

// ─── Props ─────────────────────────────────────────────────────────────────────
export interface ProfileMacroMapProps {
  initials: string;
  onStarPress: (key: StarKey) => void;
  onCenterPress: () => void;
}

// ─── Component ─────────────────────────────────────────────────────────────────
export function ProfileMacroMap({ initials, onStarPress, onCenterPress }: ProfileMacroMapProps) {
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
          <RadialGradient id="centerGlow" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
            <Stop offset="0%" stopColor="#A67C52" stopOpacity="0.2" />
            <Stop offset="100%" stopColor="#A67C52" stopOpacity="0" />
          </RadialGradient>
        </Defs>

        {/* Connection lines — static, per-star color */}
        {STARS.map((star) => {
          const pos = starPosition(star.angle);
          return (
            <Line
              key={`line-${star.key}`}
              x1={CX} y1={CY} x2={pos.x} y2={pos.y}
              stroke={`rgba(${hexToRgb(star.color)},0.28)`}
              strokeWidth={1}
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Central ambient glow */}
        <Circle cx={CX} cy={CY} r={CENTER_RADIUS + 14} fill="url(#centerGlow)" />

        {/* Central circle */}
        <Circle
          cx={CX} cy={CY} r={CENTER_RADIUS}
          fill="#0D1B2A"
          stroke="rgba(166,124,82,0.45)"
          strokeWidth={1.5}
        />

        {/* Decorative inner ring */}
        <Circle
          cx={CX} cy={CY} r={CENTER_RADIUS - 4}
          fill="none"
          stroke="rgba(166,124,82,0.12)"
          strokeWidth={3}
        />

        {/* Orbital stars */}
        {STARS.map((star) => {
          const pos = starPosition(star.angle);
          return (
            <React.Fragment key={`star-${star.key}`}>
              {/* Glow halo */}
              <Circle
                cx={pos.x} cy={pos.y}
                r={STAR_RADIUS + 10}
                fill={`rgba(${hexToRgb(star.color)},0.07)`}
              />
              {/* Main circle */}
              <Circle
                cx={pos.x} cy={pos.y}
                r={STAR_RADIUS}
                fill={`rgba(${hexToRgb(star.color)},0.16)`}
                stroke={`rgba(${hexToRgb(star.color)},0.55)`}
                strokeWidth={1.5}
              />
            </React.Fragment>
          );
        })}
      </Svg>

      {/* ── Center tap zone + initials ─────────────────────────────────────────── */}
      <TouchableOpacity
        style={{
          position: "absolute",
          left: CX - CENTER_RADIUS,
          top: CY - CENTER_RADIUS,
          width: CENTER_RADIUS * 2,
          height: CENTER_RADIUS * 2,
          alignItems: "center",
          justifyContent: "center",
        }}
        onPress={onCenterPress}
        activeOpacity={0.7}
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
      </TouchableOpacity>

      {/* ── Star icons + tap zones ─────────────────────────────────────────────── */}
      {STARS.map((star) => {
        const pos = starPosition(star.angle);
        const labelY = pos.y + STAR_RADIUS + 10;
        const labelWidth = 64;

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
              <Ionicons name={star.icon} size={18} color={star.color} />
            </TouchableOpacity>

            {/* Label below star */}
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
                  color: star.color,
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
