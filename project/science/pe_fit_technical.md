# Harmony Analytics — Document de référence
## Cadre théorique et méthodologique du modèle P-E fit maritime

*Version 0.8 — Mars 2026*

---

## 0. Positionnement produit — Les 7 Questions

> Validé scientifiquement en mars 2026 (head-of-science). Ancrage : Kristof-Brown, Zimmerman & Johnson (2005), méta-analyse P-E Fit (172 études, n > 66 000).

Le moteur Harmony répond à **7 questions diagnostiques** structurantes. Ce cadre est la colonne vertébrale de toute décision produit, priorisation de développement, et communication client.

```
Q1 — What is his personality profile?
     → CUTTY SARK T-IRT (Big Five forced-choice)
     → Input descriptif universel — alimente Q2 à Q6

Q2 — Does he have the abilities for this job?
     → PJ D-A Fit : GCA + Conscientiousness + profil SME + barrière sécurité
     → Référence : Schmidt & Hunter (1998) — validité opérationnelle GCA ~ 0.51

Q3 — Does this job match his motivations?
     → PJ N-S Fit : MWMS (SDT, 6 régulations) + JDR vessel_params
     → Référence : Cable & DeRue (2002) ; Deci & Ryan (2000) ; Bakker & Demerouti (2007)
     ⚠ Profils idéaux Temps 0 — indicatif jusqu'à calibration empirique

Q4 — Will he integrate into this crew?
     → PG/PT Fit : formule Bell (2007) — 0.30·min(A) + 0.30·μ(C) + 0.28·μ(ES) − 0.12·σ(C)
     → Prend en compte le "jerk filter" (minimum Agréabilité)

Q5 — Does he share our values and culture?
     → PO Fit : congruence CES (Ravlin & Meglino, 1987) — 4 valeurs
     → ≠ Q4 (équipe) et ≠ Q6 (superviseur) — niveau organisationnel distinct
     → Temps 2 : OCP/Q-Sort pour congruence de valeurs complète

Q6 — Is he compatible with the captain's leadership style?
     → PS Fit : distance euclidienne LMX (Graen & Uhl-Bien, 1995)
     → Dimensions : autonomy_given, feedback_style, structure_imposed

Q7 — Can he handle life aboard? [maritime-specific / ICE context]
     → Fit physique-environnemental + fit mobilité-temporel
     → Non-compensatoire : un score élevé sur Q1-Q6 ne compense pas Q7
     → Référence : Stuster (2010) — environnements ICE
```

### Mapping complet

| Question | Construct P-E Fit | Module engine | Poids global_score |
|----------|-------------------|---------------|-------------------|
| Q1 | Trait measure (input) | `psychometric_snapshot` | — |
| Q2 | PJ D-A Fit | `pj_fit/demands_abilities/` | 0.28 |
| Q3 | PJ N-S Fit | `pj_fit/motivation_fit/` + `needs_supplies/` | 0.25 |
| Q4 | PG/PT Fit | `pt_fit/f_team.py` | 0.22 |
| Q5 | PO Fit | `po_fit/f_values.py` | 0.18 |
| Q6 | PS Fit | `ps_fit/f_lmx.py` | 0.12 |
| Q7 | Physical + Mobility Fit | `physical_fit/` + `mobility_fit/` | 0.05 + 0.05 |

### Distinctions critiques à ne jamais confondre

- **Q2 "Can he do it?"** = capacités objectives face aux exigences du *poste*
- **Q3 "Why does he do it?"** = besoins motivationnels face aux *ressources du poste*
- **Q4 "Team fit"** = composition de *l'équipage* (dynamique collective)
- **Q5 "Culture fit"** = congruence avec les *valeurs de l'organisation/armateur*
- **Q6 "Supervisor fit"** = compatibilité avec le *style du capitaine*

Ces cinq constructs sont empiriquement distincts (corrélations croisées 0.10–0.50 selon Kristof-Brown 2005) et prédisent des outcomes différents (performance, engagement, turnover, bien-être).

---

## 1. Fondements théoriques

### 1.1 Cadre de référence

Le modèle s'appuie sur la théorie du Person-Environment fit (P-E fit), définie comme le degré de compatibilité entre les caractéristiques d'un individu et celles de son environnement de travail (Edwards et al., 1998 ; Kristof-Brown & Billsberry, 2013).

**Références structurantes :**
- Cable & DeRue (2002) — Définition des trois dimensions fondamentales (D-A, N-S, P-O fit)
- Kristof-Brown et al. (2005) — Méta-analyse, conséquences du fit au travail
- Chuang, Shen & Judge (2016) — PPEFS, instrument multidimensionnel de référence
- Jung et al. (2024) — Association P-E fit et santé mentale (LIFE-Adult-Study)
- Kühner, Stein & Zacher (2024) — Extension thématique du P-E fit (domaine environnemental)
- Edwards et al. (2006) — Niveaux de mesure : atomistic, molecular, molar
- Barrick & Mount (1991) — Big Five et performance au travail
- Schmidt & Hunter (1998) — GCA comme prédicteur de performance
- Deci & Ryan (1985, 2000) — Self-Determination Theory
- Gagné et al. (2015) — Multidimensional Work Motivation Scale (MWMS)
- Rounds & Su (2014) — Intérêts professionnels comme facette de la motivation intrinsèque
- De Fruyt & Mervielde (1997) ; Larson et al. (2002) — Convergence Big Five / RIASEC (justifie retrait Holland)

### 1.2 Taxonomie du P-E fit retenue

| Type | Définition |
|------|-----------|
| PJ fit (D-A) | Adéquation exigences du poste ↔ capacités de l'individu |
| PJ fit (N-S) | Adéquation besoins de l'individu ↔ ressources/apports du poste |
| PO fit | Adéquation valeurs/objectifs individuels ↔ valeurs/objectifs organisationnels |
| PG fit | Adéquation caractéristiques individuelles ↔ caractéristiques du groupe de travail |
| PS fit | Adéquation caractéristiques individuelles ↔ caractéristiques du supérieur hiérarchique |
| Fit physique-environnemental | Adéquation tolérances individuelles ↔ conditions physiques de l'environnement embarqué |
| Fit mobilité-temporel | Adéquation situation personnelle ↔ contraintes de mobilité et temporelles du poste |

---

## 2. Architecture de l'instrument

### 2.1 Principe modulaire

```
COUCHE UNIVERSELLE (ancrée dans la littérature)
────────────────────────────────────────────────────────
PJ fit (D-A + N-S) | PO fit | PG fit | PS fit
Instruments standardisés + items Likert complémentaires

                    +

COUCHE CONTEXTUELLE (modules spécifiques par secteur)
────────────────────────────────────────────────────────
Module Maritime     | Module Santé      | Module Construction
Fit physique-env.   | (à développer)    | (à développer)
Fit mobilité-temp.  |                   |
```

### 2.2 Cartographie complète des dimensions

#### COUCHE UNIVERSELLE

**Famille 1 — PJ fit / D-A fit** | Pondération : 0.28
| # | Dimension | Pertinence | Misfit critique | Instrument primaire | Items Likert | Seuil |
|---|-----------|------------|-----------------|--------------------|-----------------------------|-------|
| 1.1 | Compétences techniques métier | ÉLEVÉE | Sous-fit D-A | GCA + certifications | Oui | Éliminatoire absolu |
| 1.2 | Compétences relationnelles | ÉLEVÉE | Sous-fit D-A | Big Five (A, E) | Oui | Seuil configurable |
| 1.3 | Personnalité professionnelle | ÉLEVÉE | Sous-fit ET sur-fit | Big Five complet (TIPI) | Non | Seuil configurable |
| 1.4 | Compétences physiques | MOYENNE | Sous-fit D-A | — | Oui | Seuil configurable |

**Famille 2 — PJ fit / N-S fit** | Pondération : 0.25
| # | Dimension | Pertinence | Misfit critique | Instrument primaire | Items Likert | Seuil |
|---|-----------|------------|-----------------|--------------------|-----------------------------|-------|
| 2.1 | Besoin d'autonomie vs. délégation | ÉLEVÉE | Sur-fit N-S | SDT/MWMS | Non | Seuil informatif |
| 2.2 | Besoin de progression vs. opportunités | ÉLEVÉE | Sur-fit N-S | SDT/MWMS | Oui | Seuil informatif |
| 2.3 | Intérêts vs. contenu du poste | ÉLEVÉE | Sous-fit N-S | SDT/MWMS étendu (intérêts = facette motivation intrinsèque) | Oui — items complémentaires | Seuil configurable |
| 2.4 | Besoin de reconnaissance vs. feedback | MOYENNE | Sous-fit N-S | SDT/MWMS | Oui | Seuil informatif |
| 2.5 | Stabilité financière vs. rémunération | MOYENNE | Sous-fit N-S | — | Oui | Seuil informatif |
| 2.6 | Besoin de stimulation vs. richesse poste | MOYENNE | Sous-fit N-S | SDT/MWMS | Oui | Seuil informatif |

