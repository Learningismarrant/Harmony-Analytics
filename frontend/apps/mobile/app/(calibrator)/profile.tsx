import { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  FlatList,
  ActivityIndicator,
  StyleSheet,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibratorDemographicsIn } from "@harmony/types";

// ── Constantes ────────────────────────────────────────────────────────────────

const BIRTH_YEARS: number[] = Array.from({ length: 61 }, (_, i) => 1950 + i); // 1950–2010

const YEARS_AT_SEA_OPTIONS: Array<{ value: number; label: string }> = [
  { value: 0, label: "0" },
  { value: 1, label: "1" },
  { value: 2, label: "2" },
  { value: 3, label: "3" },
  { value: 5, label: "5" },
  { value: 10, label: "10" },
  { value: 15, label: "15" },
  { value: 20, label: "20" },
  { value: 25, label: "25" },
  { value: 30, label: "30+" },
];

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

const STEP_TITLES: Record<1 | 2 | 3, string> = {
  1: "Qui êtes-vous ?",
  2: "Votre parcours",
  3: "Contexte maritime",
};

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

function SectionLabel({ label }: { label: string }) {
  return <Text style={styles.fieldLabel}>{label}</Text>;
}

// ── Year picker ───────────────────────────────────────────────────────────────

interface YearPickerProps {
  selectedYear: number | null;
  onSelect: (year: number) => void;
}

function YearPicker({ selectedYear, onSelect }: YearPickerProps) {
  const flatListRef = useRef<FlatList<number>>(null);

  useEffect(() => {
    if (selectedYear !== null) {
      const idx = BIRTH_YEARS.indexOf(selectedYear);
      if (idx !== -1 && flatListRef.current) {
        // Small delay so the list has time to mount before scrolling
        setTimeout(() => {
          flatListRef.current?.scrollToIndex({ index: idx, animated: false, viewPosition: 0.5 });
        }, 80);
      }
    }
  }, [selectedYear]);

  return (
    <FlatList
      ref={flatListRef}
      data={BIRTH_YEARS}
      horizontal
      keyExtractor={(item) => String(item)}
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.yearPickerContent}
      getItemLayout={(_, index) => ({ length: 64, offset: 64 * index, index })}
      onScrollToIndexFailed={() => {
        // Silently ignore — occurs only if list not yet laid out
      }}
      renderItem={({ item }) => {
        const isSelected = item === selectedYear;
        return (
          <TouchableOpacity
            onPress={() => onSelect(item)}
            activeOpacity={0.75}
            style={[styles.yearItem, isSelected && styles.yearItemSelected]}
          >
            <Text style={[styles.yearText, isSelected && styles.yearTextSelected]}>
              {item}
            </Text>
          </TouchableOpacity>
        );
      }}
    />
  );
}

// ── Years-at-sea chip picker ──────────────────────────────────────────────────

interface YearsAtSeaPickerProps {
  selected: number | null;
  onSelect: (value: number) => void;
}

