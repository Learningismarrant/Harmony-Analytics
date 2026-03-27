import { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  FlatList,
  ActivityIndicator,
  Modal,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibratorDemographicsIn } from "@harmony/types";
import {
  NATIONALITIES,
  YEARS_AT_SEA_OPTIONS,
  GENDER_OPTIONS,
  EDUCATION_OPTIONS,
  LANGUAGE_OPTIONS,
  YACHT_POSITION_OPTIONS,
} from "@harmony/types";

// ── Constantes ────────────────────────────────────────────────────────────────

const ITEM_HEIGHT = 44;

interface OptionItem {
  value: string;
  label: string;
}

const STEP_TITLES: Record<1 | 2 | 3, string> = {
  1: "Qui êtes-vous ?",
  2: "Votre parcours",
  3: "Contexte maritime",
};

// Birth date picker constants
const DAYS: number[] = Array.from({ length: 31 }, (_, i) => i + 1);
const MONTHS: string[] = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"];
const YEARS: number[] = Array.from({ length: 61 }, (_, i) => 1950 + i);

// ── Sous-composants ───────────────────────────────────────────────────────────

interface RadioGroupProps {
  options: readonly OptionItem[];
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

// ── Modal overlay wrapper ─────────────────────────────────────────────────────

function ModalOverlay({
  visible,
  onClose,
  children,
  withKeyboard = false,
}: {
  visible: boolean;
  onClose: () => void;
  children: React.ReactNode;
  withKeyboard?: boolean;
}) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableOpacity
        style={styles.modalBackdrop}
        activeOpacity={1}
        onPress={onClose}
      >
        {withKeyboard ? (
          <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            style={styles.modalKeyboardWrapper}
          >
            <TouchableOpacity activeOpacity={1} onPress={() => {}}>
              {children}
            </TouchableOpacity>
          </KeyboardAvoidingView>
        ) : (
          <TouchableOpacity activeOpacity={1} onPress={() => {}}>
            {children}
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    </Modal>
  );
}

// ── Birth date button ─────────────────────────────────────────────────────────

interface BirthDateButtonProps {
  day: number | null;
  month: number | null;
  year: number | null;
  onPress: () => void;
}

function BirthDateButton({ day, month, year, onPress }: BirthDateButtonProps) {
  const hasAll = day !== null && month !== null && year !== null;
  const label = hasAll
    ? `${String(day).padStart(2, "0")}/${String(month).padStart(2, "0")}/${year}`
    : "Sélectionner";

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8} style={styles.pickerButton}>
      <Text style={hasAll ? styles.pickerButtonValue : styles.pickerButtonPlaceholder}>
        {label}
      </Text>
      <Text style={styles.pickerChevron}>›</Text>
    </TouchableOpacity>
  );
}

// ── Birth date modal (3-column drum picker) ───────────────────────────────────

interface BirthDateModalProps {
  visible: boolean;
  day: number | null;
  month: number | null;
  year: number | null;
  onClose: () => void;
  onConfirm: (day: number, month: number, year: number) => void;
}

