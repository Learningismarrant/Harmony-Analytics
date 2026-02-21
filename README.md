# Harmony Analytics Backend

## 📋 Project Overview

**Harmony** is a psychometric analytics platform designed for **crew recruitment and management in superyacht operations**. The backend provides:

- 🧪 **Psychometric assessment scoring** (test result calculations, reliability validation, normalization)
- 👥 **Candidate-to-team matching** (skills alignment, team dynamics, pool comparison)
- 🤝 **Team harmony analysis** (cohesion metrics, volatility tracking, performance diagnostics)
- 🎯 **Recruitment optimization** (success prediction, what-if simulations, candidate ranking)
- 🔐 **Identity & authentication** management
- 📊 **Survey & assessment** campaign management
- 🚢 **Vessel/yacht** crew management

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, PostgreSQL, NumPy/Pandas

---

## 🏗️ Backend Architecture

The backend follows a **modular + transversal engine** pattern:

```
backend/app/
│
├── main.py                        # FastAPI app entry point
│
├── core/                          # Infrastructure & configuration
│   ├── config.py                  # Settings (DB, env variables, CORS)
│   ├── database.py                # SQLAlchemy engine & session management
│   ├── security.py                # Password hashing, JWT tokens
│   └── __pycache__/
│
├── engine/                        # Pure computation layer (NO database)
│   │                              # Services that receive data, return results
│   │                              # Reused across multiple modules
│   │
│   ├── psychometrics/
│   │   ├── scoring.py             # calculate_test_results() — raw score to percentile
│   │   ├── reliability.py         # Desirability detection, timing validation
│   │   ├── normalizer.py          # Z-score normalization
│   │   ├── formatter.py           # format_user_profile() — structure psychometric output
│   │   └── snapshot.py            # Historical snapshot management
│   │
│   ├── matching/                  # Candidate comparison algorithms
│   │   ├── sme.py                 # Candidate vs Subject Matter Expert fit
│   │   ├── pool.py                # Candidate vs candidate pool analysis
│   │   └── team.py                # Candidate vs existing team compatibility
│   │
│   ├── team/                      # Team-level analytics
│   │   ├── harmony.py             # Team cohesion & performance metrics
│   │   ├── volatility.py          # TVI + HCD (Team Volatility Index)
│   │   └── diagnosis.py           # Text-based insights & diagnostic matrix
│   │
│   ├── ml/                        # Machine learning models
│   │   ├── anova.py               # Statistical variance analysis
│   │   ├── regression.py          # Predictive regression models
│   │   └── model_store.py         # Model persistence & versioning
│   │
│   ├── recruitment/               # Recruitment pipeline algorithms
│   │   ├── p_ind.py               # Individual prediction factors
│   │   ├── f_team.py              # Team fit factors
│   │   ├── f_env.py               # Environment fit factors
│   │   ├── f_lmx.py               # Leader-member exchange factors
│   │   ├── master.py              # Ŷ_success — master prediction algorithm
│   │   └── simulator.py           # What-if scenario analysis (delta modeling)
│   │
│   ├── benchmarking/
│   │   └── benchmarking.py        # Comparison & normalization against benchmarks
│   │
│   └── verif/                     # Verification & OCR
│       ├── ocr.py                 # Optical character recognition for documents
│       └── promete.py             # Document verification
│
├── modules/                       # Vertical slices (domain-specific)
│   │                              # Each module owns: models, schemas, DB, service logic
│   │                              # Minimal cross-module dependencies
│   │
│   ├── assessment/                # Test creation, deployment, scoring
│   │   ├── models.py              # Database models (Assessment, Question, Response)
│   │   ├── schemas.py             # Request/response validation (Pydantic)
│   │   ├── repository.py          # SQL queries (zero business logic)
│   │   ├── service.py             # Business logic + engine calls
│   │   └── router.py              # HTTP endpoints (/assessments/*)
│   │
│   ├── crew/                      # Crew member profiles & management
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py              # (/crew/*)
│   │
│   ├── recruitment/               # Candidate pipeline & job matching
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py              # (/recruitment/*)
│   │
│   ├── vessel/ (yacht)            # Yacht/vessel operations
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py              # (/vessels/*)
│   │
│   ├── survey/                    # Pulse surveys, engagement tracking
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py              # (/survey/*)
│   │
│   ├── identity/                  # User profiles, attributes
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py              # (/identity/*)
│   │
│   ├── gateway/                   # Cross-cutting concerns, external integrations
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py              # (/gateway/*)
│   │
│   └── auth/                      # Authentication, token management
│       ├── schemas.py
│       ├── service.py
│       └── router.py              # (/auth/*)
│
├── shared/                        # Shared utilities across all modules
│   ├── __init__.py
│   ├── deps.py                    # Dependency injection (DB session, auth)
│   ├── enums.py                   # Shared enumerations
│   ├── limiter.py                 # Rate limiting
│   └── models/
│       ├── __init__.py
│       ├── User.py                # User base model
│       ├── Assessment.py          # Assessment base model
│       ├── Yacht.py               # Yacht base model
│       ├── Campaign.py            # Campaign base model
│       ├── Pulse.py               # Pulse survey base model
│       └── Survey.py              # Survey base model
│
├── content/                       # Static business data
│   ├── sme_profiles.py            # JOB_PROFILES_NORM, skill categories, standards
│   ├── feedback.py                # Pre-written feedback templates
│   ├── advice.py                  # Coaching advice & recommendations
│   └── seed/
│       └── psycho_tests.py        # Test definitions (questions, scoring rules)
│
├── infra/                         # External service integrations
│   ├── email.py                   # Email sending (reports, notifications)
│   ├── storage.py                 # File storage (S3, GCS, local)
│   └── notifications.py           # Push notifications, alerts
│
└── tests/                         # Test suite
    ├── unit/
    │   └── engine/                # Pure function tests (no DB)
    └── integration/
        └── modules/               # End-to-end module tests
```

