import { useRef, useCallback } from "react";
import { Animated } from "react-native";

export function useQuestionTransition() {
  // 0 = visible au centre, 1 = invisible décalé à droite
  const slideAnim = useRef(new Animated.Value(0)).current;

  const resetAnimation = useCallback(() => {
    slideAnim.setValue(0);
  }, [slideAnim]);

  const triggerTransition = useCallback(
    (callback: () => void) => {
      // Sortie : slide vers la droite + fade out
      Animated.timing(slideAnim, {
        toValue: 1,
        duration: 150,
        useNativeDriver: true,
      }).start(() => {
        // La carte est invisible — on change la question
        callback();
        slideAnim.setValue(1);
        // Différer le spring après que React ait traité le state update
        // (évite l'interruption de l'animation sur New Arch / React 19)
        requestAnimationFrame(() => {
          Animated.spring(slideAnim, {
            toValue: 0,
            friction: 8,
            tension: 80,
            useNativeDriver: true,
          }).start();
        });
      });
    },
    [slideAnim],
  );

  const animatedStyle = {
    opacity: slideAnim.interpolate({
      inputRange: [0, 1],
      outputRange: [1, 0],
    }),
    transform: [
      {
        translateX: slideAnim.interpolate({
          inputRange: [0, 1],
          outputRange: [0, 20],
        }),
      },
    ],
  };

  return { animatedStyle, triggerTransition, resetAnimation };
}