function YearsAtSeaPicker({ selected, onSelect }: YearsAtSeaPickerProps) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.yearPickerContent}
    >
      {YEARS_AT_SEA_OPTIONS.map((opt) => {
        const isSelected = selected === opt.value;
        return (
          <TouchableOpacity
            key={opt.value}
            onPress={() => onSelect(opt.value)}
            activeOpacity={0.75}
            style={[styles.yearItem, isSelected && styles.yearItemSelected]}
          >
            <Text style={[styles.yearText, isSelected && styles.yearTextSelected]}>
              {opt.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
}

// ── Step indicator ────────────────────────────────────────────────────────────

interface StepIndicatorProps {
  current: 1 | 2 | 3;
}

function StepIndicator({ current }: StepIndicatorProps) {
  return (
    <View style={styles.stepIndicatorRow}>
      {([1, 2, 3] as const).map((n) => (
        <View
          key={n}
          style={[styles.stepDot, current === n && styles.stepDotActive]}
        />
      ))}
    </View>
  );
}

// ── Écran principal ───────────────────────────────────────────────────────────

export default function CalibProfileScreen() {
  const queryClient = useQueryClient();

  const { data: me, isLoading } = useQuery({
    queryKey: calibrationQueryKeys.me(),
    queryFn: () => calibrationApi.getMe(),
  });

  // Stepper state
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Form state — Step 1
  const [birthYear, setBirthYear] = useState<number | null>(null);
  const [gender, setGender] = useState("");

  // Form state — Step 2
  const [educationLevel, setEducationLevel] = useState("");
  const [yearsAtSea, setYearsAtSea] = useState<number | null>(null);

  // Form state — Step 3
  const [nationality, setNationality] = useState("");
  const [nativeLanguage, setNativeLanguage] = useState("");
  const [maritimeRole, setMaritimeRole] = useState("");

  const [saveSuccess, setSaveSuccess] = useState(false);

  // Pre-fill from existing data
  useEffect(() => {
    if (me) {
      if (me.age) setBirthYear(new Date().getFullYear() - me.age);
      if (me.years_experience !== undefined && me.years_experience !== null) {
        setYearsAtSea(me.years_experience);
      }
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

  function buildPayload(): CalibratorDemographicsIn {
    const currentYear = new Date().getFullYear();
    const payload: CalibratorDemographicsIn = {};

    if (birthYear !== null) {
      const age = currentYear - birthYear;
      if (age > 0 && age < 120) payload.age = age;
    }
    if (yearsAtSea !== null) payload.years_experience = yearsAtSea;
    if (nationality.trim()) payload.nationality = nationality.trim();
    if (gender) payload.gender = gender;
    if (educationLevel) payload.education_level = educationLevel;
    if (nativeLanguage) payload.occupation = nativeLanguage; // mapped to occupation as native_language proxy
    if (maritimeRole) payload.cohort = maritimeRole; // mapped to cohort as maritime_role proxy

    return payload;
  }

  function handleNext() {
    if (currentStep < 3) setCurrentStep((s) => (s + 1) as 1 | 2 | 3);
  }

  function handlePrev() {
    if (currentStep > 1) setCurrentStep((s) => (s - 1) as 1 | 2 | 3);
  }

  function handleSave() {
    patchMutation.mutate(buildPayload());
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
      {/* Section identité — read-only */}
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

      {/* DIF notice */}
      <View style={styles.difCard}>
        <Text style={styles.difText}>
          Ces informations nous permettent de vérifier que nos tests ne sont pas discriminants
          (analyse DIF — Differential Item Functioning).
        </Text>
      </View>

      {/* Stepper card */}
      <View style={styles.card}>
        {/* Step indicator */}
        <StepIndicator current={currentStep} />

        {/* Step title */}
        <Text style={styles.stepTitle}>{STEP_TITLES[currentStep]}</Text>

        {/* ── Step 1 : Qui êtes-vous ? ── */}
        {currentStep === 1 && (
          <>
            <View style={styles.fieldGroup}>
              <SectionLabel label="Année de naissance" />
              <YearPicker selectedYear={birthYear} onSelect={setBirthYear} />
              {birthYear !== null && (
                <Text style={styles.yearHint}>Sélectionné : {birthYear}</Text>
              )}
            </View>

            <View style={[styles.fieldGroup, { marginBottom: 0 }]}>
              <SectionLabel label="Genre" />
              <RadioGroup options={GENDER_OPTIONS} selected={gender} onSelect={setGender} wrap />
            </View>
          </>
        )}

        {/* ── Step 2 : Votre parcours ── */}
        {currentStep === 2 && (
          <>
            <View style={styles.fieldGroup}>
              <SectionLabel label="Niveau d'études" />
              <RadioGroup
                options={EDUCATION_OPTIONS}
                selected={educationLevel}
                onSelect={setEducationLevel}
                wrap
              />
            </View>

            <View style={[styles.fieldGroup, { marginBottom: 0 }]}>
              <SectionLabel label="Années d'expérience en mer" />
              <YearsAtSeaPicker selected={yearsAtSea} onSelect={setYearsAtSea} />
            </View>
          </>
        )}

        {/* ── Step 3 : Contexte maritime ── */}
        {currentStep === 3 && (
          <>
            <View style={styles.fieldGroup}>
              <SectionLabel label="Nationalité" />
              <View style={styles.textInputRow}>
                <TextInput
                  style={[styles.textInput, { flex: 1 }]}
                  value={nationality}
                  onChangeText={setNationality}
                  placeholder="ex: Française"
                  placeholderTextColor="#64748B"
                />
                {nationality.length > 0 && (
                  <TouchableOpacity
                    onPress={() => setNationality("")}
                    style={styles.clearButton}
                    activeOpacity={0.7}
                  >
                    <Text style={styles.clearButtonText}>✕</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>

            <View style={styles.fieldGroup}>
              <SectionLabel label="Langue maternelle" />
              <RadioGroup
                options={LANGUAGE_OPTIONS}
                selected={nativeLanguage}
                onSelect={setNativeLanguage}
              />
            </View>

            <View style={[styles.fieldGroup, { marginBottom: 0 }]}>
              <SectionLabel label="Rôle maritime (si applicable)" />
              <RadioGroup
                options={MARITIME_ROLE_OPTIONS}
                selected={maritimeRole}
                onSelect={setMaritimeRole}
                wrap
              />
            </View>
          </>
        )}

        {/* Navigation buttons */}
        <View style={styles.navRow}>
          {currentStep > 1 && (
            <TouchableOpacity
              onPress={handlePrev}
              style={styles.navButtonSecondary}
              activeOpacity={0.8}
            >
              <Text style={styles.navButtonSecondaryText}>PRÉCÉDENT</Text>
            </TouchableOpacity>
          )}

          {currentStep < 3 && (
            <TouchableOpacity
              onPress={handleNext}
              style={[styles.navButtonSecondary, currentStep === 1 && { flex: 1 }]}
              activeOpacity={0.8}
            >
              <Text style={styles.navButtonSecondaryText}>SUIVANT</Text>
            </TouchableOpacity>
          )}

          {currentStep === 3 && (
            <TouchableOpacity
              onPress={handleSave}
              disabled={patchMutation.isPending}
              style={[
                styles.saveButton,
                { flex: 1 },
                patchMutation.isPending && styles.saveButtonDisabled,
              ]}
              activeOpacity={0.8}
            >
              <Text style={styles.saveButtonText}>
                {patchMutation.isPending ? "Enregistrement..." : "ENREGISTRER"}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Success banner */}
      {saveSuccess && (
        <View style={styles.successBanner}>
          <Text style={styles.successText}>Mis à jour ✓</Text>
        </View>
      )}
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
  // Step indicator
  stepIndicatorRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 8,
    marginBottom: 14,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#1E3050",
    borderWidth: 1,
    borderColor: "#2A4060",
  },
  stepDotActive: {
    backgroundColor: "#A67C52",
    borderColor: "#A67C52",
  },
  stepTitle: {
    color: "#F1F4F8",
    fontSize: 16,
    fontWeight: "800",
    marginBottom: 24,
    textAlign: "center",
  },
  // Fields
  fieldGroup: {
    marginBottom: 20,
  },
  fieldLabel: {
    color: "#CBD5E1",
    fontSize: 12,
    fontWeight: "700",
    marginBottom: 10,
  },
  // Year picker
  yearPickerContent: {
    paddingVertical: 4,
    gap: 6,
  },
  yearItem: {
    width: 58,
    height: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#1E3050",
    backgroundColor: "#0D1B2A",
    alignItems: "center",
    justifyContent: "center",
  },
  yearItemSelected: {
    borderColor: "#A67C52",
    backgroundColor: "#A67C5222",
  },
  yearText: {
    color: "#94A3B8",
    fontSize: 12,
    fontWeight: "600",
  },
  yearTextSelected: {
    color: "#A67C52",
    fontWeight: "800",
  },
  yearHint: {
    color: "#64748B",
    fontSize: 11,
    marginTop: 8,
    textAlign: "center",
  },
  // TextInput with clear button
  textInputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
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
  clearButton: {
    width: 36,
    height: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#1E3050",
    backgroundColor: "#0D1B2A",
    alignItems: "center",
    justifyContent: "center",
  },
  clearButtonText: {
    color: "#64748B",
    fontSize: 13,
    fontWeight: "700",
  },
  // Radio chips
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
  // Navigation
  navRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 28,
  },
  navButtonSecondary: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#2A4060",
    backgroundColor: "#0D1B2A",
  },
  navButtonSecondaryText: {
    color: "#94A3B8",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.5,
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
  // Success
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
});
