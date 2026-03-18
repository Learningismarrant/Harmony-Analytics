# Radiant Analytics — by Fondation Technologies

Plateforme psychométrique pour le recrutement et la gestion d'équipage dans l'industrie du yachting de luxe.

> *Nom inspiré du Prime Radiant d'Isaac Asimov — l'instrument qui intègre les équations de la Psychohistoire pour prédire les comportements des civilisations. Nous appliquons la même ambition à l'échelle d'un équipage.*

---

## Concept

Les décisions de recrutement maritime reposent encore sur le CV et l'intuition, alors que 70 % des conflits et départs anticipés à bord trouvent leur origine dans des incompatibilités psychologiques identifiables.

Radiant Analytics fournit :

- **Pour le recruteur :** un pipeline P-E Fit en 7 dimensions (adéquation personne-poste, personne-équipe, personne-environnement, personne-capitaine…) qui classe les candidats par probabilité de succès prédit, visualisé comme une molécule 3D interactive.
- **Pour le candidat :** un parcours de passation de tests psychométriques sur mobile (Big Five T-IRT, cognition, valeurs, mobilité, tolérance maritime) qui construit son profil et augmente sa visibilité.
- **Pour l'armateur :** des métriques d'équipage en continu (F_team, TVI, diagnostic Performance × Cohésion) et un système d'alerte précoce sur les risques de départ ou de conflit.

---

## Structure du projet

```
Harmony/
├── backend/        # API FastAPI — logique métier + moteurs psychométriques
├── frontend/       # Monorepo Turborepo — dashboard web + app mobile
└── README.md
```

---

## Stack technique

### Backend

| Composant | Technologie |
|---|---|
| Langage | Python 3.12 |
| Framework API | FastAPI 0.128 |
| ORM | SQLAlchemy 2.0 async |
| Base de données | PostgreSQL 14+ + asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (jose) + bcrypt |
| ML / calcul | scikit-learn · NumPy · Pandas |
| Tests | pytest · pytest-asyncio · httpx · pytest-mock |

### Frontend

| Composant | Technologie |
|---|---|
| Monorepo | Turborepo 2 |
| Web (employeur) | Next.js 15 App Router |
| Mobile (candidat) | Expo SDK 55 + Expo Router |
| 3D | React Three Fiber 8 + @react-three/drei |
| Physique 3D | D3-force 3 |
| Requêtes serveur | TanStack Query v5 |
| État UI | Zustand v5 |
| Styles web | Tailwind CSS 3 |
| Styles mobile | NativeWind 4 |

---

## Architecture système

```
┌─────────────────────┐      ┌─────────────────────┐
│   apps/web          │      │   apps/mobile        │
│   Next.js 15        │      │   Expo SDK 55        │
│   Employeur         │      │   Candidat           │
│   (Vercel)          │      │   (EAS Build)        │
└────────┬────────────┘      └──────────┬───────────┘
         │  HTTPS + Bearer token        │
         │  Refresh : HttpOnly cookie   │  Refresh : SecureStore
         ▼                              ▼
┌─────────────────────────────────────────────────────┐
│             FastAPI — port 8000                      │
│                                                      │
│  ┌──────────────────┐   ┌──────────────────────┐    │
│  │ Modules HTTP     │   │ Engine (calcul pur)  │    │
│  │ auth · identity  │   │ pe_fit (7 familles)  │    │
│  │ crew · vessel    │   │ Psychometrics        │    │
│  │ recruitment      │   │ Benchmarking         │    │
│  │ assessment       │   │ use_cases            │    │
│  │ survey           │   └──────────────────────┘    │
│  └──────────────────┘                               │
└─────────────────────┬───────────────────────────────┘
                      ▼
             PostgreSQL 14+
         (snapshots JSON dénormalisés
          pour lectures O(1) dashboard)
```

---

## Moteur scientifique — P-E Fit

Radiant Analytics est construit sur le cadre **Person-Environment Fit** (Kristof-Brown et al., 2005) — méta-analyse de 172 études sur 30 ans. L'adéquation est mesurée sur 7 dimensions orthogonales, chacune avec un poids calibré sur la littérature I/O :

