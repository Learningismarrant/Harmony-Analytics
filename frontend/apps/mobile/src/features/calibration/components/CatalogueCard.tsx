import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { CalibCatalogueOut, CalibSessionOut } from "@harmony/types";

interface CatalogueCardProps {
  catalogue: CalibCatalogueOut;
  session: CalibSessionOut | null;
  onPress: () => void;
}

export function CatalogueCard({ catalogue, session, onPress }: CatalogueCardProps) {
  const isCompleted = session !== null && session.completed_at !== null;
  const isInProgress = session !== null && session.completed_at === null;

  const isEtalon = catalogue.status === "ETALON";
  const accentColor = isEtalon ? "#A67C52" : "#5B8DB8";

  function renderCTA() {
    if (isCompleted) {
      return (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
          <Text style={{ color: "#2E8A5C", fontSize: 10, fontWeight: "800", letterSpacing: 0.5 }}>
            COMPLÉTÉ
          </Text>
          <Ionicons name="checkmark-circle" size={13} color="#2E8A5C" />
        </View>
      );
    }
    if (isInProgress) {
      return (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
          <Text style={{ color: accentColor, fontSize: 10, fontWeight: "800", letterSpacing: 0.5 }}>
            REPRENDRE
          </Text>
          <Ionicons name="arrow-forward-circle" size={13} color={accentColor} />
        </View>
      );
    }
    return (
      <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
        <Text style={{ color: accentColor, fontSize: 10, fontWeight: "900", letterSpacing: 0.5 }}>
          COMMENCER
        </Text>
        <Ionicons name="chevron-forward" size={13} color={accentColor} />
      </View>
    );
  }

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.85}
      testID={`catalogue-card-${catalogue.id}`}
      style={{ opacity: isCompleted ? 0.8 : 1, marginBottom: 14 }}
    >
      <View
        style={{
          backgroundColor: "#1A2C42",
          borderRadius: 14,
          borderLeftWidth: 3,
          borderLeftColor: accentColor,
          borderTopWidth: 1,
          borderTopColor: "#1E3050",
          borderRightWidth: 1,
          borderRightColor: "#1E3050",
          borderBottomWidth: 1,
          borderBottomColor: "#1E3050",
          padding: 18,
          shadowColor: "#000",
          shadowOpacity: 0.15,
          shadowRadius: 8,
          elevation: 3,
        }}
      >
        {/* Header row */}
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
          <View style={{ flex: 1 }}>
            <Text
              style={{ color: "#F1F4F8", fontSize: 14, fontWeight: "800", letterSpacing: 0.5 }}
              numberOfLines={1}
            >
              {catalogue.name.toUpperCase()}
            </Text>

            {/* Badge ÉTALON / ALPHA */}
            <View
              style={{
                alignSelf: "flex-start",
                marginTop: 6,
                paddingHorizontal: 8,
                paddingVertical: 3,
                borderRadius: 6,
                backgroundColor: `${accentColor}22`,
              }}
            >
              <Text style={{ color: accentColor, fontSize: 9, fontWeight: "800", letterSpacing: 0.5 }}>
                {isEtalon ? "ÉTALON" : "ALPHA"}
              </Text>
            </View>
          </View>

          {/* Icon circle */}
          <View
            style={{
              width: 36,
              height: 36,
              borderRadius: 18,
              backgroundColor: `${accentColor}18`,
              borderWidth: 1,
              borderColor: `${accentColor}33`,
              alignItems: "center",
              justifyContent: "center",
              marginLeft: 12,
            }}
          >
            {isCompleted ? (
              <Ionicons name="checkmark" size={18} color="#2E8A5C" />
            ) : (
              <Ionicons name="layers-outline" size={17} color={accentColor} />
            )}
          </View>
        </View>

        {/* Description */}
        <Text
          style={{ color: "#94A3B8", fontSize: 12, lineHeight: 18, marginBottom: 14 }}
          numberOfLines={2}
        >
          {catalogue.description}
        </Text>

        {/* Footer */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            borderTopWidth: 1,
            borderTopColor: "#1E3050",
            paddingTop: 11,
          }}
        >
          {/* Question count */}
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <Ionicons name="help-circle-outline" size={11} color="#64748B" />
            <Text style={{ color: "#64748B", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
              {catalogue.n_questions} QUESTIONS
            </Text>
          </View>

          {/* CTA */}
          <View style={{ flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "flex-end" }}>
            {renderCTA()}
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}