**Famille 3 — PO fit** | Pondération : 0.18
| # | Dimension | Pertinence | Misfit critique | Instrument primaire | Items Likert | Seuil |
|---|-----------|------------|-----------------|--------------------|-----------------------------|-------|
| 3.1 | Congruence de valeurs | ÉLEVÉE | Sous-fit PO | — | Oui — CES | Seuil configurable |
| 3.2 | Congruence d'objectifs | ÉLEVÉE | Sous-fit PO | SDT/MWMS | Oui | Seuil configurable |
| 3.3 | Rapport à la hiérarchie | MOYENNE | Sous-fit PO | — | Oui | Seuil informatif |
| 3.4 | Culture de sécurité | MOYENNE | Sous-fit PO | — | Oui | Seuil configurable |

**Famille 4 — PG fit** | Pondération : 0.16
| # | Dimension | Pertinence | Misfit critique | Instrument primaire | Items Likert | Seuil |
|---|-----------|------------|-----------------|--------------------|-----------------------------|-------|
| 4.1 | Compatibilité de valeurs de travail | ÉLEVÉE | Sous-fit PG | — | Oui — CES | Seuil configurable |
| 4.2 | Compatibilité de style de travail | ÉLEVÉE | Sous-fit PG | — | Oui | Seuil configurable |
| 4.3 | Compatibilité de personnalité | ÉLEVÉE | Sous-fit PG | Big Five (vs. mean équipe) | Non | Seuil informatif |
| 4.4 | Compatibilité culturelle / linguistique | MOYENNE | Sous-fit PG | — | Oui | Seuil informatif |
| 4.5 | Compatibilité des objectifs de séjour | MOYENNE | Sous-fit PG | SDT/MWMS | Oui | Seuil informatif |

**Famille 5 — PS fit** | Pondération : 0.13
| # | Dimension | Pertinence | Misfit critique | Instrument primaire | Items Likert | Seuil |
|---|-----------|------------|-----------------|--------------------|-----------------------------|-------|
| 5.1 | Compatibilité de valeurs professionnelles | ÉLEVÉE | Sous-fit PS | — | Oui — CES | Seuil configurable |
| 5.2 | Compatibilité de style de management | ÉLEVÉE | Sous-fit PS | SDT/MWMS (vs. cap.) | Oui | Seuil configurable |
| 5.3 | Compatibilité de style de communication | MOYENNE | Sous-fit PS | — | Oui | Seuil informatif |
| 5.4 | Compatibilité de personnalité | MOYENNE | Sous-fit PS | Big Five (vs. cap.) | Non | Seuil informatif |

#### MODULE MARITIME

**Famille 6 — Fit physique-environnemental** | Pondération : 0.05
| # | Dimension | Pertinence | Misfit critique | Seuil |
|---|-----------|------------|-----------------|-------|
| 6.1 | Tolérance espace restreint / promiscuité | ÉLEVÉE | Sous-fit | Seuil configurable |
| 6.2 | Tolérance à l'isolement géographique | ÉLEVÉE | Sous-fit | Seuil configurable |
| 6.3 | Rapport au risque physique | ÉLEVÉE | Sous-fit ET sur-fit | Éliminatoire si sous-seuil |
| 6.4 | Tolérance aux rythmes atypiques | ÉLEVÉE | Sous-fit | Seuil configurable |
| 6.5 | Sensibilité aux conditions météo | MOYENNE | Sous-fit | Seuil informatif |

**Famille 7 — Fit mobilité-temporel** | Pondération : 0.05
| # | Dimension | Pertinence | Misfit critique | Seuil |
|---|-----------|------------|-----------------|-------|
| 7.1 | Mobilité requise vs. situation personnelle | ÉLEVÉE | Sous-fit | Seuil configurable |
| 7.2 | Durée embarquement vs. besoins de rupture | ÉLEVÉE | Sous-fit | Seuil configurable |
| 7.3 | Tolérance à l'incertitude de programme | MOYENNE | Sous-fit | Seuil informatif |
| 7.4 | Rapport au contrat non-permanent | FAIBLE | Sous-fit | Seuil informatif |

---

## 3. Architecture des mesures atomistic

### 3.1 Trois logiques de comparaison

```
TYPE 1 — Individu vs. Profil de référence (PJ fit, PO fit)
────────────────────────────────────────────────────────────
Le candidat passe l'instrument (profil réel).
Le profil E est un profil de référence pré-construit en phase alpha
par un panel de SMEs, affiné à la marge par le recruteur.
→ Élimine le biais de similarité lié à un évaluateur unique.

TYPE 2 — Individu vs. Individu superviseur (PS fit)
─────────────────────────────────────────────────────
Le candidat passe l'instrument (profil réel).
Le capitaine passe le même instrument (profil réel, son propre profil).
On compare les deux profils directement.
→ Le capitaine ne remplit JAMAIS de profil projectif pour son poste.
   Cette fonction est assurée par les profils types alpha.

TYPE 3 — Individu vs. Agrégat groupe (PG fit)
──────────────────────────────────────────────
Le candidat passe l'instrument (profil réel).
Le profil d'équipe est calculé automatiquement à partir des profils
réels de chaque membre embarqué.
→ Actif cumulatif Harmony — se bonifie à chaque recrutement.
```

### 3.2 Phase alpha — Construction des profils de référence

#### Justification

L'industrie du yachting présente une structure favorable :
- Nombre limité de postes distincts (15 à 20 maximum)
- Similarité structurelle entre yachts au sein d'une même sous-catégorie
- Accessibilité des SMEs

Cette approche élimine le biais de similarité et réduit la charge des capitaines lors des recrutements.

#### Sous-catégories de yachts

| Sous-catégorie | Culture | Profil Big Five dominant | Motivation dominante (MWMS) |
|----------------|---------|--------------------------|------------------------------|
| Superyacht charter (30–60m) | Service excellence, rotation clients | Haute A, haute C | Extrinsèque-identifiée |
| Yacht privé famille (20–45m) | Relation long terme, discrétion | Haute A, faible N | Identifiée-intégrée |
| Superyacht expédition (40m+) | Autonomie technique, hauturière | Haute O, haute C | Intrinsèque-identifiée |
| Yacht racing (12–30m) | Performance, compétition | Haute E, haute C | Intrinsèque-extrinsèque |
| Yacht charter voile (15–30m) | Pédagogie, accueil, polyvalence | Haute A, haute O | Intrinsèque-identifiée |

*Hypothèses initiales à valider empiriquement en phase alpha.*

#### Postes identifiés

```
PONT                    INTÉRIEUR               TECHNIQUE
─────────────           ─────────────           ─────────────
Capitaine               Chef steward/ess        Chef mécanicien
Premier officier        Steward/ess senior      Second mécanicien
Second officier         Steward/ess junior      Électronicien
Chef bossman            Chef cuisinier
Matelot AB              Second cuisinier
Matelot OS              Purser (grands yachts)
Stagiaire pont
```

#### Protocole de construction

**Étape 1 — Panel SME :** 5 à 8 experts par poste × sous-catégorie (capitaines expérimentés, armateurs, yacht managers, anciens incumbents performants). Diversité des profils SMEs obligatoire.

**Étape 2 — Passation projective :** TIPI, MWMS étendu en mode "personne idéale pour ce poste". Estimation GCA sur échelle structurée.

**Étape 3 — Agrégation :** profil moyen pondéré + calcul dispersion inter-SME. Forte dispersion → investigation.

**Étape 4 — Validation indépendante :** second panel évalue la pertinence des profils générés.

**Étape 5 — Intégration :** profils chargés automatiquement dans l'application. Ajustements fins possibles par le recruteur (±1 point).

#### Ce que le capitaine remplit lors d'un recrutement (post phase alpha)

```
TIPI réel (son propre profil)            → PS fit
MWMS réel (son propre profil)            → PS fit
Items Likert E (ajustements fins)        → Dimensions contextuelles
Charge réduite de ~50% vs. version initiale.
Biais de similarité structurellement éliminé.
```

### 3.3 Instruments standardisés — Usage par type de fit

#### Big Five (TIPI — 10 items)
| Type de fit | Profil P | Profil E | Score |
|-------------|----------|----------|-------|
| PJ fit (D-A) | Candidat — TIPI réel | Profil type alpha | PSI(P, E_ref) |
| PS fit | Candidat — TIPI réel | Capitaine — TIPI réel | PSI(P_cand, P_cap) |
| PG fit | Candidat — TIPI réel | Moyenne TIPI équipage | PSI(P_cand, mean(P_équipe)) |

#### GCA — Matrices abstraites (ICAR-16 ou Raven SPM court)
| Type de fit | Profil P | Profil E | Score |
|-------------|----------|----------|-------|
| PJ fit (D-A) | Candidat — score test | Niveau requis du profil type alpha | Système de seuils |

Asymétrie : GCA < requis → éliminatoire / GCA >> requis → sur-fit (postes peu qualifiés).
Privilégier matrices non verbales pour équipages multinationaux.

#### SDT / MWMS (Gagné et al., 2015 — 12 items, 9 langues)
Structure : intrinsèque | intégrée | identifiée | introjectée | externe | amotivation

