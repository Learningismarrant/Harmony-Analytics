import { useRef, useEffect } from "react";
import { View, Text, Animated, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface Props {
  onExit: () => void;
}

export function AssessmentSuccess({ onExit }: Props) {
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 6,
        tension: 40,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
    ]).start();
  }, [scaleAnim, fadeAnim]);

  return (
    <View className="flex-1 bg-bg-primary items-center justify-center p-8">
      {/* Icône animée */}
      <Animated.View
        className="items-center justify-center mb-10"
        style={{ transform: [{ scale: scaleAnim }] }}
      >
        <View
          className="w-24 h-24 rounded-full bg-success items-center justify-center"
          style={{
            shadowColor: "#000",
            shadowOffset: { width: 0, height: 10 },
            shadowOpacity: 0.3,
            shadowRadius: 10,
            elevation: 10,
          }}
        >
          <Ionicons name="checkmark" size={60} color="#F1F4F8" />
        </View>
        {/* Halo */}
        <View
          className="absolute rounded-full"
          style={{
            width: 140,
            height: 140,
            backgroundColor: "rgba(90,130,121,0.2)",
          }}
        />
      </Animated.View>

      {/* Contenu */}
      <Animated.View className="w-full items-center" style={{ opacity: fadeAnim }}>
        <Text className="text-ice text-2xl font-black tracking-[2px] mb-2.5 text-center">
          MISSION ACCOMPLIE
        </Text>
        <Text className="text-white/70 text-sm text-center leading-[22px] mb-10">
          Vos réponses ont été transmises au centre d&apos;analyse.{"\n"}
          Le profil se mettra à jour automatiquement.
        </Text>

        {/* Résumé */}
        <View
          className="flex-row items-center bg-white p-4 rounded-2xl w-full mb-8"
          style={{ shadowColor: "#000", shadowOpacity: 0.08, shadowRadius: 10, elevation: 3 }}
        >
          <View className="flex-1 flex-row items-center justify-center gap-2">
            <Ionicons name="shield-checkmark-outline" size={20} color="#0D1B2A" />
            <Text className="text-bg-primary text-xs font-bold">Données sécurisées</Text>
          </View>
          <View className="w-px h-5 bg-silver/30" />
          <View className="flex-1 flex-row items-center justify-center gap-2">
            <Ionicons name="sync-outline" size={20} color="#0D1B2A" />
            <Text className="text-bg-primary text-xs font-bold">Synchro. immédiate</Text>
          </View>
        </View>

        <TouchableOpacity
          onPress={onExit}
          className="w-full py-4 items-center rounded-xl border border-white/30"
          style={{ backgroundColor: "rgba(255,255,255,0.1)" }}
          activeOpacity={0.75}
        >
          <Text className="text-ice font-semibold tracking-wider">RETOUR AU CENTRE</Text>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
}
