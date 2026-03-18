# Data Requirements — Harmony P-E Fit Engine

**Version :** 1.0 — Mars 2026
**Périmètre :** Données nécessaires pour alimenter le moteur P-E Fit et ses 5 use cases.

Ce document recense tous les tests, surveys et données contextuelles requis, leur statut de seed, et leur mapping vers les dimensions du moteur.

---

## Vue d'ensemble

```
Candidat (CrewProfile)
  └── psychometric_snapshot
        ├── big_five          ← IPIP-120 ou HBF-50 (Big Five forced-choice)
        ├── cognitive         ← COG-IQ (logical + numerical + verbal → GCA)
        ├── motivation        ← R-MAWS (SDT 6 régulations)        ← MANQUANT SEED
        ├── resilience        ← HMR-24 ou dérivé (100 - neuroticism)
        └── leadership_preferences  ← Survey LP-3               ← MANQUANT SEED

Yacht (Vessel)
  └── vessel_snapshot
        ├── vessel_params     ← Form employeur (JDR inputs)       ← MANQUANT SEED
        └── captain_vector    ← Survey capitaine (style leadership) ← MANQUANT SEED
```

---

## CÔTÉ CANDIDAT

### TEST 1 — Big Five : IPIP-120 / HBF-50
**Statut seed :** ✅ Implémenté (`tests/questions/etalons/ipip120.py`, `cutty_sark.py`)
**Produit :** `big_five.{agreeableness, conscientiousness, neuroticism, openness, extraversion}` (0-100)
**Dérivé automatiquement :** `emotional_stability = 100 - neuroticism`

**Dimensions alimentées :**
- P-J D-A fit : `conscientiousness` (w=0.40)
- P-J Safety barrier : `emotional_stability`, `agreeableness`, `conscientiousness`
- P-T fit : `min(agreeableness)`, `μ(conscientiousness)`, `σ(conscientiousness)`, `μ(emotional_stability)`
- P-S fit : `leadership_preferences` dérivés si manquants (`openness`, `conscientiousness`)
- Training/Talent : gap analysis sur tous les traits

**Format snapshot attendu :**
```json
"big_five": {
  "agreeableness":     {"score": 72.0, "reliable": true},
  "conscientiousness": {"score": 82.0, "reliable": true},
  "neuroticism":       {"score": 22.0, "reliable": true},
  "openness":          {"score": 68.0, "reliable": true},
  "extraversion":      {"score": 74.0, "reliable": true}
}
```

---

### TEST 2 — Cognitif : COG-IQ
**Statut seed :** ✅ Implémenté (`tests/questions/cogiq.py`)
**Produit :** `cognitive.{logical_score, numerical_score, verbal_score, gca_score}` (0-100)
**GCA calculé :** moyenne pondérée logical + numerical + verbal (ou moyenne simple)

**Dimensions alimentées :**
- P-J D-A fit : `gca` (w=0.60) — prédicteur le plus fort (Schmidt & Hunter, 1998)
- P-J Safety barrier : `gca` (soft veto si < 20 pour postes de commandement)
- Training/Talent : gap analysis cognitive

**Format snapshot attendu :**
```json
"cognitive": {
  "gca_score": 80.0,
  "logical_score": 78.0,
  "numerical_score": 82.0,
  "verbal_score": 80.0,
  "n_tests": 3
}
```

---

### TEST 3 — Résilience : HMR-24
**Statut seed :** ✅ Implémenté (`tests/questions/hmr24.py`)
**Produit :** `resilience` (0-100) — score direct de résilience comportementale
**Fallback si absent :** `emotional_stability` (ES = 100 - N)

**Dimensions alimentées :**
- P-J N-S fit (JDR) : `resilience_modulator` — module l'effet buffer
- P-J Safety barrier : advisory si resilience < 35
- P-O fit (Temps 2) : robustesse face à l'isolement

**Format snapshot attendu :**
```json
"resilience": 76.0
```

---

### TEST 4 — Motivation : R-MAWS (Reduced Multidimensional Work Motivation Scale)
**Statut seed :** ⚠️ Test seeded (`tests/questions/etalons/rmaws.py`) MAIS **motivation absente du snapshot**
**Action requise :** Faire produire `motivation` au scoring de R-MAWS et l'injecter dans le snapshot

**Produit :** `motivation.{intrinsic, identified, introjected, extrinsic_social, extrinsic_material, amotivation}` (0-100)