| Type de fit | Profil P | Profil E | Score |
|-------------|----------|----------|-------|
| PJ fit (N-S) | Candidat — MWMS réel | Profil type alpha | PSI(P, E_ref) |
| PO fit | Candidat — MWMS réel | Armateur — MWMS climat org. | PSI(P, E_org) |
| PS fit | Candidat — MWMS réel | Capitaine — MWMS réel | PSI(P_cand, P_cap) |
| PG fit | Candidat — MWMS réel | Moyenne MWMS équipage | PSI(P_cand, mean(P_équipe)) |

### 3.4 Justification du retrait de Holland RIASEC — Cohérence théorique

L'exclusion de l'inventaire RIASEC de Holland (1996) est un choix délibéré fondé sur trois arguments théoriques convergents.

**Argument 1 — Incompatibilité ontologique avec l'architecture dimensionnelle**

Notre modèle repose entièrement sur une logique dimensionnelle et continue : profils P et E comparés via PSI (corrélation de profils continus), score global agrégé de scores continus. Holland RIASEC est une théorie des types — elle classe individus et environnements dans des catégories discrètes et calcule la congruence comme une distance sur un hexagone (indice de Zener & Schnuelle, valeurs 0–3). Intégrer un score catégoriel dans un PSI continu constitue un mélange de métriques hétérogènes qui fragilise la cohérence mathématique du score global.

**Argument 2 — Redondance substantielle avec le Big Five**

La littérature établit des corrélations robustes entre les types Holland et les dimensions Big Five (Larson et al., 2002 ; De Fruyt & Mervielde, 1997) : Réaliste ↔ faible Ouverture/Agréabilité ; Investigateur ↔ haute Ouverture ; Social ↔ haute Agréabilité/Extraversion ; Conventionnel ↔ haute Conscienciosité. Dès lors que le TIPI est administré, le RIASEC capture en grande partie de la variance déjà présente dans notre modèle — la variance additionnelle ne justifie pas l'ajout d'un cinquième instrument.

**Argument 3 — Inadéquation du niveau d'analyse**

Holland a été développé pour l'orientation vocationnelle au niveau de la carrière (médecin, ingénieur), non au niveau du poste spécifique (second mécanicien sur superyacht charter). La méta-analyse de Kristof-Brown et al. (2005) n'inclut pas Holland dans ses analyses du PJ fit opérationnel — ce qui reflète cette limite de transposabilité.

**Solution retenue : intérêts comme facette de la motivation intrinsèque**

Rounds & Su (2014) montrent que les intérêts professionnels et la motivation intrinsèque partagent le même noyau théorique (l'activité est choisie pour ce qu'elle est, pas pour ses conséquences). Cette convergence permet d'absorber la dimension "intérêts professionnels" dans le MWMS étendu via deux items complémentaires ciblés, sans rupture ontologique et sans instrument additionnel. Les intérêts deviennent une sous-dimension de la motivation intrinsèque dans le N-S fit, cohérente avec l'ensemble de l'architecture dimensionnelle.

### 3.5 Rôle complémentaire des items Likert maison

```
INSTRUMENTS STANDARDISÉS couvrent :
Big Five (TIPI)  → personnalité (1.3, 4.3, 5.4)
GCA (matrices)   → capacité cognitive (1.1 complément)
SDT/MWMS étendu  → motivation + intérêts (2.1, 2.2, 2.3, 2.4, 2.6,
                   3.2, 4.5, 5.2)

ITEMS LIKERT MAISON couvrent :
Compétences techniques déclarées → 1.1
Compétences relationnelles → 1.2
Compétences physiques → 1.4
Valeurs (CES) → 3.1, 4.1, 5.1
Objectifs → 3.2 | Hiérarchie → 3.3 | Sécurité → 3.4
Style de travail → 4.2 | Culturel/linguistique → 4.4
Style management → 5.2 | Communication → 5.3
Rémunération → 2.5
Module maritime complet → 6.x, 7.x
```

### 3.6 Normalisation et score global

| Instrument | Score brut | Normalisation 0–1 |
|------------|------------|-------------------|
| Big Five (TIPI) | PSI : −1 à +1 | (PSI + 1) / 2 |
| GCA (matrices) | Seuils | Selon seuil |
| SDT / MWMS étendu | PSI : −1 à +1 | (PSI + 1) / 2 |
| Items Likert | 0 à 1 | Déjà normalisé |

```
PSI_pondéré = Σ(w(i) × Score_normalisé(i)) / Σw(i)
```

---

## 4. Double dispositif de mesure

### 4.1 Niveaux de mesure

| Niveau | Approche | Moment |
|--------|----------|--------|
| Atomistic | Instruments standardisés + Likert P vs. profil référence | Pré-recrutement |
| Molecular | Écart perçu P/E | Optionnel, embarquement |
| Molar | Fit global perçu (items M) | Embarquement T1/T2/T3 |

### 4.2 Timeline du double dispositif

```
PRÉ-RECRUTEMENT      EMBARQUEMENT              FIN DE CONTRAT
      │                    │                          │
Atomistic              Molar T1, T2, T3          Molar T3 + outcomes
(instruments +         (items M)                 (performance, renouvellement)
 Likert P/E)                │
      │               Alerte misfit              Validation longitudinale
Score PSI              précoce                   Recalibration pondérations
(matching)             (rétention)
```

---

## 5. Protocole de scoring

### 5.1 Architecture hybride (3 niveaux)

**Niveau 1 — Score dimensionnel (exposé utilisateur)**
- Instruments standardisés → PSI normalisé ou indice de congruence normalisé
- Items Likert → `Score_dim(i) = 1 − |P(i) − E(i)| / max_écart`
- Pondération w(i) paramétrable par le recruteur

**Niveau 2 — PSI pondéré global (exposé utilisateur)**
```
PSI_pondéré = Σ(w(i) × Score_normalisé(i)) / Σw(i)
```

**Niveau 3 — RSA en backend (non exposé)**
Response Surface Analysis sur données agrégées — calibration et détection asymétries.

### 5.2 Architecture des seuils

```
NIVEAU 1 — ÉLIMINATOIRE ABSOLU (non configurable)
Certifications manquantes, GCA critique, risque physique, incompatibilité légale
→ Exclusion quelle que soit la valeur PSI

NIVEAU 2 — SEUIL CONFIGURABLE (opérateur)
Compétences techniques, valeurs, fit physique, GCA sur-fit
Valeur par défaut : Score_normalisé(i) < 0.40
→ Alerte — recruteur décide

NIVEAU 3 — INFORMATIF
Communication, motivations, besoins secondaires
→ Affiché dans le profil détaillé, utilisé pour conseil et suivi à bord
```

### 5.3 Pondérations par défaut

```
D-A fit    0.28  ████████████████████████████  (Jung et al. + Kristof-Brown)
N-S fit    0.25  █████████████████████████
PO fit     0.18  ██████████████████
PG fit     0.16  ████████████████
PS fit     0.13  █████████████
Fit phys.  0.05  █████  ← à calibrer
Fit mob.   0.05  █████  ← à calibrer
           ────
Total      1.00
```

---

## 6. Items — Couche universelle

### 6.1 Principes

- **Série P** : candidat (auto-déclaration)
- **Série E** : ajustements fins du profil de référence (recruteur)
- **Série M** : fit perçu molar (à bord, T1/T2/T3)
- Échelle P/E : Likert 1–7 (1 = Pas du tout / 7 = Tout à fait)
- Échelle M : Likert 1–7 (1 = Aucune adéquation / 7 = Adéquation totale)
- Principe de non-redondance avec les instruments standardisés

---

### 6.2 Famille 1 — D-A fit

#### 1.1 — Compétences techniques métier
*Instrument primaire : GCA + certifications. Items Likert : niveau déclaré contextuel.*

**Série P**
```
P1.1a  À quel niveau évaluez-vous vos connaissances dans votre domaine de spécialité ?
       (1 = débutant / 7 = expert confirmé)
P1.1b  À quel niveau votre expérience pratique vous permet-elle de réaliser
       de façon autonome les tâches typiques de votre métier ?
P1.1c  À quel niveau maîtrisez-vous les outils, équipements ou procédures
       standards de votre domaine ?
```
**Série E**
```
E1.1a  À quel niveau de connaissances ce poste requiert-il de la personne recrutée ?
       (1 = débutant / 7 = expert confirmé)
E1.1b  À quel niveau d'expérience pratique ce poste requiert-il pour
       assumer ses tâches de façon autonome ?
E1.1c  À quel niveau de maîtrise des outils et procédures ce poste requiert-il ?
```
**Série M**
```
M1.1a  Comment évaluez-vous l'adéquation entre vos compétences techniques
       et les exigences réelles de votre poste actuel ?
M1.1b  Dans quelle mesure vos connaissances vous permettent-elles de répondre
       efficacement aux demandes techniques de votre poste ?
```

---

#### 1.2 — Compétences relationnelles
*Instrument primaire : Big Five A et E. Items Likert : compétences relationnelles contextuelles.*

