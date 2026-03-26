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
4. **`response_value: str` partout.** Un entier est trop restrictif pour couvrir Likert ("4"), QCM ("B"), et les futures extensions. Toutes les valeurs transitent en string. Le nom `response_value` est intentionnellement anglophone pour être lisible par une équipe internationale.
5. **`catalogue_id` dénormalisé dans `test_responses`.** La requête analytique fondamentale est "toutes les réponses à la question X pour le catalogue Y". Sans cette dénormalisation, chaque analyse nécessite un JOIN supplémentaire. `catalogue_id` étant immuable après création de session, il n'y a aucun risque de désynchronisation. Il est toujours dérivé server-side — jamais accepté du client.
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
  completed_at      TIMESTAMPTZ           NULLABLE    -- NULL = en cours
  device_info       JSON                  NULLABLE    -- platform, os_version, app_version
                                                      -- schéma strict, jamais free-form

  INDEX(crew_profile_id, catalogue_id)
  INDEX(calibrator_id,   catalogue_id)
  UNIQUE(calibrator_id,  catalogue_id) WHERE calibrator_id IS NOT NULL
  CONSTRAINT check_xor_user : (crew_profile_id IS NOT NULL)::int
                             + (calibrator_id   IS NOT NULL)::int = 1

-- Réponses individuelles (append-only, jamais modifiées)
test_responses
  id                SERIAL PK
  session_id        FK → test_sessions    NOT NULL  ON DELETE CASCADE
  catalogue_id      FK → test_catalogues  NOT NULL  -- dénormalisé, toujours dérivé server-side
  question_id       FK → questions        NOT NULL  ON DELETE CASCADE
  response_value    VARCHAR(50)           NOT NULL   -- "4" | "B" | "strongly_agree"
  seconds_spent     FLOAT                 NULLABLE
    CHECK(seconds_spent IS NULL OR (seconds_spent >= 0 AND seconds_spent <= 3600))

  INDEX(session_id)
  INDEX(catalogue_id, question_id)   -- requête analytics principale (DIF, alpha)
  INDEX(question_id)

-- Résultats calculés (candidats ET calibrateurs, discriminés par user_type)
test_results
  id                SERIAL PK
  user_type         user_type_enum        NOT NULL   -- ENUM PG : 'candidate' | 'calibrator'
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

### Règles UX de passation (non-négociables)

Ces règles s'appliquent à tous les hooks de passation (`useTakeTest`, `useCalibPassation`, et tout futur hook) et à leurs écrans associés.

1. **Répondre avant d'avancer.** Le bouton "Suivant" est désactivé tant que la question courante n'a pas de réponse. L'utilisateur ne peut pas naviguer en avant sur une question vide — seulement en arrière.
2. **Toutes les questions répondues avant submit.** Le bouton "Terminer" / "Soumettre" est désactivé si `unanswered > 0`. Pas d'alerte de confirmation partielle — le submit est simplement bloqué. L'UI indique le nombre de questions restantes.
3. **Navigation libre en arrière.** L'utilisateur peut revenir sur ses réponses précédentes librement et les modifier.
4. **Protection anti-double submit.** Le bouton "Terminer" est désactivé dès le premier appui (`isPending || isSubmitted`). Pas de deuxième envoi possible.
5. **Protection retour Android.** `BackHandler` intercepte le retour matériel pendant une session active et affiche une confirmation avant de quitter (avec perte de la session en cours).

```typescript
// Pattern à respecter dans tout hook de passation
const canGoNext = responses[currentQuestion.id] !== undefined;
const canSubmit = questions.every(q => responses[q.id] !== undefined);

// Bouton Suivant
<Button disabled={!canGoNext} onPress={goNext} />

// Bouton Terminer
<Button
  disabled={!canSubmit || submitMutation.isPending || isSubmitted}
  onPress={handleSubmit}
/>
```

### Sécurité — Règles obligatoires pour les endpoints de passation

#### 🔴 Validation des question_id (critique)

Avant tout `save_responses`, le service **doit** vérifier que chaque `question_id` soumis appartient au catalogue de la session. Sans ça, un client malveillant peut injecter des réponses pour des questions d'un autre catalogue et corrompre les normes.

```python
# Pattern obligatoire dans submit_responses
valid_ids = await repo.get_question_ids_for_catalogue(db, session.catalogue_id)
invalid = [r.question_id for r in data.responses if r.question_id not in valid_ids]
if invalid:
    raise HTTPException(400, {"error": True, "code": "INVALID_QUESTION_IDS",
                               "message": f"question_ids invalides : {invalid}"})
```

#### 🔴 `user_type` comme enum PostgreSQL (critique)

