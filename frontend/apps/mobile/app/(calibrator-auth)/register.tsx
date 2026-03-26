import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  ScrollView,
  ImageBackground,
} from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";
import { calibrationApi } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import { saveCalibToken } from "@/features/auth/lib";
import { setAccessToken } from "@harmony/api";

export default function CalibratorRegisterScreen() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [cohort, setCohort] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    if (!name || !email || !password) {
      Alert.alert("Erreur", "Nom, email et mot de passe sont obligatoires.");
      return;
    }
    if (password.length < 8) {
      Alert.alert("Erreur", "Le mot de passe doit faire au moins 8 caractères.");
      return;
    }

    setLoading(true);
    try {
      const token = await calibrationApi.register({
        email: email.trim().toLowerCase(),
        name: name.trim(),
        password,
        ...(cohort.trim() ? { cohort: cohort.trim() } : {}),
      });

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
        "Inscription échouée",
        "Cet email est peut-être déjà utilisé. Veuillez réessayer.",
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
          <ScrollView
            style={{ flex: 1 }}
            contentContainerStyle={{ flexGrow: 1, justifyContent: "center", padding: 24 }}
            keyboardShouldPersistTaps="handled"
          >
            {/* Header */}
            <View className="items-center mb-8">
              <Text className="text-teak text-2xl font-black tracking-widest mb-1">
                RADIANT
              </Text>
              <Text className="text-ice text-sm font-semibold tracking-wider mb-4">
                Inscription calibrateur
              </Text>
              <View className="bg-bg-elevated border border-bg-border rounded-xl p-4">
                <Text className="text-muted text-xs text-center leading-5">
                  Vous participez à une étude scientifique d'étalonnage des tests
                  psychométriques. Vos données anonymisées contribuent à la validité
                  des instruments de mesure.
                </Text>
              </View>
            </View>

            {/* Form */}
            <View className="space-y-5">
              <View>
                <Text className="text-muted text-xs mb-2 tracking-widest uppercase">
                  Nom complet
                </Text>
                <TextInput
                  className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-4 text-text-primary text-base"
                  placeholder="Prénom Nom"
                  placeholderTextColor="#8FA3B8"
                  autoCapitalize="words"
                  value={name}
                  onChangeText={setName}
                />
              </View>

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
                  placeholder="8 caractères minimum"
                  placeholderTextColor="#8FA3B8"
                  secureTextEntry
                  value={password}
                  onChangeText={setPassword}
                />
              </View>

              <View>
                <Text className="text-muted text-xs mb-2 tracking-widest uppercase">
                  Cohorte{" "}
                  <Text className="text-muted text-xs normal-case font-normal">
                    (optionnel — fourni par le chercheur)
                  </Text>
                </Text>
                <TextInput
                  className="bg-bg-elevated border border-bg-border rounded-xl px-4 py-4 text-text-primary text-base"
                  placeholder="ex : ESMA-2025"
                  placeholderTextColor="#8FA3B8"
                  autoCapitalize="characters"
                  value={cohort}
                  onChangeText={setCohort}
                />
              </View>

              <TouchableOpacity
                onPress={handleRegister}
                disabled={loading}
                className="bg-teak rounded-xl py-4 items-center mt-6"
                style={{ opacity: loading ? 0.6 : 1 }}
              >
                {loading ? (
                  <ActivityIndicator color="#0D1B2A" />
                ) : (
                  <Text className="text-bg-primary font-semibold text-base tracking-widest uppercase">
                    Créer mon compte
                  </Text>
                )}
              </TouchableOpacity>

              <View className="flex-row justify-center mt-2">
                <Text className="text-muted text-sm">Déjà un compte ? </Text>
                <TouchableOpacity onPress={() => router.replace("/(calibrator-auth)/login")}>
                  <Text className="text-teak text-sm font-medium">Se connecter</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </View>
    </ImageBackground>
  );
}