**Série P**
```
P1.2a  À quel niveau évaluez-vous votre capacité à communiquer de façon
       claire et constructive dans un contexte professionnel exigeant ?
P1.2b  À quel niveau êtes-vous capable de gérer des désaccords ou tensions
       au sein d'une équipe de travail ?
P1.2c  À quel niveau adaptez-vous votre communication selon votre interlocuteur ?
```
**Série E**
```
E1.2a  À quel niveau ce poste requiert-il des compétences de communication
       interpersonnelle développées ?
E1.2b  À quel niveau ce poste expose-t-il à des situations relationnelles
       complexes ou tendues ?
E1.2c  À quel niveau ce poste exige-t-il une adaptabilité relationnelle ?
```
**Série M**
```
M1.2a  Comment évaluez-vous l'adéquation entre vos compétences relationnelles
       et ce que votre poste actuel exige de vous ?
M1.2b  Dans quelle mesure vous sentez-vous à l'aise pour gérer les interactions
       professionnelles propres à votre poste ?
```

---

#### 1.3 — Personnalité professionnelle
*Entièrement couvert par TIPI vs. profil type alpha. Série M uniquement.*

**Série M**
```
M1.3a  Comment évaluez-vous l'adéquation entre votre personnalité
       et les exigences comportementales de votre poste actuel ?
```

---

#### 1.4 — Compétences physiques
*Pas d'instrument standardisé. Items Likert maison uniquement.*

**Série P**
```
P1.4a  À quel niveau votre condition physique actuelle vous permet-elle
       d'assumer les contraintes physiques de votre métier ?
P1.4b  À quel niveau avez-vous l'habitude de travailler dans des conditions
       physiquement exigeantes de manière prolongée ?
```
**Série E**
```
E1.4a  À quel niveau ce poste impose-t-il des exigences physiques significatives
       (effort soutenu, endurance, conditions dégradées) ?
E1.4b  À quel niveau une bonne condition physique est-elle nécessaire
       pour tenir ce poste sur la durée du contrat ?
```
**Série M**
```
M1.4a  Comment évaluez-vous l'adéquation entre votre condition physique
       et les exigences physiques réelles de votre poste ?
```

---

### 6.3 Famille 2 — N-S fit

#### 2.1 — Besoin d'autonomie
*Entièrement couvert par SDT/MWMS. Série M uniquement.*

**Série M**
```
M2.1a  Comment évaluez-vous l'adéquation entre votre besoin d'autonomie
       et le degré de liberté que vous offre votre poste actuel ?
M2.1b  Dans quelle mesure le niveau de délégation correspond-il à ce dont
       vous avez besoin pour travailler efficacement ?
```

---

#### 2.2 — Besoin de progression
*SDT/MWMS + items Likert sur opportunités concrètes.*

**Série E**
```
E2.2a  Dans quelle mesure ce poste offre-t-il des perspectives réelles
       d'évolution professionnelle à moyen terme ?
E2.2b  Dans quelle mesure l'organisation investit-elle concrètement dans
       le développement des compétences de ses collaborateurs ?
```
**Série M**
```
M2.2a  Comment évaluez-vous l'adéquation entre vos aspirations de progression
       et les perspectives offertes par votre poste actuel ?
```

---

#### 2.3 — Intérêts professionnels vs. contenu du poste
*SDT/MWMS étendu — intérêts absorbés comme facette de la motivation intrinsèque (Rounds & Su, 2014). Items Likert complémentaires pour la congruence contextuelle.*

**Série P**
```
P2.3a  Dans quelle mesure les activités centrales de votre métier vous semblent-elles
       intrinsèquement stimulantes, indépendamment de la rémunération ou de la
       reconnaissance qu'elles procurent ?
P2.3b  Dans quelle mesure avez-vous le sentiment que votre domaine professionnel
       correspond à ce que vous êtes naturellement porté à faire et à explorer ?
```
**Série E**
```
E2.3a  Dans quelle mesure ce poste est-il dominé par des activités
       à forte composante manuelle et technique ?
E2.3b  Dans quelle mesure ce poste implique-t-il des activités relationnelles
       et d'interaction humaine comme dimension principale ?
E2.3c  Dans quelle mesure ce poste requiert-il une dimension analytique
       et de résolution de problèmes complexes ?
```
**Série M**
```
M2.3a  Comment évaluez-vous l'adéquation entre vos intérêts professionnels
       et le contenu réel de votre poste actuel ?
```

---

#### 2.4 — Besoin de reconnaissance
*SDT/MWMS + items Likert sur culture feedback concrète.*

**Série P**
```
P2.4a  Dans quelle mesure avez-vous besoin de recevoir des retours réguliers
       sur la qualité de votre travail pour maintenir votre motivation ?
```
**Série E**
```
E2.4a  Dans quelle mesure ce poste s'inscrit-il dans une culture où
       les retours réguliers sur le travail sont une pratique établie ?
E2.4b  Dans quelle mesure les efforts et contributions individuelles sont-ils
       reconnus concrètement par la hiérarchie dans ce contexte ?
```
**Série M**
```
M2.4a  Comment évaluez-vous l'adéquation entre votre besoin de reconnaissance
       et la culture de feedback de votre environnement de travail actuel ?
```

---

#### 2.5 — Stabilité financière
*Pas d'instrument standardisé. Items Likert maison.*

**Série P**
```
P2.5a  Dans quelle mesure avez-vous besoin d'une rémunération stable
       et prévisible pour travailler sereinement ?
P2.5b  Dans quelle mesure êtes-vous à l'aise avec une rémunération variable
       ou liée à des facteurs indépendants de votre contrôle ?
```
**Série E**
```
E2.5a  Dans quelle mesure la structure de rémunération de ce poste
       est-elle stable et prévisible sur la durée du contrat ?
E2.5b  Dans quelle mesure la rémunération totale comprend-elle
       une part variable significative ?
```
**Série M**
```
M2.5a  Comment évaluez-vous l'adéquation entre vos besoins financiers
       et la structure de rémunération de votre poste actuel ?
```

---

#### 2.6 — Besoin de stimulation
*SDT/MWMS + items Likert sur richesse concrète des tâches.*

**Série P**
```
P2.6a  Dans quelle mesure avez-vous besoin que votre travail quotidien
       soit varié et stimulant pour rester engagé ?
```
**Série E**
```
E2.6a  Dans quelle mesure ce poste implique-t-il une variété de tâches
       suffisante pour éviter la routine ?
E2.6b  Dans quelle mesure ce poste expose-t-il à des défis nouveaux
       et stimulants de façon régulière ?
```
**Série M**
```
M2.6a  Comment évaluez-vous l'adéquation entre votre besoin de stimulation
       et la richesse des tâches que propose votre poste actuel ?
```

---

### 6.4 Famille 3 — PO fit

#### 3.1 — Congruence de valeurs
*CES adaptée (honnêteté, accomplissement, équité, entraide).*

**Série P**
```
P3.1a  Dans quelle mesure l'honnêteté et la transparence sont-elles des valeurs
       centrales dans votre façon de travailler ?
P3.1b  Dans quelle mesure l'équité dans les relations de travail est-elle
       une valeur importante pour vous ?
P3.1c  Dans quelle mesure l'accomplissement par le travail bien fait est-il
       un moteur fort pour vous ?
P3.1d  Dans quelle mesure l'entraide et la solidarité entre collègues sont-elles
       des valeurs que vous défendez activement ?
```
**Série E**
```
E3.1a  Dans quelle mesure l'honnêteté et la transparence sont-elles des valeurs
       explicitement promues dans cette organisation ?
E3.1b  Dans quelle mesure l'équité dans le traitement des collaborateurs est-elle
       une priorité réelle de cette organisation ?
E3.1c  Dans quelle mesure cette organisation valorise-t-elle l'excellence
       et l'accomplissement dans le travail ?
E3.1d  Dans quelle mesure la culture de cette organisation favorise-t-elle
       l'entraide et la solidarité ?
```
**Série M**
```
M3.1a  Comment évaluez-vous l'adéquation entre vos valeurs personnelles
       et les valeurs de l'organisation pour laquelle vous travaillez ?
M3.1b  Dans quelle mesure vous reconnaissez-vous dans la culture
       et les principes de votre organisation actuelle ?
```

---

#### 3.2 — Congruence d'objectifs
*SDT/MWMS + items Likert sur objectifs concrets.*

**Série P**
```
P3.2a  Dans quelle mesure vos objectifs professionnels sont-ils alignés
       avec le type de mission que vous souhaitez accomplir ?
```
**Série E**
```
E3.2a  Dans quelle mesure les objectifs de cette organisation sont-ils
       clairement communiqués à ses collaborateurs ?
E3.2b  Dans quelle mesure ces objectifs sont-ils susceptibles de correspondre
       aux aspirations professionnelles de la personne recrutée ?
```
**Série M**
```
M3.2a  Comment évaluez-vous l'adéquation entre vos objectifs professionnels
       et ceux de l'organisation pour laquelle vous travaillez ?
```

---

#### 3.3 — Rapport à la hiérarchie

**Série P**
```
P3.3a  Dans quelle mesure êtes-vous à l'aise pour travailler dans
       un environnement à hiérarchie clairement définie et respectée ?
P3.3b  Dans quelle mesure le respect de procédures formelles vous semble-t-il
       naturel dans un contexte professionnel ?
```
**Série E**
```
E3.3a  Dans quelle mesure ce poste s'inscrit-il dans une structure
       hiérarchique clairement définie et formalisée ?
E3.3b  Dans quelle mesure ce poste requiert-il le respect strict
       de protocoles et procédures établies ?
```
**Série M**
```
M3.3a  Comment évaluez-vous l'adéquation entre votre rapport à la hiérarchie
       et le niveau de formalisme de votre environnement de travail actuel ?
```

