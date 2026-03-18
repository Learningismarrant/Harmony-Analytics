/**
 * RavenMatrix — Renderer pour les questions HMR-24 (Harmony Matrix Reasoning)
 *
 * NOTE: react-native-svg n'est pas dans le package.json de ce projet.
 * Les formes sont donc approximées avec View + StyleSheet :
 *   - circle  → borderRadius = 50 % de la taille
 *   - square  → View simple
 *   - triangle → astuce border CSS (transparent + couleur pour un seul bord)
 *   - diamond  → View + rotation 45°
 * Limitation : "half" fill est rendu via un clip manuel (overflow:hidden +
 * demi-View colorée) — fonctionne mais moins précis qu'un vrai SVG clipPath.
 */

import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import type { RavenMatrixConfig, RavenCell, RavenAnswerOption, RavenShape, RavenFill } from "@harmony/types";
import { colors } from "@harmony/ui";

// ── Thème maritime (tokens @harmony/ui) ───────────────────────────────────────
const COLORS = {
  bg:          colors.bg.primary,       // "#0D1B2A" — fond extérieur
  navy:        colors.bg.secondary,     // "#1A2C42" — fond cellule
  navyBorder:  colors.bg.border,        // "#1E3050" — bordure visible (≠ fond)
  silver:      colors.brand.secondary,  // "#94A3B8" — formes
  teak:        colors.brand.primary,    // "#A67C52" — sélection
  muted:       colors.text.secondary,   // "#CBD5E1" — texte "?"
} as const;

// ── Dimensions ────────────────────────────────────────────────────────────────
const CELL_SIZE = 80;
const CELL_GAP = 4;
const OPTION_SIZE = 64;

// ── Helpers de rendu des formes ───────────────────────────────────────────────

function shapePercent(size: 1 | 2 | 3): number {
  if (size === 1) return 0.4;
  if (size === 2) return 0.65;
  return 0.85;
}

interface ShapeProps {
  shape: RavenShape;
  size: 1 | 2 | 3;
  fill: RavenFill;
  rotation?: 0 | 90 | 180 | 270;
  /** Taille de la cellule contenante en pt */
  containerSize: number;
}

function ShapeView({ shape, size, fill, rotation = 0, containerSize }: ShapeProps) {
  const pct = shapePercent(size);
  const dim = Math.floor(containerSize * pct);
  const color = COLORS.silver;
  const borderWidth = 2;

  if (shape === "circle") {
    return <CircleShape dim={dim} fill={fill} color={color} borderWidth={borderWidth} />;
  }
  if (shape === "square") {
    return <SquareShape dim={dim} fill={fill} color={color} borderWidth={borderWidth} />;
  }
  if (shape === "triangle") {
    return (
      <TriangleShape dim={dim} fill={fill} color={color} rotation={rotation} />
    );
  }
  // diamond = carré pivoté 45°
  return <DiamondShape dim={dim} fill={fill} color={color} borderWidth={borderWidth} rotation={rotation} />;
}

// ── Formes individuelles ──────────────────────────────────────────────────────

interface BaseShapeProps {
  dim: number;
  fill: RavenFill;
  color: string;
  borderWidth: number;
}

function CircleShape({ dim, fill, color, borderWidth }: BaseShapeProps) {
  const radius = dim / 2;

  if (fill === "empty") {
    return (
      <View
        style={{
          width: dim,
          height: dim,
          borderRadius: radius,
          borderWidth,
          borderColor: color,
          backgroundColor: "transparent",
        }}
      />
    );
  }

  if (fill === "full") {
    return (
      <View
        style={{
          width: dim,
          height: dim,
          borderRadius: radius,
          backgroundColor: color,
        }}
      />
    );
  }

  // half — demi-cercle gauche coloré
  return (
    <View
      style={{
        width: dim,
        height: dim,
        borderRadius: radius,
        borderWidth,
        borderColor: color,
        overflow: "hidden",
        backgroundColor: "transparent",
      }}
    >
      <View
        style={{
          width: dim / 2,
          height: dim,
          backgroundColor: color,
        }}
      />
    </View>
  );
}

function SquareShape({ dim, fill, color, borderWidth }: BaseShapeProps) {
  if (fill === "empty") {
    return (
      <View
        style={{
          width: dim,
          height: dim,
          borderWidth,
          borderColor: color,
          backgroundColor: "transparent",
        }}
      />
    );
  }

  if (fill === "full") {
    return <View style={{ width: dim, height: dim, backgroundColor: color }} />;
  }

  // half
  return (
    <View
      style={{
        width: dim,
        height: dim,
        borderWidth,
        borderColor: color,
        overflow: "hidden",
        backgroundColor: "transparent",
      }}
    >
      <View style={{ width: dim / 2, height: dim, backgroundColor: color }} />
    </View>
  );
}

