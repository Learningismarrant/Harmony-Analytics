import React from "react";
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  useWindowDimensions,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type {
  CalibCatalogueOut,
  CalibSessionOut,
  CatalogueDomain,
} from "@harmony/types";
import { CatalogueCard } from "./CatalogueCard";
import {
  DOMAIN_LABELS,
  DOMAIN_ICONS,
  DOMAIN_COLORS,
} from "./ConstellationMap";

// ─── Domain descriptions ───────────────────────────────────────────────────────
const DOMAIN_DESCRIPTIONS: Record<CatalogueDomain, string> = {
  personality:  "Vos traits de personnalité fondamentaux",
  cognitive:    "Vos aptitudes et capacités de raisonnement",
  motivation:   "Ce qui vous pousse à agir et vous engage",
  person_job:   "L'adéquation entre vos besoins et votre poste",
  person_org:   "Votre compatibilité avec la culture du yacht",
  person_team:  "La qualité de vos relations avec votre équipe",
  physical:     "Vos capacités physiques et de mobilité",
};

// ─── Props ─────────────────────────────────────────────────────────────────────
interface DomainSheetProps {
  domain: CatalogueDomain | null;
  catalogues: CalibCatalogueOut[];
  sessions: CalibSessionOut[];
  onClose: () => void;
  onCataloguePress: (catalogue: CalibCatalogueOut) => void;
}

export function DomainSheet({
  domain,
  catalogues,
  sessions,
  onClose,
  onCataloguePress,
}: DomainSheetProps) {
  const { height } = useWindowDimensions();
  const sheetHeight = Math.round(height * 0.62);

  const isVisible = domain !== null;

  const domainCatalogues = isVisible
    ? catalogues.filter((c) => (c.domain ?? "personality") === domain)
    : [];

  function getSession(catalogueId: number): CalibSessionOut | null {
    return sessions.find((s) => s.catalogue_id === catalogueId) ?? null;
  }

  if (!isVisible) return null;

  const color = DOMAIN_COLORS[domain];
  const icon = DOMAIN_ICONS[domain];
  const label = DOMAIN_LABELS[domain].replace("\n", " ");
  const description = DOMAIN_DESCRIPTIONS[domain];

  return (
    <Modal
      visible={isVisible}
      transparent
      animationType="slide"
      statusBarTranslucent
      onRequestClose={onClose}
    >
      {/* Backdrop semi-transparent */}
      <TouchableOpacity
        style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.55)" }}
        activeOpacity={1}
        onPress={onClose}
      />

      {/* Sheet */}
      <View
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: sheetHeight,
          backgroundColor: "#0D1B2A",
          borderTopLeftRadius: 20,
          borderTopRightRadius: 20,
          borderTopWidth: 1,
          borderLeftWidth: 1,
          borderRightWidth: 1,
          borderColor: "#1A2C42",
          overflow: "hidden",
          // Shadow iOS
          shadowColor: "#000",
          shadowOffset: { width: 0, height: -4 },
          shadowOpacity: 0.4,
          shadowRadius: 16,
          // Elevation Android
          elevation: 16,
        }}
      >
        {/* Drag handle */}
        <View style={{ alignItems: "center", paddingTop: 10, paddingBottom: 4 }}>
          <View
            style={{
              width: 36,
              height: 4,
              borderRadius: 2,
              backgroundColor: "rgba(255,255,255,0.18)",
            }}
          />
        </View>

        {/* Header */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "flex-start",
            paddingHorizontal: 20,
            paddingTop: 10,
            paddingBottom: 14,
            borderBottomWidth: 1,
            borderBottomColor: "#1A2C42",
          }}
        >
          {/* Icône domaine */}
          <View
            style={{
              width: 40,
              height: 40,
              borderRadius: 20,
              backgroundColor: `${color}1A`,
              borderWidth: 1,
              borderColor: `${color}44`,
              alignItems: "center",
              justifyContent: "center",
              marginRight: 12,
              marginTop: 2,
            }}
          >
            <Ionicons name={icon} size={20} color={color} />
          </View>

          {/* Textes */}
          <View style={{ flex: 1 }}>
            <Text
              style={{
                color: "#F1F4F8",
                fontSize: 15,
                fontWeight: "800",
                marginBottom: 3,
              }}
            >
              {label}
            </Text>
            <Text style={{ color: "#64748B", fontSize: 11, lineHeight: 16 }}>
              {description}
            </Text>
          </View>

          {/* Bouton fermer */}
          <TouchableOpacity
            onPress={onClose}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={{
              width: 28,
              height: 28,
              borderRadius: 14,
              backgroundColor: "rgba(255,255,255,0.08)",
              alignItems: "center",
              justifyContent: "center",
              marginLeft: 8,
              marginTop: 2,
            }}
          >
            <Ionicons name="close" size={16} color="#94A3B8" />
          </TouchableOpacity>
        </View>

        {/* Contenu */}
        {domainCatalogues.length === 0 ? (
          <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
            <Ionicons name="telescope-outline" size={32} color="#1A2C42" />
            <Text
              style={{
                color: "#64748B",
                fontSize: 13,
                marginTop: 12,
                textAlign: "center",
              }}
            >
              Aucun catalogue dans ce domaine
            </Text>
          </View>
        ) : (
          <ScrollView
            contentContainerStyle={{ padding: 16, paddingBottom: Platform.OS === "ios" ? 40 : 24 }}
            showsVerticalScrollIndicator={false}
          >
            {domainCatalogues.map((catalogue) => (
              <CatalogueCard
                key={catalogue.id}
                catalogue={catalogue}
                session={getSession(catalogue.id)}
                onPress={() => {
                  onClose();
                  onCataloguePress(catalogue);
                }}
              />
            ))}
          </ScrollView>
        )}
      </View>
    </Modal>
  );
}
