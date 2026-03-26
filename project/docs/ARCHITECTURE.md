# Architecture — Radiant Analytics

> Vue d'ensemble du système. Pour les détails d'implémentation : voir `backend/README.md` et `frontend/README.md`.

---

## Vue système

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                                                             │
│  apps/web (Next.js 15)          apps/mobile (Expo SDK 55)   │
│  Employeur — dashboard fleet    Candidat — tests + profil   │
│  /dashboard, /vessel/[id]       /(candidate)/assessment     │
│                                                             │
│  packages/types  packages/api  packages/ui                  │
│  (Pydantic mirrors) (Axios+TQ) (design tokens)             │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────────────────┐
│                        BACKEND                               │
│                                                             │
│  FastAPI — modules/                                         │
│  auth/ crew/ vessel/ survey/ recruitment/ assessment/       │
│  [analytics/ — à créer Temps 1]                            │
│                                                             │
│  Router → Service → Repository → Engine                     │
│                                                             │
│  engine/pe_fit/           engine/use_cases/                │
│  (pure computation)       (business orchestration)          │
│                                                             │
│  SQLAlchemy + PostgreSQL + Alembic migrations               │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend — Patterns fondamentaux

### Request flow (non-négociable)
```
HTTP Request
  → Router      : validation Pydantic, auth dependency, pas de logique
  → Service     : orchestration, transactions, appels engine
  → Repository  : SQL uniquement, pas de logique métier
  → Engine      : calcul pur, pas de DB, pas d'I/O
```

### Snapshot caching
Le moteur P-E Fit est pur (pas de DB). Il consomme des snapshots JSON dénormalisés.

| Snapshot | Modèle | Rebuild trigger |
|----------|--------|-----------------|
| `psychometric_snapshot` | `CrewProfile` | Après chaque soumission de test (synchrone) |
| `vessel_snapshot` | `Yacht` | Après changement d'équipage (background task) |
| `fleet_snapshot` | `EmployerProfile` | Périodique |

**Règle :** ne jamais appeler l'engine directement sur des modèles DB. Toujours passer par les snapshots.

### Tests — 3 couches obligatoires
| Couche | Stratégie | Marqueur pytest |
|--------|-----------|-----------------|
| Engine | Appels directs, aucun mock | `@pytest.mark.engine` |
| Service | `AsyncMock` sur les repos | `@pytest.mark.service` |
| Router | `httpx.AsyncClient + ASGITransport` + `dependency_overrides` | `@pytest.mark.router` |

### Auth dependencies
| Dep | Rôle |
|-----|------|
| `UserDep` | Tout utilisateur authentifié |
| `CrewDep` | Rôle `candidate` |
| `EmployerDep` | Rôle `client` ou `admin` |
| `AdminDep` | Rôle `admin` uniquement |

---

## Engine P-E Fit — Structure

```
engine/pe_fit/
  pj_fit/
    demands_abilities/   → Q2 : GCA + compétences (scorer.py)
    needs_supplies/      → Q3 : JD-R buffer effect (jdr.py)
    motivation_fit/      → Q3 : SDT cosine distance (scorer.py)
    safety_barrier.py    → Barrières non-compensatoires
    profiles.py          → Profils SME par poste
  po_fit/
    f_values.py          → Q5 : CES value congruence
  pt_fit/
    f_team.py            → Q4 : Bell 2007 formula
  ps_fit/
    f_lmx.py             → Q6 : LMX Euclidean distance
  physical_fit/
    f_physical.py        → Q7a : maritime tolerance
  mobility_fit/
    f_mobility.py        → Q7b : mobility/temporal fit
  master.py              → global_score + PEFitResult
  pipeline.py            → orchestration complète
  trait_extractor.py     → extraction traits depuis snapshot
  compat.py              → compatibilité formats

engine/use_cases/        ← couche orchestration métier (au-dessus de pe_fit)
  recruitment.py         → HIRE / CONDITIONAL / DISQUALIFY
  management.py          → TEAM_HEALTH + alertes
  training.py            → GAP_ANALYSIS + plan dev
  talent.py              → READINESS par niveau
  rps.py                 → RISK_LEVEL psychosocial
  _base.py
```

**Pondérations actuelles `global_score` :**
| Dimension | Poids |
|-----------|-------|
| Q2 — PJ D-A Fit | 0.28 |
| Q3 — PJ N-S Fit | 0.25 |
| Q4 — PG/PT Fit | 0.22 |
| Q5 — PO Fit | 0.18 |
| Q6 — PS Fit | 0.12 |
| Q7a — Physical | 0.05 |
| Q7b — Mobility | 0.05 |

---

## Frontend — Patterns fondamentaux

### Monorepo (Turborepo)
```
frontend/
  apps/web/       → Next.js 15 App Router — employeur
  apps/mobile/    → Expo SDK 55 + Expo Router — candidat
  packages/
    types/        → Miroirs TypeScript des schémas Pydantic (SOURCE : backend)
    api/          → Axios client + TanStack Query v5 keys
    ui/           → Design tokens uniquement (pas de composants)
```

