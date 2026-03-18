# Radiant Analytics — Backend

Psychometric analytics platform for crew recruitment and team management in superyacht operations.

**Stack:** Python 3.12, FastAPI 0.128, SQLAlchemy 2.0 async, PostgreSQL, asyncpg, Alembic, Pydantic 2, scikit-learn, NumPy/Pandas

---

## Table of Contents

1. [Architecture](#architecture)
2. [Domain Model](#domain-model)
3. [P-E Fit Engine](#p-e-fit-engine)
4. [Scientific Foundations](#scientific-foundations)
5. [Setup](#setup)
6. [Environment Variables](#environment-variables)
7. [Database Migrations](#database-migrations)
8. [Running the Server](#running-the-server)
9. [Running Tests](#running-tests)
10. [API Reference](#api-reference)
11. [Known Issues & Backlog](#known-issues--backlog)

---

## Architecture

The application is organized around two main layers: **vertical modules** for HTTP and persistence, and a **transversal engine** for pure computation.

```
backend/app/
├── core/
│   ├── config.py          # Pydantic Settings (DATABASE_URL, JWT, SMTP, S3)
│   ├── database.py        # Async SQLAlchemy engine + session factory
│   └── security.py        # bcrypt password hashing, JWT sign/verify
│
├── shared/
│   ├── deps.py            # FastAPI dependencies (UserDep, CrewDep, EmployerDep, AdminDep)
│   ├── enums.py           # UserRole, YachtPosition (16), YachtTypeAlpha (7), CampaignStatus…
│   ├── limiter.py         # slowapi rate limiter
│   └── models/            # SQLAlchemy ORM models (shared across modules)
│       ├── User.py        # User, CrewProfile, EmployerProfile, UserDocument
│       ├── Yacht.py       # Yacht, CrewAssignment
│       ├── Assessment.py  # TestCatalogue, Question, TestResult
│       ├── Campaign.py    # Campaign, CampaignCandidate
│       ├── Survey.py      # Survey, SurveyResponse, RecruitmentEvent, ModelVersion, JobWeightConfig
│       └── Pulse.py       # DailyPulse
│
├── modules/               # Vertical slices — each owns its HTTP, service, and repo layer
│   ├── auth/              # POST /auth/register/crew, /register/employer, /login, /refresh
│   ├── identity/          # GET|PATCH /identity/candidate/{id}, /me
│   ├── crew/              # GET|POST|DELETE /crew/{yacht_id}/members, /dashboard, /pulse
│   ├── assessment/        # GET /assessments/catalogue, POST /submit, GET /results
│   ├── recruitment/       # POST /campaigns, GET /matching, /impact, /decide
│   ├── survey/            # POST /surveys/trigger, GET /results, POST /respond
│   ├── vessel/            # CRUD /vessels, PATCH /environment
│   └── gateway/           # Aggregated composite endpoints for frontend consumption
│
├── engine/                # Pure computation — zero DB access, fully testable
│   ├── psychometrics/
│   │   ├── scoring.py       # Likert + cognitive scoring, reliability detection
│   │   ├── tirt_scoring.py  # T-IRT engine (CUTTY SARK) — MAP estimation, probit model
│   │   ├── snapshot.py      # Rebuilds CrewProfile.psychometric_snapshot from TestResult set
│   │   ├── normalizer.py    # Score normalization against population norms
│   │   ├── formatter.py     # Report formatting per viewer context
│   │   └── reliability.py   # Response bias, speedrun detection
│   │
│   ├── pe_fit/            # P-E Fit framework (Kristof-Brown 2005) — 7 families
│   │   ├── pj_fit/        # Person-Job Fit (DA + NS + motivation)
│   │   │   ├── demands_abilities/  # scorer.py — GCA+C SME score, DA-fit PSI
│   │   │   ├── needs_supplies/     # jdr.py — JD-R buffer effect, NS-fit PSI
│   │   │   ├── motivation_fit/     # scorer.py — SDT cosine distance
│   │   │   ├── safety_barrier.py
│   │   │   ├── profiles.py         # SME profiles (16 positions) + matrix (position × yacht_type)
│   │   │   └── weights.py
│   │   ├── po_fit/        # Person-Organisation Fit (CES values PSI — Ravlin & Meglino 1987)
│   │   │   ├── f_values.py
│   │   │   └── values_weights.py
│   │   ├── pt_fit/        # Person-Team Fit (Bell 2007 formula)
│   │   │   └── f_team.py
│   │   ├── ps_fit/        # Person-Supervisor Fit (LMX Euclidean distance)
│   │   │   └── f_lmx.py
│   │   ├── vessel_profile.py   # YachtStructuralProfile — generates vessel_params per yacht type
│   │   ├── master.py           # PEFitResult dataclass + compute()
│   │   ├── pipeline.py         # Orchestrates pe_fit for all candidates in a campaign
│   │   └── trait_extractor.py
│   │
│   ├── use_cases/         # Business orchestration — combines pe_fit results into decisions
│   │   ├── recruitment.py # HIRE / CONDITIONAL / DISQUALIFY
│   │   ├── management.py  # TEAM_HEALTH + alerts
│   │   ├── training.py    # GAP_ANALYSIS + development plan
│   │   ├── talent.py      # READINESS by career level
│   │   └── rps.py         # RISK_LEVEL psychosocial
│   │
│   ├── benchmarking/
│   │   ├── diagnosis.py   # Performance × Cohesion matrix, TVI, HCD
│   │   └── matrice.py     # Sociogram data (D_ij dyad compatibility)
│   │
│   └── ml/
│       ├── regression.py  # OLS β-fitting when n_samples > 150
│       └── model_store.py # ModelVersion persistence
│
├── infra/
│   ├── storage.py         # File upload (local sim; S3 config present, not wired)
│   ├── email.py           # SMTP/SendGrid — not implemented
│   └── notifications.py
│
└── seed/
    ├── seed.py                       # Orchestrateur principal (CLI)
    ├── environment/                  # employers, candidates, yachts, campaigns
    ├── tests/
    │   ├── tests.py                  # Orchestre les 7 catalogues
    │   └── questions/
    │       ├── etalons/ipip120.py    # CUTTY SARK — 60 paires T-IRT
    │       ├── etalons/rmaws.py      # Résilience
    │       ├── cogiq.py              # Cognition
    │       ├── hmr24.py              # Motivation (SDT)
    │       ├── ces_values.py         # Valeurs (CES — Ravlin & Meglino 1987)
    │       ├── maritime_tolerance.py # METS — 15 items, 5 dimensions
    │       └── mobility_profile.py   # MMFS — 12 items, 4 dimensions
    └── surveys/
        ├── surveys.py
        └── pulses.py
```

### Request Flow

```
HTTP Request
  → Router          (HTTP marshaling only — validates schema, calls service)
  → Service         (orchestration — calls repo + engine, owns transaction boundaries)
  → Repository      (SQL queries only — no business logic)
  → Engine          (pure computation — receives data, returns result, no side effects)
  → HTTP Response
```

### Caching Pattern (Snapshots)

Rather than recomputing psychometric aggregates on every dashboard load, the application maintains denormalized JSON caches:

- `CrewProfile.psychometric_snapshot` — rebuilt **synchronously** after each test submission. Contains Big Five, cognitive, motivation, resilience, values_profile, maritime_tolerance, mobility_profile.
- `Yacht.vessel_snapshot` — rebuilt **in a background task** after crew changes.
- `EmployerProfile.fleet_snapshot` — rebuilt periodically across managed yachts.

---

## Domain Model

```
User (auth + identity)
  ├── CrewProfile      1:1   psychometric_snapshot (JSON), position_targeted, trust_score
  └── EmployerProfile  1:1   fleet_snapshot (JSON), company_name

Yacht
  ├── CrewAssignment         active crew (is_active=True) + past experiences (is_active=False)
  ├── vessel_snapshot (JSON) harmony metrics, captain_leadership_vector
  └── DailyPulse             score 1–5 daily well-being signal

Campaign (a hiring position on a Yacht)
  └── CampaignCandidate      application (PENDING / HIRED / REJECTED / JOINED)

TestCatalogue (7 catalogues) → Question → TestResult
  └── test_type = "tirt" → routes to TirtScoringEngine (CUTTY SARK)

Survey → SurveyResponse
  └── intent_to_stay (0–100) feeds y_actual in RecruitmentEvent

RecruitmentEvent             one record per hiring decision
  ├── y_success_predicted    global_score from pe_fit at decision time
  └── y_actual               filled post-hire from SurveyResponse.intent_to_stay
```

---

## P-E Fit Engine

The P-E Fit framework (Kristof-Brown et al., 2005) evaluates fit across 7 orthogonal families. Each returns a **PSI score** (Profile Similarity Index) in [0, 1]:

```
PSI_dim = 1 − |P_norm − E_level|
```

where `P_norm = P/100` (candidate score normalised) and `E_level` is the environment requirement.

**Global score:**
```
global_score = Σ(w_i × PSI_i) / Σ(w_i disponibles)   × 100
```

Weights renormalise automatically when a dimension is unavailable.

### Dimension Weights

| Dimension | Weight | Engine file |
|---|---|---|
| `da_fit` — Demands-Abilities | 0.28 | `pj_fit/demands_abilities/scorer.py` |
| `ns_fit` — Needs-Supplies (JD-R) | 0.25 | `pj_fit/needs_supplies/jdr.py` |
| `po_values_fit` — Person-Organisation | 0.18 | `po_fit/f_values.py` |
| `pg_fit` — Person-Group (Bell 2007) | 0.16 | `pt_fit/f_team.py` |
| `ps_fit` — Person-Supervisor (LMX) | 0.13 | `ps_fit/f_lmx.py` |
| `physical_fit` — Maritime tolerance | 0.05 | *(pending)* |
| `mobility_fit` — Mobility flexibility | 0.05 | *(pending)* |
| **Sum** | **1.10** | intentional — enables renormalisation |

### PG-Fit — F_team (Bell 2007)

```
F_team = 0.30·min(A) + 0.30·μ(C) + 0.28·μ(ES) − 0.12·σ(C)
```

- `min(A)` — Bad Apple Effect (Felps et al., 2006): one toxic member degrades the whole team
- `μ(C)` — mean Conscientiousness: shared work ethics
- `μ(ES)` — Collective Affective Tone (George, 1990): team stress resilience
- `σ(C)` — Faultline Index (Lau & Murnighan, 1998): variance predicts latent conflict

### PS-Fit — F_lmx (LMX)

```
F_lmx = (1 − ‖L_capt − V_crew‖₂ / d_max) × 100
```

3D leadership space: `autonomy_preference`, `feedback_preference`, `structure_imposed`.

### PO-Fit — CES Values (Ravlin & Meglino 1987)

4 value dimensions, equiweighted PSI: `honesty`, `achievement`, `fairness`, `solidarity`.

### DA-Fit — Demands-Abilities

```
SME score (C1) = ω₁·GCA + ω₂·C + ω₃·GCA×C/100
ω₁ = 0.60, ω₂ = 0.40
```

Non-compensatory safety barrier: ES < 15 or Agreeableness < 15 → `DISQUALIFIED`.

### SME Profiles — Position × Yacht Type Matrix

`pj_fit/profiles.py` contains:
- 16 generic profiles by `YachtPosition` (Captain, First Mate, Bosun, Deckhand, Chief Engineer, 2nd Engineer, Chief Stewardess, Stewardess, Chef, Second Officer, 3rd Engineer, ETO, Butler, Sous Chef, Dive Instructor, Medic)
- A `SME_MATRIX_PATCHES` lookup for specific `(position, yacht_type)` combinations with context-specific trait adjustments (e.g. Captain × sailing_racing, Chef × megayacht)
- Accessor: `get_ideal_profile(position, yacht_type=None)` — fallback to generic when no override

### Use Cases (business orchestration)

```python
# engine/use_cases/recruitment.py
decision = compute_recruitment_decision(snapshot, vessel_params, crew_snapshots, captain_vector)
# → RecruitmentDecision(verdict=HIRE/CONDITIONAL/DISQUALIFY, global_score, alerts)

# engine/use_cases/management.py
health = compute_team_health(crew_snapshots, vessel_params)
# → TeamHealthReport(status=HEALTHY/AT_RISK/CRITICAL, alerts)
```

---

## Scientific Foundations

### T-IRT — Thurstonian Item Response Theory (CUTTY SARK)

**Decision question:** *What are the candidate's true Big Five latent traits, corrected for social desirability and ipsativity bias?*

The CUTTY SARK is a 60-item forced-choice assessment using the IPIP-120 item pool. Each item forces a binary trade-off between statements from different Big Five domains — eliminating acquiescence bias.

#### Probit Model

For each pair $l$ opposing item $i$ (left) and item $j$ (right):

$$P(y_l = 1 \mid \theta) = \Phi\!\left(\frac{(\mu_i - \mu_j) + (\lambda^\text{eff}_i \cdot \theta_{d_i} - \lambda^\text{eff}_j \cdot \theta_{d_j})}{\sqrt{\psi_i^2 + \psi_j^2}}\right)$$

Where $\lambda^\text{eff}_i = \lambda_i \times \text{score\_weight}_i$ — reversed items (`score_weight = -1`) contribute negatively to their domain trait.

#### MAP Estimation

$$\theta^* = \arg\max_\theta \left[\sum_{l=1}^{60} \ln P(y_l \mid \theta) - \frac{1}{2}\sum_{k=1}^{5} \theta_k^2\right]$$

$N(0, I)$ prior makes $\theta^*$ directly interpretable as Z-scores. Optimised via BFGS.

**Implementation:** `engine/psychometrics/tirt_scoring.py`

**References:**
- Brown, A., & Maydeu-Olivares, A. (2011). *Educational and Psychological Measurement*, 71(3), 460–502.
- Maples, J. L., et al. (2014). *Psychological Assessment*, 26(4), 1116–1138.

### Sociogram — Dyad Compatibility

$$D_{ij} = 0.55 \cdot (1 - |C_i - C_j|/100) + 0.25 \cdot (A_i + A_j)/200 + 0.20 \cdot (ES_i + ES_j)/200$$

- **C similarity (α=0.55):** Homophily on work ethics — dominant predictor of dyad stability
- **A additive (β=0.25):** Complementarity term, not similarity — high A compounds well-being
- **ES mean (γ=0.20):** Collective resilience buffer (George, 1990)

**Implementation:** `engine/benchmarking/matrice.py`

### Key References

- Kristof-Brown, A. L., Zimmerman, R. D., & Johnson, E. C. (2005). *Personnel Psychology*, 58(2), 281–342.
- Bell, S. T. (2007). *Journal of Applied Psychology*, 92(3), 595–615.
- Schmidt, F. L., & Hunter, J. E. (1998). *Psychological Bulletin*, 124(2), 262–274.
- Bakker, A. B., & Demerouti, E. (2007). *Journal of Managerial Psychology*, 22(3), 309–328.
- Ravlin, E. C., & Meglino, B. M. (1987). *Journal of Applied Psychology*, 72, 666–673.
- Lau, D. C., & Murnighan, J. K. (1998). *Academy of Management Review*, 23(2), 325–340.
- Felps, W., Mitchell, T. R., & Byington, E. (2006). *Research in Organizational Behavior*, 27, 175–222.
- George, J. M. (1990). *Journal of Applied Psychology*, 75(2), 107–116.
- Graen, G. B., & Uhl-Bien, M. (1995). *The Leadership Quarterly*, 6(2), 219–247.

---

## Setup

### Prerequisites

- Python 3.12
- PostgreSQL 14+
- Tesseract OCR binary (for document verification)

### Install

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env — see Environment Variables section
```

---

## Environment Variables

```bash
# Application
PROJECT_NAME="Radiant Analytics"
DEBUG=False
BASE_URL="https://api.yourdomain.com"

# Database
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/harmony"

# Auth
SECRET_KEY=""       # REQUIRED — openssl rand -hex 32
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=30

# SMTP
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""

# S3-compatible storage (optional)
S3_BUCKET=""
S3_ACCESS_KEY=""
S3_SECRET_KEY=""
S3_ENDPOINT_URL=""
```

---

## Database Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1
alembic current
```

Migrations live in `migrations/versions/`. Note: PostgreSQL named ENUMs require manual `ALTER TYPE ... ADD VALUE IF NOT EXISTS` — Alembic cannot autogenerate these.

### Seed data

```bash
python -m app.seed.seed                        # Full : drop + recreate + seed tout
python -m app.seed.seed --module environment   # Reseed uniquement employers/candidates/yachts
python -m app.seed.seed --module tests         # Reseed uniquement les 7 catalogues
python -m app.seed.seed --module surveys       # Reseed uniquement surveys + pulses
```

---

## Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: `http://localhost:8000/docs` · Health check: `GET /health`

---

## Running Tests

```bash
# Full suite (1104 tests, 0 failures)
pytest tests/ -v

# By layer
pytest tests/engine/ -v -m engine     # Pure functions — no DB, no mocks
pytest tests/ -v -m service           # Service layer — mocked AsyncSession
pytest tests/ -v -m router            # Router layer — httpx AsyncClient

# Coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Test structure

```
tests/
├── conftest.py
├── engine/
│   ├── psychometrics/             # scoring, snapshot, tirt_scoring, normalizer, reliability
│   ├── recruitment/
│   │   └── pe_fit/
│   │       ├── test_master.py         # PEFitResult, global_score, weights
│   │       ├── test_da_fit.py         # Demands-Abilities
│   │       ├── test_ns_fit.py         # Needs-Supplies (JD-R)
│   │       ├── test_pg_fit.py         # Person-Group (Bell 2007)
│   │       ├── test_ps_fit.py         # Person-Supervisor (LMX)
│   │       ├── test_po_values.py      # Person-Organisation (CES values)
│   │       ├── test_profiles_extended.py   # 16 positions
│   │       ├── test_profiles_matrix.py     # SME matrix (position × yacht_type)
│   │       └── test_vessel_profile.py      # YachtStructuralProfile
│   ├── use_cases/                 # recruitment, management, training, talent, rps
│   └── benchmarking/              # diagnosis, matrice (sociogram)
└── modules/                       # service + router tests per module
    ├── auth/ · identity/ · crew/ · assessment/
    ├── recruitment/ · survey/ · vessel/
```

### Test layers

| Layer | Strategy | Tools |
|-------|----------|-------|
| Engine | Direct function calls, no mocks | pytest, parametrize |
| Service | Mock repos via `AsyncMock`; real service logic | pytest-mock |
| Router | HTTP round-trip via `httpx.AsyncClient + ASGITransport` | dependency_overrides |

---

## API Reference

All protected endpoints require `Authorization: Bearer <access_token>`.

| Module | Prefix | Auth |
|--------|--------|------|
| Auth | `/auth` | Public + Bearer |
| Identity | `/identity` | `CrewDep` / `EmployerDep` |
| Crew | `/crew` | `CrewDep` / `EmployerDep` |
| Assessment | `/assessments` | `CrewDep` / `EmployerDep` |
| Recruitment | `/recruitment` | `EmployerDep` |
| Survey | `/surveys` | `CrewDep` / `EmployerDep` |
| Vessel | `/vessels` | `EmployerDep` |

Full schema at `/docs`.

### Auth roles

| Dependency | Role | Returns |
|------------|------|---------|
| `UserDep` | Any authenticated | `User` |
| `CrewDep` | `CANDIDATE` | `CrewProfile` |
| `EmployerDep` | `CLIENT` or `ADMIN` | `EmployerProfile` |
| `AdminDep` | `ADMIN` | `User` |

---

## Known Issues & Backlog

### Critical (blocks production)

- [ ] `SECRET_KEY` defaults to unsafe placeholder — rotate before any deployment
- [ ] `allow_origins=["*"]` in CORS — restrict to frontend domain
- [ ] `DEBUG=True` in `.env` — exposes stack traces
- [ ] `app.state.limiter` never set in `main.py` — rate limiter defined but inactive
- [ ] `infra/email.py` empty — survey invitations will silently fail

### Application bugs

- [ ] **`SurveyTriggerIn` missing `yacht_id`** — `modules/survey/router.py:37` accesses `payload.yacht_id` but the schema has no such field → `AttributeError 500`. Fix: add `yacht_id: int` to `SurveyTriggerIn`.

### High priority

- [ ] Endpoints sociogramme (`GET /crew/{id}/sociogram`, `GET /crew/{id}/simulate/{cid}`)
- [ ] Module Training (ORM models, 5 endpoints, seed, trigger logic in assessment service)
- [ ] Replace `print()` with `logging.getLogger(__name__)` throughout
- [ ] Background task error handling — currently swallows exceptions silently

### Medium priority

- [ ] Wire S3 storage in `infra/storage.py`
- [ ] Physical Fit engine (`pj_fit/physical_fit/`) — feeds `snapshot['maritime_tolerance']` from METS
- [ ] Mobility Fit engine (`pj_fit/mobility_fit/`) — feeds `snapshot['mobility_profile']` from MMFS
- [ ] P-O Fit (Temps 2) — value congruence via OCP/Q-Sort (`po_fit/` currently empty)
- [ ] Centile normalization on candidate pool (replace raw scores with percentiles)
- [ ] Docker + docker-compose setup

### Psychometric validation roadmap

- [ ] CFA (confirmatory factor analysis) on METS, MMFS, CES — N ≥ 200 required
- [ ] Calibrate PSI breakpoints on real field data before production use
- [ ] Calibrate CUTTY SARK item parameters (λ, μ) from ≥ 200 field administrations
- [ ] Population norm tables for maritime-specific percentile computation