Ne jamais stocker `user_type` comme VARCHAR libre. Utiliser un `ENUM` PostgreSQL ou une contrainte `CHECK(user_type IN ('candidate', 'calibrator'))`. Une valeur arbitraire en base est un vecteur d'escalade de privilèges.

#### 🟠 `catalogue_id` toujours dérivé server-side

Dans `test_responses`, `catalogue_id` est dénormalisé pour les analytics. Il doit toujours être rempli par le service depuis `session.catalogue_id` — jamais lu depuis le payload client. Si le client envoie un `catalogue_id`, il est ignoré.

#### 🟠 Validation de `seconds_spent`

`seconds_spent` doit être validé au niveau Pydantic : `0 <= seconds_spent <= 3600`. Une valeur négative ou supérieure à 1h est soit une manipulation, soit un bug — les deux doivent être rejetés avec HTTP 400.

#### 🟠 Vérification de propriété sur session_id (IDOR)

Tout endpoint qui prend un `session_id` en paramètre doit vérifier que la session appartient bien à l'utilisateur authentifié. Cette vérification est obligatoire même si l'endpoint semble "en lecture seule".

```python
session = await repo.get_session(db, session_id)
if session.calibrator_id != current_user.id:  # ou crew_profile_id
    raise HTTPException(403, {"code": "SESSION_FORBIDDEN"})
```

#### 🟡 `device_info` — schéma strict, pas de free-form JSON

`device_info` doit respecter un schéma Pydantic fixe avant persistance :

```python
class DeviceInfo(BaseModel):
    platform: Literal["ios", "android", "web"]
    os_version: str = Field(max_length=20)
    app_version: str = Field(max_length=20)
    screen_size: str | None = Field(None, max_length=20)
```

Tout champ hors schéma est rejeté. Ne jamais persister de JSON free-form provenant du client.

#### 🟡 RGPD — Droit à l'oubli sur `calib_users`

`calib_users` stocke des données démographiques sensibles (genre, année de naissance, nationalité). Il faut une voie d'anonymisation conforme au RGPD : `DELETE /calibration/me` remplace les champs PII par `NULL` sans supprimer les réponses (qui sont des données de norming anonymisées après dissociation).

```python
# Anonymisation — ne jamais DELETE la ligne, les réponses restent pour les normes
await repo.anonymize_calibrator(db, calibrator_id)
# → email = f"deleted_{id}@radiant.invalid"
# → name = "Participant anonymisé"
# → gender, birth_year, nationality, native_language = NULL
```

### Ce que ce schéma remplace

| Ancien | Nouveau | Raison |
|--------|---------|--------|
| `calib_sessions` | `test_sessions` | Unification candidat/calibrateur |
| `calib_responses` (`value: int`) | `test_responses` (`response_value: str`) | Type unifié, dénorm `catalogue_id`, nom anglophone |
| `valeur_choisie` partout | `response_value` | Lisibilité équipe internationale |
| `test_results` (`crew_profile_id NOT NULL`) | `test_results` (`user_type` enum + XOR FK) | Couverture calibrateur, type safe |
| Scoring inline dans `CalibrationService` | `engine.psychometrics.scoring` | Respect architecture 3-layer |
| Assessment sans persistance des réponses | `test_responses` | Perte de données psychométriques inacceptable |

### Scalabilité

Volume estimé à plein régime :
- `test_sessions`  : ~800K lignes (50K candidats × 7 tests + 5K calibrateurs × 12 tests)
- `test_responses` : ~24M lignes (800K sessions × 30 questions en moyenne)
- `test_results`   : ~800K lignes (1:1 avec sessions)

24M lignes dans `test_responses` est banal pour PostgreSQL avec les index ci-dessus. Toutes les requêtes applicatives filtrent par `session_id` (index lookup). Les requêtes analytiques (DIF, alpha) filtrent par `catalogue_id + question_id` (index composite). Si le volume atteint 100M+ lignes, activer le **table partitioning PostgreSQL par `catalogue_id`** — une ligne d'Alembic.

### Règles non-négociables pour les implémentations futures

- Ne jamais créer un endpoint de soumission qui ne persiste pas les réponses individuelles
- Ne jamais stocker `value: int` — toujours `response_value: str`
- Ne jamais accepter `catalogue_id` depuis le client dans `test_responses` — toujours dérivé server-side
- Toujours valider que chaque `question_id` soumis appartient au catalogue de la session
- Ne jamais scorer avant d'avoir persisté les réponses (ordre obligatoire : save → score → result)
- Ne jamais laisser un résultat `test_results` sans `session_id` (sauf données legacy migrées)
- Le scoring reste dans `engine/psychometrics/scoring/` — jamais dans un service
- Nommage anglophone obligatoire pour toutes les colonnes, endpoints et variables partagées

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