**Règle :** `@harmony/types` est toujours généré/synchronisé depuis le backend. Ne jamais écrire les types manuellement.

### Auth flow
- **Web** : access token en mémoire → refresh token `sessionStorage` (`harmony_rt`) → cookie session Next.js middleware
- **Mobile** : access token en mémoire → refresh token `SecureStore` (`harmony_rt`)

### Design system (dark maritime)
| Token | Hex | Usage |
|-------|-----|-------|
| `ocean` (bg) | `#0D1B2A` | Background principal |
| `navy` | `#1A2C42` | Surfaces |
| `teak` | `#A67C52` | CTA prestige |
| `silver` | `#94A3B8` | Texte secondaire |
| `ice` | `#F1F4F8` | Texte principal |

Sociogramme : excellent `#2E8A5C` (≥80) · bon `#5A8A30` (65-80) · moyen `#9A7030` (45-65) · faible `#883838` (<45)

### 3D Sociogramme
React Three Fiber + D3-force physics. SSR désactivé via `next/dynamic`. Z-axis manuel pour vrai 3D.

---

## Architecture de passation de tests — Vision cible

> Cette section documente le schéma DB cible pour toute la couche de collecte de données psychométriques. C'est le cœur du produit Radiant : des données mal persistées à l'alpha signifient des normes inutilisables à vie. Ce schéma s'applique **candidats et calibrateurs confondus**.

### Principes directeurs

1. **Les réponses individuelles sont sacrées.** Sans elles : pas d'alpha de Cronbach, pas d'analyse DIF, pas de détection de straightlining, pas de recalcul après correction d'un bug engine. Le JSON agrégé dans une colonne `scores` n'est pas suffisant.
2. **Session server-side obligatoire.** Toute passation crée une session en base avant la première question. Cela permet la reprise après crash et garantit la traçabilité complète.
3. **Une seule paire de tables** pour candidats et calibrateurs (`test_sessions` + `test_responses`). Le discriminateur `user_type` sépare les deux populations au niveau des requêtes, pas au niveau du schéma.
4. **`valeur_choisie: str` partout.** Un entier est trop restrictif pour couvrir Likert ("4"), QCM ("B"), et les futures extensions. Toutes les valeurs transitent en string.
5. **`catalogue_id` dénormalisé dans `test_responses`.** La requête analytique fondamentale est "toutes les réponses à la question X pour le catalogue Y". Sans cette dénormalisation, chaque analyse nécessite un JOIN supplémentaire. `catalogue_id` étant immuable après création de session, il n'y a aucun risque de désynchronisation.
6. **`seconds_spent` persiste par item.** Prérequis pour détecter les réponses aléatoires (< 1s) et les patterns de distraction (> 60s). Nullable pour compatibilité legacy.

### Schéma cible

```sql
-- Sessions de passation (candidats ET calibrateurs)
test_sessions
  id                SERIAL PK
  catalogue_id      FK → test_catalogues  NOT NULL
  crew_profile_id   FK → crew_profiles    NULLABLE  ┐ XOR strict :
  calibrator_id     FK → calib_users      NULLABLE  ┘ exactement l'un des deux
  started_at        TIMESTAMPTZ           DEFAULT NOW()
  completed_at      TIMESTAMPTZ           NULLABLE   -- NULL = en cours
  device_info       JSON                  NULLABLE   -- platform, os_version, app_version

  INDEX(crew_profile_id, catalogue_id)
  INDEX(calibrator_id,   catalogue_id)
  UNIQUE(calibrator_id,  catalogue_id) WHERE calibrator_id IS NOT NULL
  CONSTRAINT check_xor_user : (crew_profile_id IS NOT NULL)::int
                             + (calibrator_id   IS NOT NULL)::int = 1

-- Réponses individuelles (append-only, jamais modifiées)
test_responses
  id                SERIAL PK
  session_id        FK → test_sessions    NOT NULL  ON DELETE CASCADE
  catalogue_id      FK → test_catalogues  NOT NULL  -- dénormalisé pour analytics
  question_id       FK → questions        NOT NULL  ON DELETE CASCADE
  valeur_choisie    VARCHAR(50)           NOT NULL   -- "4" | "B" | "strongly_agree"
  seconds_spent     FLOAT                 NULLABLE

  INDEX(session_id)
  INDEX(catalogue_id, question_id)   -- requête analytics principale (DIF, alpha)
  INDEX(question_id)

-- Résultats calculés (candidats ET calibrateurs, discriminés par user_type)
test_results
  id                SERIAL PK
  user_type         VARCHAR(20)           NOT NULL   -- "candidate" | "calibrator"
  crew_profile_id   FK → crew_profiles    NULLABLE  ┐ XOR strict
  calibrator_id     FK → calib_users      NULLABLE  ┘
  session_id        FK → test_sessions    NULLABLE   -- NULL = données legacy pré-migration
  test_id           FK → test_catalogues  NOT NULL
  global_score      FLOAT                 NOT NULL
  scores            JSON                  NOT NULL   -- {traits, reliability, meta}
  created_at        TIMESTAMPTZ           DEFAULT NOW()

  PARTIAL INDEX(crew_profile_id, test_id) WHERE user_type = 'candidate'
  PARTIAL INDEX(calibrator_id,   test_id) WHERE user_type = 'calibrator'
  INDEX(session_id)
  CONSTRAINT check_xor_user : identique à test_sessions
```

