# Harmony Analytics — Backend

Psychometric analytics platform for crew recruitment and team management in superyacht operations.

**Stack:** Python 3.12, FastAPI 0.128, SQLAlchemy 2.0 async, PostgreSQL, asyncpg, Alembic, Pydantic 2, scikit-learn, NumPy/Pandas

---

## Table of Contents

1. [Architecture](#architecture)
2. [Domain Model](#domain-model)
3. [Recruitment Engine](#recruitment-engine)
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
│   ├── enums.py           # UserRole, YachtPosition, CampaignStatus, ApplicationStatus, …
│   ├── limiter.py         # slowapi rate limiter (defined — not yet attached to app)
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

JobWeightConfig              DB-injectable weight configuration (P3)
  ├── sme_weights (JSON)     SME trait weights per competency — overrides DNRE defaults
  ├── omega_gca/C/interaction P_ind omegas — overrides p_ind.py module constants
  └── is_active              single active config at a time (ML scripts update nightly)
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

## Scientific Foundations

This section documents the psychometric and organizational psychology literature underlying each engine component, and maps each theoretical construct to its concrete implementation.

---

### 1. DNRE — Dynamic Normative-Relative Engine

**Decision question:** *Is this candidate a technically valid profile for this position type, and how rare is that profile on the current market?*

The DNRE is a two-pass filter. Pass 1 evaluates absolute competency fit against expert-defined job norms. Pass 2 establishes market position via dynamic percentile ranking. A non-compensatory safety barrier runs in parallel and can veto any candidate regardless of aggregate score.

#### A. SME-Weighted Competency Score

$$S_{i,c} = \frac{\sum_{t=1}^{n} w_t \cdot x_{i,t}}{\sum_{t=1}^{n} w_t}$$

Each competency $c$ (Individual Performance, Team Fit, Environmental Fit, Leadership Fit) is scored as a weighted average of the relevant psychometric traits $x_{i,t}$, with weights $w_t$ set by Subject Matter Expert elicitation.

**Theoretical basis:** Content-oriented validation (Manea, 2020). Traits are not interchangeable — a Chief Engineer's Conscientiousness carries a different weight than a Stewardess's Social Agreeableness. The weight vector encodes domain expertise as a first-class model parameter rather than treating all traits as equally predictive.

**Implementation:** `engine/recruitment/DNRE/sme_score.py` — four competencies (C1–C4) with `DEFAULT_SME_WEIGHTS` derived from maritime-domain priors. Data quality is tracked per trait; missing traits fall back to population medians and flag `PARTIAL_DATA`.

#### B. Dynamic Percentile Rank

$$\Pi_{i,c} = \left( \frac{cf_i + 0.5 \cdot f_i}{N} \right) \times 100$$

$cf_i$ = cumulative frequency below candidate $i$'s score; $f_i$ = frequency at that score; $N$ = pool size. This is Tukey's mid-rank formula, which handles ties symmetrically.

**Theoretical basis:** Social Comparison Theory (Festinger, 1954) applied to labour market dynamics (Kristof-Brown et al., 2005). An absolute score of 80/100 is meaningless without knowing that the current applicant pool averages 90. The percentile corrects for cohort inflation and gives recruiters the true market scarcity of a profile.

**Implementation:** `engine/recruitment/DNRE/centile_rank.py` — computes individual and batch percentiles, labels reliability by pool size (LOW < 2, MEDIUM < 5, HIGH ≥ 5), and annotates with human-readable labels ("Top 10%", etc.).

#### C. Adjusted Global Fit with Non-Compensatory Barrier

$$G_{\text{fit}} = \frac{1}{K} \sum_{c=1}^{K} S_{i,c} \qquad \text{subject to } \prod_{t \in \mathcal{T}_{\text{critical}}} \mathbb{1}\!\left(x_{i,t} \geq S_{\min,t}\right) = 1$$

The global fit is the unweighted mean of the $K$ competency scores. The product of indicator functions enforces a hard floor: if any safety-critical trait falls below its minimum threshold $S_{\min,t}$, the candidate is vetoed regardless of their aggregate score.

**Theoretical basis:** Non-compensatory selection models (Barrick & Mount, 1991). In high-consequence maritime environments, Emotional Stability below a critical threshold cannot be compensated by exceptional GCA. The indicator function formalises this as a safety barrier rather than a soft penalty — a design choice grounded in aviation and maritime risk psychology.

**Implementation:** `engine/recruitment/DNRE/safety_barrier.py` — three veto levels:

| Level | Threshold | Effect |
|-------|-----------|--------|
| HARD | ES < 15 or Agreeableness < 15 | `DISQUALIFIED` — blocked from Stage 2 |
| SOFT | ES 15–30 or Agreeableness 15–30 or Conscientiousness < 25 | `HIGH_RISK` — surfaced to recruiter |
| ADVISORY | Resilience < 35 | `ADVISORY` — annotation only |

---

### 2. MLPSM — Multi-Level Predictive Stability Model

**Decision question:** *Will this specific candidate stay, perform, and integrate on this specific yacht with this specific team?*

The MLPSM moves from the individual to the system. Each sub-component isolates a distinct causal mechanism of attrition and team failure.

#### Master Equation (v1 — Linear)

$$\hat{Y}_{\text{success}} = \beta_1 P_{\text{ind}} + \beta_2 F_{\text{team}} + \beta_3 F_{\text{env}} + \beta_4 F_{\text{lmx}}$$

$$\hat{Y} \in [0, 100], \quad \text{clamped via } \max(0, \min(100, \hat{Y}))$$

Default β weights (literature priors, v1.0):

| Term | β | Rationale |
|------|---|-----------|
| $\beta_1$ P_ind | 0.25 | Individual competency ceiling |
| $\beta_2$ F_team | 0.35 | Team dynamics dominate retention in confined-space crews |
| $\beta_3$ F_env | 0.20 | Structural burnout risk |
| $\beta_4$ F_lmx | 0.20 | Management relationship quality |

**v1 active (SKILL.md P1):** The raw score is passed through a **sigmoid** $P(\text{success}) = 1 / (1 + e^{-k(\hat{Y} - 50)})$ centred at 50 to model the psychological tipping point at which a crew member decides to leave (Schelling, 1978). This transforms the unbounded linear sum into a probability-like output in [0, 100] before clamping. Planned for v2: interaction term $\beta_5 (F_{\text{env}} \times \text{TypeYacht})$ for Heavy Charter non-linearity.

**Implementation:** `engine/recruitment/MLPSM/master.py` — `compute()`, `compute_with_delta()`, `compute_batch()`. β weights are passed explicitly at call time; `MLPSMResult.to_event_snapshot()` serialises them immutably for audit.

#### A. Individual Performance Potential — $P_{\text{ind}}$

$$P_{\text{ind}} = \omega_1 \cdot GCA + \omega_2 \cdot C + \omega_3 \cdot \frac{GCA \times C}{100}$$
$$\omega_1 = 0.55,\quad \omega_2 = 0.35,\quad \omega_3 = 0.10 \qquad (\Sigma\,\omega = 1.0 \text{ at } GCA=C=100)$$

The interaction term $\omega_3 \cdot (GCA \times C / 100)$ captures the synergistic effect: cognitive capacity is only mobilised when the motivation to apply effort (Conscientiousness) is present. A candidate with GCA=90 and C=20 is penalised relative to GCA=70 and C=75 — capability without engagement is not enough.

**Theoretical basis:** Schmidt & Hunter (1998) — the combination of GCA and Conscientiousness is the strongest predictor of job performance. GCA sets the learning ceiling; Conscientiousness determines whether that ceiling is reached through sustained effort.

**Injectable weights (P3):** omegas are resolved at runtime from `JobWeightConfig` if an active config exists in the DB — ML scripts can update nightly without touching Python code. Module constants (`OMEGA_GCA`, `OMEGA_CONSCIENTIOUSNESS`, `OMEGA_INTERACTION`) are the fallback.

**Implementation:** `engine/recruitment/MLPSM/p_ind.py` — extracts GCA from cognitive sub-scores (logical, numerical, verbal mean), applies a reliability flag if `n_tests = 0` (`GCA_MISSING`), tracks data quality penalty of −0.35 for absent cognitive data.

#### B. Team Friction — $F_{\text{team}}$

$$F_{\text{team}} = w_a \cdot \min(A_i) - w_c \cdot \sigma(C_i) + w_e \cdot \mu(ES_i)$$
$$w_a = 0.40,\quad w_c = 0.30,\quad w_e = 0.30$$

Three orthogonal mechanisms, each with an independent literature source:

| Term | Construct | Theory |
|------|-----------|--------|
| $\min(A_i)$ | Jerk Filter | Bad Apple Effect (Felps et al., 2006; Bell, 2007) — one toxic member degrades collective output disproportionately. The minimum, not the mean, is the load-bearing statistic. |
| $\sigma(C_i)$ | Faultline Index | Faultline Theory (Lau & Murnighan, 1998) — high variance in conscientiousness creates a structural rift between the "rigorous" and "relaxed" sub-groups, predictive of latent conflict. Standard deviation operationalises faultline strength. |
| $\mu(ES_i)$ | Emotional Buffer | Collective Affective Tone (George, 1990) — mean emotional stability sets the team's stress absorption capacity. Low mean = brittle team under charter pressure. |

**Danger thresholds** (implementation):
- `JERK_FILTER_DANGER = 35` → triggers `JERK_RISK` flag
- `FAULTLINE_DANGER = 20` (σ) → triggers `FAULTLINE_RISK` flag
- `ES_MINIMUM_THRESHOLD = 45` (μ) → triggers `EMOTIONAL_FRAGILITY` flag

**Implementation:** `engine/recruitment/MLPSM/f_team.py` — `compute_delta()` isolates the marginal impact of adding a specific candidate to the existing crew (`FTeamDelta.net_impact ∈ {POSITIVE, NEUTRAL, NEGATIVE}`).

#### C. Environmental Load — $F_{\text{env}}$

$$F_{\text{env}} = \frac{R_{\text{yacht}}}{D_{\text{yacht}}} \times \text{Resilience}_{\text{ind}}$$

Where:
- $D_{\text{yacht}} = 0.60 \cdot \text{charter\_intensity} + 0.40 \cdot \text{management\_pressure}$ (demands)
- $R_{\text{yacht}} = 0.40 \cdot \text{salary\_index} + 0.35 \cdot \text{rest\_days\_ratio} + 0.25 \cdot \text{private\_cabin\_ratio}$ (resources)

**Theoretical basis:** Job Demands-Resources model (Bakker & Demerouti, 2007). Burnout is not caused by high demands alone — it occurs when demands structurally exceed resources. The ratio $R/D$ captures the systemic imbalance; individual resilience modulates how much of that imbalance a specific candidate can absorb. A highly resilient candidate on a demanding yacht may score identically to a fragile candidate on a relaxed one — same environmental output, different individual input.

**Burnout risk thresholds** (implementation): ratio < 0.40 = critical, 0.40–0.70 = at risk, 0.70–1.10 = balanced, > 1.50 = comfortable.

**Implementation:** `engine/recruitment/MLPSM/f_env.py` — resilience extracted from dedicated score, falls back to Emotional Stability if absent.

#### D. Leadership Alignment — $F_{\text{lmx}}$

$$F_{\text{lmx}} = \left(1 - \frac{\|L_{\text{capt}} - V_{\text{crew}}\|_2}{d_{\max}}\right) \times 100$$

The 3D leadership space spans: `autonomy_preference`, `feedback_preference`, `structure_imposed`. Euclidean distance between the captain's leadership vector and the crew member's preference vector is normalised by the maximum possible distance $d_{\max} = \sqrt{3}$.

**Theoretical basis:** Leader-Member Exchange theory (Graen & Uhl-Bien, 1995). High-quality LMX relationships (small distance) are empirically associated with lower turnover intent, higher job satisfaction, and greater organisational citizenship behaviour — all critical in the closed social system of a superyacht. The vector distance operationalises misalignment without requiring a direct personality match: what matters is whether the captain's *style* meets the crew member's *needs*.

**Compatibility labels** (implementation): EXCELLENT < 0.25, GOOD 0.25–0.50, TENSION 0.50–0.70, CRITICAL > 0.70.

**Implementation:** `engine/recruitment/MLPSM/f_lmx.py` — extracts captain vector from `Yacht.captain_leadership_vector`; infers crew preferences from `leadership_preferences` snapshot or Big Five proxies.

---

### 3. Sociogram — Pairwise Dyad Compatibility

**Decision question:** *Who should share a cabin? Which two crew members placed on the same watch will create friction vs. synergy?*

$$D_{ij} = \alpha \cdot \underbrace{\left(1 - \frac{|C_i - C_j|}{100}\right)}_{\text{Work-ethic similarity}} + \beta \cdot \underbrace{\frac{A_i + A_j}{200}}_{\text{Social energy (additive)}} + \gamma \cdot \underbrace{\frac{ES_i + ES_j}{200}}_{\text{Resilience buffer (mean)}}$$

$$\alpha = 0.55,\quad \beta = 0.25,\quad \gamma = 0.20 \qquad (\alpha + \beta + \gamma = 1.0)$$

**Design notes (SKILL.md V1, P2):**

- **C is dominant (α > β):** Shared work ethics (Conscientiousness similarity) is the strongest predictor of dyad stability in confined professional environments. Divergent standards create chronic friction.
- **A is additive complementarity, not similarity:** $f(A_i+A_j) = (A_i+A_j)/200$ rewards both members having high social energy — the collaborative pair compounds well-being. The old similarity term `1-|ΔA|/100` penalised a pairing of (high, low) which is psychologically inaccurate: one very agreeable member positively influences the other.
- **ES is the mean, not the product:** The product $\frac{ES_a}{100} \times \frac{ES_b}{100}$ is too harsh — one emotionally fragile member would destroy any pair score. The mean models the team's collective resilience buffer more faithfully (George, 1990).

**Theoretical basis:**

- **Homophily principle** (McPherson et al., 2001): on values and work-ethic dimensions, high dissimilarity in Conscientiousness generates chronic friction — operationalised as $1-|C_i-C_j|/100$.
- **Sociometry** (Moreno, 1934): structured pairwise compatibility measurement predicts sub-group formation and latent conflict before they manifest behaviourally.
- **Collective Affective Tone** (George, 1990): mean Emotional Stability sets the dyad's stress absorption capacity.

**Implementation:** `engine/benchmarking/matrice.py` — `compute_sociogram()` returns `SociogramNode` and `SociogramEdge` objects for 3D visualisation. Edge colours: green (synergy, $D > 0.70$), blue (neutral), red (friction, $D < 0.30$). `compute_candidate_preview()` shows real-time delta on the existing sociogram when a candidate is dragged in.

---

### Summary: Decision Architecture

```
Candidate psychometric snapshot
        │
        ▼
┌───────────────────────────────────────┐
│  Stage 1 — DNRE                       │
│  ├── SME Score (S_{i,c})  ────────────┤→ G_fit (0–100)
│  ├── Percentile (Π_{i,c}) ────────────┤→ market rank
│  └── Safety Barrier ──────────────────┤→ CLEAR / ADVISORY / HIGH_RISK / DISQUALIFIED
└───────────────────────────────────────┘
        │ CLEAR or ADVISORY only
        ▼
┌───────────────────────────────────────┐
│  Stage 2 — MLPSM                      │
│  ├── P_ind  (ω₁·GCA + ω₂·C + ω₃·GCA×C/100) ─┤→ β₁ = 0.25
│  ├── F_team (min-A, σ-C, μ-ES) ───────┤→ β₂ = 0.35
│  ├── F_env  (JD-R ratio × resilience)─┤→ β₃ = 0.20
│  └── F_lmx  (‖L_capt – V_crew‖) ─────┤→ β₄ = 0.20
│                                        │
│  Ŷ = σ(Σ βᵢ·Fᵢ) via sigmoid ∈ [0,100]│
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Sociogram — Dyad Compatibility       │
│  D_{ij} = α·sim_C + β·f(A+A) + γ·f(ES+ES) │→ cabin / watch assignment
└───────────────────────────────────────┘
        │
        ▼
   RecruitmentEvent stored
   (y_predicted, β_snapshot, y_actual ← post-hire surveys)
        │
        ▼
   OLS retrain when n ≥ 150            → updated β weights
```

**References**

- Bakker, A. B., & Demerouti, E. (2007). The Job Demands-Resources model. *Journal of Managerial Psychology*, 22(3), 309–328.
- Barrick, M. R., & Mount, M. K. (1991). The Big Five personality dimensions and job performance. *Personnel Psychology*, 44(1), 1–26.
- Bell, S. T. (2007). Deep-level composition variables as predictors of team performance. *Journal of Applied Psychology*, 92(3), 595–615.
- Felps, W., Mitchell, T. R., & Byington, E. (2006). How, when, and why bad apples spoil the barrel. *Research in Organizational Behavior*, 27, 175–222.
- Festinger, L. (1954). A theory of social comparison processes. *Human Relations*, 7(2), 117–140.
- George, J. M. (1990). Personality, affect, and behavior in groups. *Journal of Applied Psychology*, 75(2), 107–116.
- Graen, G. B., & Uhl-Bien, M. (1995). Relationship-based approach to leadership. *The Leadership Quarterly*, 6(2), 219–247.
- Kenny, D. A. (1994). *Interpersonal Perception: A Social Relations Analysis*. Guilford Press.
- Kristof-Brown, A. L., Zimmerman, R. D., & Johnson, E. C. (2005). Consequences of individuals' fit at work. *Personnel Psychology*, 58(2), 281–342.
- Lau, D. C., & Murnighan, J. K. (1998). Demographic diversity and faultlines. *Academy of Management Review*, 23(2), 325–340.
- Manea, L. (2020). Content validity and its role in test construction. *Romanian Journal of Applied Psychology*, 22(1).
- McPherson, M., Smith-Lovin, L., & Cook, J. M. (2001). Birds of a feather: Homophily in social networks. *Annual Review of Sociology*, 27, 415–444.
- Moreno, J. L. (1934). *Who Shall Survive?* Beacon House.
- Schmidt, F. L., & Hunter, J. E. (1998). The validity and utility of selection methods in personnel psychology. *Psychological Bulletin*, 124(2), 262–274.

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

# Full suite (481 tests)
pytest tests/ -v

# Engine layer only — no DB, no mocks required
pytest tests/engine/ -v -m engine

# Service layer only — mocked AsyncSession + repos
pytest tests/ -v -m service

# Router layer only — httpx AsyncClient + dependency overrides
pytest tests/ -v -m router

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Test structure

```
tests/
├── conftest.py                   # Fixtures, factories, dependency overrides
│
├── engine/                       # Pure function tests — zero DB, zero mocks
│   ├── psychometrics/
│   │   ├── test_scoring.py       # Likert/cognitive scoring, reliability detection
│   │   ├── test_snapshot.py      # Snapshot rebuild from TestResult set
│   │   ├── test_normalizer.py    # Score normalization against population norms
│   │   └── test_reliability.py  # Response bias and speedrun detection
│   ├── recruitment/
│   │   ├── DNRE/
│   │   │   └── test_dnre.py      # Stage 1: global_fit, centile, safety_level
│   │   ├── MLPSM/
│   │   │   ├── test_master.py    # Ŷ equation, batch computation, MLPSMResult
│   │   │   ├── test_p_ind.py     # P_ind: conscientiousness, GCA, autonomy
│   │   │   ├── test_f_team.py    # F_team: jerk filter, faultline, ES buffer
│   │   │   ├── test_f_env.py     # F_env: JD-R demands vs. resources
│   │   │   └── test_f_lmx.py    # F_lmx: captain style vs. crew preferences
│   │   └── test_pipeline.py      # DNRE → MLPSM orchestration
│   └── benchmarking/
│       ├── test_diagnosis.py     # Perf × Cohesion matrix, TVI, HCD
│       └── test_matrice.py       # Sociogram data generation
│
└── modules/                      # Two layers per module: service + router
    ├── auth/
    │   ├── test_service.py        # JWT, bcrypt, token rotation
    │   └── test_router.py         # POST /register, /login, /refresh, GET /me
    ├── assessment/
    │   ├── test_service.py        # submit_and_score, snapshot propagation
    │   └── test_router.py         # GET /catalogue, POST /submit, GET /results
    ├── crew/
    │   ├── test_service.py        # assign_member, get_full_dashboard, TVI pipeline
    │   └── test_router.py         # /members, /dashboard, /pulse
    ├── identity/
    │   ├── test_service.py        # get_full_profile, resolve_access_context, reports
    │   └── test_router.py         # GET /candidate/{id}, PATCH /me, POST /experiences
    ├── recruitment/
    │   ├── test_service.py        # create_campaign, apply, get_matching
    │   └── test_router.py         # POST /campaigns, GET /matching, POST /apply
    ├── survey/
    │   ├── test_service.py        # trigger_survey, submit_response, _normalize_response
    │   └── test_router.py         # GET /pending, POST /respond, GET /results
    └── vessel/
        ├── test_service.py        # create, get_secure, update, delete, boarding-token
        └── test_router.py         # CRUD /vessels, PATCH /environment, /boarding-token
```

### Test layers

| Layer | Strategy | Tools |
|-------|----------|-------|
| Engine | Direct function calls, no mocks | pytest, parametrize |
| Service | Mock repos via `AsyncMock`; real service logic | pytest-mock, `make_async_db()` |
| Router | HTTP round-trip via `httpx.AsyncClient + ASGITransport`; mock service | dependency_overrides, `mocker.patch` |

**Current status: 481 tests, 0 failures.**

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

- [ ] Alembic migration for `job_weight_configs` table (`JobWeightConfig` model added, migration not yet generated)
- [ ] Replace `print()` calls with `logging.getLogger(__name__)` throughout
- [ ] Background task error handling — currently swallows exceptions silently; needs `try/except` + structured logging
- [ ] File upload size limit — no max size validation on document upload endpoint
- [ ] Add composite index on `daily_pulses(crew_profile_id, yacht_id, created_at)` — required for TVI queries at scale
- [x] Unit test coverage for engine and module layers — 481 tests across engine, service and router layers

### Application bugs (surfaced by test suite)

- [ ] **`SurveyTriggerIn` missing `yacht_id`** — `modules/survey/router.py` line 37 accesses `payload.yacht_id` but the schema declares no such field. Any authenticated `POST /surveys/trigger` call raises `AttributeError 500`. Fix: add `yacht_id: int` to `SurveyTriggerIn`.
- [x] **Vessel router / service interface mismatch** — fixed. Tests now mock `service.get_all_for_employer` (matching the actual service method name).

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