---

#### 3.4 — Culture de sécurité

**Série P**
```
P3.4a  Dans quelle mesure accordez-vous une importance prioritaire au respect
       des règles de sécurité, même sous pression ?
P3.4b  Dans quelle mesure êtes-vous prêt à signaler un problème de sécurité
       même si cela implique de remettre en question une décision hiérarchique ?
```
**Série E**
```
E3.4a  Dans quelle mesure cette organisation fait-elle de la sécurité
       une priorité non négociable dans toutes ses opérations ?
E3.4b  Dans quelle mesure les collaborateurs sont-ils activement encouragés
       à signaler les risques et incidents ?
```
**Série M**
```
M3.4a  Comment évaluez-vous l'adéquation entre votre rapport à la sécurité
       et la culture de sécurité de votre organisation actuelle ?
```

---

### 6.5 Famille 4 — PG fit

#### 4.1 — Valeurs de travail
*CES — P vs. profil agrégé équipe. Série M uniquement en mode molar.*

**Série M**
```
M4.1a  Comment évaluez-vous l'adéquation entre vos valeurs de travail
       et celles des membres de votre équipe actuelle ?
```

---

#### 4.2 — Style de travail

**Série P**
```
P4.2a  Dans quelle mesure votre façon de vous organiser est-elle compatible
       avec un travail en équipe rapprochée sur la durée ?
P4.2b  Dans quelle mesure votre rythme et méthode de travail s'adaptent-ils
       facilement à ceux des autres ?
```
**Série E**
```
E4.2a  Dans quelle mesure les membres de cette équipe partagent-ils
       un style de travail homogène et compatible ?
E4.2b  Dans quelle mesure cette équipe valorise-t-elle la rigueur
       et l'organisation dans la réalisation des tâches communes ?
```
**Série M**
```
M4.2a  Comment évaluez-vous l'adéquation entre votre style de travail
       et celui des membres de votre équipe actuelle ?
```

---

#### 4.3 — Personnalité équipe
*Entièrement couvert par TIPI (P vs. mean équipe). Série M uniquement.*

**Série M**
```
M4.3a  Comment évaluez-vous l'adéquation entre votre personnalité
       et celle des membres de votre équipe actuelle ?
M4.3b  Dans quelle mesure vous sentez-vous à votre place au sein
       de votre équipe sur le plan humain ?
```

---

#### 4.4 — Compatibilité culturelle et linguistique

**Série P**
```
P4.4a  Dans quelle mesure êtes-vous à l'aise pour travailler au sein
       d'une équipe multiculturelle et multilingue ?
P4.4b  Dans quelle mesure maîtrisez-vous la ou les langues nécessaires
       pour communiquer efficacement avec vos collègues ?
```
**Série E**
```
E4.4a  Dans quelle mesure cette équipe est-elle composée de membres
       d'horizons culturels diversifiés ?
E4.4b  Dans quelle mesure cette équipe travaille-t-elle dans une ou plusieurs
       langues qui ne sont pas la langue maternelle de tous ?
```
**Série M**
```
M4.4a  Comment évaluez-vous l'adéquation entre votre profil culturel
       et linguistique et celui de votre équipe actuelle ?
```

---

#### 4.5 — Objectifs de séjour
*SDT/MWMS (P vs. mean équipe). Série M uniquement.*

**Série M**
```
M4.5a  Comment évaluez-vous l'adéquation entre vos motivations
       et celles des membres de votre équipe actuelle ?
```

---

### 6.6 Famille 5 — PS fit

#### 5.1 — Valeurs professionnelles
*CES — P candidat vs. P capitaine (profils réels). Série M uniquement.*

**Série M**
```
M5.1a  Comment évaluez-vous l'adéquation entre vos valeurs professionnelles
       et celles de votre supérieur direct actuel ?
```

---

#### 5.2 — Style de management
*SDT/MWMS (P cand. vs. P cap.) + items Likert sur préférences concrètes.*

**Série P**
```
P5.2a  Dans quelle mesure préférez-vous un style de management directif,
       avec des instructions claires et un cadre bien défini ?
P5.2b  Dans quelle mesure avez-vous besoin d'un supérieur qui vous accompagne
       plutôt que d'un supérieur qui contrôle ?
P5.2c  Dans quelle mesure êtes-vous à l'aise avec un supérieur qui délègue
       largement et attend de l'initiative de votre part ?
```
**Série E (profil capitaine — renseigné par le capitaine lui-même)**
```
E5.2a  Dans quelle mesure votre style de management est-il directif
       et structurant ?
E5.2b  Dans quelle mesure adoptez-vous une posture d'accompagnement
       et de soutien auprès de vos collaborateurs ?
E5.2c  Dans quelle mesure déléguez-vous largement et encouragez-vous
       l'initiative individuelle ?
```
**Série M**
```
M5.2a  Comment évaluez-vous l'adéquation entre le style de management
       de votre supérieur direct et celui dont vous avez besoin ?
```

---

#### 5.3 — Style de communication

**Série P**
```
P5.3a  Dans quelle mesure préférez-vous une communication directe
       et franche avec votre supérieur hiérarchique ?
P5.3b  Dans quelle mesure vous sentez-vous à l'aise pour exprimer
       un désaccord constructif à votre supérieur ?
```
**Série E (profil capitaine)**
```
E5.3a  Dans quelle mesure communiquez-vous de façon directe
       et transparente avec vos collaborateurs ?
E5.3b  Dans quelle mesure encouragez-vous l'expression de désaccords
       ou suggestions de façon constructive ?
```
**Série M**
```
M5.3a  Comment évaluez-vous l'adéquation entre votre style de communication
       et celui de votre supérieur direct actuel ?
```

---

#### 5.4 — Personnalité superviseur
*Entièrement couvert par TIPI (P cand. vs. P cap., profils réels). Série M uniquement.*

**Série M**
```
M5.4a  Comment évaluez-vous l'adéquation entre votre personnalité
       et celle de votre supérieur direct sur le plan humain ?
M5.4b  Dans quelle mesure vous sentez-vous en confiance dans votre
       relation avec votre supérieur direct actuel ?
```

---

## 7. Items — Module maritime

### 7.1 Principes spécifiques

Dimensions sans équivalent dans la littérature générale. Pas d'instruments standardisés applicables. Items Likert maison = mesures primaires. Format identique à la couche universelle.

---

### 7.2 Famille 6 — Fit physique-environnemental

#### 6.1 — Tolérance espace restreint / promiscuité

**Série P**
```
P6.1a  Dans quelle mesure êtes-vous à l'aise pour vivre et travailler
       dans un espace physique très restreint de façon continue ?
P6.1b  Dans quelle mesure supportez-vous bien de partager en permanence
       votre espace de vie avec des collègues de travail ?
P6.1c  Dans quelle mesure avez-vous déjà vécu des expériences similaires
       (colocation intensive, internat, vie à bord) ?
       (1 = aucune expérience / 7 = expérience longue et répétée)
```
**Série E**
```
E6.1a  Dans quelle mesure ce poste implique-t-il de vivre et travailler
       dans un espace physique restreint de façon continue ?
E6.1b  Dans quelle mesure ce poste requiert-il de partager en permanence
       son espace de vie avec ses collègues ?
```
**Série M**
```
M6.1a  Comment évaluez-vous l'adéquation entre votre tolérance à l'espace
       restreint et les conditions de logement de votre poste actuel ?
M6.1b  Dans quelle mesure la cohabitation permanente avec votre équipage
       correspond-elle à ce que vous êtes en mesure de supporter sereinement ?
```

---

#### 6.2 — Tolérance à l'isolement géographique

**Série P**
```
P6.2a  Dans quelle mesure êtes-vous à l'aise pour rester coupé de votre
       réseau social et familial terrestre pendant plusieurs semaines ?
P6.2b  Dans quelle mesure l'absence d'accès immédiat aux infrastructures
       urbaines vous affecte-t-elle ?
P6.2c  Dans quelle mesure avez-vous déjà vécu des périodes d'isolement
       géographique prolongées ?
       (1 = jamais / 7 = expérience longue et répétée)
```
**Série E**
```
E6.2a  Dans quelle mesure ce poste implique-t-il des périodes prolongées
       loin des infrastructures urbaines et du réseau social terrestre ?
E6.2b  Dans quelle mesure la connectivité (internet, téléphone) est-elle
       limitée ou contrainte dans ce contexte de navigation ?
```
**Série M**
```
M6.2a  Comment évaluez-vous l'adéquation entre votre tolérance à l'isolement
       et les conditions de navigation de votre poste actuel ?
M6.2b  Dans quelle mesure la coupure avec votre vie terrestre correspond-elle
       à ce que vous êtes en mesure de vivre sereinement ?
```

---

