import React from "react";
import { View, TouchableOpacity, Text } from "react-native";
import Svg, { Circle, Line, Defs, RadialGradient, Stop } from "react-native-svg";
import { Ionicons } from "@expo/vector-icons";
import type { CalibCatalogueOut, CalibSessionOut, CatalogueDomain } from "@harmony/types";

// ─── Layout constants ──────────────────────────────────────────────────────────
const SVG_SIZE = 350;
const CX = 175;
const CY = 175;
const ORBIT_RADIUS = 130;
const CENTER_RADIUS = 48;
const STAR_RADIUS = 22;

// ─── Domain metadata ───────────────────────────────────────────────────────────
const DOMAINS: CatalogueDomain[] = [
  "cognitive",
  "personality",
  "motivation",
  "person_team",
  "physical",
  "person_org",
  "person_job",
];

// Angles in degrees from top (north), clockwise
const DOMAIN_ANGLES: Record<CatalogueDomain, number> = {
  cognitive:   -90,
  personality: -40,
  motivation:   25,
  person_team:  85,
  physical:    140,
  person_org:  -155,
  person_job:  -120,
};

export const DOMAIN_LABELS: Record<CatalogueDomain, string> = {
  personality:  "Qui suis-je ?",
  cognitive:    "En suis-je\ncapable ?",
  motivation:   "Le ferai-je ?",
  person_job:   "Ce que je cherche\ndans un poste ?",
  person_org:   "Ce que je cherche\ndans ce yacht ?",
  person_team:  "Ce que je cherche\ndans mon équipe ?",
  physical:     "Suis-je\nphysiquement apte ?",
};

export const DOMAIN_ICONS: Record<CatalogueDomain, keyof typeof Ionicons.glyphMap> = {
  personality:  "person-outline",
  cognitive:    "bulb-outline",
  motivation:   "flash-outline",
  person_job:   "briefcase-outline",
  person_org:   "boat-outline",
  person_team:  "people-outline",
  physical:     "body-outline",
};

export const DOMAIN_COLORS: Record<CatalogueDomain, string> = {
  personality:  "#A67C52",
  cognitive:    "#4A90B8",
  motivation:   "#C4A35A",
  person_job:   "#94A3B8",
  person_org:   "#5B8DB8",
  person_team:  "#2E8A5C",
  physical:     "#C47A52",
};

// ─── Helpers ───────────────────────────────────────────────────────────────────
function degToRad(deg: number) {
  return (deg * Math.PI) / 180;
}

function starPosition(domain: CatalogueDomain): { x: number; y: number } {
  const angleRad = degToRad(DOMAIN_ANGLES[domain]);
  return {
    x: CX + ORBIT_RADIUS * Math.cos(angleRad),
    y: CY + ORBIT_RADIUS * Math.sin(angleRad),
  };
}

function hexToRgb(hex: string): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `${r},${g},${b}`;
}

// ─── Dot progress indicator ────────────────────────────────────────────────────
function DotRow({
  total,
  completed,
  color,
  cx,
  cy,
}: {
  total: number;
  completed: number;
  color: string;
  cx: number;
  cy: number;
}) {
  if (total === 0) return null;
  const dots = Math.min(total, 5);
  const dotSpacing = 8;
  const startX = cx - ((dots - 1) * dotSpacing) / 2;
  const dotY = cy + STAR_RADIUS + 8;

  return (
    <>
      {Array.from({ length: dots }).map((_, i) => {
        const dotIndex = i;
        const isCompleted = dotIndex < completed;
        return (
          <Circle
            key={i}
            cx={startX + i * dotSpacing}
            cy={dotY}
            r={2.5}
            fill={isCompleted ? color : "rgba(255,255,255,0.12)"}
          />
        );
      })}
    </>
  );
}

// ─── Component props ───────────────────────────────────────────────────────────
interface ConstellationMapProps {
  catalogues: CalibCatalogueOut[];
  sessions: CalibSessionOut[];
  onDomainPress: (domain: CatalogueDomain) => void;
}

