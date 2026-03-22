import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  ImageBackground,
} from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";
import { calibrationApi } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import { saveCalibToken } from "@/features/auth/lib";
import { setAccessToken } from "@harmony/api";

import { AuthHeader } from "@/features/auth/AuthHeader";
import { AuthFooter } from "@/features/auth/AuthFooter";

export default function CalibratorLoginScreen() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) {
      Alert.alert("Erreur", "Veuillez saisir votre email et mot de passe.");
      return;
    }

    setLoading(true);
    try {
      const token = await calibrationApi.login(email.trim().toLowerCase(), password);

      await saveCalibToken(token.access_token);
      setAccessToken(token.access_token);

      await login({
        accessToken: token.access_token,
        role: "calibrator",
        crewProfileId: null,
        calibratorId: token.calibrator_id,
        name: token.name,
      });

      router.replace("/(calibrator)/catalogues");
    } catch {
      Alert.alert(
        "Connexion échouée",
        "Email ou mot de passe invalide. Veuillez réessayer.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <ImageBackground
      source={require("../../assets/images/Background1.png")}
      style={{ flex: 1 }}
      resizeMode="cover"
    >
      <View style={{ flex: 1}}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View className="flex-1 justify-center px-6">
            {/* Header */}
            <View className="items-center mb-10">
              <AuthHeader title="RADIANT" subtitle="Espace calibrateur" />
              <Text className="text-muted text-xs text-center mt-2 leading-5">
                Accès réservé aux participants des études d'étalonnage
              </Text>
            </View>

            {/* Form */}
            <View className="space-y-6">
              <View>
                <Text className="text-muted text-xs mb-2 tracking-widest uppercase">
                  Email
                </Text>
                <TextInput
                  className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-4 text-text-primary text-base"
                  placeholder="votre@email.com"
                  placeholderTextColor="#8FA3B8"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  value={email}
                  onChangeText={setEmail}
                />
              </View>

              <View>
                <Text className="text-muted text-xs mb-2 tracking-widest uppercase">
                  Mot de passe
                </Text>
                <TextInput
                  className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-4 text-text-primary text-base"
                  placeholder="••••••••"
                  placeholderTextColor="#8FA3B8"
                  secureTextEntry
                  value={password}
                  onChangeText={setPassword}
                />
              </View>

              <TouchableOpacity
                onPress={handleLogin}
                disabled={loading}
                className="bg-teak rounded-xl py-4 items-center mt-8"
                style={{ opacity: loading ? 0.6 : 1 }}
              >
                {loading ? (
                  <ActivityIndicator color="#0D1B2A" />
                ) : (
                  <Text className="text-bg-primary font-semibold text-base tracking-widest uppercase">
                    Se connecter
                  </Text>
                )}
              </TouchableOpacity>

              {/* Register link */}
              <View className="flex-row justify-center mt-2">
                <Text className="text-muted text-sm">Pas encore de compte ? </Text>
                <TouchableOpacity onPress={() => router.push("/(calibrator-auth)/register")}>
                  <Text className="text-teak text-sm font-medium">S'inscrire</Text>
                </TouchableOpacity>
              </View>

              {/* Back to candidate login */}
              <View className="flex-row justify-center mt-2">
                <TouchableOpacity onPress={() => router.replace("/(auth)/login")}>
                  <Text className="text-muted text-xs">← Retour connexion candidat</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
          <AuthFooter/>
        </KeyboardAvoidingView>
      </View>
    </ImageBackground>
  );
}