#### 6.3 — Rapport au risque physique réel
*Note : seuil éliminatoire si sous-fit critique ET si sur-fit (insouciance dangereuse)*

**Série P**
```
P6.3a  Dans quelle mesure êtes-vous à l'aise pour travailler dans des
       conditions comportant un risque physique réel et non nul ?
P6.3b  Dans quelle mesure appliquez-vous systématiquement les consignes
       de sécurité même lorsqu'elles ralentissent le travail ?
P6.3c  Dans quelle mesure évaluez-vous calmement les risques avant d'agir
       dans une situation physiquement dangereuse ?
```
**Série E**
```
E6.3a  Dans quelle mesure ce poste expose-t-il régulièrement à des situations
       comportant un risque physique réel (hauteur, mer formée, manœuvres) ?
E6.3b  Dans quelle mesure ce poste requiert-il une vigilance constante
       sur les procédures de sécurité dans l'exécution des tâches quotidiennes ?
```
**Série M**
```
M6.3a  Comment évaluez-vous l'adéquation entre votre rapport au risque
       et le niveau d'exposition réelle de votre poste actuel ?
M6.3b  Dans quelle mesure votre approche de la sécurité correspond-elle
       à la culture de sécurité de votre environnement de travail actuel ?
```

---

#### 6.4 — Tolérance aux rythmes atypiques

**Série P**
```
P6.4a  Dans quelle mesure êtes-vous capable de maintenir des performances
       satisfaisantes avec des horaires irréguliers et des quarts de nuit ?
P6.4b  Dans quelle mesure acceptez-vous d'être disponible en dehors de vos
       heures habituelles selon les besoins opérationnels ?
P6.4c  Dans quelle mesure récupérez-vous efficacement lors de courtes
       périodes de repos entre deux quarts de travail ?
```
**Série E**
```
E6.4a  Dans quelle mesure ce poste implique-t-il des horaires atypiques,
       des quarts de nuit ou une disponibilité étendue ?
E6.4b  Dans quelle mesure les périodes de repos sont-elles contraintes
       et peu prévisibles dans ce contexte de navigation ?
```
**Série M**
```
M6.4a  Comment évaluez-vous l'adéquation entre votre tolérance aux rythmes
       atypiques et les horaires réels de votre poste actuel ?
M6.4b  Dans quelle mesure les contraintes horaires de votre poste correspondent-elles
       à ce que vous êtes en mesure de gérer sereinement ?
```

---

#### 6.5 — Sensibilité aux conditions météo et à l'instabilité

**Série P**
```
P6.5a  Dans quelle mesure supportez-vous bien le mouvement continu
       d'un bateau en navigation sur plusieurs jours ?
P6.5b  Dans quelle mesure maintenez-vous votre efficacité dans des
       conditions météorologiques difficiles ?
```
**Série E**
```
E6.5a  Dans quelle mesure ce poste implique-t-il des navigations en conditions
       météorologiques potentiellement difficiles de façon régulière ?
E6.5b  Dans quelle mesure les conditions impliquent-elles un mouvement permanent
       du bateau susceptible d'affecter le confort ?
```
**Série M**
```
M6.5a  Comment évaluez-vous l'adéquation entre votre tolérance aux conditions
       de navigation et les conditions réelles de votre poste actuel ?
```

---

### 7.3 Famille 7 — Fit mobilité-temporel

#### 7.1 — Mobilité requise vs. situation personnelle

**Série P**
```
P7.1a  Dans quelle mesure votre situation personnelle actuelle est-elle
       compatible avec une absence prolongée de votre domicile ?
P7.1b  Dans quelle mesure disposez-vous d'une flexibilité géographique
       suffisante pour embarquer sur différentes zones de navigation ?
P7.1c  Dans quelle mesure vos proches comprennent-ils et acceptent-ils
       les contraintes de mobilité liées à votre activité professionnelle ?
```
**Série E**
```
E7.1a  Dans quelle mesure ce poste requiert-il une disponibilité
       géographique étendue (zones de navigation variables) ?
E7.1b  Dans quelle mesure la durée d'absence impliquée par ce poste
       est-elle significative (supérieure à 4 semaines consécutives) ?
```
**Série M**
```
M7.1a  Comment évaluez-vous l'adéquation entre votre situation personnelle
       et les exigences de mobilité de votre poste actuel ?
M7.1b  Dans quelle mesure les contraintes géographiques de votre poste
       correspondent-elles à ce que vous et vos proches pouvez assumer ?
```

---

#### 7.2 — Durée d'embarquement vs. besoins de rupture

**Série P**
```
P7.2a  Dans quelle mesure êtes-vous à l'aise pour rester embarqué
       de façon continue pendant la durée typique prévue pour ce poste ?
P7.2b  Dans quelle mesure avez-vous besoin de périodes régulières à terre
       pour maintenir votre équilibre personnel et professionnel ?
P7.2c  Dans quelle mesure avez-vous déjà tenu des périodes d'embarquement
       comparables sans difficulté majeure ?
       (1 = jamais / 7 = expérience longue et répétée sans difficulté)
```
**Série E**
```
E7.2a  Quelle est la durée d'embarquement continu typique pour ce poste ?
       (item numérique : durée en semaines)
E7.2b  Dans quelle mesure des périodes de shore leave régulières
       sont-elles garanties dans le cadre de ce contrat ?
```
**Série M**
```
M7.2a  Comment évaluez-vous l'adéquation entre votre besoin de rupture
       et les périodes de shore leave réelles de votre poste actuel ?
M7.2b  Dans quelle mesure la durée de votre embarquement actuel correspond-elle
       à ce que vous êtes en mesure de tenir sereinement ?
```

---

#### 7.3 — Tolérance à l'incertitude de programme

**Série P**
```
P7.3a  Dans quelle mesure êtes-vous à l'aise face à des changements
       d'itinéraire ou de planning de dernière minute ?
P7.3b  Dans quelle mesure pouvez-vous maintenir votre engagement professionnel
       lorsque les plans changent sans préavis ?
```
**Série E**
```
E7.3a  Dans quelle mesure le programme de navigation est-il sujet à des
       modifications fréquentes ou de dernière minute ?
E7.3b  Dans quelle mesure la planification à long terme est-elle limitée
       par la nature des activités de ce yacht ?
```
**Série M**
```
M7.3a  Comment évaluez-vous l'adéquation entre votre tolérance à l'incertitude
       et le niveau de prévisibilité du programme de votre poste actuel ?
```

---

#### 7.4 — Rapport au contrat non-permanent

**Série P**
```
P7.4a  Dans quelle mesure êtes-vous à l'aise avec un contrat à durée
       déterminée ou saisonnier sans garantie de renouvellement ?
P7.4b  Dans quelle mesure avez-vous anticipé et planifié les périodes
       de non-emploi entre deux contrats d'embarquement ?
```
**Série E**
```
E7.4a  Dans quelle mesure ce poste est-il proposé sur une base contractuelle
       non permanente (CDD saisonnier, MLC) ?
E7.4b  Dans quelle mesure des perspectives de continuité à plus long terme
       sont-elles possibles dans ce contexte ?
```
**Série M**
```
M7.4a  Comment évaluez-vous l'adéquation entre votre rapport à l'emploi
       non-permanent et le cadre contractuel de votre poste actuel ?
```

---

## 8. Protocole de validation psychométrique

### 8.1 Structure générale

```
PHASE 0 — Validation de contenu        (qualitatif, avant collecte)
PHASE 1 — Validation pilote            (N = 30–50, environnements proches)
PHASE 2 — Validation principale        (N = 150–300, multi-contextes)
PHASE 3 — Validation longitudinale     (N = 80–100, yachting)
PHASE 4 — Recalibration continue       (données opérationnelles)
```

---

### 8.2 Phase 0 — Validation de contenu

**Panel d'experts (8–12 personnes) :**
- Groupe A (3–4 experts psychométrie/P-E fit) : ancrage théorique, redondances, ambiguïtés
- Groupe B (4–6 experts domaine maritime) : pertinence contextuelle, dimensions manquantes

**Évaluation par item (échelle 1–4) :** pertinence, clarté, représentativité

**Critères :**
```
CVI_item = experts ayant coté 3–4 / total experts  ≥ 0.78  (Lynn, 1986)
S-CVI    = moyenne CVI des items d'une dimension    ≥ 0.90
```

**Outputs :** items retenus/révisés/supprimés, version finale pour phase pilote.

---

### 8.3 Phase 1 — Validation pilote

**N = 30–50** — formations maritimes STCW, hôtellerie saisonnière, marine marchande junior.

**Analyses :**

1. **Distributions :** absence d'effet plancher/plafond (< 20% aux extrémités)

2. **Cohérence interne préliminaire :**
```
Alpha de Cronbach ≥ 0.70  (Nunnally, 1976)
Omega de McDonald ≥ 0.70
r item-total corrigé ≥ 0.30  → item à réviser si inférieur
```

3. **Entretiens cognitifs (think-aloud, n = 8–10) :**
Identification des incompréhensions et interprétations erronées. Prioritaire pour items module maritime (sans précédent littéraire).

**Outputs :** version finale des items, rapport pilote, estimation durée de passation.

---

### 8.4 Phase 2 — Validation principale

