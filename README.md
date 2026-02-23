# Harmony Analytics — Backend

Psychometric analytics platform for crew recruitment and team management in superyacht operations.

**Stack:** Python 3.12, FastAPI 0.128, SQLAlchemy 2.0 async, PostgreSQL, asyncpg, Alembic, Pydantic 2, scikit-learn, NumPy/Pandas

---

## Table of Contents

1. [Architecture](#architecture)
2. [Domain Model](#domain-model)
3. [Recruitment Engine](#recruitment-engine)
4. [Setup](#setup)
5. [Environment Variables](#environment-variables)
6. [Database Migrations](#database-migrations)
7. [Running the Server](#running-the-server)
8. [Running Tests](#running-tests)
9. [API Reference](#api-reference)
10. [Known Issues & Backlog](#known-issues--backlog)

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
│   ├── enums.py           # UserRole, YachtPosition, CampaignStatus, ApplicationStatus, …
│   ├── limiter.py         # slowapi rate limiter (defined — not yet attached to app)
│   └── models/            # SQLAlchemy ORM models (shared across modules)
│       ├── User.py        # User, CrewProfile, EmployerProfile, UserDocument
│       ├── Yacht.py       # Yacht, CrewAssignment
│       ├── Assessment.py  # TestCatalogue, Question, TestResult
│       ├── Campaign.py    # Campaign, CampaignCandidate
│       ├── Survey.py      # Survey, SurveyResponse, RecruitmentEvent, ModelVersion
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
│   │   ├── scoring.py     # Likert + cognitive scoring, reliability detection
│   │   ├── snapshot.py    # Rebuilds CrewProfile.psychometric_snapshot from TestResult set
│   │   ├── normalizer.py  # Score normalization against population norms
│   │   ├── formatter.py   # Report formatting per viewer context
│   │   └── reliability.py # Response bias, speedrun detection
│   │
│   ├── recruitment/
│   │   ├── DNRE/          # Stage 1: normative-relative fit (g_fit, centile, safety_level)
│   │   │   ├── master.py
│   │   │   ├── global_fit.py
│   │   │   ├── centile_rank.py
│   │   │   ├── safety_barrier.py
│   │   │   └── sme_score.py
│   │   ├── MLPSM/         # Stage 2: team-fit prediction (Ŷ = β₁P_ind + β₂F_team + β₃F_env + β₄F_lmx)
│   │   │   ├── master.py
│   │   │   ├── p_ind.py
│   │   │   ├── f_team.py
│   │   │   ├── f_env.py
│   │   │   ├── f_lmx.py
│   │   │   └── simulator.py
│   │   └── pipeline.py    # Orchestrates DNRE → MLPSM for all candidates in a campaign
│   │
│   ├── benchmarking/
│   │   ├── diagnosis.py   # Performance × Cohesion matrix, TVI, HCD, short-term prediction
│   │   └── matrice.py     # Sociogram data for dashboard visualization
│   │
│   ├── ml/
│   │   ├── regression.py  # OLS β-fitting when n_samples > 150
│   │   ├── anova.py       # Cross-yacht toxicity detection
│   │   └── model_store.py # ModelVersion persistence
│   │
│   └── verif/
│       ├── ocr.py         # pytesseract extraction from uploaded documents
│       └── promete.py     # Promete API integration for official maritime cert verification
│
├── infra/
│   ├── storage.py         # File upload (local simulation; S3 config present, not wired)
│   ├── email.py           # SMTP/SendGrid — not implemented
│   └── notifications.py
│
├── content/               # Static business data (job norms, feedback templates, advice)
│   ├── sme_profiles.py
│   ├── feedback.py
│   └── advice.py
│
└── seed/
    ├── seed_environment.py
    └── seed_tests_surveys.py
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

Rather than recomputing psychometric aggregates on every dashboard load, the application maintains two denormalized JSON caches:

- `CrewProfile.psychometric_snapshot` — rebuilt **synchronously** after each test submission. Contains Big Five, cognitive, motivation, resilience, leadership preferences.
- `Yacht.vessel_snapshot` — rebuilt **in a background task** after crew changes or snapshot updates. Contains harmony metrics, baseline F_team score, crew count.
- `EmployerProfile.fleet_snapshot` — rebuilt periodically across all managed yachts.

This trades write-time complexity for O(1) dashboard reads.

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

TestCatalogue → Question → TestResult
  └── Feeds into psychometric_snapshot rebuild

Survey → SurveyResponse
  └── intent_to_stay (0–100) feeds y_actual in RecruitmentEvent

RecruitmentEvent             one record per hiring decision
  ├── y_success_predicted    Ŷ from MLPSM at decision time
  ├── beta_weights_snapshot  β₁–β₄ at prediction time (immutable, for audit)
  └── y_actual               filled post-hire from SurveyResponse.intent_to_stay

ModelVersion                 OLS-fitted β weights, versioned
  └── is_active              single active version at a time
```

---

## Recruitment Engine

The matching pipeline runs in two independent stages. Both scores are surfaced separately to the recruiter — they are not collapsed into a single opaque number.

### Stage 1 — DNRE (Dynamic Normative-Relative Engine)

Answers: *Is this candidate a valid profile for this position type?*

- **Normative dimension:** candidate traits vs. position benchmark norms (`sme_profiles.py`)
- **Relative dimension:** percentile rank within the current applicant pool
- **Safety barrier:** DISQUALIFIED candidates are hard-filtered before Stage 2

Output: `g_fit` (0–100), `centile`, `SafetyLevel` (CLEAR / ADVISORY / HIGH_RISK / DISQUALIFIED)

### Stage 2 — MLPSM (Multi Level Predictive Stability Model)

Answers: *Will this candidate succeed on this specific yacht with this specific team?*

```
Ŷ_success = β₁·P_ind + β₂·F_team + β₃·F_env + β₄·F_lmx
```

| Component | Description | Default β |
|-----------|-------------|-----------|
| P_ind | Individual performance (conscientiousness, GCA, autonomy drive) | 0.25 |
| F_team | Team compatibility (jerk filter, faultline index, emotional buffer) | 0.35 |
| F_env | Environmental fit — JD-R job demands vs. candidate resources | 0.20 |
| F_lmx | Leader-member exchange — captain style vs. candidate preferences | 0.20 |

**F_team components:**
- Jerk Filter: `min(Agreeableness)` across crew — one highly disagreeable member degrades the whole team score
- Faultline Index: `σ(Conscientiousness)` — high variance predicts conflict
- Emotional Buffer: `μ(EmotionalStability)` — team-level stress resilience

**Model versioning (learning loop):**
- v1.0: seeded with literature priors (Schmidt & Hunter 1998, Bakker & Demerouti JD-R 2007)
- v2+: OLS retrain triggered when `n_samples > 150` RecruitmentEvents with `y_actual` populated
- β weights snapshot is stored immutably at each hiring decision for reproducibility

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
# Edit .env — see Environment Variables section below
```

---

## Environment Variables

```bash
# Application
PROJECT_NAME="Harmony Analytics"
DEBUG=False                     # Never True in production
BASE_URL="https://api.yourdomain.com"

# Database
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/harmony"

# Auth
SECRET_KEY=""                   # REQUIRED — generate with: openssl rand -hex 32
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=30

# SMTP (required for survey invitations, hiring notifications)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER=""
SMTP_PASSWORD=""

# SendGrid (alternative to SMTP)
SENDGRID_API_KEY=""

# S3-compatible storage (optional, falls back to local uploads/)
S3_BUCKET=""
S3_ACCESS_KEY=""
S3_SECRET_KEY=""
S3_ENDPOINT_URL=""
CDN_BASE_URL=""
```

> `SECRET_KEY` must be set to a cryptographically random value. An empty or default key is a critical security vulnerability.
> Generate one with: `openssl rand -hex 32`

---

## Database Migrations

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1

# Check current revision
alembic current
```

Migrations live in `migrations/versions/`. The Alembic env converts the `+asyncpg` URL to a synchronous driver for migration execution.

### Seed data

```bash
python -m app.seed.seed_environment       # Base config, model versions
python -m app.seed.seed_tests_surveys     # Psychometric test catalogue + questions
```

---

## Running the Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

Health check: `GET /health`

---

## Running Tests

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Engine layer only (no DB required)
pytest tests/engine/ -v
```

### Test structure

```
tests/
├── engine/            # Pure function tests — no DB, no fixtures required
│   └── recruitment/
│       └── dnre/
└── integration/       # Full request/response cycles against a test DB
```

Current coverage is limited to the DNRE engine. The engine layer (scoring, DNRE, MLPSM sub-modules) is the highest-priority testing target as it contains the core algorithmic logic.

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
| Gateway | `/gateway` | `EmployerDep` |

Full schema available at `/docs` when the server is running.

### Auth roles

| Dependency | Role required | Returns |
|------------|---------------|---------|
| `UserDep` | Any authenticated | `User` |
| `CrewDep` | `CANDIDATE` | `CrewProfile` |
| `EmployerDep` | `CLIENT` or `ADMIN` | `EmployerProfile` |
| `AdminDep` | `ADMIN` | `User` |

---

## Known Issues & Backlog

### Critical (blocks production)

- [ ] `SECRET_KEY` defaults to an unsafe placeholder — rotate before any deployment
- [ ] `allow_origins=["*"]` in CORS config — restrict to frontend domain
- [ ] `DEBUG=True` in `.env` — exposes stack traces
- [ ] `app.state.limiter` never set in `main.py` — rate limiter is defined but inactive
- [ ] `infra/email.py` is empty — survey invitations and hiring notifications will silently fail

### High priority

- [ ] Replace `print()` calls with `logging.getLogger(__name__)` throughout
- [ ] Background task error handling — currently swallows exceptions silently; needs `try/except` + structured logging
- [ ] File upload size limit — no max size validation on document upload endpoint
- [ ] Add composite index on `daily_pulses(crew_profile_id, yacht_id, created_at)` — required for TVI queries at scale
- [ ] Unit test coverage for engine layer — target 90%+ on scoring, DNRE, MLPSM sub-modules

### Medium priority

- [ ] Wire S3-compatible storage in `infra/storage.py` — currently writes to local `uploads/` directory
- [ ] Define psychometric basis for `captain_leadership_vector` — currently populated manually with no validated instrument
- [ ] Add R² bounds check on OLS retrain — prevent theoretically invalid β values (e.g., negative weights)
- [ ] Integration tests for assessment submission → snapshot propagation flow
- [ ] Docker + docker-compose setup

### Low priority

- [ ] Redis caching layer for vessel_snapshot (currently in-process only)
- [ ] Prometheus metrics endpoint
- [ ] WebSocket endpoint for live dashboard updates
- [ ] Population norm tables for maritime-specific percentile computation
