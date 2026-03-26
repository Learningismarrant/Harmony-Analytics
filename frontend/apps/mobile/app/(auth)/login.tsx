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
import { authApi } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import { saveRefreshToken } from "@/features/auth/lib";
import { AuthFooter } from "@/features/auth/AuthFooter";
import { AuthHeader } from "@/features/auth/AuthHeader";
import type { UserRole } from "@harmony/types";

export default function LoginScreen() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) {
      Alert.alert("Error", "Please enter your email and password.");
      return;
    }

    setLoading(true);
    try {
      const token = await authApi.login(email.trim().toLowerCase(), password);

      await saveRefreshToken(token.refresh_token);

      await login({
        accessToken: token.access_token,
        role: token.role as UserRole,
        crewProfileId: token.profile_id,
        name: email,
      });

      router.replace("/(candidate)/profile");
    } catch {
      Alert.alert(
        "Login failed",
        "Invalid email or password. Please try again.",
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
      <View style={{ flex: 1 }}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <View className="flex-1 justify-center px-6">
            {/* Logo */}
            <View className="items-center mb-10">
              <AuthHeader title="HARMONY" subtitle="Yachting Assessment Center" />
            </View>

            {/* Form */}
            <View className="space-y-6">
              <View>
                <Text className="text-muted text-xs mb-2 tracking-widest uppercase">
                  Email
                </Text>
                <TextInput
                  className="bg-bg-elevated mb-2 border border-bg-border rounded-xl px-4 py-4 text-text-primary text-base"
                  placeholder="your@email.com"
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
                  Password
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
                className="bg-brand-primary rounded-xl py-4 items-center mt-8"
                style={{ opacity: loading ? 0.6 : 1 }}
              >
                {loading ? (
                  <ActivityIndicator color="#0D1B2A" />
                ) : (
                  <Text className="text-bg-primary font-semibold text-base tracking-widest uppercase">
                    Sign in
                  </Text>
                )}
              </TouchableOpacity>

              {/* Register link */}
              <View className="flex-row justify-center mt-2">
                <Text className="text-muted text-sm">No account yet? </Text>
                <TouchableOpacity onPress={() => router.replace("/(auth)/register")}>
                  <Text className="text-brand-secondary text-sm font-medium">
                    Create one
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Calibrator access */}
              <View className="flex-row justify-center mt-4 pt-4 border-t border-bg-border">
                <TouchableOpacity
                  onPress={() => router.push("/(calibrator-auth)/login")}
                  className="items-center"
                >
                  <Text className="text-muted text-xs">
                    Participant à une étude de calibration ?{" "}
                    <Text className="text-teak font-medium">Accès calibrateur →</Text>
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>

          <AuthFooter />
        </KeyboardAvoidingView>
      </View>
    </ImageBackground>
  );
}
