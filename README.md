# Harmony Analytics

Plateforme d'analyse psychométrique pour le recrutement et la gestion d'équipage dans l'industrie des superyachts.

---

## Concept

Harmony résout un problème structurel du secteur : les décisions de recrutement maritime reposent sur le CV et l'intuition, alors que 70 % des conflits et départs anticipés à bord trouvent leur origine dans des incompatibilités psychologiques identifiables.

La plateforme fournit :

- **Pour le recruteur :** un pipeline de matching en deux étapes (normativité individuelle → fit équipe/environnement) qui classe les candidats par probabilité de succès prédit, visualisé comme une molécule 3D interactive.
- **Pour le candidat :** un parcours de passation de tests psychométriques sur mobile qui construit son profil et augmente sa visibilité auprès des employeurs.
- **Pour l'armateur :** des métriques d'équipage en continu (F_team, TVI, diagnostic Performance × Cohésion) et un système d'alerte précoce sur les risques de départ ou de conflit.

---

## Structure du projet

```
Harmony/
├── backend/        # API FastAPI — logique métier + moteurs psychométriques
├── frontend/       # Monorepo Turborepo — dashboard web + app mobile
└── README.md       # Ce fichier
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
| Mobile (candidat) | Expo SDK 52 + Expo Router 4 |
| 3D | React Three Fiber 8 + @react-three/drei |
| Physique 3D | D3-force 3 |
| Requêtes serveur | TanStack Query v5 |
| État UI | Zustand v5 |
| Styles web | Tailwind CSS 3 |
| Styles mobile | NativeWind 4 |
| Déploiement web | Vercel |
| Déploiement mobile | EAS Build (iOS + Android) |

---

## Architecture système

```
┌─────────────────────┐      ┌─────────────────────┐
│   apps/web          │      │   apps/mobile        │
│   Next.js 15        │      │   Expo SDK 52        │
│   Employeur         │      │   Candidat           │
│   (Vercel)          │      │   (EAS Build)        │
└────────┬────────────┘      └──────────┬───────────┘
         │                              │
         │  HTTPS + Bearer token        │
         │  Refresh : HttpOnly cookie   │  Refresh : SecureStore
         ▼                              ▼
┌─────────────────────────────────────────────────────┐
│             FastAPI — port 8000                      │
│                                                      │
│  ┌──────────────────┐   ┌──────────────────────┐    │
│  │ Modules HTTP     │   │ Engine (calcul pur)  │    │
│  │ auth · identity  │   │ DNRE · MLPSM         │    │
│  │ crew · vessel    │   │ Psychometrics        │    │
│  │ recruitment      │   │ Benchmarking         │    │
│  │ assessment       │   │ ML / OLS retrain     │    │
│  │ survey           │   └──────────────────────┘    │
│  └──────────────────┘                               │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
             PostgreSQL 14+
         (snapshots JSON dénormalisés
          pour lectures O(1) dashboard)
```

---

## Moteurs scientifiques

Harmony est construit sur trois moteurs d'analyse orthogonaux. Chaque composant s'appuie sur la littérature de psychologie organisationnelle et de sélection du personnel.

### Stage 1 — DNRE

*Is this candidate a valid profile for this position type?*

Évalue la conformité normative d'un candidat par rapport aux benchmarks du poste (score SME pondéré) et sa position dans le pool courant (percentile dynamique, formule de Tukey). Un filtre de sécurité non-compensatoire bloque les profils à risque sévère avant l'étape 2.

### Stage 2 — MLPSM

*Will this candidate succeed on this specific yacht with this team?*

$$\hat{Y} = \beta_1 P_{\text{ind}} + \beta_2 F_{\text{team}} + \beta_3 F_{\text{env}} + \beta_4 F_{\text{lmx}}$$

Quatre composantes indépendantes modélisent les causes distinctes d'échec : performance individuelle (GCA × Consciencieux), dynamiques d'équipe (filtre "jerk", faultline, buffer ES), charge environnementale (JD-R ratio), et alignement capitaine-marin (distance vectorielle LMX).

Les β sont appris par OLS à partir des données réelles (`y_actual` post-hire via surveys) dès que 150 événements de recrutement sont disponibles.

### Sociogramme

*Who should share a cabin? Which pair will create synergy vs. friction?*

$$D_{ij} = 0.40 \cdot (1 - |A_i - A_j|/100) + 0.35 \cdot (1 - |C_i - C_j|/100) + 0.25 \cdot \mu(ES_i, ES_j)/100$$

Visualisé comme une molécule 3D interactive — nœuds = marins, arêtes = compatibilité dyadique. Permet la simulation d'impact en temps réel : "que se passe-t-il si j'ajoute ce candidat à cet équipage ?"

> **Documentation complète :** [`backend/README.md#scientific-foundations`](backend/README.md#scientific-foundations)

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
python -m app.seed.seed_environment
python -m app.seed.seed_tests_surveys