**Dimensions alimentées :**
- P-J motivation_fit : distance cosinus profil SDT candidat vs profil idéal poste
- Training : motivation_gaps par dimension SDT
- Talent : cohérence du profil motivationnel avec la trajectoire cible
- RPS : amotivation élevée + identified bas = signal précoce de désengagement

**Format snapshot attendu :**
```json
"motivation": {
  "intrinsic":          85.0,
  "identified":         80.0,
  "introjected":        35.0,
  "extrinsic_social":   55.0,
  "extrinsic_material": 50.0,
  "amotivation":        8.0
}
```

**TODO seed :**
- [ ] Vérifier que `seed_rmaws()` calcule et stocke les 6 scores SDT dans le snapshot
- [ ] Ajouter `motivation` dans `_snapshot()` de `environment/snapshots.py`
- [ ] Ajouter valeurs motivation pour les 15 profils de seed (marcus_webb, isabelle_moreau, etc.)

---

### SURVEY 1 — Préférences Leadership : LP-3
**Statut seed :** ⚠️ **Absent** — présent dans snapshot comme valeurs par défaut (0.5/0.5/0.6) mais pas de survey dédié
**Action requise :** Créer un survey de 6-9 items mesurant les 3 préférences

**Produit :** `leadership_preferences.{autonomy_preference, feedback_preference, structure_preference}` (0.0-1.0)

**Dimensions alimentées :**
- P-S fit (F_lmx) : distance entre préférences candidat et style capitaine

**Format snapshot attendu :**
```json
"leadership_preferences": {
  "autonomy_preference":  0.70,
  "feedback_preference":  0.45,
  "structure_preference": 0.75
}
```

**Fallback si absent :** dérivation depuis Big Five
- `autonomy_preference ≈ openness / 100`
- `feedback_preference ≈ openness / 100`
- `structure_preference ≈ conscientiousness / 100`

**TODO seed :**
- [ ] Créer `seed/surveys/lp3.py` avec 9 items (3 par dimension, échelle Likert 5)
- [ ] Inclure dans `seed_surveys()` de `surveys/surveys.py`
- [ ] Mettre à jour `_snapshot()` avec des valeurs LP-3 réalistes pour chaque profil

---

## CÔTÉ YACHT / EMPLOYEUR

### FORM 1 — Paramètres JDR : Vessel Params
**Statut seed :** ⚠️ Snapshot yacht contient `jdr_params` mais **pas au format attendu par le moteur**
**Format moteur attendu (`vessel_params`) :**

```json
{
  "salary_index":          0.75,
  "rest_days_ratio":       0.55,
  "private_cabin_ratio":   1.0,
  "charter_intensity":     0.70,
  "management_pressure":   0.50
}
```

**Format seed actuel (`jdr_params`) :**
```json
{
  "demands_level":   0.6,
  "resources_level": 0.7,
  "workload_index":  0.46
}
```

**TODO seed :**
- [ ] Remplacer `jdr_params` par `vessel_params` dans `_vessel_snapshot()`
- [ ] Définir des valeurs réalistes pour chaque yacht de seed (Lady Aurora, Nomad Spirit, Stella Maris, Blue Horizon)
- [ ] Adapter les paramètres `_vessel_snapshot()` : `salary_index, rest_days_ratio, private_cabin_ratio, charter_intensity, management_pressure`

**Valeurs de référence par type de yacht :**
| Yacht | salary_index | rest_days | cabin | charter | management |
|---|---|---|---|---|---|
| Lady Aurora (60m, charter 5★) | 0.85 | 0.45 | 1.0 | 0.85 | 0.60 |
| Nomad Spirit (45m, privé) | 0.75 | 0.60 | 0.90 | 0.40 | 0.50 |
| Stella Maris (35m, mixte) | 0.65 | 0.55 | 0.70 | 0.60 | 0.55 |
| Blue Horizon (28m, charter) | 0.60 | 0.40 | 0.60 | 0.90 | 0.70 |

---

### FORM 2 — Profil Leadership Capitaine : Captain Vector
**Statut seed :** ⚠️ Présent dans `_vessel_snapshot()` comme `captain_leadership_vector` mais **clés différentes** du format moteur
**Format moteur attendu (`captain_vector`) :**
```json
{
  "autonomy_given":      0.60,
  "feedback_style":      0.70,
  "structure_imposed":   0.75
}
```