**N requis :**
- Couche universelle : N = 150–300 (multi-contextes)
- Module maritime : N = 80–150 (contextes maritimes uniquement)

```
Règle générale : N ≥ max(200, 5 × nombre d'items testés simultanément)
Possible par sous-ensembles (famille par famille) si N limité.
```

#### 2.1 — Analyse Factorielle Confirmatoire (CFA)

**Logiciel :** R (lavaan) ou Python (semopy)
**Estimateur :** WLSMV pour données Likert avec N < 200 (robuste à la non-normalité)

**Modèles comparés :**
```
Modèle 1 : Structure théorique proposée
Modèle 2 : Modèle unidimensionnel (tout → 1 facteur)
Modèle 3 : Modèle saturé (1 facteur par item)
→ Modèle 1 doit ajuster significativement mieux que 2 et 3
```

**Indices d'ajustement :**
| Indice | Acceptable | Bon |
|--------|-----------|-----|
| CFI | ≥ 0.90 | ≥ 0.95 |
| RMSEA | ≤ 0.08 | ≤ 0.06 |
| SRMR | ≤ 0.08 | ≤ 0.05 |
| χ²/df | ≤ 5 | ≤ 3 |

#### 2.2 — Fiabilité

```
Alpha de Cronbach et Omega de McDonald par dimension :
≥ 0.70 acceptable | ≥ 0.80 bien | ≥ 0.90 excellent (attention redondance)

ICC test-retest (n = 30–40, intervalle 2–3 semaines) ≥ 0.70
```

#### 2.3 — Validité convergente

Tests de convergence prioritaires :
| Nos items | Instrument référence | r attendu |
|-----------|---------------------|-----------|
| Besoin d'autonomie (P2.1) | MWMS régulation autonome | ≥ 0.50 |
| Valeurs PO fit (P3.1) | CES originale | ≥ 0.55 |
| Culture sécurité (P3.4) | Safety Attitudes Questionnaire | ≥ 0.45 |
| Tolérance isolement (P6.2) | Échelle solitude Cacioppo | ≥ 0.40 |
| Tolérance risque (P6.3) | DOSPERT | ≥ 0.45 |

**Average Variance Extracted (AVE) :**
```
AVE = Σ(λ²) / (Σ(λ²) + Σ(1 - λ²))  ≥ 0.50  (Fornell & Larcker, 1981)
```

#### 2.4 — Validité discriminante

**Test de Fornell-Larcker :**
```
Pour chaque paire (i,j) : AVE(i) > r²(i,j)  ET  AVE(j) > r²(i,j)
```

**Test HTMT (plus robuste) :**
```
HTMT(i,j) < 0.85  →  validité discriminante acceptable
HTMT(i,j) < 0.90  →  limite acceptable
```

Paires à surveiller : D-A vs. N-S fit | PG vs. PS fit | dim. 6.1 vs. 6.2

#### 2.5 — Validité critérielle

Outcomes mesurés dans la même passation :
| Outcome | Instrument | Prédiction |
|---------|-----------|-----------|
| Satisfaction | BRS-5 ou item unique Wanous | r > 0 |
| Intention de quitter | 3 items Lauver & Kristof-Brown | r < 0 |
| Engagement | UWES-9 | r > 0 |
| Bien-être | GHQ-12 | r > 0 (cohérent Jung et al., 2024) |

Hiérarchie attendue (Kristof-Brown et al., 2005) :
```
D-A → performance r > .30
N-S → satisfaction r > .40
PO → engagement et turnover r > .35
PG → satisfaction et OCB r > .30
PS → satisfaction et turnover r > .35
```

#### 2.6 — Validité incrémentale (items maison vs. instruments standardisés)

Régressions hiérarchiques (méthode Chuang et al., 2016) :
```
Procédure 1 : instruments standardisés → ΔR² en ajoutant items maison
Procédure 2 : items maison → ΔR² en ajoutant instruments standardisés

ΔR² significatif dans P1 → items maison capturent quelque chose d'additionnel
```

---

### 8.5 Phase 3 — Validation longitudinale (yachting)

**N = 80–100 embarquements avec suivi complet ≥ 3 mois**

**Design temporel :**
```
T0 Pré-recrutement : mesures atomistic → PSI_pondéré
T1 +4 semaines    : mesures molar → satisfaction, engagement, intention quitter
T2 +3 mois        : mesures molar → outcomes + performance (éval. capitaine)
T3 Fin contrat    : outcome final → renouvellement (oui/non) + raison départ
```

**Analyses :**

**3.1 — Relation fit objectif → fit perçu**
```
Fit_molar_T1 ~ PSI_T0 + contrôles  →  β > 0, p < .05
Test de la proposition Edwards et al. (2006) : atomistic précède molar
```

**3.2 — Relation fit objectif → outcomes**
```
Outcome_T2 ~ PSI_T0 + contrôles  →  β significatif direction attendue
```

**3.3 — Médiation du fit perçu**
```
PSI_T0 → Fit_molar_T1 → Outcome_T2
Bootstrap 5000 iterations (cohérent Kühner et al., 2024)
```

**3.4 — Validité prédictive sur turnover réel**
```
Régression logistique : Renouvellement_T3 (0/1) ~ PSI_T0 + contrôles
Critère : AUC > 0.65  (mesure d'impact principale pour les recruteurs)
```

**3.5 — Calibration des pondérations via RSA**
RSA sur sous-ensemble avec outcomes T3 disponibles.
Remplacement des pondérations littérature par des pondérations empiriques maritimes.

---

### 8.6 Phase 4 — Recalibration continue

```
PIPELINE DE RECALIBRATION
───────────────────────────────────────────────────────────────
Nouveau recrutement → passation → PSI_T0
Embarquement → mesures molar T1, T2, T3
Fin contrat → outcome final enregistré

Tous les 6 mois (ou N += 50 observations) :
→ Mise à jour pondérations w(i) via RSA
→ Mise à jour profils types alpha si divergence > seuil
→ Rapport de calibration documenté (traçabilité)
```

**Gouvernance :** toute modification de pondération ou profil type est documentée avec date, N, et changements opérés. Essentiel pour traçabilité scientifique et conformité RGPD/IA Act.

---

### 8.7 Synthèse des critères par phase

| Phase | N requis | Critères clés | Décision |
|-------|----------|---------------|---------|
| 0 — Contenu | 8–12 experts | CVI ≥ 0.78, S-CVI ≥ 0.90 | Items retenus/révisés |
| 1 — Pilote | 30–50 | α ≥ 0.70, pas d'effet plafond | Version finale items |
| 2 — Principale | 150–300 | CFI ≥ 0.90, RMSEA ≤ 0.08, AVE ≥ 0.50, HTMT < 0.85 | Validation formelle |
| 3 — Longitudinale | 80–100 | β fit→outcomes p < .05, AUC > 0.65 | Validité prédictive |
| 4 — Continue | N += 50 | Stabilité pondérations, RMSE décroissant | Amélioration continue |

---

---

## 9. Taxonomie maritime — Postes et types de yachts

### 9.1 Inventaire des postes

#### Liste complète V1

```python
class YachtPosition(str, Enum):
    # PONT
    CAPTAIN           = "Captain"
    CHIEF_OFFICER     = "Chief Officer"       # = First Mate sur grands yachts
    SECOND_OFFICER    = "Second Officer"      # Sur yachts 40m+
    BOSUN             = "Bosun"
    DECKHAND          = "Deckhand"
    DECK_STEWARD      = "Deck/Steward"        # Rôle hybride pont/service (20–35m)

    # INTÉRIEUR
    CHIEF_STEWARDESS  = "Chief Stewardess"
    CHIEF_STEWARD     = "Chief Steward"       # Équivalent masculin
    PURSER            = "Purser"              # Sur yachts 50m+
    SECOND_STEWARDESS = "2nd Stewardess"
    STEWARDESS        = "Stewardess"          # = Steward

    # CUISINE
    CHEF              = "Chef"
    SOUS_CHEF         = "Sous Chef"

    # TECHNIQUE
    CHIEF_ENGINEER    = "Chief Engineer"
    SECOND_ENGINEER   = "2nd Engineer"
    ETO               = "ETO"                 # Electro-Technical Officer (MLC)
```

**Postes hors scope V1 :**
- Dive instructor / Water sports instructor → effectifs trop faibles
- Nanny / Private chef résidentiel → hors équipage MLC
- Delivery crews → contrats trop courts, profil atypique

#### Regroupements statistiques (3 niveaux)

**Niveau 1 — Département** *(N cumulé maximal — CFA et fiabilité)*

```python
class Department(str, Enum):
    DECK      = "Deck"
    # Captain, Chief/Second Officer, Bosun, Deckhand, Deck/Steward
    INTERIOR  = "Interior"
    # Chief/2nd Steward(ess), Purser, Stewardess, Chef, Sous Chef
    TECHNICAL = "Technical"
    # Chief/2nd Engineer, ETO
```

**Niveau 2 — Strate hiérarchique** *(validité critérielle — outcomes variables par niveau)*