| Famille | Poids | Question |
|---|---|---|
| DA — Demands-Abilities | 0.28 | Le candidat a-t-il les capacités pour les exigences du poste ? |
| NS — Needs-Supplies | 0.25 | L'environnement répond-il aux besoins du candidat (JD-R) ? |
| PO — Person-Organisation | 0.18 | Les valeurs du candidat s'alignent-elles avec celles du bord ? |
| PG — Person-Group | 0.16 | Le candidat est-il compatible avec l'équipe en place ? |
| PS — Person-Supervisor | 0.13 | Le style de commandement du capitaine correspond-il aux préférences du candidat ? |
| Physical Fit | 0.05 | Le candidat tolère-t-il les contraintes physiques du milieu maritime ? |
| Mobility Fit | 0.05 | Le candidat est-il flexible face aux exigences de mobilité ? |

**Score global :** `Σ(w_i × PSI_i) / Σ(w_i disponibles)` — renormalisé automatiquement sur les dimensions disponibles. Somme des poids = 1.10 (intentionnel — permet la renormalisation).

**PSI (Profile Similarity Index) :** `Score_dim = 1 − |P_norm − E|` — distance absolue entre le profil candidat normalisé et le niveau requis par l'environnement.

### Pipeline de décision

```
snapshot psychométrique candidat
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  pe_fit.compute(snapshot, vessel_params,             │
│                 crew_snapshots, captain_vector)       │
│                                                      │
│  ├── DA-Fit  (GCA + C SME-score + safety barrier)   │→ 0.28
│  ├── NS-Fit  (JD-R Resources/Demands × Resilience)  │→ 0.25
│  ├── PO-Fit  (CES values PSI — honesty/achiev/…)    │→ 0.18
│  ├── PG-Fit  (Bell 2007 team formula)               │→ 0.16
│  ├── PS-Fit  (LMX Euclidean distance)               │→ 0.13
│  ├── Physical Fit (METS tolerance PSI)              │→ 0.05
│  └── Mobility Fit (MMFS flexibility PSI)            │→ 0.05
│                                                      │
│  global_score = Σ(wᵢ·PSIᵢ) / Σ(wᵢ)                 │
└─────────────────────────────────────────────────────┘
        │
        ▼
use_cases/
  ├── recruitment.py  → HIRE / CONDITIONAL / DISQUALIFY
  ├── management.py   → TEAM_HEALTH + alertes
  ├── training.py     → GAP_ANALYSIS + plan de développement
  ├── talent.py       → READINESS par niveau de carrière
  └── rps.py          → RISK_LEVEL psychosocial
```

### Instruments de mesure

| Instrument | Items | Familles alimentées |
|---|---|---|
| CUTTY SARK T-IRT (IPIP-120) | 60 paires forced-choice | DA, PG, PS |
| RMAWS (résilience) | — | DA (safety barrier) |
| COGIQ (cognition) | — | DA |
| HMR-24 (motivation) | 24 Likert | NS, DA |
| CES Values (Ravlin & Meglino 1987) | 16 Likert | PO |
| METS (tolérance maritime) | 15 Likert | Physical Fit |
| MMFS (mobilité) | 12 Likert | Mobility Fit |

### Sociogramme

$$D_{ij} = 0.55 \cdot (1 - |C_i - C_j|/100) + 0.25 \cdot (A_i + A_j)/200 + 0.20 \cdot (ES_i + ES_j)/200$$

Visualisé comme une molécule 3D interactive — nœuds = marins, arêtes = compatibilité dyadique. Mode simulation en temps réel : "que se passe-t-il si j'ajoute ce candidat à cet équipage ?"

---

## Démarrage rapide

### 1. Backend

**Prérequis :** Python 3.12, PostgreSQL 14+