---

## 🔄 Data Flow & Module Patterns

**Typical request flow:**

```
HTTP Request
    ↓
Router (endpoints)
    ↓
Service (orchestration) → calls Engine & Repository
    ↓
Engine (computation)        Repository (DB queries)
    ↓                        ↓
Result combine & format
    ↓
HTTP Response (JSON)
```

**Key principles:**

- **Engine modules** are stateless, database-agnostic computation
- **Service modules** orchestrate repo calls + engine calls
- **Repositories** handle all SQL; they don't contain business logic
- **Routers** only route; they call services
- **Shared models** define base classes for inheritance

---

## 🚀 What's Working

- ✅ FastAPI application structure & routing
- ✅ Database connection & ORM (SQLAlchemy)
- ✅ Module registration (auth, crew, assessment, vessel, recruitment, survey, identity, gateway)
- ✅ Psychometric scoring engine (basic implementation)
- ✅ Team matching algorithms
- ✅ Authentication & JWT tokens
- ✅ CORS middleware
- ✅ Health check endpoint

---

## 📋 TODO / Outstanding Tasks

- [ ] **Database migrations** — Set up Alembic for schema versioning
- [ ] **Complete service implementations** — Flesh out service.py for all modules (currently partial)
- [ ] **API documentation** — Add OpenAPI schemas for all endpoints
- [ ] **Error handling** — Standardize exception handling & HTTP error responses
- [ ] **Logging** — Add structured logging across all modules
- [ ] **Testing** — Set up comprehensive unit & integration tests
  - [ ] Engine module tests (pure functions)
  - [ ] Service layer tests (mocked repos)
  - [ ] Integration tests (full request/response cycles)
- [ ] **Validation** — Tighten Pydantic schemas (required fields, constraints)
- [ ] **Performance** — Add database indexing strategy
- [ ] **Caching** — Implement Redis caching for expensive computations
- [ ] **Email service** — Implement actual email sending (SendGrid, SMTP)
- [ ] **File storage** — Configure cloud storage integration (S3, GCS)
- [ ] **Monitoring** — Add performance metrics & alerting
- [ ] **Documentation** — Add docstrings to all functions & classes
- [ ] **Security hardening** — Rate limiting per endpoint, input sanitization
- [ ] **Deployment** — Docker setup, environment configuration, CI/CD pipeline
- [ ] **OCR/verification module** — Complete document verification pipeline
- [ ] **ML model endpoints** — Set up model serving for recruitment & team predictions