function BirthDateModal({ visible, day, month, year, onClose, onConfirm }: BirthDateModalProps) {
  const [pendingDay, setPendingDay] = useState<number>(day ?? 1);
  const [pendingMonth, setPendingMonth] = useState<number>(month ?? 6);
  const [pendingYear, setPendingYear] = useState<number>(year ?? 1985);

  const dayRef = useRef<FlatList<number>>(null);
  const monthRef = useRef<FlatList<string>>(null);
  const yearRef = useRef<FlatList<number>>(null);

  useEffect(() => {
    if (visible) {
      const initDay = day ?? 1;
      const initMonth = month ?? 6;
      const initYear = year ?? 1985;
      setPendingDay(initDay);
      setPendingMonth(initMonth);
      setPendingYear(initYear);

      const dayIdx = DAYS.indexOf(initDay);
      const monthIdx = initMonth - 1;
      const yearIdx = YEARS.indexOf(initYear);

      setTimeout(() => {
        if (dayIdx !== -1) {
          dayRef.current?.scrollToOffset({ offset: dayIdx * ITEM_HEIGHT, animated: false });
        }
        if (monthIdx !== -1) {
          monthRef.current?.scrollToOffset({ offset: monthIdx * ITEM_HEIGHT, animated: false });
        }
        if (yearIdx !== -1) {
          yearRef.current?.scrollToOffset({ offset: yearIdx * ITEM_HEIGHT, animated: false });
        }
      }, 80);
    }
  }, [visible, day, month, year]);

  function handleConfirm() {
    onConfirm(pendingDay, pendingMonth, pendingYear);
    onClose();
  }

  function makeScrollHandler<T>(
    data: T[],
    setter: (val: T) => void
  ) {
    return (e: { nativeEvent: { contentOffset: { y: number } } }) => {
      const idx = Math.round(e.nativeEvent.contentOffset.y / ITEM_HEIGHT);
      const clamped = Math.max(0, Math.min(idx, data.length - 1));
      setter(data[clamped]);
    };
  }

  const DRUM_HEIGHT = 220;
  const paddingV = DRUM_HEIGHT / 2 - ITEM_HEIGHT / 2;

  return (
    <ModalOverlay visible={visible} onClose={onClose}>
      <View style={styles.modalCard}>
        <Text style={styles.modalTitle}>Date de naissance</Text>

        <View style={[styles.drumRow, { height: DRUM_HEIGHT }]}>
          {/* Day column */}
          <View style={styles.drumColumn}>
            <View style={styles.drumHighlight} pointerEvents="none" />
            <FlatList
              ref={dayRef}
              data={DAYS}
              keyExtractor={(item) => String(item)}
              showsVerticalScrollIndicator={false}
              snapToInterval={ITEM_HEIGHT}
              decelerationRate="fast"
              getItemLayout={(_, index) => ({
                length: ITEM_HEIGHT,
                offset: ITEM_HEIGHT * index,
                index,
              })}
              onMomentumScrollEnd={makeScrollHandler(DAYS, setPendingDay)}
              style={styles.drumList}
              contentContainerStyle={{ paddingVertical: paddingV }}
              renderItem={({ item }) => {
                const isCenter = item === pendingDay;
                return (
                  <View style={styles.drumItem}>
                    <Text style={[styles.drumItemText, isCenter && styles.drumItemTextCenter]}>
                      {String(item).padStart(2, "0")}
                    </Text>
                  </View>
                );
              }}
            />
          </View>

          {/* Month column */}
          <View style={styles.drumColumn}>
            <View style={styles.drumHighlight} pointerEvents="none" />
            <FlatList
              ref={monthRef}
              data={MONTHS}
              keyExtractor={(item) => item}
              showsVerticalScrollIndicator={false}
              snapToInterval={ITEM_HEIGHT}
              decelerationRate="fast"
              getItemLayout={(_, index) => ({
                length: ITEM_HEIGHT,
                offset: ITEM_HEIGHT * index,
                index,
              })}
              onMomentumScrollEnd={makeScrollHandler(MONTHS, (label: string) => {
                setPendingMonth(MONTHS.indexOf(label) + 1);
              })}
              style={styles.drumList}
              contentContainerStyle={{ paddingVertical: paddingV }}
              renderItem={({ item }) => {
                const isCenter = MONTHS.indexOf(item) + 1 === pendingMonth;
                return (
                  <View style={styles.drumItem}>
                    <Text style={[styles.drumItemText, isCenter && styles.drumItemTextCenter]}>
                      {item}
                    </Text>
                  </View>
                );
              }}
            />
          </View>

          {/* Year column */}
          <View style={styles.drumColumn}>
            <View style={styles.drumHighlight} pointerEvents="none" />
            <FlatList
              ref={yearRef}
              data={YEARS}
              keyExtractor={(item) => String(item)}
              showsVerticalScrollIndicator={false}
              snapToInterval={ITEM_HEIGHT}
              decelerationRate="fast"
              getItemLayout={(_, index) => ({
                length: ITEM_HEIGHT,
                offset: ITEM_HEIGHT * index,
                index,
              })}
              onMomentumScrollEnd={makeScrollHandler(YEARS, setPendingYear)}
              style={styles.drumList}
              contentContainerStyle={{ paddingVertical: paddingV }}
              renderItem={({ item }) => {
                const isCenter = item === pendingYear;
                return (
                  <View style={styles.drumItem}>
                    <Text style={[styles.drumItemText, isCenter && styles.drumItemTextCenter]}>
                      {item}
                    </Text>
                  </View>
                );
              }}
            />
          </View>
        </View>

        <TouchableOpacity onPress={handleConfirm} style={styles.modalConfirmButton} activeOpacity={0.8}>
          <Text style={styles.modalConfirmText}>CONFIRMER</Text>
        </TouchableOpacity>
      </View>
    </ModalOverlay>
  );
}

