# Harmony — Frontend

Interface utilisateur de la plateforme Harmony Analytics.

**Stack :** Turborepo · Next.js 15 · Expo SDK 52 · React Three Fiber · D3-force · TanStack Query v5 · Zustand · NativeWind · shadcn/ui

---

## Table des matières

1. [Architecture](#architecture)
2. [Packages partagés](#packages-partagés)
3. [Applications](#applications)
4. [Démarrage rapide](#démarrage-rapide)
5. [Modèle de sécurité auth](#modèle-de-sécurité-auth)
6. [Sociogramme 3D](#sociogramme-3d)
7. [Travail restant](#travail-restant)

---

## Architecture

Le frontend est un **monorepo Turborepo** avec deux applications et trois packages internes.

```
frontend/
├── apps/
│   ├── web/                    # Next.js 15 — dashboard employeur
│   └── mobile/                 # Expo SDK 52 — app candidat iOS/Android
│
├── packages/
│   ├── types/                  # Miroirs TypeScript de tous les schémas Pydantic backend
│   ├── api/                    # Client Axios + clés TanStack Query + endpoints typés
│   └── ui/                     # Design tokens (thème maritime sombre)
│
├── turbo.json
├── tsconfig.base.json
└── package.json
```

### Flux de données

```
Component → useQuery/useMutation → @harmony/api → Axios (avec token Bearer)
                                                 → FastAPI backend (port 8000)
```

### Convention de nommage

| Dossier / fichier | Contenu |
|---|---|
| `app/(auth)/` | Pages publiques — login, register |
| `app/(candidate)/` | Pages protégées candidat — tabs Expo Router |
| `src/features/<feature>/components/` | Composants React par fonctionnalité (feature-centered) |
| `src/features/<feature>/hooks/` | Hooks personnalisés par fonctionnalité |
| `src/shared/` | Composants et utilitaires transverses |

---

## Packages partagés

### `@harmony/types`

Miroir TypeScript de l'intégralité des schémas Pydantic du backend. Source unique de vérité pour les types partagés entre web et mobile.

Fichier principal : [`packages/types/src/index.ts`](packages/types/src/index.ts)

Types exportés : `UserRole`, `YachtPosition`, `AvailabilityStatus`, `TokenOut`, `UserIdentityOut`, `FullCrewProfileOut`, `TestInfoOut`, `QuestionOut`, `SubmitTestIn`, `TestResultOut`, `YachtOut`, `CampaignOut`, `MatchResultOut`, `SociogramOut`, `SociogramNode`, `SociogramEdge`, `SimulationPreviewOut`, `SurveyOut`, `SurveyResponseIn`, `DashboardOut`, `HarmonyMetrics`, …

### `@harmony/api`

Client Axios configuré avec refresh token silencieux + modules d'endpoints typés + factory de clés de cache TanStack Query.

```
packages/api/src/
├── client.ts               # Instance Axios — refresh automatique sur 401
└── endpoints/
    ├── auth.ts             # login, register, refresh, me, logout
    ├── assessment.ts       # catalogue, questions, submit, results
    ├── crew.ts             # dashboard, sociogram, assign, pulse
    ├── identity.ts         # profile, update, experiences
    ├── recruitment.ts      # campaigns, matching, simulate, hire, reject
    └── vessel.ts           # CRUD yachts, environment update
```

Usage :
```typescript
import { assessmentApi, queryKeys } from "@harmony/api";

const { data } = useQuery({
  queryKey: queryKeys.assessment.catalogue(),
  queryFn: () => assessmentApi.getCatalogue(),
});
```

### `@harmony/ui`

Tokens de design du thème maritime sombre. Utilisables dans les deux apps.

Couleurs principales :

| Token | Valeur | Usage |
|-------|--------|-------|
| `colors.bg.primary` | `#07090F` | Fond général |
| `colors.bg.secondary` | `#0B1018` | Cards |
| `colors.brand.primary` | `#4A90B8` | CTA, accents (maritime steel blue) |
| `colors.brand.secondary` | `#50528A` | Psychométrie (muted slate-indigo) |
| `colors.sociogram.excellent` | `#2E8A5C` | Edge score ≥ 80 |
| `colors.sociogram.good` | `#5A8A30` | Edge score 65–80 |
| `colors.sociogram.moderate` | `#9A7030` | Edge score 45–65 |
| `colors.sociogram.weak` | `#883838` | Edge score < 45 |

Helpers :
```typescript
import { dyadScoreToColor, dyadScoreToThickness } from "@harmony/ui";
// Renvoient des entiers hex THREE.Color-compatibles
```

---

## Applications

### `apps/web` — Dashboard employeur

**Déploiement :** Vercel

Architecture feature-centered (`src/features/<feature>/`) — chaque module regroupe composants, hooks et tests co-localisés :
- `features/auth/` — store Zustand + hook `useAuth`
- `features/sociogram/` — composants R3F + `physics.ts` + hooks `useCockpit`
- `features/recruitment/` — `CampaignPanel` (+ sous-composants) + hooks `useCampaigns`, `useMatching`
- `features/vessel/` — `CockpitStrip` + hooks `useVessel`, `useSimulation`
- `shared/` — `Sidebar`, `providers.tsx`, `query-client.ts`

| Route | Description |
|---|---|
| `/login` | Authentification employeur |
| `/register` | Création de compte *(à construire)* |
| `/dashboard` | Vue flotte — liste des yachts |
| `/vessel/[id]` | Cockpit — sociogramme 3D + CampaignPanel + simulation |

#### Sociogramme 3D

Intégré dans `/vessel/[id]`. Combine :
- **D3-force** pour la physique 3D (positions calculées CPU)
- **React Three Fiber** pour le rendu GPU (WebGL)
- **OrbitControls** pour la navigation
- **Simulation d'impact** : drag-and-drop d'un candidat dans la molécule → calcul des deltas F_team en temps réel

Architecture des composants (`src/features/sociogram/components/`) :

```
SociogramCanvas              # Canvas R3F + boucle physique + HUD
├── CrewNode                 # Sphère pulsante — taille ∝ P_ind, couleur ∝ score
├── DyadEdge                 # Cylindre — épaisseur + couleur ∝ dyad_score
├── NodeInfoPanel            # Panel info flottant — scores, dyades, CTA simuler
└── SimulationOverlay        # Overlay résultat simulation — ΔF_team, flags, embauche
```

Physics engine : [`src/features/sociogram/physics.ts`](apps/web/src/features/sociogram/physics.ts)

### `apps/mobile` — Application candidat

**Déploiement :** EAS Build (iOS + Android)

| Route | Description |
|---|---|
| `/(auth)/login` | Authentification candidat |
| `/(candidate)/profile` | Profil, Big Five, expériences |
| `/(candidate)/assessment` | Catalogue des tests psychométriques |
| `/(candidate)/assessment/[testId]` | Passation — question par question, chronomètre |
| `/(candidate)/assessment/result` | Résultat immédiat post-soumission |
| `/(candidate)/applications` | Candidatures en cours *(à compléter)* |

---

## Démarrage rapide

### Prérequis

- Node.js ≥ 20
- npm ≥ 11
- Backend FastAPI démarré sur le port 8000

### Installation

```bash
cd frontend
npm install
```

### Web

```bash
cp apps/web/.env.example apps/web/.env.local
# Éditer .env.local : NEXT_PUBLIC_API_URL=http://localhost:8000

npx turbo dev --filter=@harmony/web
# → http://localhost:3000
```

### Mobile

```bash
cp apps/mobile/.env.example apps/mobile/.env
# Éditer .env : EXPO_PUBLIC_API_URL=http://localhost:8000

cd apps/mobile
npx expo start
# Scanner le QR code avec Expo Go (iOS/Android)
```

### Tests web

```bash
cd frontend/apps/web
npm test
# → 126 tests, 13 suites, 0 failures
```

### Build complet

```bash
cd frontend
npx turbo build          # Build toutes les apps
npx turbo type-check     # Vérification TypeScript
```

---

## Modèle de sécurité auth

| Surface | Refresh token | Access token |
|---------|--------------|--------------|
| Web | HttpOnly cookie (jamais accessible via JS) | Zustand en mémoire uniquement |
| Mobile | `expo-secure-store` (chiffré sur le device) | Zustand en mémoire uniquement |

**Flux :**
1. Login → backend retourne `access_token` (JSON) + `refresh_token` (cookie HttpOnly pour web, JSON pour mobile)
2. L'access token est stocké en mémoire Zustand **uniquement** — jamais dans `localStorage`
3. À chaque requête : intercepteur Axios injecte `Authorization: Bearer <token>`
4. Sur 401 : intercepteur tente un refresh silencieux via `/auth/refresh`, re-queue les requêtes
5. Si le refresh échoue : `clearAccessToken()` + redirection vers `/login`
6. Sur fermeture d'onglet/redémarrage app : l'access token est perdu, le refresh token permet de restaurer la session

**Implémentation :**
- Web : [`apps/web/src/features/auth/store.ts`](apps/web/src/features/auth/store.ts)
- Mobile : [`apps/mobile/src/lib/auth.ts`](apps/mobile/src/lib/auth.ts)
- Client : [`packages/api/src/client.ts`](packages/api/src/client.ts) (intercepteur 401)

---

## Sociogramme 3D

### Concept

La molécule représente l'équipage actif d'un yacht. Chaque **nœud** (sphère) est un marin, chaque **arête** (cylindre) une relation dyadique entre deux membres.

| Propriété visuelle | Source de données | Signification |
|---|---|---|
| Taille du nœud | `SociogramNode.p_ind` | Performance individuelle potentielle |
| Couleur du nœud | `p_ind` par tranches | Vert ≥ 75 · Ambre ≥ 55 · Rouge < 55 |
| Épaisseur de l'arête | `SociogramEdge.dyad_score` | Intensité de la relation |
| Couleur de l'arête | `dyad_score` | Vert = synergie · Rouge = friction |
| Distance entre nœuds | `1 - dyad_score / 100` via D3-force | Plus proches = plus compatibles |

### Mode simulation

1. Clic sur un nœud → `NodeInfoPanel` → bouton "Simuler l'ajout à l'équipage"
2. Appel `GET /crew/{yacht_id}/simulate/{crew_profile_id}` → `SimulationPreviewOut`
3. Le candidat apparaît en violet dans la molécule avec ses arêtes virtuelles
4. `SimulationOverlay` affiche ΔF_team, Δcohésion, flags de risque
5. CTA "Embaucher" → décision enregistrée + recalcul snapshot

### Données requises (backend)

```
GET /crew/{yacht_id}/sociogram   → SociogramOut
GET /crew/{yacht_id}/simulate/{crewProfileId} → SimulationPreviewOut
```

Ces deux endpoints n'existent pas encore — voir [Travail restant](#travail-restant).

---

## Travail restant

### 🔴 Bloquant (backend — manquant)

Ces endpoints sont appelés par le frontend mais n'existent pas encore dans le backend :

| Endpoint | Schema de réponse | Implémentation backend |
|---|---|---|
| `GET /crew/{yacht_id}/sociogram` | `SociogramOut` | Appeler `engine/benchmarking/matrice.py::compute_sociogram()` |
| `GET /crew/{yacht_id}/simulate/{id}` | `SimulationPreviewOut` | Appeler `matrice.py::compute_candidate_preview()` |
| `POST /auth/logout` | `void` | Supprimer le cookie `refresh_token` côté serveur |
| Auth mobile | — | `/auth/refresh` doit accepter le token en header `Authorization: Refresh <token>` (pas seulement en cookie) pour React Native |

### 🔴 Bloquant (bugs backend existants)

| Bug | Fichier | Fix |
|---|---|---|
| `SurveyTriggerIn` sans champ `yacht_id` | `app/modules/survey/schemas.py` | Ajouter `yacht_id: int` |
| Mismatch méthode VesselService | `app/modules/vessel/router.py` | `get_all_for_owner` → `get_all_for_employer`, `create(owner_id)` → `create(employer)` |

### 🟠 Priorité haute (pages manquantes — web)

| Page | Route | Description |
|---|---|---|
| Register | `/register` | Formulaire inscription employeur |
| Gestion yacht | `/vessel/[id]` | Détail yacht + sliders paramètres JD-R (F_env) + vecteur capitaine (F_lmx) |
| Campagnes | `/recruitment` | Liste des campagnes, création, archivage |
| Candidats | `/recruitment/[id]` | Vue candidature individuelle + décision hire/reject |
| Intégration simulation | sociogram | Connecter `hireMutation` dans `SociogramCanvas` avec le vrai endpoint + campaign context |

### 🟠 Priorité haute (fonctionnalités manquantes — mobile)

| Fonctionnalité | Fichier cible | Description |
|---|---|---|
| Survey / pulse | `app/(candidate)/survey.tsx` | Formulaire réponse survey + daily pulse |
| Edit profil | `app/(candidate)/profile.tsx` | Formulaire PATCH /identity/me (nom, téléphone, lieu) |
| Ajout expérience | `app/(candidate)/profile.tsx` | Formulaire POST /identity/me/experiences |
| Invite campaign | `app/(candidate)/invite/[token].tsx` | Landing page lien d'invitation deep link |
| Candidate applications | `app/(candidate)/applications/index.tsx` | Connecter au vrai endpoint backend |

### 🟡 Priorité moyenne

| Sujet | Description |
|---|---|
| Upload avatar / documents | Composant picker image → POST multipart → mise à jour `avatar_url` |
| Error boundaries | Wrapper `<ErrorBoundary>` sur les pages critiques + Sentry ou équivalent |
| Gestion offline mobile | Cache TanStack Query + indicateur de connectivité |
| Deep linking mobile | Schéma `harmony://` — liens d'invitation campaign, onboarding |
| Internationalisation | Le projet mélange français et anglais — choisir une langue et uniformiser |
| Tests mobile | Jest + RNTL (mobile) |
| Storybook | Documentation des composants partagés |

### 🟢 Priorité basse (optimisations)

| Sujet | Description |
|---|---|
| Performance sociogramme | Web Workers pour la boucle physique D3 (libère le thread UI) |
| SSR sociogramme | Rendu serveur du squelette — Three.js lazy-loaded côté client uniquement |
| EAS Build CI | GitHub Actions → `eas build` automatique sur merge main |
| Vercel preview | Environnements de preview par PR |
| PWA (web) | Service worker + installation standalone (future) |
| Push notifications | `expo-notifications` + endpoint `/notifications` backend |

---

### Résumé état MVP

| Composant | État |
|---|---|
| Monorepo Turborepo | ✅ Configuré |
| `@harmony/types` — tous les schemas | ✅ Complet |
| `@harmony/api` — client + endpoints | ✅ Complet |
| `@harmony/ui` — tokens design | ✅ Complet |
| Web — auth (login + guard middleware) | ✅ Complet |
| Web — layout maritime sombre + sidebar | ✅ Complet |
| Web — dashboard flotte | ✅ Complet |
| Web — cockpit `/vessel/[id]` (sociogramme 3D + simulation + matching) | ✅ Complet *(endpoint backend manquant)* |
| Web — tests Jest + Testing Library | ✅ 126 tests, 0 failures (13 suites) |
| Mobile — auth (login + SecureStore) | ✅ Complet |
| Mobile — profile candidat | ✅ Complet |
| Mobile — catalogue + passation tests | ✅ Complet |
| Web — register / campagnes / vessel | ⏳ À construire |
| Mobile — survey / pulse / invite | ⏳ À construire |
| Backend — endpoints sociogramme | ⏳ À construire |