# Démarrer
uvicorn app.main:app --reload --port 8000
# → API disponible sur http://localhost:8000
# → Swagger UI : http://localhost:8000/docs
```

### 2. Frontend — web

```bash
cd frontend
npm install

# Variables d'environnement
cp apps/web/.env.example apps/web/.env.local
# Éditer : NEXT_PUBLIC_API_URL=http://localhost:8000

npx turbo dev --filter=@harmony/web
# → http://localhost:3000
```

### 3. Frontend — mobile

```bash
cp apps/mobile/.env.example apps/mobile/.env
# Éditer : EXPO_PUBLIC_API_URL=http://localhost:8000

cd frontend/apps/mobile
npx expo start
# Scanner le QR code avec Expo Go
```

---

## Tests

### Backend — 442 tests, 0 failures

```bash
cd backend
pytest tests/ -v

# Par couche
pytest tests/engine/ -v -m engine     # Fonctions pures
pytest tests/ -v -m service           # Services (mock DB)
pytest tests/ -v -m router            # HTTP (httpx AsyncClient)
```

### Frontend — à venir

Les tests frontend (Vitest + Testing Library pour web, Jest + RNTL pour mobile) sont listés dans le backlog.

---

## Documentation détaillée

| Partie | Fichier |
|---|---|
| Architecture backend, modèle de domaine, moteurs, API, migrations, backlog | [`backend/README.md`](backend/README.md) |
| Architecture frontend, packages, auth, sociogramme 3D, travail restant | [`frontend/README.md`](frontend/README.md) |

---

## État d'avancement

### Backend

| Composant | État |
|---|---|
| Modules HTTP (auth, identity, crew, vessel, recruitment, assessment, survey) | ✅ Implémenté |
| Engine DNRE + MLPSM + Sociogramme + Benchmarking | ✅ Implémenté |
| ORM models + Alembic migrations | ✅ Implémenté |
| Suite de tests (442 tests) | ✅ 0 failure |
| Endpoints sociogramme (`/crew/{id}/sociogram`) | ⏳ Manquant |
| Email (invitations survey, notifications embauche) | ⏳ Non implémenté |
| Rate limiting | ⏳ Configuré mais inactif |
| S3 storage | ⏳ Config présente, non branché |

### Frontend

| Composant | État |
|---|---|
| Monorepo + packages partagés (types, api, ui) | ✅ Complet |
| Web — auth + layout + dashboard flotte | ✅ Complet |
| Web — sociogramme 3D + mode simulation | ✅ Complet *(endpoint backend manquant)* |
| Web — matching DNRE/MLPSM | ✅ Complet |
| Mobile — auth + profil candidat | ✅ Complet |
| Mobile — passation tests psychométriques | ✅ Complet |
| Web — register / campagnes / vessel detail | ⏳ À construire |
| Mobile — survey / pulse / invitations | ⏳ À construire |

> **Détail complet du backlog frontend :** [`frontend/README.md#travail-restant`](frontend/README.md#travail-restant)

---

## Sécurité

Points de vigilance avant tout déploiement en production :

- [ ] **`SECRET_KEY`** — générer avec `openssl rand -hex 32` et ne jamais committer
- [ ] **CORS** — remplacer `allow_origins=["*"]` par le domaine Vercel exact
- [ ] **`DEBUG=False`** — vérifier dans `.env`
- [ ] **Access token** — stocké uniquement en mémoire Zustand (jamais `localStorage`)
- [ ] **Refresh token web** — HttpOnly cookie, `Secure`, `SameSite=Strict`
- [ ] **Refresh token mobile** — `expo-secure-store` avec `WHEN_UNLOCKED`
- [ ] **CSP** — headers configurés dans `next.config.js`

---

## Contribuer

```
Harmony/
├── backend/      # Python — lire backend/README.md pour le setup
└── frontend/     # TypeScript — lire frontend/README.md pour le setup
```

Les branches sont nommées `feature/<sujet>`, `fix/<sujet>`, `chore/<sujet>`.
Les PRs passent par `main` — pas de `develop`.
