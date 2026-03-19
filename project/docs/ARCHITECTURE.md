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