### Flux de données complet

```
[FRONTEND]
  useCalibPassation / useTakeTest
  └─ accumule {question_id, valeur_choisie, seconds_spent}[] en mémoire
  └─ soumet en batch unique en fin de passation (1 seul appel réseau)

[BACKEND — submit endpoint]
  1. GET session → vérifier completed_at IS NULL (sinon 409)
  2. INSERT INTO test_responses (bulk)
  3. UPDATE test_sessions SET completed_at = NOW()
  4. engine.scoring.calculate_scores(responses, catalogue) → scores dict
  5. INSERT INTO test_results
  6. IF candidate → rebuild psychometric_snapshot (synchrone)
                  → propagate vessel/fleet snapshots (background task)
  7. RETURN {session_id, overall_score, traits}

[ANALYTICS — hors request cycle]
  SELECT valeur_choisie, seconds_spent
  FROM test_responses
  WHERE catalogue_id = X AND question_id = Y
  → alpha de Cronbach, analyse DIF, détection outliers
```

### Tables partagées (inchangées)

```
test_catalogues — définition des instruments (partagé candidats + calibrateurs)
questions       — items (partagé candidats + calibrateurs)
calib_users     — auth isolée intentionnellement (pas de contamination avec users commerciaux)
```

### Ce que ce schéma remplace

| Ancien | Nouveau | Raison |
|--------|---------|--------|
| `calib_sessions` | `test_sessions` | Unification candidat/calibrateur |
| `calib_responses` (value: int) | `test_responses` (valeur_choisie: str) | Type unifié, dénorm catalogue_id |
| `test_results` (crew_profile_id NOT NULL) | `test_results` (user_type + XOR FK) | Couverture calibrateur |
| Scoring inline dans CalibrationService | `engine.psychometrics.scoring` | Respect 3-layer |
| Assessment sans persistance des réponses | `test_responses` | Perte de données inacceptable |

### Scalabilité

Volume estimé à plein régime :
- `test_sessions`  : ~800K lignes (50K candidats × 7 tests + 5K calibrateurs × 12 tests)
- `test_responses` : ~24M lignes (800K sessions × 30 questions en moyenne)
- `test_results`   : ~800K lignes (1:1 avec sessions)

24M lignes dans `test_responses` est banal pour PostgreSQL avec les index ci-dessus. Toutes les requêtes applicatives filtrent par `session_id` (index lookup). Les requêtes analytiques (DIF, alpha) filtrent par `catalogue_id + question_id` (index composite). Si le volume atteint 100M+ lignes, activer le **table partitioning PostgreSQL par `catalogue_id`** — une ligne d'Alembic.

### Règles non-négociables pour les implémentations futures

- Ne jamais créer un endpoint de soumission qui ne persiste pas les réponses individuelles
- Ne jamais stocker `value: int` — toujours `valeur_choisie: str`
- Ne jamais scorer avant d'avoir persisté les réponses (ordre : save → score → result)
- Ne jamais laisser un résultat `test_results` sans `session_id` (sauf données legacy migrées)
- Le scoring reste dans `engine/psychometrics/scoring/` — jamais dans un service

---

## Contraintes d'architecture non-négociables

1. **Zod/Pydantic sur tous les inputs** — côté backend ET frontend (pas de trust implicite)
2. **Rate limiter** — auth routes : 5 req/15 min ; routes sensibles : 100 req/15 min
3. **Format d'erreur standardisé** : `{ error, message, code }` — jamais de stack trace exposée
4. **TypeScript strict** : `strict: true`, zéro `any` (utiliser `unknown` + narrowing)
5. **Tests co-localisés** : chaque nouveau fichier source a son `.test.{ts,tsx,py}` co-localisé
6. **0 régression** : le merge d'une feature ne doit jamais casser des tests existants

---

## Enums à ne jamais confondre

```python
UserRole: "candidate" | "client" | "admin"          # tout minuscule
YachtPosition: "Captain" | "Bosun" | "Deckhand"...  # capitalisé
```

---

## Références

- [DATA_REQUIREMENTS.md](DATA_REQUIREMENTS.md) — Format exact des snapshots et seed
- `backend/README.md` — Détail complet backend (setup, migrations, tests)
- `frontend/README.md` — Détail complet frontend (dev, build, tests par app)
- `.claude/TESTS_AND_SECURITY.md` — Standards qualité & sécurité obligatoires
