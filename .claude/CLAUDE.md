# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Repository Layout

```
Harmony/
├── backend/          # FastAPI + SQLAlchemy + Alembic (Python 3.12)
└── frontend/         # Turborepo monorepo (Node ≥ 20, npm@11)
    ├── apps/web/     # Next.js 15 App Router — employer dashboard
    ├── apps/mobile/  # Expo SDK 52 + Expo Router — candidate app
    ├── packages/types/   # TypeScript mirrors of all backend Pydantic schemas
    ├── packages/api/     # Axios client + TanStack Query keys
    └── packages/ui/      # Design tokens (dark maritime theme)
```

---

## Backend

### Commands

```bash
cd backend
source .venv/Scripts/activate          # Windows (Linux: .venv/bin/activate)
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Tests
pytest tests/ -v                        # full suite (442 tests, 0 failures)
pytest tests/engine/ -v -m engine       # pure function tests — no DB
pytest tests/ -v -m service             # service layer — mocked AsyncSession
pytest tests/ -v -m router             # router layer — httpx AsyncClient
pytest tests/ --cov=app --cov-report=term-missing

# Migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1

# Seed
python -m app.seed.seed_environment
python -m app.seed.seed_tests_surveys
```

### Architecture

**Request flow:** HTTP → Router (schema only) → Service (orchestration + transactions) → Repository (SQL only) → Engine (pure computation, no DB)

**Three-layer tests:**
| Layer | Strategy |
|-------|----------|
| Engine | Direct function calls, no mocks |
| Service | `AsyncMock` repos; real service logic |
| Router | `httpx.AsyncClient + ASGITransport`; mocked service via `dependency_overrides` |

**Mock pattern for router tests:** `mocker.patch("app.modules.X.router.service.method", AsyncMock(...))`

**Snapshot caching pattern:** Write-time denormalized JSON caches for O(1) dashboard reads:
- `CrewProfile.psychometric_snapshot` — rebuilt synchronously after each test submission
- `Yacht.vessel_snapshot` — rebuilt in a background task after crew changes
- `EmployerProfile.fleet_snapshot` — rebuilt periodically

### Key Enums

- `UserRole` values are **lowercase**: `"candidate"`, `"client"`, `"admin"`
- `YachtPosition` values are **capitalized**: `"Captain"`, `"Bosun"`, `"Deckhand"`, etc.

### Auth Dependencies

| Dependency | Role |
|------------|------|
| `UserDep` | Any authenticated user |
| `CrewDep` | `CANDIDATE` role |
| `EmployerDep` | `CLIENT` or `ADMIN` role |
| `AdminDep` | `ADMIN` only |

### Known Bugs (do not regress)

- **`SurveyTriggerIn` missing `yacht_id`**: `modules/survey/router.py:37` accesses `payload.yacht_id` but the Pydantic schema has no such field → `AttributeError 500`. Fix: add `yacht_id: int` to `SurveyTriggerIn`.
- **Vessel service interface mismatch**: `modules/vessel/router.py` calls `service.get_all_for_owner()` / `service.create(owner_id=...)` but `VesselService` defines `get_all_for_employer()` / `create(employer=...)`. Both `GET /vessels/` and `POST /vessels/` raise `AttributeError` at runtime.

---

## Frontend

### Commands

```bash
# From frontend/ root (runs all apps via Turborepo)
npm run dev        # turbo dev
npm run build      # turbo build
npm run lint       # turbo lint
npm run type-check # turbo type-check

# Web app only
cd frontend/apps/web
npm run dev        # next dev --port 3000
npm test           # jest
npm run test:watch
npm run test:coverage

# Mobile app only
cd frontend/apps/mobile
npm run dev        # expo start --clear
npm run android
npm run ios
npm test           # jest (jest-expo preset)
```

### Web App Architecture (apps/web)

**Pages:**
- `/dashboard` — fleet overview
- `/vessel/[id]` — cockpit: 3D sociogram + CampaignPanel + CockpitStrip

**Feature structure** (`src/features/`):
- `auth/` — Zustand store (`store.ts`), `useAuth` hook
- `recruitment/` — `useCampaigns`, `useMatching` hooks + `CampaignPanel` component
- `sociogram/` — `useCockpit` hook, D3-force physics (`physics.ts`), R3F canvas components
- `vessel/` — `useVessel`, `useSimulation` hooks + `CockpitStrip`

**Auth flow:** access token in memory → refresh token in `sessionStorage` (`harmony_rt`) → session cookie for Next.js middleware.

**3D Sociogram:** React Three Fiber + D3-force physics. SSR-disabled via `next/dynamic`. True 3D with manual z-axis forces.

**Design tokens:** bg `#07090F`, brand `#4A90B8` (steel blue), secondary `#50528A`. Sociogram edge colors: excellent `#2E8A5C` (≥80), good `#5A8A30` (65–80), moderate `#9A7030` (45–65), weak `#883838` (<45).

