/**
 * SwipePairCard — Carte de choix forcé ipsatif (T-IRT / HEXACO)
 *
 * UX : la carte affiche les deux propositions (A et B).
 *  - Swipe gauche  → choisir la proposition gauche (A)
 *  - Swipe droite  → choisir la proposition droite (B)
 *  - Tap sur l'une des zones de texte → même effet que le swipe
 *
 * Implémenté avec Animated + PanResponder (0 dépendance externe).
 * Le geste dépasse SWIPE_THRESHOLD → animation de sortie + onChoose(side).
 * En-deçà du seuil → spring de retour.
 */

import { useRef, useEffect } from "react";
import {
  View,
  Text,
  Animated,
  PanResponder,
  Dimensions,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import type { ForcedChoiceOption } from "@harmony/types";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const SWIPE_THRESHOLD = SCREEN_WIDTH * 0.28;
const EXIT_VELOCITY = 1200;

interface SwipePairCardProps {
  leftOption: ForcedChoiceOption;
  rightOption: ForcedChoiceOption;
  /** Côté déjà sélectionné (undefined = aucun) */
  selectedSide: "left" | "right" | undefined;
  onChoose: (side: "left" | "right") => void;
  /** Numéro de la question (1-based) pour forcer la réinitialisation entre paires */
  pairIndex: number;
}

export function SwipePairCard({
  leftOption,
  rightOption,
  selectedSide,
  onChoose,
  pairIndex,
}: SwipePairCardProps) {
  const translateX = useRef(new Animated.Value(0)).current;
  const rotate = translateX.interpolate({
    inputRange: [-SCREEN_WIDTH / 2, 0, SCREEN_WIDTH / 2],
    outputRange: ["-12deg", "0deg", "12deg"],
    extrapolate: "clamp",
  });

  // Opacités des labels directionnels sur les bords
  const leftHintOpacity = translateX.interpolate({
    inputRange: [-SCREEN_WIDTH * 0.15, 0],
    outputRange: [1, 0],
    extrapolate: "clamp",
  });
  const rightHintOpacity = translateX.interpolate({
    inputRange: [0, SCREEN_WIDTH * 0.15],
    outputRange: [0, 1],
    extrapolate: "clamp",
  });

  // Couleur de fond dynamique de la carte (gauche = bleu A, droite = bleu B)
  const leftOverlayOpacity = translateX.interpolate({
    inputRange: [-SCREEN_WIDTH * 0.4, 0],
    outputRange: [0.18, 0],
    extrapolate: "clamp",
  });
  const rightOverlayOpacity = translateX.interpolate({
    inputRange: [0, SCREEN_WIDTH * 0.4],
    outputRange: [0, 0.18],
    extrapolate: "clamp",
  });

  // Réinitialiser la carte quand on change de paire
  useEffect(() => {
    translateX.setValue(0);
  }, [pairIndex, translateX]);

  function animateOut(side: "left" | "right") {
    const toValue = side === "left" ? -SCREEN_WIDTH * 1.6 : SCREEN_WIDTH * 1.6;
    Animated.timing(translateX, {
      toValue,
      duration: 280,
      useNativeDriver: true,
    }).start(() => {
      translateX.setValue(0);
      onChoose(side);
    });
  }

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 5,
      onPanResponderMove: (_, g) => {
        translateX.setValue(g.dx);
      },
      onPanResponderRelease: (_, g) => {
        const isFastSwipeLeft = g.vx < -(EXIT_VELOCITY / 1000);
        const isFastSwipeRight = g.vx > EXIT_VELOCITY / 1000;
        const isThresholdLeft = g.dx < -SWIPE_THRESHOLD;
        const isThresholdRight = g.dx > SWIPE_THRESHOLD;

        if (isFastSwipeLeft || isThresholdLeft) {
          animateOut("left");
        } else if (isFastSwipeRight || isThresholdRight) {
          animateOut("right");
        } else {
          Animated.spring(translateX, {
            toValue: 0,
            useNativeDriver: true,
            friction: 5,
          }).start();
        }
      },
    }),
  ).current;

  const cardStyle = {
    transform: [{ translateX }, { rotate }],
  };

  return (
    <View style={styles.container}>
      {/* Indicateur gauche (A) */}
      <Animated.View
        style={[styles.hint, styles.hintLeft, { opacity: leftHintOpacity }]}
        pointerEvents="none"
      >
        <Text style={styles.hintTextLeft}>← A</Text>
      </Animated.View>

      {/* Indicateur droite (B) */}
      <Animated.View
        style={[styles.hint, styles.hintRight, { opacity: rightHintOpacity }]}
        pointerEvents="none"
      >
        <Text style={styles.hintTextRight}>B →</Text>
      </Animated.View>

      {/* Carte principale */}
      <Animated.View
        {...panResponder.panHandlers}
        style={[styles.card, cardStyle]}
      >
        {/* Overlay coloré selon la direction */}
        <Animated.View
          style={[styles.overlay, styles.overlayLeft, { opacity: leftOverlayOpacity }]}
          pointerEvents="none"
        />
        <Animated.View
          style={[styles.overlay, styles.overlayRight, { opacity: rightOverlayOpacity }]}
          pointerEvents="none"
        />

        {/* Option A (gauche) */}
        <TouchableOpacity
          onPress={() => animateOut("left")}
          activeOpacity={0.85}
          style={[
            styles.option,
            styles.optionTop,
            selectedSide === "left" && styles.optionSelected,
          ]}
        >
          <View style={styles.optionLabel}>
            <Text style={styles.optionLabelText}>A</Text>
          </View>
          <Text style={[styles.optionText, selectedSide === "left" && styles.optionTextSelected]}>
            {leftOption.text.fr}
          </Text>
        </TouchableOpacity>

        {/* Séparateur "ou" */}
        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>ou</Text>
          <View style={styles.dividerLine} />
        </View>

        {/* Option B (droite) */}
        <TouchableOpacity
          onPress={() => animateOut("right")}
          activeOpacity={0.85}
          style={[
            styles.option,
            styles.optionBottom,
            selectedSide === "right" && styles.optionSelected,
          ]}
        >
          <View style={styles.optionLabel}>
            <Text style={styles.optionLabelText}>B</Text>
          </View>
          <Text style={[styles.optionText, selectedSide === "right" && styles.optionTextSelected]}>
            {rightOption.text.fr}
          </Text>
        </TouchableOpacity>
      </Animated.View>

      {/* Hint textuel en bas */}
      <Text style={styles.swipeHint}>← glisse ou tape pour choisir →</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  hint: {
    position: "absolute",
    top: "30%",
    zIndex: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  hintLeft: {
    left: 12,
    borderColor: "#A67C52",
    borderWidth: 1.5,
    backgroundColor: "rgba(166,124,82,0.12)",
  },
  hintRight: {
    right: 12,
    borderColor: "#94A3B8",
    borderWidth: 1.5,
    backgroundColor: "rgba(148,163,184,0.10)",
  },
  hintTextLeft: {
    color: "#A67C52",
    fontWeight: "700",
    fontSize: 14,
  },
  hintTextRight: {
    color: "#94A3B8",
    fontWeight: "700",
    fontSize: 14,
  },
  card: {
    width: SCREEN_WIDTH - 40,
    backgroundColor: "#1A2C42",   // navy
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#1E3050",
    shadowColor: "#1A2C42",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.45,
    shadowRadius: 16,
    elevation: 12,
    overflow: "hidden",
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 20,
    zIndex: 10,
    pointerEvents: "none",
  },
  overlayLeft: {
    backgroundColor: "#A67C52",   // teak
  },
  overlayRight: {
    backgroundColor: "#94A3B8",   // silver
  },
  option: {
    padding: 24,
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 14,
  },
  optionTop: {
    borderBottomWidth: 0,
  },
  optionBottom: {
    borderTopWidth: 0,
  },
  optionSelected: {
    backgroundColor: "rgba(166,124,82,0.10)",  // teak subtle
  },
  optionLabel: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#1E3050",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginTop: 2,
  },
  optionLabelText: {
    color: "#94A3B8",   // silver
    fontSize: 12,
    fontWeight: "700",
  },
  optionText: {
    flex: 1,
    color: "#CBD5E1",   // silverLight
    fontSize: 16,
    lineHeight: 24,
  },
  optionTextSelected: {
    color: "#A67C52",   // teak — sélectionné
    fontWeight: "500",
  },
  divider: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: "#1E3050",
  },
  dividerText: {
    color: "#718096",   // slate
    fontSize: 12,
    fontStyle: "italic",
    marginHorizontal: 10,
  },
  swipeHint: {
    marginTop: 20,
    color: "#718096",   // slate
    fontSize: 12,
    letterSpacing: 0.3,
  },
});
