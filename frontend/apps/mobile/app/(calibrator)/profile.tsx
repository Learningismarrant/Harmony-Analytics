import { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibratorDemographicsIn } from "@harmony/types";

// ── Types locaux pour les options ─────────────────────────────────────────────

type FieldKey = keyof CalibratorDemographicsIn;

interface OptionItem {
  value: string;
  label: string;
}

const GENDER_OPTIONS: OptionItem[] = [
  { value: "male", label: "Homme" },
  { value: "female", label: "Femme" },
  { value: "non_binary", label: "Non-binaire" },
  { value: "prefer_not_to_say", label: "Préfère ne pas répondre" },
];

const EDUCATION_OPTIONS: OptionItem[] = [
  { value: "below_bac", label: "< Bac" },
  { value: "bac", label: "Bac" },
  { value: "bac_plus_2", label: "Bac+2" },
  { value: "bac_plus_3", label: "Bac+3" },
  { value: "bac_plus_5", label: "Bac+5" },
  { value: "phd", label: "Doctorat" },
];

const LANGUAGE_OPTIONS: OptionItem[] = [
  { value: "french", label: "Français" },
  { value: "english", label: "Anglais" },
  { value: "other", label: "Autre" },
];

const MARITIME_ROLE_OPTIONS: OptionItem[] = [
  { value: "captain", label: "Capitaine" },
  { value: "officer", label: "Officier" },
  { value: "bosun", label: "Bosco" },
  { value: "deckhand", label: "Matelot" },
  { value: "steward", label: "Steward/ess" },
  { value: "engineer", label: "Ingénieur" },
  { value: "other", label: "Autre" },
  { value: "none", label: "Aucun" },
];

// ── Sous-composants ───────────────────────────────────────────────────────────

interface RadioGroupProps {
  options: OptionItem[];
  selected: string;
  onSelect: (value: string) => void;
  wrap?: boolean;
}

