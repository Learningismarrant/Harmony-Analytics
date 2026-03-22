import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useCalibPassation } from "@/features/calibration/hooks/useCalibPassation";
import { AssessmentHeader } from "@/features/assessment/components/session/AssessmentHeader";
import { AssessmentFooter } from "@/features/assessment/components/session/AssessmentFooter";
import { LikertQuestion } from "@/features/assessment/components/session/LikertQuestion";
import { RavenMatrix } from "@/features/assessment/components/session/RavenMatrix";
import { InstructionsView } from "@/features/assessment/components/session/InstructionsView";
import { QuestionCard } from "@/features/assessment/components/session/QuestionCard";
import type { CalibQuestionOut, RavenMatrixConfig } from "@harmony/types";

// ── Composant QCM inline ──────────────────────────────────────────────────────

interface QCMOption {
  key: string;
  text: string;
}

interface QCMQuestionProps {
  question: CalibQuestionOut;
  selectedIndex: number | undefined;
  onSelect: (index: number) => void;
}

function QCMQuestion({ question, selectedIndex, onSelect }: QCMQuestionProps) {
  const options = Array.isArray(question.options) ? (question.options as string[]) : [];
  const labels = ["A", "B", "C", "D", "E", "F"];

  return (
    <View style={{ gap: 10, paddingHorizontal: 20 }}>
      {options.map((text, idx) => {
        const isSelected = selectedIndex === idx;
        return (
          <TouchableOpacity
            key={idx}
            testID={`qcm-option-${idx}`}
            onPress={() => onSelect(idx)}
            activeOpacity={0.75}
            style={{
              flexDirection: "row",
              alignItems: "center",
              backgroundColor: isSelected ? "#A67C5222" : "#1A2C42",
              borderWidth: isSelected ? 2 : 1,
              borderColor: isSelected ? "#A67C52" : "#1E3050",
              borderRadius: 10,
              padding: 14,
              gap: 12,
            }}
          >
            <View
              style={{
                width: 28,
                height: 28,
                borderRadius: 14,
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: isSelected ? "#A67C52" : "#0D1B2A",
                borderWidth: 1,
                borderColor: isSelected ? "#A67C52" : "#1E3050",
              }}
            >
              <Text style={{ color: isSelected ? "#F1F4F8" : "#94A3B8", fontSize: 11, fontWeight: "800" }}>
                {labels[idx] ?? String(idx + 1)}
              </Text>
            </View>
            <Text style={{ flex: 1, color: "#CBD5E1", fontSize: 14, lineHeight: 20 }}>
              {text}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

// ── Composant bouton nav ──────────────────────────────────────────────────────

interface NavButtonProps {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "danger";
}

function NavButton({ label, onPress, disabled = false, variant = "secondary" }: NavButtonProps) {
  const bgColor = variant === "primary" ? "#A67C52" : variant === "danger" ? "#883838" : "#1A2C42";
  const borderColor = variant === "primary" ? "#A67C52" : variant === "danger" ? "#883838" : "#1E3050";

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.75}
      style={{
        flex: 1,
        paddingVertical: 14,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: disabled ? "#0D1B2A" : bgColor,
        borderWidth: 1,
        borderColor: disabled ? "#1E3050" : borderColor,
        borderRadius: 12,
        opacity: disabled ? 0.4 : 1,
      }}
    >
      <Text style={{ color: "#F1F4F8", fontSize: 12, fontWeight: "800", letterSpacing: 0.5 }}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

// ── Écran principal ───────────────────────────────────────────────────────────

export default function CalibSessionScreen() {
  const { sessionId, catalogueId } = useLocalSearchParams<{ sessionId: string; catalogueId: string }>();
  const router = useRouter();

  const {
    session,
    questions,
    isLoading,
    currentIndex,
    responses,
    isSubmitted,
    showInstructions,
    setShowInstructions,
    selectAnswer,
    goNext,
    goPrev,
    handleSubmit,
    submitMutation,
  } = useCalibPassation(Number(catalogueId), Number(sessionId));

  if (isLoading || !session) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#94A3B8" size="large" />
        <Text className="text-muted text-sm mt-4">Initialisation de la session...</Text>
      </View>
    );
  }

  // Instructions
  if (showInstructions) {
    return (
      <InstructionsView
        data={{
          name: "Briefing calibrateur",
          instructions: "Répondez avec franchise et spontanéité. Vos réponses aident à étalonner nos instruments psychométriques.",
        }}
        onStart={() => setShowInstructions(false)}
      />
    );
  }

  if (!questions || questions.length === 0) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center p-6">
        <Text className="text-muted text-sm text-center">Aucune question disponible pour ce catalogue.</Text>
      </View>
    );
  }

  const question = questions[currentIndex];
  if (!question) return null;

  const isFirst = currentIndex === 0;
  const isLast = currentIndex === questions.length - 1;

  // Render question input selon le type
  function renderQuestionInput() {
    if (question.question_type === "likert") {
      return (
        <LikertQuestion
          question={{
            id: question.id,
            test_id: 0,
            text: question.text,
            question_type: question.question_type,
            options: Array.isArray(question.options) ? (question.options as string[]) : null,
            trait: question.trait,
          }}
          selectedValue={responses[question.id] !== undefined ? String(responses[question.id]) : undefined}
          onSelect={(qId, value) => selectAnswer(qId, parseInt(value, 10))}
        />
      );
    }

    if (question.question_type === "raven") {
      const config = question.options as RavenMatrixConfig;
      if (!config || !config.matrix) return null;
      return (
        <ScrollView showsVerticalScrollIndicator={false}>
          <RavenMatrix
            config={config}
            selectedAnswer={responses[question.id] !== undefined ? String(responses[question.id]) : undefined}
            onSelect={(answerId) => {
              // Pour raven, l'answerId est une lettre ("A","B",...) mais on stocke l'index
              const opts = config.answer_options;
              const idx = opts.findIndex((o) => o.id === answerId);
              selectAnswer(question.id, idx >= 0 ? idx : 0);
            }}
          />
        </ScrollView>
      );
    }

    if (question.question_type === "qcm" || question.question_type === "qcm_timed") {
      return (
        <QCMQuestion
          question={question}
          selectedIndex={responses[question.id]}
          onSelect={(idx) => selectAnswer(question.id, idx)}
        />
      );
    }

    return (
      <Text className="text-muted text-sm text-center px-6">
        Type de question non supporté : {question.question_type}
      </Text>
    );
  }

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Header avec barre de progression */}
      <AssessmentHeader current={currentIndex} total={questions.length} />

      {/* Question */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingBottom: 24, flexGrow: 1, justifyContent: "center" }}
        showsVerticalScrollIndicator={false}
      >
        <QuestionCard
          questionText={question.text}
          questionNumber={currentIndex + 1}
          totalQuestions={questions.length}
        />

        {renderQuestionInput()}
      </ScrollView>

      {/* Navigation bas */}
      <View
        style={{
          paddingHorizontal: 20,
          paddingTop: 12,
          paddingBottom: 24,
          borderTopWidth: 1,
          borderTopColor: "#1E3050",
          flexDirection: "row",
          gap: 10,
        }}
      >
        <NavButton label="PRÉC." onPress={goPrev} disabled={isFirst} />
        {isLast ? (
          <NavButton
            label={submitMutation.isPending ? "ENVOI..." : "TERMINER"}
            onPress={handleSubmit}
            disabled={submitMutation.isPending}
            variant="primary"
          />
        ) : (
          <NavButton label="SUIV." onPress={goNext} variant="secondary" />
        )}
      </View>

      <AssessmentFooter />
    </View>
  );
}