export function ConstellationMap({
  catalogues,
  sessions,
  onDomainPress,
}: ConstellationMapProps) {
  // ── Progression par domaine ──────────────────────────────────────────────────
  function getDomainProgress(domain: CatalogueDomain) {
    const domainCatalogues = catalogues.filter(
      (c) => (c.domain ?? "personality") === domain
    );
    const completed = domainCatalogues.filter((c) => {
      const session = sessions.find((s) => s.catalogue_id === c.id);
      return session != null && session.completed_at !== null;
    });
    return { total: domainCatalogues.length, completed: completed.length };
  }

  // ── Progression globale ──────────────────────────────────────────────────────
  const totalCatalogues = catalogues.length;
  const completedCatalogues = catalogues.filter((c) => {
    const session = sessions.find((s) => s.catalogue_id === c.id);
    return session != null && session.completed_at !== null;
  }).length;
  const globalPct =
    totalCatalogues > 0 ? completedCatalogues / totalCatalogues : 0;

  // Anneau de progression (stroke-dasharray)
  const ringCircumference = 2 * Math.PI * (CENTER_RADIUS - 4);
  const ringDash = ringCircumference * globalPct;
  const ringGap = ringCircumference - ringDash;

  // ── Ligne de connexion opacity selon progression ──────────────────────────────
  function lineStroke(domain: CatalogueDomain): string {
    const { total, completed } = getDomainProgress(domain);
    if (total === 0 || completed === 0) return "rgba(255,255,255,0.06)";
    if (completed === total) {
      const rgb = hexToRgb(DOMAIN_COLORS[domain]);
      return `rgba(${rgb},0.85)`;
    }
    const rgb = hexToRgb(DOMAIN_COLORS[domain]);
    return `rgba(${rgb},0.4)`;
  }

  // ── Étoile fill selon progression ────────────────────────────────────────────
  function starFill(domain: CatalogueDomain): string {
    const { total, completed } = getDomainProgress(domain);
    if (total === 0 || completed === 0) return "#1A2C42";
    const rgb = hexToRgb(DOMAIN_COLORS[domain]);
    const alpha = completed === total ? "0.28" : "0.16";
    return `rgba(${rgb},${alpha})`;
  }

  function starBorderColor(domain: CatalogueDomain): string {
    const { total, completed } = getDomainProgress(domain);
    if (total === 0 || completed === 0) {
      return "rgba(255,255,255,0.12)";
    }
    const rgb = hexToRgb(DOMAIN_COLORS[domain]);
    return completed === total
      ? `rgba(${rgb},0.9)`
      : `rgba(${rgb},0.55)`;
  }

  function iconColor(domain: CatalogueDomain): string {
    const { total, completed } = getDomainProgress(domain);
    if (total === 0 || completed === 0) return "rgba(255,255,255,0.25)";
    const rgb = hexToRgb(DOMAIN_COLORS[domain]);
    return completed === total
      ? DOMAIN_COLORS[domain]
      : `rgba(${rgb},0.75)`;
  }

  // ── Texte label opacity ───────────────────────────────────────────────────────
  function labelColor(domain: CatalogueDomain): string {
    const { total, completed } = getDomainProgress(domain);
    if (total === 0 || completed === 0) return "rgba(255,255,255,0.22)";
    return completed === total ? "#F1F4F8" : "rgba(255,255,255,0.55)";
  }

  // ── Calcul du décalage du label ───────────────────────────────────────────────
  // Le label est positionné au-dessus ou en dessous de l'étoile selon l'angle
  function labelOffset(domain: CatalogueDomain): { labelAbove: boolean } {
    const angle = DOMAIN_ANGLES[domain];
    // Au-dessus si l'étoile est dans la moitié haute (angle entre -180 et 0)
    return { labelAbove: angle < -10 || angle > 160 };
  }

  const globalPctDisplay =
    totalCatalogues > 0
      ? `${Math.round(globalPct * 100)}%`
      : "0%";

  return (
    <View style={{ width: SVG_SIZE, height: SVG_SIZE }}>
      {/* ── SVG layer : lignes + cercles ──────────────────────────────────────── */}
      <Svg
        width={SVG_SIZE}
        height={SVG_SIZE}
        style={{ position: "absolute" }}
        viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`}
      >
        <Defs>
          {/* Gradient pour l'étoile centrale */}
          <RadialGradient
            id="centralGlow"
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

        {/* Lignes de connexion centre → étoiles */}
        {DOMAINS.map((domain) => {
          const pos = starPosition(domain);
          return (
            <Line
              key={`line-${domain}`}
              x1={CX}
              y1={CY}
              x2={pos.x}
              y2={pos.y}
              stroke={lineStroke(domain)}
              strokeWidth={1}
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Glow ambiant de l'étoile centrale */}
        <Circle
          cx={CX}
          cy={CY}
          r={CENTER_RADIUS + 12}
          fill="url(#centralGlow)"
        />

        {/* Fond étoile centrale */}
        <Circle
          cx={CX}
          cy={CY}
          r={CENTER_RADIUS}
          fill="#0D1B2A"
          stroke="rgba(166,124,82,0.3)"
          strokeWidth={1.5}
        />

        {/* Anneau de progression global */}
        {globalPct > 0 && (
          <Circle
            cx={CX}
            cy={CY}
            r={CENTER_RADIUS - 4}
            fill="none"
            stroke="#A67C52"
            strokeWidth={3}
            strokeDasharray={`${ringDash} ${ringGap}`}
            strokeLinecap="round"
            rotation={-90}
            origin={`${CX},${CY}`}
          />
        )}

        {/* Anneau de fond (track) */}
        <Circle
          cx={CX}
          cy={CY}
          r={CENTER_RADIUS - 4}
          fill="none"
          stroke="rgba(166,124,82,0.12)"
          strokeWidth={3}
        />

        {/* Étoiles orbitales — fond SVG */}
        {DOMAINS.map((domain) => {
          const pos = starPosition(domain);
          const { total, completed } = getDomainProgress(domain);

          return (
            <React.Fragment key={`star-${domain}`}>
              {/* Glow si domaine complété */}
              {completed > 0 && completed === total && (
                <Circle
                  cx={pos.x}
                  cy={pos.y}
                  r={STAR_RADIUS + 10}
                  fill={`rgba(${hexToRgb(DOMAIN_COLORS[domain])},0.08)`}
                />
              )}

              {/* Cercle principal */}
              <Circle
                cx={pos.x}
                cy={pos.y}
                r={STAR_RADIUS}
                fill={starFill(domain)}
                stroke={starBorderColor(domain)}
                strokeWidth={1.5}
              />

              {/* Dots de progression */}
              <DotRow
                total={Math.min(total, 5)}
                completed={completed}
                color={DOMAIN_COLORS[domain]}
                cx={pos.x}
                cy={pos.y}
              />
            </React.Fragment>
          );
        })}
      </Svg>

      {/* ── Texte central ─────────────────────────────────────────────────────── */}
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
            fontSize: 16,
            fontWeight: "800",
            textAlign: "center",
          }}
        >
          {globalPctDisplay}
        </Text>
        <Text
          style={{
            color: "rgba(166,124,82,0.6)",
            fontSize: 8,
            fontWeight: "600",
            letterSpacing: 0.5,
            textAlign: "center",
            marginTop: 1,
          }}
        >
          GLOBAL
        </Text>
      </View>

      {/* ── Icônes + labels des étoiles ───────────────────────────────────────── */}
      {DOMAINS.map((domain) => {
        const pos = starPosition(domain);
        const { labelAbove } = labelOffset(domain);
        const color = iconColor(domain);
        const lColor = labelColor(domain);
        const label = DOMAIN_LABELS[domain];
        const labelLines = label.split("\n");

        // Décalage du label (au-dessus ou en dessous)
        const labelTopOffset = labelAbove
          ? pos.y - STAR_RADIUS - 6 - labelLines.length * 10
          : pos.y + STAR_RADIUS + 8;

        return (
          <React.Fragment key={`overlay-${domain}`}>
            {/* Zone tappable centrée sur l'étoile */}
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
              onPress={() => onDomainPress(domain)}
              activeOpacity={0.7}
            >
              <Ionicons
                name={DOMAIN_ICONS[domain]}
                size={16}
                color={color}
              />
            </TouchableOpacity>

            {/* Label texte */}
            <View
              style={{
                position: "absolute",
                left: pos.x - 48,
                top: labelTopOffset,
                width: 96,
                alignItems: "center",
              }}
              pointerEvents="none"
            >
              {labelLines.map((line, i) => (
                <Text
                  key={i}
                  style={{
                    color: lColor,
                    fontSize: 8,
                    textAlign: "center",
                    lineHeight: 10,
                    fontWeight: "500",
                  }}
                >
                  {line}
                </Text>
              ))}
            </View>
          </React.Fragment>
        );
      })}
    </View>
  );
}
