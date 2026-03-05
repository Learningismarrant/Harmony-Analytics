/**
 * Harmony Design System — Palette officielle
 *
 * Navy + White (primaires) · Silver (secondaire) · Teak (accent prestige)
 *
 * Usage direct (inline styles) : import { Colors } from "@/constants/Colors"
 * Usage NativeWind (className)  : classes définies dans tailwind.config.js
 */
export const Colors = {
  // --- PALETTE PRINCIPALE ---
  navy: '#1A2C42',         // Bleu Nocturne velouté — fond principal
  navyDeep: '#0D1B2A',     // Sous le navy (fond le plus sombre)
  navyElevated: '#243347', // Navy clair — cartes, modales

  // Silver "Titanium" : gris métallique froid et pur
  silver: '#94A3B8',
  // Silver Light : reflets et textes fins
  silverLight: '#CBD5E1',

  // Teak Wood : ambre profond, cuir, prestige
  teak: '#A67C52',
  teakLight: '#C4945C',    // Teak plus lumineux (hover / glow)

  white: '#FFFFFF',
  ice: '#F1F4F8',          // Ice Brume — surfaces légères
  slate: '#718096',        // Slate Fumée — secondaire plus sombre

  // --- STATUTS COHÉRENTS ---
  success: '#5A8279',      // Vert Eucalyptus
  error: '#9C6B6B',        // Terre d'Ombre rouge
  warning: '#A68D6A',      // Ocre Doré

  // --- SYSTÈME DE FEEDBACK ---
  // Mode Recrutement (Analytique / Décisionnel)
  recruiterAction: '#1A2C42', // Navy
  recruiterBg: '#F1F4F8',

  // Mode Manager (Humain / Développement)
  managerAction: '#A67C52',   // Teak
  managerBg: '#FAF5F0',

  // Statuts avec polarité
  AdviceGood: '#5A8279',       // Eucalyptus
  AdviceNeutral: '#94A3B8',    // Silver
  AdviceWarning: '#9C6B6B',    // Terre d'ombre

  // --- STRUCTURE ---
  border: 'rgba(26, 44, 66, 0.12)',  // Navy très transparent
  shadow: '#1A2C42',                  // Ombre navy (pas noir pur)

  // Utilitaires
  teakOverlay: 'rgba(166, 124, 82, 0.10)',
  overlay: 'rgba(13, 27, 42, 0.88)', // Modales / "lock" — base navyDeep
};
