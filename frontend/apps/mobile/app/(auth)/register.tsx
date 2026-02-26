import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ScrollView,
  ActivityIndicator,
} from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";
import { authApi } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import { saveRefreshToken } from "@/features/auth/lib";
import type { UserRole, YachtPosition } from "@harmony/types";

const POSITIONS: YachtPosition[] = [
  "Deckhand",
  "Bosun",
  "First Mate",
  "Captain",
  "Chief Stewardess",
  "Stewardess",
  "Chef",
  "Chief Engineer",
  "2nd Engineer",
];

export default function RegisterScreen() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [position, setPosition] = useState<YachtPosition>("Deckhand");
  const [experienceYears, setExperienceYears] = useState("0");
  const [showPositionPicker, setShowPositionPicker] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    if (!name.trim() || name.trim().length < 2) {
      Alert.alert("Error", "Name must be at least 2 characters.");
      return;
    }
    if (!email.trim()) {
      Alert.alert("Error", "Please enter your email.");
      return;
    }
    if (password.length < 6) {
      Alert.alert("Error", "Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert("Error", "Passwords do not match.");
      return;
    }

    const years = parseInt(experienceYears, 10);
    if (isNaN(years) || years < 0) {
      Alert.alert("Error", "Experience years must be a positive number.");
      return;
    }

    setLoading(true);
    try {
      const token = await authApi.registerCrew({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        position_targeted: position,
        experience_years: years,
      });

      await saveRefreshToken(token.refresh_token);
      await login({
        accessToken: token.access_token,
        role: token.role as UserRole,
        crewProfileId: token.profile_id,
        name: name.trim(),
      });

      router.replace("/(candidate)/profile");
    } catch {
      Alert.alert(
        "Registration failed",
        "This email may already be in use. Please try again.",
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
      <ScrollView
        contentContainerStyle={{ padding: 24, paddingBottom: 40 }}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo */}
        <View className="items-center mb-8 mt-8">
          <View className="w-14 h-14 rounded-full bg-brand-primary/20 border border-brand-primary/40 items-center justify-center mb-3">
            <Text className="text-brand-primary font-bold text-2xl">H</Text>
          </View>
          <Text className="text-text-primary text-2xl font-bold">Create account</Text>
          <Text className="text-muted text-sm mt-1">Join Harmony as a crew member</Text>
        </View>

        {/* Form */}
        <View className="space-y-4">
          {/* Full name */}
          <View>
            <Text className="text-muted text-sm mb-1.5">Full name</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3 text-text-primary text-base"
              placeholder="John Smith"
              placeholderTextColor="#8FA3B8"
              autoCapitalize="words"
              value={name}
              onChangeText={setName}
            />
          </View>

          {/* Email */}
          <View>
            <Text className="text-muted text-sm mb-1.5">Email</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3 text-text-primary text-base"
              placeholder="your@email.com"
              placeholderTextColor="#8FA3B8"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              value={email}
              onChangeText={setEmail}
            />
          </View>

          {/* Password */}
          <View>
            <Text className="text-muted text-sm mb-1.5">Password</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3 text-text-primary text-base"
              placeholder="••••••••"
              placeholderTextColor="#8FA3B8"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />
          </View>

          {/* Confirm password */}
          <View>
            <Text className="text-muted text-sm mb-1.5">Confirm password</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3 text-text-primary text-base"
              placeholder="••••••••"
              placeholderTextColor="#8FA3B8"
              secureTextEntry
              value={confirmPassword}
              onChangeText={setConfirmPassword}
            />
          </View>

          {/* Position */}
          <View>
            <Text className="text-muted text-sm mb-1.5">Position targeted</Text>
            <TouchableOpacity
              onPress={() => setShowPositionPicker(!showPositionPicker)}
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3 flex-row justify-between items-center"
            >
              <Text className="text-text-primary text-base">{position}</Text>
              <Text className="text-muted text-sm">{showPositionPicker ? "▲" : "▼"}</Text>
            </TouchableOpacity>
            {showPositionPicker && (
              <View className="bg-bg-elevated border border-bg-border rounded-xl mt-1 overflow-hidden">
                {POSITIONS.map((pos) => (
                  <TouchableOpacity
                    key={pos}
                    onPress={() => {
                      setPosition(pos);
                      setShowPositionPicker(false);
                    }}
                    className="px-4 py-3 border-b border-bg-border"
                    style={{ borderBottomWidth: pos === POSITIONS[POSITIONS.length - 1] ? 0 : 1 }}
                  >
                    <Text
                      style={{ color: pos === position ? "#4A90B8" : "#E8EFF7" }}
                      className="text-base"
                    >
                      {pos}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          {/* Experience years */}
          <View>
            <Text className="text-muted text-sm mb-1.5">Years of experience</Text>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-3 text-text-primary text-base"
              placeholder="0"
              placeholderTextColor="#8FA3B8"
              keyboardType="numeric"
              value={experienceYears}
              onChangeText={setExperienceYears}
            />
          </View>

          {/* Submit */}
          <TouchableOpacity
            onPress={handleRegister}
            disabled={loading}
            className="bg-brand-primary rounded-xl py-4 items-center mt-2"
            style={{ opacity: loading ? 0.6 : 1 }}
          >
            {loading ? (
              <ActivityIndicator color="#07090F" />
            ) : (
              <Text className="text-bg-primary font-semibold text-base">Create account</Text>
            )}
          </TouchableOpacity>

          {/* Sign in link */}
          <View className="flex-row justify-center mt-2">
            <Text className="text-muted text-sm">Already have an account? </Text>
            <TouchableOpacity onPress={() => router.replace("/(auth)/login")}>
              <Text className="text-brand-primary text-sm font-medium">Sign in</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