```python
class HierarchyLevel(str, Enum):
    SENIOR = "Senior"
    # Captain, Chief Officer, Chief Stewardess/Steward, Chef, Chief Engineer, Purser
    MID    = "Mid"
    # Second Officer, Bosun, 2nd Stewardess, Sous Chef, 2nd Engineer, ETO
    JUNIOR = "Junior"
    # Deckhand, Stewardess, Deck/Steward
```

**Niveau 3 — Profil de contraintes** *(RSA et calibration des pondérations — plus prédictif)*

```python
class ConstraintProfile(str, Enum):
    COMMAND        = "Command"
    # Captain, Chief Officer
    # Haute responsabilité, leadership, sécurité, représentation

    TECHNICAL_OPS  = "Technical Operations"
    # Chief/2nd Engineer, ETO, Second Officer
    # Résolution de problèmes, autonomie technique, rigueur procédurale

    DECK_OPS       = "Deck Operations"
    # Bosun, Deckhand, Deck/Steward
    # Physique, travail d'équipe, exécution, polyvalence

    SERVICE_SENIOR = "Senior Service"
    # Chief Stewardess/Steward, Purser, Chef
    # Leadership d'équipe, relation client, excellence service

    SERVICE_JUNIOR = "Junior Service"
    # 2nd Stewardess, Stewardess, Sous Chef
    # Exécution service, adaptabilité, endurance
```

**Utilisation des regroupements selon l'analyse :**

```
ANALYSE                    GRANULARITÉ RECOMMANDÉE
────────────────────────────────────────────────────────────
Phase alpha SME        →   Poste individuel (profils distincts)
CFA / fiabilité        →   Département (N cumulé suffisant)
Validité critérielle   →   Strate hiérarchique (outcomes variables)
RSA / calibration      →   Profil de contraintes (plus prédictif)
Reporting recruteur    →   Poste individuel
```

---

### 9.2 Taxonomie des types de yachts

#### Deux dimensions structurantes

La culture à bord et le profil de fit requis sont déterminés par le croisement de deux dimensions :

- **Usage** : type d'activité et de relation avec les occupants
- **Taille (LOA)** : détermine la taille d'équipage, le degré de spécialisation et les conditions de vie

#### Dimension Usage

```
CHARTER      Yacht loué à des clients externes
             → rotation rapide, service d'excellence, pression tips,
               relation client centrale

PRIVATE      Yacht appartenant à un propriétaire/famille
             → relation long terme, discrétion, continuité d'équipage,
               adaptation aux préférences du propriétaire

EXPEDITION   Yacht conçu pour la navigation hauturière et l'exploration
             → autonomie technique, compétences navigation avancées,
               tolérance à l'isolement élevée

RACING       Yacht de compétition ou orienté performance
             → esprit d'équipe intense, priorité performance,
               tolérance à l'inconfort
```

#### Dimension Taille (LOA)

```
SMALL      < 24m    Équipage 2–4    Polyvalence extrême
MEDIUM     24–40m   Équipage 4–8    Spécialisation partielle
LARGE      40–60m   Équipage 8–14   Départements structurés
SUPERYACHT > 60m    Équipage 14+    Organisation quasi-corporate
```

#### Regroupements opérationnels pour la phase alpha (7 types)

Conçus pour maximiser la taille de panel SME tout en maintenant une homogénéité culturelle suffisante pour des profils de référence fiables.

```python
class YachtTypeAlpha(str, Enum):

    CHARTER_MED       = "Charter Mediterranean"
    # MEDIUM + LARGE charter — cœur du marché charter yachting
    # Culture : service excellence, tips, rotation clients, haute pression
    # Taille typique : 25–55m | Équipage : 4–12

    CHARTER_MEGA      = "Charter Superyacht"
    # SUPERYACHT charter — organisation quasi-hôtelière
    # Culture : standards ultra-luxury, hiérarchie forte, protocole
    # Taille typique : > 60m | Équipage : 14+

    PRIVATE_FAMILY    = "Private Family"
    # SMALL + MEDIUM + LARGE privé — propriétaires résidents
    # Culture : discrétion, relation long terme, flexibilité, loyauté
    # Taille typique : 15–50m | Équipage : 2–12

    PRIVATE_CORPORATE = "Private Corporate / UHNWI"
    # SUPERYACHT privé — gestion professionnalisée
    # Culture : protocole, confidentialité, excellence opérationnelle
    # Taille typique : > 55m | Équipage : 14+

    EXPEDITION        = "Expedition"
    # MEDIUM + LARGE + SUPERYACHT expédition
    # Culture : autonomie, compétence technique, tolérance isolement
    # Taille typique : 30m+ | Équipage : 6–20

    RACING            = "Racing / Performance"
    # SMALL + MEDIUM racing
    # Culture : performance, compétition, esprit d'équipe, inconfort accepté
    # Taille typique : 12–30m | Équipage : 5–15

    SAILING_CHARTER   = "Sailing Charter Small"
    # SMALL charter voile
    # Culture : pédagogie, polyvalence, relation client directe
    # Taille typique : 12–24m | Équipage : 2–5
```

#### Variables structurelles objectives du profil yacht

Ces variables alimentent directement les dimensions 6.x et 7.x sans passer par la perception — données E objectives du poste.

```python
@dataclass
class YachtStructuralProfile:
    yacht_type: YachtTypeAlpha
    loa_meters: float
    crew_size: int

    # → Dimension 7.1 (mobilité) et 7.2 (durée embarquement)
    charter_weeks_per_year: int
    avg_passage_duration_days: int
    home_port_stability: bool          # Port base fixe ou navigation permanente

    # → Dimension 6.2 (isolement)
    connectivity_level: str            # "high" | "medium" | "limited" | "offshore"

    # → Dimension 4.4 (culturel/linguistique)
    crew_nationality_diversity: str    # "homogeneous" | "mixed" | "highly_diverse"

    # → Items Likert E couche universelle
    formality_level: int               # 1–5 (décontracté → très protocolaire)
    owner_presence_ratio: float        # % du temps où le propriétaire est à bord
    service_standard: str              # "comfort" | "premium" | "ultra_luxury"
```

---

## Références

- Barrick, M.R., & Mount, M.K. (1991). The Big Five personality dimensions and job performance. *Personnel Psychology*, 44, 1–26.
- Cable, D.M., & DeRue, D.S. (2002). The convergent and discriminant validity of subjective fit perceptions. *Journal of Applied Psychology*, 87, 875–884.
- Chuang, A., Shen, C.T., & Judge, T.A. (2016). Development of a multidimensional instrument of person-environment fit: The PPEFS. *Applied Psychology: An International Review*, 65(1), 66–98.
- Deci, E.L., & Ryan, R.M. (1985). *Intrinsic motivation and self-determination in human behavior*. Plenum.
- Deci, E.L., & Ryan, R.M. (2000). The "what" and "why" of goal pursuits. *Psychological Inquiry*, 11, 227–268.
- Edwards, J.R. (1994). The study of congruence in organizational behavior research. *Organizational Behavior and Human Decision Processes*, 58, 51–100.
- Edwards, J.R., Cable, D.M., Williamson, I.O., Lambert, L.S., & Shipp, A.J. (2006). The phenomenology of fit. *Journal of Applied Psychology*, 91(4), 802–827.
- Edwards, J.R., & Parry, M.E. (1993). On the use of polynomial regression equations as an alternative to difference scores. *Academy of Management Journal*, 36, 1577–1613.
- Fornell, C., & Larcker, D.F. (1981). Evaluating structural equation models with unobservable variables and measurement error. *Journal of Marketing Research*, 18(1), 39–50.
- Gagné, M., et al. (2015). The multidimensional work motivation scale. *European Journal of Work and Organizational Psychology*, 24(2), 238–265.
- De Fruyt, F., & Mervielde, I. (1997). The five-factor model of personality and Holland's RIASEC interest types. *Personality and Individual Differences*, 23(1), 87–103.
- Holland, J.L. (1996). Exploring careers with a typology. *American Psychologist*, 51, 397–406. *(retrait justifié en §3.4)*
- Jung et al. (2024). Associations between person-environment fit and mental health. *BMC Public Health*, 24, 2083.
- Kristof-Brown, A.L., Zimmerman, R.D., & Johnson, E.C. (2005). Consequences of individuals' fit at work. *Personnel Psychology*, 58, 281–342.
- Kühner, C., Stein, M., & Zacher, H. (2024). A person-environment fit approach to environmental sustainability in the workplace. *Journal of Environmental Psychology*, 95, 102270.
- Larson, L.M., et al. (2002). Do Big Five and narrow personality traits predict distinctive facets of vocational interest types? *Journal of Career Assessment*, 10(4), 429–448.
- Lynn, M.R. (1986). Determination and quantification of content validity. *Nursing Research*, 35(6), 382–385.
- Ravlin, E.C., & Meglino, B.M. (1987). Effect of values on perception and decision making. *Journal of Applied Psychology*, 72, 666–673.
- Rounds, J., & Su, R. (2014). The nature and power of interests. *Current Directions in Psychological Science*, 23(2), 98–103.
- Schmidt, F.L., & Hunter, J.E. (1998). The validity and utility of selection methods in personnel psychology. *Psychological Bulletin*, 124(2), 262–274.