// ── Years at sea modal ────────────────────────────────────────────────────────

interface YearsAtSeaButtonProps {
  selected: number | null;
  onPress: () => void;
}

function YearsAtSeaButton({ selected, onPress }: YearsAtSeaButtonProps) {
  const label = selected !== null
    ? YEARS_AT_SEA_OPTIONS.find((o) => o.value === selected)?.label ?? String(selected)
    : null;

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8} style={styles.pickerButton}>
      <Text style={label !== null ? styles.pickerButtonValue : styles.pickerButtonPlaceholder}>
        {label ?? "Sélectionner"}
      </Text>
      <Text style={styles.pickerChevron}>›</Text>
    </TouchableOpacity>
  );
}

interface YearsAtSeaModalProps {
  visible: boolean;
  selected: number | null;
  onClose: () => void;
  onSelect: (value: number) => void;
}

function YearsAtSeaModal({ visible, selected, onClose, onSelect }: YearsAtSeaModalProps) {
  function handleSelect(value: number) {
    onSelect(value);
    onClose();
  }

  return (
    <ModalOverlay visible={visible} onClose={onClose}>
      <View style={styles.modalCard}>
        <Text style={styles.modalTitle}>Années d'expérience en mer</Text>
        <FlatList
          data={YEARS_AT_SEA_OPTIONS}
          keyExtractor={(item) => String(item.value)}
          showsVerticalScrollIndicator={false}
          style={{ maxHeight: 300 }}
          renderItem={({ item }) => {
            const isSelected = selected === item.value;
            return (
              <TouchableOpacity
                onPress={() => handleSelect(item.value)}
                activeOpacity={0.75}
                style={[styles.listPickerItem, isSelected && styles.listPickerItemSelected]}
              >
                <Text style={[styles.listPickerItemText, isSelected && styles.listPickerItemTextSelected]}>
                  {item.label}
                </Text>
              </TouchableOpacity>
            );
          }}
        />
      </View>
    </ModalOverlay>
  );
}

// ── Nationality modal ─────────────────────────────────────────────────────────

interface NationalityButtonProps {
  selected: string;
  onPress: () => void;
}

function NationalityButton({ selected, onPress }: NationalityButtonProps) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8} style={styles.pickerButton}>
      <Text style={selected ? styles.pickerButtonValue : styles.pickerButtonPlaceholder}>
        {selected || "Sélectionner"}
      </Text>
      <Text style={styles.pickerChevron}>›</Text>
    </TouchableOpacity>
  );
}

interface NationalityModalProps {
  visible: boolean;
  selected: string;
  onClose: () => void;
  onSelect: (value: string) => void;
}