function RadioGroup({ options, selected, onSelect, wrap = false }: RadioGroupProps) {
  return (
    <View style={[styles.radioGroup, wrap && styles.radioGroupWrap]}>
      {options.map((opt) => {
        const isSelected = selected === opt.value;
        return (
          <TouchableOpacity
            key={opt.value}
            onPress={() => onSelect(opt.value)}
            activeOpacity={0.75}
            style={[
              styles.radioButton,
              isSelected && styles.radioButtonSelected,
              wrap && styles.radioButtonWrap,
            ]}
          >
            <Text style={[styles.radioLabel, isSelected && styles.radioLabelSelected]}>
              {opt.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

interface SectionLabelProps {
  label: string;
}

function SectionLabel({ label }: SectionLabelProps) {
  return (
    <Text style={styles.fieldLabel}>{label}</Text>
  );
}

// ── Écran principal ───────────────────────────────────────────────────────────

export default function CalibProfileScreen() {
  const queryClient = useQueryClient();

  const { data: me, isLoading } = useQuery({
    queryKey: calibrationQueryKeys.me(),
    queryFn: () => calibrationApi.getMe(),
  });

  // État local du formulaire
  const [birthYear, setBirthYear] = useState("");
  const [yearsAtSea, setYearsAtSea] = useState("");
  const [nationality, setNationality] = useState("");
  const [gender, setGender] = useState("");
  const [educationLevel, setEducationLevel] = useState("");
  const [nativeLanguage, setNativeLanguage] = useState("");
  const [maritimeRole, setMaritimeRole] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Pré-remplir depuis les données existantes
  useEffect(() => {
    if (me) {
      if (me.age) setBirthYear(String(new Date().getFullYear() - me.age));
      if (me.years_experience) setYearsAtSea(String(me.years_experience));
      if (me.nationality) setNationality(me.nationality);
      if (me.gender) setGender(me.gender);
      if (me.education_level) setEducationLevel(me.education_level);
    }
  }, [me]);

  const patchMutation = useMutation({
    mutationFn: (data: CalibratorDemographicsIn) => calibrationApi.updateDemographics(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.me() });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  function handleSave() {
    const currentYear = new Date().getFullYear();
    const payload: CalibratorDemographicsIn = {};

    if (birthYear.trim()) {
      const yearNum = parseInt(birthYear.trim(), 10);
      if (!isNaN(yearNum) && yearNum > 1900 && yearNum < currentYear) {
        payload.age = currentYear - yearNum;
      }
    }
    if (yearsAtSea.trim()) {
      const n = parseInt(yearsAtSea.trim(), 10);
      if (!isNaN(n)) payload.years_experience = n;
    }
    if (nationality.trim()) payload.nationality = nationality.trim();
    if (gender) payload.gender = gender;
    if (educationLevel) payload.education_level = educationLevel;
    if (nativeLanguage) payload.occupation = nativeLanguage; // mapped to occupation as native_language proxy
    if (maritimeRole) payload.cohort = maritimeRole; // mapped to cohort as maritime_role proxy

    patchMutation.mutate(payload);
  }

  if (isLoading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color="#94A3B8" size="large" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ padding: 20, paddingBottom: 48 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Section identité */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>IDENTITÉ</Text>

        <View style={styles.identityRow}>
          <Text style={styles.identityLabel}>Nom</Text>
          <Text style={styles.identityValue}>{me?.name ?? "—"}</Text>
        </View>
        <View style={[styles.identityRow, { borderBottomWidth: 0 }]}>
          <Text style={styles.identityLabel}>Email</Text>
          <Text style={styles.identityValue}>{me?.email ?? "—"}</Text>
        </View>
        {me?.cohort && (
          <View style={[styles.identityRow, { borderBottomWidth: 0 }]}>
            <Text style={styles.identityLabel}>Cohorte</Text>
            <Text style={styles.identityValue}>{me.cohort}</Text>
          </View>
        )}
      </View>

      {/* Intro DIF */}
      <View style={styles.difCard}>
        <Text style={styles.difText}>
          Ces informations nous permettent de vérifier que nos tests ne sont pas discriminants
          (analyse DIF — Differential Item Functioning).
        </Text>
      </View>

      {/* Section démographiques */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>DONNÉES DÉMOGRAPHIQUES</Text>

        {/* Année de naissance */}
        <View style={styles.fieldGroup}>
          <SectionLabel label="Année de naissance" />
          <TextInput
            style={styles.textInput}
            value={birthYear}
            onChangeText={setBirthYear}
            keyboardType="numeric"
            placeholder="ex: 1990"
            placeholderTextColor="#64748B"
            maxLength={4}
          />
        </View>

        {/* Années en mer */}
        <View style={styles.fieldGroup}>
          <SectionLabel label="Années d'expérience en mer" />
          <TextInput
            style={styles.textInput}
            value={yearsAtSea}
            onChangeText={setYearsAtSea}
            keyboardType="numeric"
            placeholder="ex: 5"
            placeholderTextColor="#64748B"
            maxLength={2}
          />
        </View>

        {/* Nationalité */}
        <View style={styles.fieldGroup}>
          <SectionLabel label="Nationalité" />
          <TextInput
            style={styles.textInput}
            value={nationality}
            onChangeText={setNationality}
            placeholder="ex: Française"
            placeholderTextColor="#64748B"
          />
        </View>

        {/* Genre */}
        <View style={styles.fieldGroup}>
          <SectionLabel label="Genre" />
          <RadioGroup options={GENDER_OPTIONS} selected={gender} onSelect={setGender} wrap />
        </View>

        {/* Niveau d'études */}
        <View style={styles.fieldGroup}>
          <SectionLabel label="Niveau d'études" />
          <RadioGroup options={EDUCATION_OPTIONS} selected={educationLevel} onSelect={setEducationLevel} wrap />
        </View>

        {/* Langue maternelle */}
        <View style={styles.fieldGroup}>
          <SectionLabel label="Langue maternelle" />
          <RadioGroup options={LANGUAGE_OPTIONS} selected={nativeLanguage} onSelect={setNativeLanguage} />
        </View>

        {/* Rôle maritime */}
        <View style={[styles.fieldGroup, { marginBottom: 0 }]}>
          <SectionLabel label="Rôle maritime (si applicable)" />
          <RadioGroup options={MARITIME_ROLE_OPTIONS} selected={maritimeRole} onSelect={setMaritimeRole} wrap />
        </View>
      </View>

      {/* Message succès */}
      {saveSuccess && (
        <View style={styles.successBanner}>
          <Text style={styles.successText}>Mis à jour ✓</Text>
        </View>
      )}

      {/* Bouton sauvegarder */}
      <TouchableOpacity
        onPress={handleSave}
        disabled={patchMutation.isPending}
        style={[styles.saveButton, patchMutation.isPending && styles.saveButtonDisabled]}
        activeOpacity={0.8}
      >
        <Text style={styles.saveButtonText}>
          {patchMutation.isPending ? "Enregistrement..." : "ENREGISTRER"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0D1B2A",
  },
  centered: {
    flex: 1,
    backgroundColor: "#0D1B2A",
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    backgroundColor: "#1A2C42",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#1E3050",
    padding: 20,
    marginBottom: 16,
  },
  sectionTitle: {
    color: "#64748B",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.5,
    marginBottom: 16,
  },
  identityRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#1E3050",
  },
  identityLabel: {
    color: "#64748B",
    fontSize: 12,
    fontWeight: "600",
  },
  identityValue: {
    color: "#CBD5E1",
    fontSize: 12,
    fontWeight: "700",
  },
  difCard: {
    backgroundColor: "#A67C5211",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#A67C5233",
    padding: 14,
    marginBottom: 16,
  },
  difText: {
    color: "#94A3B8",
    fontSize: 11,
    lineHeight: 17,
    fontStyle: "italic",
  },
  fieldGroup: {
    marginBottom: 20,
  },
  fieldLabel: {
    color: "#CBD5E1",
    fontSize: 12,
    fontWeight: "700",
    marginBottom: 10,
  },
  textInput: {
    backgroundColor: "#0D1B2A",
    borderWidth: 1,
    borderColor: "#1E3050",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: "#F1F4F8",
    fontSize: 14,
  },
  radioGroup: {
    flexDirection: "row",
    gap: 8,
  },
  radioGroupWrap: {
    flexWrap: "wrap",
  },
  radioButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#1E3050",
    backgroundColor: "#0D1B2A",
  },
  radioButtonSelected: {
    borderColor: "#A67C52",
    backgroundColor: "#A67C5222",
  },
  radioButtonWrap: {
    marginBottom: 4,
  },
  radioLabel: {
    color: "#94A3B8",
    fontSize: 11,
    fontWeight: "600",
  },
  radioLabelSelected: {
    color: "#A67C52",
    fontWeight: "800",
  },
  successBanner: {
    backgroundColor: "#2E8A5C22",
    borderWidth: 1,
    borderColor: "#2E8A5C44",
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
    marginBottom: 16,
  },
  successText: {
    color: "#2E8A5C",
    fontSize: 13,
    fontWeight: "700",
  },
  saveButton: {
    backgroundColor: "#A67C52",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    color: "#F1F4F8",
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0.5,
  },
});