**Web test suite:** 126 tests, 0 failures. Co-located next to source (`*.test.{ts,tsx}`).

**Known web test pitfalls:**
- React 18/19 dual install: `moduleNameMapper` forces `"^react$"` → `<rootDir>/node_modules/react` (v19)
- d3-force is ESM — in `transpilePackages` in `next.config.js`
- Next.js middleware tests require `@jest-environment node`
- jsdom v26 has no `DragEvent`/`DataTransfer` globals — use `fireEvent.dragOver()` from RTL
- For Next.js 15 params in tests, use a synchronous thenable as a `React.use()` polyfill
- Zustand mocks must handle both `useStore()` and `useStore(selector)` call patterns

**Critical SSR bugs to avoid:**
- Never gate `children` on `useState(false)` in Providers — server renders false → empty HTML. Only gate devtools with a `mounted` state check.
- Webpack aliases must be client-side only (`if (!isServer)`) in `next.config.js` — server-side aliases break `React.cache` polyfill.
- `DragEvent.dataTransfer` — null-check before assignment (HTML spec allows null for programmatic events).

### Mobile App Architecture (apps/mobile)

**Expo Router file-based routing:**
- `(auth)/login` — unauthenticated flow
- `(candidate)/profile` — crew profile
- `(candidate)/assessment/` — test catalogue, test session `[testId]`, results
- `(candidate)/applications/` — job applications

**Feature structure** (`src/features/`):
- `auth/` — Zustand store + `useAuth` hook
- `assessment/` — `useAssessment`, `useTakeTest` hooks + UI components (`LikertQuestion`, `ResultRing`, `ProgressHeader`, `TestCard`)

**Key API contract:** `ResponseIn` fields are `valeur_choisie: str` and `seconds_spent: float` (not `value`/`time_seconds`).

---

## Shared Packages

- **`@harmony/types`** — TypeScript mirrors of all backend Pydantic schemas. Update these when backend schemas change.
- **`@harmony/api`** — Axios client instance + TanStack Query v5 query keys.
- **`@harmony/ui`** — Design system tokens only (no runtime components).

---

## Agent System

Specialized sub-agents live in `.claude/agents/`. Each is a Markdown file with a YAML front-matter (`name`, `description`, `tools`, `model`, `maxTurns`) followed by a detailed system prompt.

### Available Agents

| Agent | Role | When to invoke |
|---|---|---|
| `orchestrator` | Technical project manager — decomposes a backlog feature into sequenced atomic tasks, identifies responsible agents, detects dependencies. Produces execution plans, not code. | **First** on any feature touching multiple layers |
| `backend` | FastAPI developer — implements full endpoints (router → service → repository → engine), Alembic migrations, and all 3 test layers. Enforces TESTS_AND_SECURITY.md. | Any new endpoint or backend modification |
| `frontend-web` | Next.js 15 developer — implements App Router pages, React components, TanStack Query hooks, and co-located Jest+RTL tests. | Any new web page or component |
| `frontend-mobile` | Expo SDK 52 developer — implements Expo Router screens, NativeWind components, hooks, and jest-expo tests. Handles RN New Arch pitfalls. | Any new mobile screen or component |
| `schema-sync` | Keeps `@harmony/types` and `@harmony/api` in sync with backend Pydantic schemas. | After any Pydantic schema change |
| `security-review` | Security auditor — verifies Zod/Pydantic on all inputs, rate limiters on sensitive routes, auth guards, standard error format, no sensitive data exposed. | After any new endpoint or auth route |
| `frontend-designer` | UI/UX reviewer — validates dark maritime theme consistency, UX relevance, accessibility, and user journey fluency. Produces reviews with concrete recommendations, not code. | After any new UI (web or mobile) |
| `head-of-science` | Expert in organizational psychology and data science — validates psychometric models (DNRE, MLPSM, Sociogram), ensures formulas are anchored in I/O literature. | Before any engine modification or new predictive factor |
| `debug` | Debugging specialist — reproduces, isolates, and proves root causes for failing tests and runtime errors. Never guesses. | Proactively when any test fails or runtime error appears |

### Standard Creation Process

For any feature spanning multiple layers, the mandatory sequence is:

```
1. orchestrator        → produce sequenced execution plan
2. head-of-science     → (if engine/formula change) validate scientific model BEFORE backend
3. backend             → implement endpoints + migrations + 3-layer tests
4. schema-sync   ┐     → sync @harmony/types after backend (can run in parallel)
   security-review┘    → audit new endpoints after backend (can run in parallel)
5. frontend-web / frontend-mobile → implement UI after types are synced
6. frontend-designer   → review UI after implementation
7. debug               → proactively if any test fails at any step
```

**Rules:**
- Never skip `schema-sync`, `security-review`, or tests.
- `head-of-science` must be called **before** `backend` when any engine (DNRE, MLPSM, Sociogram) is modified.
- `orchestrator` must be called first on any feature touching more than one layer.
- `debug` is called proactively — do not wait for the user to ask.