function NationalityModal({ visible, selected, onClose, onSelect }: NationalityModalProps) {
  const [search, setSearch] = useState("");

  const filtered = search.trim()
    ? NATIONALITIES.filter((n) =>
        n.toLowerCase().includes(search.trim().toLowerCase())
      )
    : NATIONALITIES;

  function handleSelect(value: string) {
    onSelect(value);
    onClose();
    setSearch("");
  }

  function handleClose() {
    onClose();
    setSearch("");
  }

  return (
    <ModalOverlay visible={visible} onClose={handleClose} withKeyboard>
      <View style={styles.modalCard}>
        <Text style={styles.modalTitle}>Nationalité</Text>

        <TextInput
          style={styles.modalSearchInput}
          value={search}
          onChangeText={setSearch}
          placeholder="Rechercher..."
          placeholderTextColor="#64748B"
          autoCorrect={false}
        />

        <FlatList
          data={filtered}
          keyExtractor={(item) => item}
          showsVerticalScrollIndicator={false}
          style={{ maxHeight: 280 }}
          keyboardShouldPersistTaps="handled"
          renderItem={({ item }) => {
            const isSelected = selected === item;
            return (
              <TouchableOpacity
                onPress={() => handleSelect(item)}
                activeOpacity={0.75}
                style={[styles.listPickerItem, isSelected && styles.listPickerItemSelected]}
              >
                <Text style={[styles.listPickerItemText, isSelected && styles.listPickerItemTextSelected]}>
                  {item}
                </Text>
              </TouchableOpacity>
            );
          }}
        />
      </View>
    </ModalOverlay>
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

// ── Profile summary card ──────────────────────────────────────────────────────

interface ProfileSummaryProps {
  me: {
    birth_date?: string | null;
    gender?: string | null;
    education_level?: string | null;
    years_at_sea?: number | null;
    nationality?: string | null;
    native_language?: string | null;
    maritime_role?: string | null;
  } | null | undefined;
}

function ProfileSummaryCard({ me }: ProfileSummaryProps) {
  function formatBirthDate(): string {
    if (me?.birth_date) {
      const parts = me.birth_date.split("-").map(Number);
      if (parts.length === 3) {
        const [y, m, d] = parts;
        return `${String(d).padStart(2, "0")}/${String(m).padStart(2, "0")}/${y}`;
      }
    }
    return "—";
  }

  function findLabel(options: readonly OptionItem[], value: string | null | undefined): string {
    if (!value) return "—";
    return options.find((o) => o.value === value)?.label ?? "—";
  }

  const rows: { label: string; value: string }[] = [
    { label: "Date de naissance", value: formatBirthDate() },
    { label: "Genre",             value: findLabel(GENDER_OPTIONS, me?.gender) },
    { label: "Niveau d'études",   value: findLabel(EDUCATION_OPTIONS, me?.education_level) },
    { label: "Années en mer",     value: me?.years_at_sea != null ? `${me.years_at_sea} ans` : "—" },
    { label: "Nationalité",       value: me?.nationality ?? "—" },
    { label: "Langue",            value: findLabel(LANGUAGE_OPTIONS, me?.native_language) },
    { label: "Rôle",              value: findLabel(YACHT_POSITION_OPTIONS, me?.maritime_role) },
  ];

  return (
    <View style={styles.summaryCard}>
      <Text style={styles.summaryHeader}>MON PROFIL</Text>
      {rows.map(({ label, value }) => {
        const isEmpty = value === "—";
        return (
          <View key={label} style={styles.summaryRow}>
            <Text style={styles.summaryLabel}>{label}</Text>
            <Text style={[styles.summaryValue, isEmpty && styles.summaryValueEmpty]}>
              {value}
            </Text>
          </View>
        );
      })}
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

  // Modal visibility
  const [showDateModal, setShowDateModal] = useState(false);
  const [showYearsAtSeaModal, setShowYearsAtSeaModal] = useState(false);
  const [showNationalityModal, setShowNationalityModal] = useState(false);

  // Form state — Step 1
  const [birthDay, setBirthDay] = useState<number | null>(null);
  const [birthMonth, setBirthMonth] = useState<number | null>(null);
  const [birthYear, setBirthYear] = useState<number | null>(null);
  const [gender, setGender] = useState("");

  // Form state — Step 2
  const [educationLevel, setEducationLevel] = useState("");
  const [yearsAtSea, setYearsAtSea] = useState<number | null>(null);

  // Form state — Step 3
  const [nationality, setNationality] = useState("");
  const [nationalityOther, setNationalityOther] = useState("");
  const [nativeLanguage, setNativeLanguage] = useState("");
  const [languageOther, setLanguageOther] = useState("");
  const [maritimeRole, setMaritimeRole] = useState("");

  const [saveSuccess, setSaveSuccess] = useState(false);

  // Pre-fill from existing data
  useEffect(() => {
    if (me) {
      if (me.birth_date) {
        const [y, m, d] = me.birth_date.split("-").map(Number);
        setBirthYear(y);
        setBirthMonth(m);
        setBirthDay(d);
      }
      if (me.years_at_sea !== undefined && me.years_at_sea !== null) {
        setYearsAtSea(me.years_at_sea);
      }
      if (me.nationality) setNationality(me.nationality);
      if (me.gender) setGender(me.gender);
      if (me.education_level) setEducationLevel(me.education_level);
      if (me.native_language) setNativeLanguage(me.native_language);
      if (me.maritime_role) setMaritimeRole(me.maritime_role);
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
    const payload: CalibratorDemographicsIn = {};

    if (birthDay && birthMonth && birthYear) {
      payload.birth_date = `${birthYear}-${String(birthMonth).padStart(2, "0")}-${String(birthDay).padStart(2, "0")}`;
    }

    if (yearsAtSea !== null) payload.years_at_sea = yearsAtSea;

    const resolvedNationality =
      nationality === "Autre" ? nationalityOther.trim() : nationality.trim();
    if (resolvedNationality) payload.nationality = resolvedNationality;

    if (gender) payload.gender = gender;
    if (educationLevel) payload.education_level = educationLevel;

    const resolvedLanguage =
      nativeLanguage === "other" ? languageOther.trim() : nativeLanguage;
    if (resolvedLanguage) payload.native_language = resolvedLanguage;

    if (maritimeRole) payload.maritime_role = maritimeRole;

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
    <>
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

        {/* Profile summary card */}
        <ProfileSummaryCard me={me} />

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
                <SectionLabel label="Date de naissance" />
                <BirthDateButton
                  day={birthDay}
                  month={birthMonth}
                  year={birthYear}
                  onPress={() => setShowDateModal(true)}
                />
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
                <YearsAtSeaButton
                  selected={yearsAtSea}
                  onPress={() => setShowYearsAtSeaModal(true)}
                />
              </View>
            </>
          )}

          {/* ── Step 3 : Contexte maritime ── */}
          {currentStep === 3 && (
            <>
              <View style={styles.fieldGroup}>
                <SectionLabel label="Nationalité" />
                <NationalityButton
                  selected={nationality}
                  onPress={() => setShowNationalityModal(true)}
                />
                {nationality === "Autre" && (
                  <TextInput
                    style={[styles.textInput, styles.otherInput]}
                    value={nationalityOther}
                    onChangeText={setNationalityOther}
                    placeholder="Préciser votre nationalité..."
                    placeholderTextColor="#64748B"
                  />
                )}
              </View>

              <View style={styles.fieldGroup}>
                <SectionLabel label="Langue maternelle" />
                <RadioGroup
                  options={LANGUAGE_OPTIONS}
                  selected={nativeLanguage}
                  onSelect={setNativeLanguage}
                  wrap
                />
                {nativeLanguage === "other" && (
                  <TextInput
                    style={[styles.textInput, styles.otherInput]}
                    value={languageOther}
                    onChangeText={setLanguageOther}
                    placeholder="Préciser votre langue..."
                    placeholderTextColor="#64748B"
                  />
                )}
              </View>

              <View style={[styles.fieldGroup, { marginBottom: 0 }]}>
                <SectionLabel label="Rôle maritime (si applicable)" />
                <RadioGroup
                  options={YACHT_POSITION_OPTIONS}
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

      {/* ── Modals (outside ScrollView to avoid z-index issues) ── */}
      <BirthDateModal
        visible={showDateModal}
        day={birthDay}
        month={birthMonth}
        year={birthYear}
        onClose={() => setShowDateModal(false)}
        onConfirm={(d, m, y) => {
          setBirthDay(d);
          setBirthMonth(m);
          setBirthYear(y);
        }}
      />

      <YearsAtSeaModal
        visible={showYearsAtSeaModal}
        selected={yearsAtSea}
        onClose={() => setShowYearsAtSeaModal(false)}
        onSelect={setYearsAtSea}
      />

      <NationalityModal
        visible={showNationalityModal}
        selected={nationality}
        onClose={() => setShowNationalityModal(false)}
        onSelect={setNationality}
      />
    </>
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
  // Profile summary card
  summaryCard: {
    backgroundColor: "#1A2C42",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1E3050",
    padding: 16,
    marginBottom: 16,
  },
  summaryHeader: {
    color: "#64748B",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1,
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 5,
  },
  summaryLabel: {
    color: "#64748B",
    fontSize: 11,
  },
  summaryValue: {
    color: "#CBD5E1",
    fontSize: 12,
    fontWeight: "600",
  },
  summaryValueEmpty: {
    color: "#475569",
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
  // Picker button (trigger for modals)
  pickerButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#0D1B2A",
    borderWidth: 1,
    borderColor: "#1E3050",
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  pickerButtonValue: {
    color: "#F1F4F8",
    fontSize: 14,
    fontWeight: "600",
    flex: 1,
  },
  pickerButtonPlaceholder: {
    color: "#64748B",
    fontSize: 14,
    flex: 1,
  },
  pickerChevron: {
    color: "#64748B",
    fontSize: 20,
    lineHeight: 22,
    transform: [{ rotate: "90deg" }],
  },
  // "Autre" inline text input
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
  otherInput: {
    marginTop: 10,
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
  // Modal
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.7)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  modalKeyboardWrapper: {
    width: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  modalCard: {
    backgroundColor: "#1A2C42",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1E3050",
    padding: 20,
    width: "100%",
  },
  modalTitle: {
    color: "#F1F4F8",
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 0.3,
    marginBottom: 16,
    textAlign: "center",
  },
  modalConfirmButton: {
    backgroundColor: "#A67C52",
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 16,
  },
  modalConfirmText: {
    color: "#F1F4F8",
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0.5,
  },
  // Drum picker (birth date)
  drumRow: {
    flexDirection: "row",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#1E3050",
    overflow: "hidden",
  },
  drumColumn: {
    flex: 1,
    position: "relative",
  },
  drumHighlight: {
    position: "absolute",
    left: 0,
    right: 0,
    top: "50%",
    marginTop: -ITEM_HEIGHT / 2,
    height: ITEM_HEIGHT,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: "#A67C52",
    backgroundColor: "rgba(166,124,82,0.15)",
    zIndex: 1,
  },
  drumList: {
    flex: 1,
  },
  drumItem: {
    height: ITEM_HEIGHT,
    alignItems: "center",
    justifyContent: "center",
  },
  drumItemText: {
    color: "#64748B",
    fontSize: 14,
    fontWeight: "500",
  },
  drumItemTextCenter: {
    color: "#F1F4F8",
    fontSize: 16,
    fontWeight: "800",
  },
  // List picker (years at sea, nationality)
  listPickerItem: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#1E3050",
    borderLeftWidth: 3,
    borderLeftColor: "transparent",
  },
  listPickerItemSelected: {
    borderLeftColor: "#A67C52",
    backgroundColor: "#A67C5211",
  },
  listPickerItemText: {
    color: "#94A3B8",
    fontSize: 14,
    fontWeight: "500",
  },
  listPickerItemTextSelected: {
    color: "#F1F4F8",
    fontWeight: "700",
  },
  // Nationality search input
  modalSearchInput: {
    backgroundColor: "#0D1B2A",
    borderWidth: 1,
    borderColor: "#1E3050",
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    color: "#F1F4F8",
    fontSize: 13,
    marginBottom: 12,
  },
});