```bash
cd backend

# Environnement virtuel
python -m venv .venv
source .venv/Scripts/activate      # Windows
# source .venv/bin/activate        # Linux / macOS

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env : DATABASE_URL, SECRET_KEY (openssl rand -hex 32)

# Base de données
alembic upgrade head
python -m app.seed.seed              # Full seed (employers + candidates + yachts + tests + surveys)

# Démarrer
uvicorn app.main:app --reload --port 8000
# → API sur http://localhost:8000
# → Swagger : http://localhost:8000/docs
```

### 2. Frontend — web

```bash
cd frontend
npm install
cp apps/web/.env.example apps/web/.env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

npx turbo dev --filter=@harmony/web
# → http://localhost:3000
```

### 3. Frontend — mobile

```bash
cp apps/mobile/.env.example apps/mobile/.env
# EXPO_PUBLIC_API_URL=http://<votre-IP>:8000

cd frontend/apps/mobile
npx expo start
```

---

## Tests

### Backend — 1104 tests, 0 failures

```bash
cd backend
pytest tests/ -v

# Par couche
pytest tests/engine/ -v -m engine     # Fonctions pures — aucun mock
pytest tests/ -v -m service           # Services — AsyncMock repos
pytest tests/ -v -m router            # HTTP — httpx AsyncClient
```

### Frontend web — 126 tests, 0 failures

```bash
cd frontend/apps/web && npm test
```

### Frontend mobile — 121 tests, 0 failures

```bash
cd frontend/apps/mobile && npm test
```

---

## Documentation détaillée

| Partie | Fichier |
|---|---|
| Architecture backend, domaine, moteurs, API, migrations, backlog | [`backend/README.md`](backend/README.md) |
| Architecture frontend, packages, auth, sociogramme 3D, travail restant | [`frontend/README.md`](frontend/README.md) |

---

## État d'avancement

### Backend

| Composant | État |
|---|---|
| Modules HTTP (auth, identity, crew, vessel, recruitment, assessment, survey) | ✅ Implémenté |
| Engine P-E Fit (7 familles : DA, NS, PO, PG, PS, Physical, Mobility) | ✅ Implémenté |
| Sociogramme (P2 dyad) | ✅ Implémenté |
| use_cases (recruitment, management, training, talent, rps) | ✅ Implémenté |
| ORM models + Alembic migrations | ✅ Implémenté |
| 7 catalogues psychométriques seedés (IPIP-120, RMAWS, COGIQ, HMR-24, CES, METS, MMFS) | ✅ Implémenté |
| Profils SME 16 postes + lookup matriciel (position × yacht_type) | ✅ Implémenté |
| Suite de tests (1104 tests) | ✅ 0 failure |
| Endpoints sociogramme (`/crew/{id}/sociogram`) | ⏳ Manquant |
| Email (invitations survey, notifications embauche) | ⏳ Non implémenté |
| Module Training (backend) | ⏳ À construire |

### Frontend

| Composant | État |
|---|---|
| Monorepo + packages partagés (types, api, ui) | ✅ Complet |
| Web — auth + layout + dashboard flotte | ✅ Complet |
| Web — sociogramme 3D + mode simulation | ✅ Complet |
| Web — matching P-E Fit | ✅ Complet |
| Mobile — auth + profil candidat | ✅ Complet |
| Mobile — passation tests (Likert + T-IRT CUTTY SARK) | ✅ Complet |
| Mobile — training (4 axes, parcours personnalisé) | ✅ Frontend · ⏳ Backend |
| Web — register / campagnes / vessel detail | ⏳ À construire |
| Mobile — survey / pulse / invitations | ⏳ À construire |

---

## Sécurité

- [ ] `SECRET_KEY` — générer avec `openssl rand -hex 32`, ne jamais committer
- [ ] CORS — remplacer `allow_origins=["*"]` par le domaine Vercel exact
- [ ] `DEBUG=False` en production
- [ ] Access token — mémoire Zustand uniquement (jamais `localStorage`)
- [ ] Refresh token web — HttpOnly cookie, `Secure`, `SameSite=Strict`
- [ ] Refresh token mobile — `expo-secure-store` avec `WHEN_UNLOCKED`

---

## Contribuer

Branches : `feature/<sujet>`, `fix/<sujet>`, `chore/<sujet>`. PRs vers `main` uniquement.
