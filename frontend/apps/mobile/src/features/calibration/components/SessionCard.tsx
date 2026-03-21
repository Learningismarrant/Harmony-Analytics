import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { CalibSessionOut } from "@harmony/types";

interface SessionCardProps {
  session: CalibSessionOut;
  catalogueName: string;
  onViewResult: () => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function SessionCard({ session, catalogueName, onViewResult }: SessionCardProps) {
  const isCompleted = session.status === "completed";
  const statusColor = isCompleted ? "#2E8A5C" : "#9A7030";
  const statusLabel = isCompleted ? "Complété" : "En cours";

  return (
    <View
      style={{
        backgroundColor: "#1A2C42",
        borderRadius: 12,
        borderWidth: 1,
        borderColor: "#1E3050",
        padding: 16,
        marginBottom: 12,
      }}
    >
      {/* Header */}
      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <Text
          style={{ color: "#F1F4F8", fontSize: 13, fontWeight: "700", flex: 1 }}
          numberOfLines={1}
        >
          {catalogueName}
        </Text>
        <View
          style={{
            paddingHorizontal: 8,
            paddingVertical: 3,
            borderRadius: 6,
            backgroundColor: `${statusColor}22`,
            marginLeft: 8,
          }}
        >
          <Text style={{ color: statusColor, fontSize: 9, fontWeight: "800", letterSpacing: 0.5 }}>
            {statusLabel.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Dates */}
      <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 4 }}>
        <Ionicons name="calendar-outline" size={11} color="#64748B" />
        <Text style={{ color: "#64748B", fontSize: 11 }}>
          Démarré le {formatDate(session.started_at)}
        </Text>
      </View>
      {isCompleted && session.completed_at && (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 4 }}>
          <Ionicons name="checkmark-circle-outline" size={11} color="#2E8A5C" />
          <Text style={{ color: "#64748B", fontSize: 11 }}>
            Terminé le {formatDate(session.completed_at)}
          </Text>
        </View>
      )}
      <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 12 }}>
        <Ionicons name="document-text-outline" size={11} color="#64748B" />
        <Text style={{ color: "#64748B", fontSize: 11 }}>
          {session.response_count} réponse(s) enregistrée(s)
        </Text>
      </View>

      {/* Action */}
      {isCompleted && (
        <TouchableOpacity
          onPress={onViewResult}
          style={{
            borderWidth: 1,
            borderColor: "#2E8A5C44",
            borderRadius: 8,
            paddingVertical: 8,
            alignItems: "center",
            backgroundColor: "#2E8A5C11",
          }}
        >
          <Text style={{ color: "#2E8A5C", fontSize: 11, fontWeight: "700", letterSpacing: 0.5 }}>
            VOIR LES RÉSULTATS
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