interface TriangleShapeProps {
  dim: number;
  fill: RavenFill;
  color: string;
  rotation: number;
}

function TriangleShape({ dim, fill, color, rotation }: TriangleShapeProps) {
  // Technique classique : borders CSS pour simuler un triangle
  // Pour "empty" : on superpose deux triangles (extérieur + intérieur plus petit)
  const half = Math.floor(dim / 2);

  if (fill === "full") {
    return (
      <View
        style={{
          transform: [{ rotate: `${rotation}deg` }],
          width: 0,
          height: 0,
          borderLeftWidth: half,
          borderRightWidth: half,
          borderBottomWidth: dim,
          borderLeftColor: "transparent",
          borderRightColor: "transparent",
          borderBottomColor: color,
        }}
      />
    );
  }

  if (fill === "half") {
    // Moitié gauche remplie : triangle plein + rectangle masque sur la moitié droite.
    // Le triangle pointe vers le haut, base = dim. Centre horizontal = dim/2.
    // Le rectangle bg couvre [dim/2 .. dim] pour effacer la moitié droite.
    return (
      <View
        style={{
          width: dim,
          height: dim,
          transform: [{ rotate: `${rotation}deg` }],
        }}
      >
        {/* Triangle plein en couleur forme */}
        <View
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            alignItems: "center",
          }}
        >
          <View
            style={{
              width: 0,
              height: 0,
              borderLeftWidth: half,
              borderRightWidth: half,
              borderBottomWidth: dim,
              borderLeftColor: "transparent",
              borderRightColor: "transparent",
              borderBottomColor: color,
            }}
          />
        </View>
        {/* Masque rectangle : efface la moitié droite avec la couleur du fond cellule */}
        <View
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: half,
            right: 0,
            backgroundColor: COLORS.navy,
          }}
        />
      </View>
    );
  }

  // empty : triangle extérieur - pas de fill parfait en pure RN sans SVG
  // On simule avec un triangle plein + un triangle intérieur de couleur bg (cavité)
  const innerHalf = Math.floor(half * 0.65);
  const innerHeight = Math.floor(dim * 0.65);
  return (
    <View style={{ width: dim, height: dim, alignItems: "center", justifyContent: "flex-end" }}>
      {/* Triangle plein en couleur shape */}
      <View
        style={{
          position: "absolute",
          bottom: 0,
          transform: [{ rotate: `${rotation}deg` }],
          width: 0,
          height: 0,
          borderLeftWidth: half,
          borderRightWidth: half,
          borderBottomWidth: dim,
          borderLeftColor: "transparent",
          borderRightColor: "transparent",
          borderBottomColor: color,
        }}
      />
      {/* Triangle intérieur en couleur bg pour simuler le contour */}
      <View
        style={{
          position: "absolute",
          bottom: Math.floor(dim * 0.08),
          transform: [{ rotate: `${rotation}deg` }],
          width: 0,
          height: 0,
          borderLeftWidth: innerHalf,
          borderRightWidth: innerHalf,
          borderBottomWidth: innerHeight,
          borderLeftColor: "transparent",
          borderRightColor: "transparent",
          borderBottomColor: COLORS.navy,
        }}
      />
    </View>
  );
}

interface DiamondShapeProps extends BaseShapeProps {
  rotation: number;
}

function DiamondShape({ dim, fill, color, borderWidth, rotation }: DiamondShapeProps) {
  const squareDim = Math.floor(dim * 0.72); // réduction pour que le losange tienne dans la cellule

  if (fill === "empty") {
    return (
      <View
        style={{
          width: squareDim,
          height: squareDim,
          borderWidth,
          borderColor: color,
          backgroundColor: "transparent",
          transform: [{ rotate: `${45 + rotation}deg` }],
        }}
      />
    );
  }

  if (fill === "full") {
    return (
      <View
        style={{
          width: squareDim,
          height: squareDim,
          backgroundColor: color,
          transform: [{ rotate: `${45 + rotation}deg` }],
        }}
      />
    );
  }

  // half
  return (
    <View
      style={{
        width: squareDim,
        height: squareDim,
        borderWidth,
        borderColor: color,
        overflow: "hidden",
        backgroundColor: "transparent",
        transform: [{ rotate: `${45 + rotation}deg` }],
      }}
    >
      <View style={{ width: squareDim / 2, height: squareDim, backgroundColor: color }} />
    </View>
  );
}

