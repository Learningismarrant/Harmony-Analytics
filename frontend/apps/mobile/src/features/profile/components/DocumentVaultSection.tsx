import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

// TODO: Replace with real document data from API
// Shape: DocumentOut[] from backend GET /identity/full-profile
const MOCK_DOCUMENTS = [
  {
    id: 1,
    title: "Passport",
    document_type: "passport",
    uploaded_at: "2024-01-15T10:00:00Z",
    is_verified: true,
    expiry_date: "2031-01-14",
  },
  {
    id: 2,
    title: "STCW Basic Safety Training",
    document_type: "stcw",
    uploaded_at: "2024-03-20T14:30:00Z",
    is_verified: true,
    expiry_date: "2029-03-19",
  },
  {
    id: 3,
    title: "ENG1 Medical Certificate",
    document_type: "medical",
    uploaded_at: "2025-09-05T09:15:00Z",
    is_verified: false,
    expiry_date: "2026-09-04",
  },
  {
    id: 4,
    title: "CV — Updated 2025",
    document_type: "cv",
    uploaded_at: "2025-11-01T16:00:00Z",
    is_verified: false,
    expiry_date: null,
  },
];

const STCW_REQUIRED = [
  { label: "Basic Safety Training", done: true },
  { label: "STCW Advanced Fire Fighting", done: false },
  { label: "Medical First Aid", done: false },
  { label: "Proficiency in Survival Craft", done: false },
];

const DOC_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  passport: "card-outline",
  stcw: "shield-outline",
  medical: "medkit-outline",
  cv: "document-text-outline",
  other: "document-outline",
};

const DOC_LABELS: Record<string, string> = {
  passport: "Passport",
  stcw: "STCW Certificate",
  medical: "Medical Certificate",
  cv: "CV",
  other: "Document",
};

function expiryColor(expiry: string | null): string {
  if (!expiry) return "#94A3B8";
  const daysLeft = Math.floor((new Date(expiry).getTime() - Date.now()) / 86400000);
  if (daysLeft < 90) return "#9C6B6B";
  if (daysLeft < 180) return "#A68D6A";
  return "#5A8279";
}

function formatExpiry(expiry: string | null): string {
  if (!expiry) return "No expiry";
  return `Exp. ${new Date(expiry).toLocaleDateString("en-GB", { month: "short", year: "numeric" })}`;
}

export function DocumentVaultSection() {
  // TODO: const { data: profile } = useQuery(queryKeys.identity.fullProfile(crewProfileId))
  // TODO: const documents = profile?.documents ?? []
  const documents = MOCK_DOCUMENTS;

  return (
    <View className="gap-y-4">
      {/* STCW compliance checklist */}
      <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5">
        <View className="flex-row items-center mb-4 gap-x-2">
          <Ionicons name="shield-checkmark-outline" size={16} color="#A67C52" />
          <Text className="text-text-primary text-sm font-semibold">STCW Compliance</Text>
          <View className="ml-auto px-2 py-0.5 rounded-full" style={{ backgroundColor: "#A67C5233" }}>
            <Text style={{ color: "#A67C52", fontSize: 10, fontWeight: "600" }}>
              1 / {STCW_REQUIRED.length}
            </Text>
          </View>
        </View>

        {STCW_REQUIRED.map((item, i) => (
          <View
            key={item.label}
            className="flex-row items-center py-3"
            style={{
              borderBottomWidth: i < STCW_REQUIRED.length - 1 ? 1 : 0,
              borderBottomColor: "#1E3050",
            }}
          >
            <View
              className="w-5 h-5 rounded-full items-center justify-center mr-3"
              style={{
                backgroundColor: item.done ? "#5A827922" : "#1E3050",
                borderWidth: 1.5,
                borderColor: item.done ? "#5A8279" : "#1E3050",
              }}
            >
              {item.done && <Ionicons name="checkmark" size={11} color="#5A8279" />}
            </View>
            <Text
              className="text-sm flex-1"
              style={{ color: item.done ? "#F1F4F8" : "#718096" }}
            >
              {item.label}
            </Text>
          </View>
        ))}
      </View>

      {/* Document list */}
      <View className="flex-row items-center justify-between">
        <Text className="text-muted text-xs tracking-widest uppercase">
          {documents.length} document{documents.length !== 1 ? "s" : ""}
        </Text>
        <TouchableOpacity
          className="flex-row items-center gap-x-1.5 px-3 py-1.5 rounded-lg"
          style={{ backgroundColor: "#A67C5233", borderWidth: 1, borderColor: "#A67C5255" }}
          onPress={() => {}} // TODO: open document picker / upload
        >
          <Ionicons name="cloud-upload-outline" size={14} color="#A67C52" />
          <Text style={{ color: "#A67C52", fontSize: 12, fontWeight: "600" }}>Upload</Text>
        </TouchableOpacity>
      </View>

      <View className="bg-bg-secondary border border-bg-border rounded-2xl overflow-hidden">
        {documents.map((doc, i) => {
          const expColor = expiryColor(doc.expiry_date);
          return (
            <TouchableOpacity
              key={doc.id}
              className="flex-row items-center px-4 py-3.5"
              style={{
                borderBottomWidth: i < documents.length - 1 ? 1 : 0,
                borderBottomColor: "#1E3050",
              }}
              onPress={() => {}} // TODO: open DocumentViewerModal
            >
              {/* Icon */}
              <View
                className="w-10 h-10 rounded-xl items-center justify-center mr-3"
                style={{ backgroundColor: "#1A2C42" }}
              >
                <Ionicons
                  name={DOC_ICONS[doc.document_type] ?? "document-outline"}
                  size={18}
                  color="#94A3B8"
                />
              </View>

              {/* Info */}
              <View className="flex-1">
                <Text className="text-text-primary text-sm font-medium">{doc.title}</Text>
                <View className="flex-row items-center gap-x-2 mt-0.5">
                  <Text className="text-slate text-xs">
                    {DOC_LABELS[doc.document_type] ?? doc.document_type}
                  </Text>
                  <Text className="text-slate text-xs">·</Text>
                  <Text className="text-xs" style={{ color: expColor }}>
                    {formatExpiry(doc.expiry_date)}
                  </Text>
                </View>
              </View>

              {/* Status */}
              <View className="items-end ml-2">
                {doc.is_verified ? (
                  <View
                    className="px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: "#5A827933" }}
                  >
                    <Text style={{ color: "#5A8279", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
                      VERIFIED
                    </Text>
                  </View>
                ) : (
                  <View
                    className="px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: "#A68D6A33" }}
                  >
                    <Text style={{ color: "#A68D6A", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
                      PENDING
                    </Text>
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Info note */}
      <View className="flex-row items-start gap-x-2 px-1">
        <Ionicons name="lock-closed-outline" size={13} color="#718096" style={{ marginTop: 1 }} />
        <Text className="text-muted text-xs leading-4 flex-1">
          Your documents are encrypted and only shared with employers after your explicit approval.
        </Text>
      </View>
    </View>
  );
}
