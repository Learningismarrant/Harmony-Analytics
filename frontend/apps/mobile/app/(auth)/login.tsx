import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";
import { authApi } from "@harmony/api";
import { useAuthStore } from "@/store/auth.store";
import { saveRefreshToken } from "@/lib/auth";
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

      // Mobile: save refresh token to SecureStore
      // Note: FastAPI returns it in the response body for mobile
      // (web uses HttpOnly cookie — mobile gets it in JSON)
      if ("refresh_token" in token) {
        await saveRefreshToken(token.refresh_token as string);
      }

      await login({
        accessToken: token.access_token,
        role: token.role as UserRole,
        crewProfileId: token.crew_profile_id,
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
    <KeyboardAvoidingView
      className="flex-1 bg-bg-primary"
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View className="flex-1 justify-center px-6">
        {/* Logo */}
        <View className="items-center mb-10">
          <View className="w-14 h-14 rounded-full bg-brand-primary/20 border border-brand-primary/40 items-center justify-center mb-3">
            <Text className="text-brand-primary font-bold text-2xl">H</Text>
          </View>
          <Text className="text-text-primary text-2xl font-bold">Harmony</Text>
          <Text className="text-muted text-sm mt-1">Candidate portal</Text>
        </View>

        {/* Form */}
        <View className="space-y-4">
          <View>
            <Text className="text-muted text-sm mb-1.5">Email</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3
                         text-text-primary text-base"
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
            <Text className="text-muted text-sm mb-1.5">Password</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3
                         text-text-primary text-base"
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
            className="bg-brand-primary rounded-xl py-4 items-center mt-2"
            style={{ opacity: loading ? 0.6 : 1 }}
          >
            {loading ? (
              <ActivityIndicator color="#07090F" />
            ) : (
              <Text className="text-bg-primary font-semibold text-base">Sign in</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