// ── CellView : une case de la grille ─────────────────────────────────────────

interface CellViewProps {
  cell: RavenCell | null;
  isMissing?: boolean;
  size?: number;
}

function CellView({ cell, isMissing = false, size = CELL_SIZE }: CellViewProps) {
  if (isMissing || cell === null) {
    return (
      <View style={[styles.cell, { width: size, height: size, borderStyle: "dashed", borderColor: colors.text.disabled }]}>
        <Text style={styles.missingMark}>?</Text>
      </View>
    );
  }

  return (
    <View style={[styles.cell, { width: size, height: size }]}>
      <ShapeView
        shape={cell.shape}
        size={cell.size}
        fill={cell.fill}
        rotation={cell.rotation ?? 0}
        containerSize={size - 8}
      />
    </View>
  );
}

// ── Props du composant principal ──────────────────────────────────────────────

export interface RavenMatrixProps {
  config: RavenMatrixConfig;
  selectedAnswer: string | undefined;
  onSelect: (answerId: string) => void;
  disabled?: boolean;
}

// ── Composant principal ───────────────────────────────────────────────────────

export function RavenMatrix({ config, selectedAnswer, onSelect, disabled = false }: RavenMatrixProps) {
  const { matrix, answer_options } = config;

  // Découpage des options en rangées de 3
  const optionRows: RavenAnswerOption[][] = [];
  for (let i = 0; i < answer_options.length; i += 3) {
    optionRows.push(answer_options.slice(i, i + 3));
  }

  return (
    <View style={styles.container} testID="raven-matrix">
      {/* ── Grille 3×3 ────────────────────────────────────────────────────── */}
      <View style={styles.gridContainer}>
        {matrix.map((row, rowIdx) => (
          <View key={rowIdx} style={styles.gridRow}>
            {row.map((cell, colIdx) => {
              const isMissing = cell === null;
              return (
                <CellView
                  key={`${rowIdx}-${colIdx}`}
                  cell={cell}
                  isMissing={isMissing}
                />
              );
            })}
          </View>
        ))}
      </View>

      {/* ── Séparateur ────────────────────────────────────────────────────── */}
      <View style={styles.separator} />

      {/* ── Options de réponse ────────────────────────────────────────────── */}
      <View style={styles.optionsContainer} testID="raven-options">
        {optionRows.map((row, rowIdx) => (
          <View key={rowIdx} style={styles.gridRow}>
            {row.map((option) => {
              const isSelected = selectedAnswer === option.id;
              return (
                <TouchableOpacity
                  key={option.id}
                  testID={`raven-option-${option.id}`}
                  onPress={() => {
                    if (!disabled) {
                      onSelect(option.id);
                    }
                  }}
                  activeOpacity={disabled ? 1 : 0.75}
                  accessibilityLabel={`Option ${option.id}`}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                >
                  <View
                    style={[
                      styles.optionCell,
                      isSelected && styles.optionCellSelected,
                    ]}
                  >
                    {/* Label de l'option */}
                    <Text style={styles.optionLabel}>{option.id}</Text>
                    {/* Forme */}
                    <ShapeView
                      shape={option.shape}
                      size={option.size}
                      fill={option.fill}
                      rotation={option.rotation ?? 0}
                      containerSize={OPTION_SIZE - 20}
                    />
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        ))}
      </View>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    paddingVertical: 12,
  },
  gridContainer: {
    gap: CELL_GAP,
  },
  gridRow: {
    flexDirection: "row",
    gap: CELL_GAP,
  },
  cell: {
    backgroundColor: COLORS.navy,
    borderWidth: 1,
    borderColor: COLORS.navyBorder,
    borderRadius: 4,
    alignItems: "center",
    justifyContent: "center",
  },
  missingMark: {
    color: COLORS.muted,
    fontSize: 22,
    fontWeight: "700",
  },
  separator: {
    width: "85%",
    height: 1,
    backgroundColor: COLORS.navyBorder,
    marginVertical: 16,
    opacity: 0.6,
  },
  optionsContainer: {
    gap: CELL_GAP,
  },
  optionCell: {
    width: OPTION_SIZE,
    height: OPTION_SIZE,
    backgroundColor: COLORS.navy,
    borderWidth: 1.5,
    borderColor: COLORS.navyBorder,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  optionCellSelected: {
    borderColor: COLORS.teak,
    borderWidth: 3,
  },
  optionLabel: {
    position: "absolute",
    top: 3,
    left: 5,
    color: COLORS.muted,
    fontSize: 10,
    fontWeight: "600",
  },
});