**Format seed actuel :**
```json
"captain_leadership_vector": {
  "autonomy":   0.5,
  "feedback":   0.6,
  "structure":  0.7
}
```

**TODO seed :**
- [ ] Renommer les clés dans `_vessel_snapshot()` : `autonomy` → `autonomy_given`, `feedback` → `feedback_style`, `structure` → `structure_imposed`
- [ ] Créer un survey dédié pour recueillir ce vecteur auprès des capitaines (Temps 2)

---

## RÉSUMÉ DES ACTIONS SEED PRIORITAIRES

### Priorité 1 — Corrections de format (bloquant pour le moteur)
| Action | Fichier | Impact |
|---|---|---|
| Renommer `jdr_params` → `vessel_params` avec les 5 bonnes clés | `environment/snapshots.py` | N-S fit (JDR) |
| Renommer `captain_leadership_vector` clés → `autonomy_given`, `feedback_style`, `structure_imposed` | `environment/snapshots.py` | P-S fit |

### Priorité 2 — Données manquantes (use cases incomplets sans ça)
| Action | Fichier à créer/modifier | Impact |
|---|---|---|
| Ajouter `motivation` dans `_snapshot()` avec valeurs SDT pour 15 profils | `environment/snapshots.py` | P-J motivation_fit, Training, RPS |
| Vérifier que R-MAWS produit et stocke les 6 scores SDT | `tests/questions/etalons/rmaws.py` | P-J motivation_fit |

### Priorité 3 — Nouveaux surveys (Temps 2)
| Survey | Items | Dimensions | Fichier à créer |
|---|---|---|---|
| LP-3 (Leadership Preferences) | 9 items | autonomy_pref, feedback_pref, structure_pref | `seed/surveys/lp3.py` |
| Survey Capitaine (Captain Vector) | 6 items | autonomy_given, feedback_style, structure_imposed | `seed/surveys/captain_profile.py` |
| Survey Culture Armateur (P-O Fit) | 12 items | valeurs organisation (OCP) | `seed/surveys/org_culture.py` |

---

## MAPPING COMPLET USE CASE → DONNÉES

| Use Case | Données obligatoires | Données optionnelles | Activées si |
|---|---|---|---|
| **Recruitment** | big_five, cognitive | motivation, vessel_params, captain_vector, crew_snapshots | vessel_params → N-S fit ; captain_vector → P-S fit ; crew → P-T delta |
| **Management** | big_five (crew complet) | captain_vector | captain_vector → P-S fit par membre |
| **Training** | big_five, cognitive | motivation | motivation → SDT gaps |
| **Talent** | big_five, cognitive | motivation | motivation → cohérence profil cible |
| **RPS** | big_five (crew complet) | vessel_params, captain_vector | vessel_params → burnout risk ; captain_vector → LMX |

---

## FORMAT SNAPSHOT COMPLET CIBLE

Structure complète visée une fois toutes les données intégrées :

```json
{
  "version": "3.0",
  "big_five": {
    "agreeableness":     {"score": 72.0, "reliable": true},
    "conscientiousness": {"score": 82.0, "reliable": true},
    "neuroticism":       {"score": 22.0, "reliable": true},
    "openness":          {"score": 68.0, "reliable": true},
    "extraversion":      {"score": 74.0, "reliable": true}
  },
  "emotional_stability": 78.0,
  "cognitive": {
    "gca_score":      80.0,
    "logical_score":  78.0,
    "numerical_score": 82.0,
    "verbal_score":   80.0,
    "n_tests": 3
  },
  "resilience": 76.0,
  "motivation": {
    "intrinsic":          85.0,
    "identified":         80.0,
    "introjected":        35.0,
    "extrinsic_social":   55.0,
    "extrinsic_material": 50.0,
    "amotivation":        8.0
  },
  "leadership_preferences": {
    "autonomy_preference":  0.70,
    "feedback_preference":  0.45,
    "structure_preference": 0.75
  }
}
```

---

## FORMAT VESSEL_PARAMS CIBLE (stocké dans Yacht.vessel_snapshot)

```json
{
  "vessel_params": {
    "salary_index":          0.75,
    "rest_days_ratio":       0.55,
    "private_cabin_ratio":   1.0,
    "charter_intensity":     0.70,
    "management_pressure":   0.50
  },
  "captain_vector": {
    "autonomy_given":      0.60,
    "feedback_style":      0.70,
    "structure_imposed":   0.75
  }
}
```
