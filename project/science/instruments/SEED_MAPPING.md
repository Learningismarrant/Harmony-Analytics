# SEED_MAPPING — Correspondance instruments ↔ seed backend

**Version :** 1.0 — Mars 2026
**Auteur :** head-of-science (Harmony)
**Objet :** Documentation exhaustive de l'etat actuel du seed backend, du statut juridique de chaque instrument, et du plan de migration vers les instruments valides P1/P2.

---

## 1. Etat actuel du seed backend

Chemin base : `backend/app/seed/tests/`

### Tableau de synthese

| Fichier seed | Instrument actuel | N items | Statut droits | Q correspondante | Action requise | Priorite |
|---|---|---|---|---|---|---|
| `etalons/ipip120.py` | IPIP-120 (Big Five, Maples 2014) | 120 | Domaine public | Q1 | Remplacer par HEXACO-60 (IPIP) | P1 |
| `etalons/rmaws.py` | R-MAWS (Gagne et al. 2010) | 19 | A clarifier | Q3 | Remplacer par custom SDT-6 | P1 |
| `hmr24.py` | HMR-24 (matrices, custom) | 24 | Custom — OK | Q2 GCA matrices | Verifier coherence specs | P2 |
| `ces_values.py` | CES adaptation maritime (custom) | 16 | Custom — OK | Q5 | Aligner sur Q5_values_items.md | P2 |
| `maritime_tolerance.py` | METS (custom) | 15 | Custom — OK | Q7 physique | Verifier coherence Q7_ICE_physical_items.md | P2 |
| `mobility_profile.py` | MMFS (custom) | 12 | Custom — OK | Q7 mobilite | Verifier coherence Q7_MMFS_mobility_items.md | P2 |

---

### Fiche instrument 1 — IPIP-120 (`etalons/ipip120.py`)

**Instrument actuel :** IPIP-120 (Maples, Guan, Carter & Miller, 2014). 120 items Likert 1-5. 5 dimensions Big Five (N, E, O, A, C) × 6 facettes chacune × 4 items. Base : pool IPIP (Goldberg et al. 2006).

**Statut droits :** Domaine public. L'IPIP (International Personality Item Pool) est explicitement place dans le domaine public par Lewis R. Goldberg (Oregon Research Institute). Aucune restriction d'usage commercial.

**Probleme scientifique :**
- 120 items = charge cognitive elevee pour un candidat (≈ 25-30 min). Taux d'abandon probable en contexte de recrutement en ligne.
- Big Five standard : absence de la dimension Honesty-Humility, critique pour la detection des comportements contre-productifs en environnement ICE (voir Q1_HEXACO_items.md).
- Maples et al. (2014) est une selection par IRT des meilleurs items IPIP pour les 30 facettes NEO — pertinent pour la recherche, sur-specifique pour notre besoin de traits de niveau domaine.

**Action requise :** Remplacer par un seed `seed_hexaco60.py` implementant les 60 items IPIP-HEXACO (Ashton, Lee & Goldberg, 2007). Conserver `ipip120.py` en archive jusqu'a la migration complete du snapshot engine.

**Reference :** Maples, J.L., Guan, L., Carter, N.T., & Miller, J.D. (2014). A test of the International Personality Item Pool as a measure of the Five-Factor Model via item response theory. *Psychological Assessment*, 26(4), 1255–1264.

---

### Fiche instrument 2 — R-MAWS (`etalons/rmaws.py`)

**Instrument actuel :** Revised Multidimensional Work Motivation Scale (Gagne et al. 2010/2015). 19 items Likert 1-7. 6 sous-echelles SDT : extrinsic_social, extrinsic_material, introjected, identified, intrinsic, amotivation.

**Statut droits :** A clarifier formellement. Les items R-MAWS sont publies dans une revue academique (Educational and Psychological Measurement) mais les auteurs (Gagne, Forest, Gilbert, Aube, Morin, Malorni) n'ont pas depose les items dans le domaine public. Le statut est celui d'une "publication ouverte" : les items peuvent etre utilises pour la recherche non-commerciale sans autorisation explicite (pratique courante dans la communaute psychometrique), mais l'usage commercial — notamment dans un produit SaaS de recrutement — necessite formellement un accord avec les auteurs ou l'editeur (SAGE Publications via la Division de Psychologie de l'Education).

**Probleme scientifique :**
- Items ancres sur "pourquoi vous efforcez-vous dans votre travail actuel" — peu adaptes a des candidats en transition professionnelle qui n'ont pas encore pris leur poste.
- Adaptation maritime requise non realisee (items generiques, non specifiques au contexte embarquement).

**Action requise :** Remplacer par le custom SDT-6 (`Q3_SDT_items.md`) deja redige. Le nouveau seed sera `seed_sdt6.py`. L'ancrage theorique SDT (Deci & Ryan, 2000) est identique — seul le wording change.

**References :**
- Gagne, M., Forest, J., Gilbert, M.-H., Aube, C., Morin, E., & Malorni, A. (2010). The Motivation at Work Scale: Validation evidence in two languages. *Educational and Psychological Measurement*, 70(4), 628–646.
- Deci, E.L., & Ryan, R.M. (2000). The "what" and "why" of goal pursuits: Human needs and the self-determination of behavior. *Psychological Inquiry*, 11(4), 227–268.

---

### Fiche instrument 3 — HMR-24 (`hmr24.py`)

**Instrument actuel :** Harmony Matrix Reasoning Test (HMR-24). 24 matrices visuospatiales QCM developpes custom par Radiant Analytics. Ancre sur la theorie CHC (Carroll-Horn-Cattell, 1993) — facteur Gf (fluid intelligence).

**Statut droits :** Custom — propriete de Radiant Analytics. Aucune contrainte de droits.

**Statut scientifique :** Instrument en cours de validation. Les matrices sont construites selon les regles de generation des matrices de Raven (distribution de formes, tailles, remplissages selon les colonnes et lignes), mais ne beneficient pas encore d'etude de validation psychometrique formelle (alpha, validite convergente avec ICAR ou Raven). Statut : ALPHA.

**Coherence avec Q2_GCA_matrices_specs.md :** A verifier (voir section 3 — lacunes).

**Action requise :** P2 — Verifier la coherence entre les matrices codees dans `hmr24.py` et les specifications de `Q2_GCA_matrices_specs.md`. Ajouter un commentaire de tracking dans le fichier seed avec le statut de validation.

**Reference CHC :** Carroll, J.B. (1993). *Human cognitive abilities: A survey of factor-analytic studies*. Cambridge University Press.

---

### Fiche instrument 4 — CES adaptation maritime (`ces_values.py`)

**Instrument actuel :** Adaptation maritime de la Comparative Emphasis Scale (Ravlin & Meglino, 1987). 16 items Likert 1-5. 4 valeurs : honesty, achievement, fairness, solidarity.

**Statut droits :** Custom — wording original Radiant Analytics. La CES originale (Ravlin & Meglino) est soumise au copyright des auteurs pour reproduction exacte, mais l'adaptation ici est suffisamment re-worded pour constituer un instrument independant. Statut : CUSTOM_ALPHA.

**Statut scientifique :** Instrument ALPHA non valide empiriquement. Les 4 valeurs sont theoriquement ancrées (Ravlin & Meglino, 1987 ; Rokeach, 1973) mais les seuils de congruence (PSI) sont calibres par jugement SME, pas sur donnees empiriques.

**Note sur la valeur `honesty` :** Chevauchement conceptuel avec la facette Sincerity/Fairness de H (Honesty-Humility HEXACO). Avec le passage HEXACO, la valeur `honesty` dans `ces_values.py` peut etre partiellement predicite par H — risque de redondance (multicollinearite Q1/Q5 a surveiller, VIF < 5 requis lors des retrains OLS).

**Coherence avec Q5_values_items.md :** A verifier — le fichier `Q5_values_items.md` (Mars 2026) contient une banque de 32 items (8/valeur) pour une cible de 16 items (4/valeur). La migration consiste a remplacer les 16 items de `ces_values.py` par les items selectionnes depuis `Q5_values_items.md`.

**Action requise :** P2 — Aligner `ces_values.py` sur la banque `Q5_values_items.md`. Conserver la meme structure de seed (4 modules, 4 items chacun).

**References :**
- Ravlin, E.C., & Meglino, B.M. (1987). Effect of values on perception and decision making: A study of alternative work values measures. *Journal of Applied Psychology*, 72(4), 666–673.
- Rokeach, M. (1973). *The nature of human values*. Free Press.

---

### Fiche instrument 5 — METS (`maritime_tolerance.py`)

**Instrument actuel :** Maritime Environmental Tolerance Scale (METS). 15 items Likert 1-5. 5 traits : confined_space_tolerance, isolation_tolerance, physical_risk_tolerance, schedule_tolerance, weather_tolerance.

**Statut droits :** Custom — propriete de Radiant Analytics. Ancre sur les exigences MCA/STCW et la litterature ICE (Stuster, 2010).

**Statut scientifique :** Instrument ALPHA. Construit ad hoc, aucune etude de validation externe disponible pour ce domaine specifique. Alpha de Cronbach non calcule sur donnees reelles (population cible = 0 au moment de la redaction).

**Coherence avec Q7_ICE_physical_items.md :** A verifier — `Q7_ICE_physical_items.md` (Mars 2026) peut contenir des items revises ou supplementaires par rapport aux 15 items du seed actuel.

**Action requise :** P2 — Comparer item-par-item avec `Q7_ICE_physical_items.md`. Mettre a jour `maritime_tolerance.py` si des items ont ete revises.

**References :**
- Stuster, J. (2010). Behavioral issues associated with long-duration space expeditions: Review and analysis of astronaut journals. *NASA/TM-2010-216130*.
- MCA (Maritime Coastguard Agency). STCW 2010 Manila Amendments — Standards of Training, Certification and Watchkeeping.

---

### Fiche instrument 6 — MMFS (`mobility_profile.py`)

**Instrument actuel :** Maritime Mobility & Flexibility Scale (MMFS). 12 items Likert 1-5. 4 traits : mobility_flexibility, embarkation_tolerance, uncertainty_tolerance, contract_flexibility.

**Statut droits :** Custom — propriete de Radiant Analytics. Ancre sur la litterature Work Flexibility (Valcour & Ladge, 2008) et les contraintes du yachting (MYBA, ISWAN).

**Statut scientifique :** Instrument ALPHA. Aucune etude de validation externe disponible.

**Coherence avec Q7_MMFS_mobility_items.md :** A verifier.

**Action requise :** P2 — Comparer avec `Q7_MMFS_mobility_items.md`. Mettre a jour si necessaire.

**References :**
- Valcour, M., & Ladge, J.J. (2008). Family and career path characteristics as predictors of women's objective and subjective career success. *Journal of Vocational Behavior*, 73(2), 300–309.

---

## 2. Ce qui n'existe pas encore dans le seed (a creer en P2)

### Tableau de creation

| Fichier seed a creer | Instrument cible | Q | Instrument source | Priorite |
|---|---|---|---|---|
| `seed_hexaco60.py` | IPIP-HEXACO-60 (60 items) | Q1 | `Q1_HEXACO_items.md` | P1 — remplace `ipip120.py` |
| `seed_sdt6.py` | SDT-6 custom maritime (18 items) | Q3 | `Q3_SDT_items.md` | P1 — remplace `rmaws.py` |
| `seed_gca_series.py` | GCA Series (sequences numeriques) | Q2 | `Q2_GCA_series.md` | P2 |
| `seed_gca_matrices.py` | GCA Matrices visuospatiales | Q2 | `Q2_GCA_matrices_specs.md` | P2 — a merger avec `hmr24.py` ou remplacer |
| `seed_gca_rotation.py` | GCA Rotation mentale | Q2 | `Q2_GCA_rotation_specs.md` | P2 |
| `seed_management_pref.py` | Preferences de management (LMX) | Q6 | `Q6_management_pref_items.md` | P2 |

### Notes de migration P1 (prioritaire)

**`seed_hexaco60.py` :** La migration de `ipip120.py` → `seed_hexaco60.py` necessite une mise a jour du `psychometric_snapshot` dans `backend/app/seed/environment/snapshots.py`. Le champ `big_five` reste (pour compatibilite backward), mais il faudra ajouter `honesty_humility` comme 6eme score. Le `trait_extractor.py` du moteur devra etre mis a jour pour lire ce nouveau champ.

**`seed_sdt6.py` :** La migration de `rmaws.py` → `seed_sdt6.py` ne change pas le schema de snapshot (`motivation` block avec 6 dimensions SDT), uniquement les items passes au candidat. Le mapping SDT n'est pas affecte : `extrinsic → extrinsic_social + extrinsic_material`, `identified + intrinsic → autonomous_regulation`, etc.

---

## 3. Impact engine pe_fit — Passage Big Five → HEXACO-60

### 3.1 Q4 (PT Fit) — `pt_fit/f_team.py`

**Formule Bell (2007) actuelle :**
```
PT_Fit = 0.30 * min(A) + 0.30 * mean(C) + 0.28 * mean(ES) - 0.12 * std(C)
```

**Ajustements requis avec HEXACO-60 :**

| Variable Bell | Source Big Five | Source HEXACO-60 | Ajustement |
|---|---|---|---|
| A (Agreeableness) | `psychometric_snapshot.big_five.A` | `psychometric_snapshot.big_five.A` (HEXACO-A) | Direct — r convergent ≈ 0.75. Vigilance : A HEXACO ne contient plus la variance sincerite/equite (deplacee dans H). |
| C (Conscientiousness) | `psychometric_snapshot.big_five.C` | `psychometric_snapshot.big_five.C` (HEXACO-C) | Direct — r convergent ≈ 0.85. Aucun ajustement. |
| ES (Emotional Stability) | `100 - psychometric_snapshot.big_five.N` | `100 - psychometric_snapshot.big_five.E` (HEXACO-Emotionality) | Approximation — r(ES_Big5, 100-E_HEXACO) ≈ 0.59. Perte de variance acceptable en Temps 1. |

**Ajout recommande :** Detection H-bas comme signal "jerk_potential" non-compensatoire dans `f_team.py` :
```python
# Apres passage HEXACO — ajouter dans f_team.py
H_JERK_THRESHOLD = 25  # score 0-100, centile ~10 — a calibrer
if any(p.honesty_humility < H_JERK_THRESHOLD for p in crew_profiles):
    flags.append("jerk_potential_h_low")
    # Ce flag est non-compensatoire : il ne reduit pas PT_Fit mais active une alerte
```

**Fichier a modifier :** `backend/app/engine/pe_fit/pt_fit/f_team.py`

### 3.2 Q5 (PO Fit) — `po_fit/f_values.py`

**Situation actuelle :** Q5 calcule la congruence valeurs candidat/entreprise sur 4 dimensions (honesty, achievement, fairness, solidarity) depuis le CES maritime (`ces_values.py`).

**Impact HEXACO :** La dimension H (Honesty-Humility) contient les facettes Sincerity et Fairness qui chevauchent les valeurs `honesty` et `fairness` du CES. Ce chevauchement cree une redondance potentielle (VIF a surveiller lors des retrains OLS). Deux options :

Option A (Temps 1 — simple) : Conserver Q5 independant de Q1. Accepter la redondance partielle. Surveiller VIF < 5 lors du premier retrain OLS.

Option B (Temps 2 — optimal) : Integrer H comme predicteur latent dans le calcul de congruence valeurs :
```python
# congruence_honesty = 0.6 * H_score/100 + 0.4 * CES_honesty_score/100
```
Cette formulation reduit la charge cognitive (moins d'items Q5 necessaires) et ameliore la validite de construct (H mesure un trait stable, CES mesure une valeur declaree).

**Recommandation head-of-science :** Option A pour Temps 1. Option B a experimenter apres N ≥ 150 profils avec donnees de retour.

**Fichier a modifier (Option B uniquement) :** `backend/app/engine/pe_fit/po_fit/f_values.py`

### 3.3 Q6 (PS Fit) — `ps_fit/f_lmx.py`

**Situation actuelle :** Q6 calcule la distance euclidienne entre le vecteur capitaine (autonomy_given, feedback_style, structure_imposed) et les preferences de leadership du candidat (Q6_management_pref_items.md).

**Impact HEXACO :** H peut etre un predicteur additionnel de la preference pour un leadership ethique/integre. Un candidat fort en H (sincerite, equite) peut preferer un capitaine avec un style de management transparent. Cette hypothese n'a pas de support empirique direct dans la litterature LMX — a traiter comme piste de recherche P3.

**Recommandation head-of-science :** Aucune modification de `f_lmx.py` en Temps 1. Documenter H comme candidat-variable pour les analyses exploratoires Temps 2.

### 3.4 `trait_extractor.py` — Mise a jour schema snapshot

Le `trait_extractor.py` extrait les traits du `psychometric_snapshot` pour les injecter dans les moteurs. Avec l'ajout de H comme 7eme dimension :

**Modification requise :**
```python
# Ajout dans trait_extractor.py
def extract_honesty_humility(snapshot: dict) -> float:
    """Extrait H (Honesty-Humility) du snapshot HEXACO.
    Retourne None si le snapshot est Big Five uniquement (legacy).
    """
    return snapshot.get("honesty_humility")  # None si snapshot pre-HEXACO
```

La valeur `None` doit etre geree gracieusement dans `f_team.py` et `po_fit/f_values.py` : si `H is None`, ne pas appliquer les ajustements HEXACO (retrocompatibilite avec snapshots Big Five existants).

**Fichier a modifier :** `backend/app/engine/pe_fit/trait_extractor.py`

---

## 4. Plan de migration — Sequence recommandee

### Phase P1 (immediate — avant premiere campagne reelle)

1. Creer `backend/app/seed/tests/questions/etalons/seed_hexaco60.py` depuis `Q1_HEXACO_items.md`
2. Creer `backend/app/seed/tests/questions/seed_sdt6.py` depuis `Q3_SDT_items.md`
3. Mettre a jour `backend/app/seed/environment/snapshots.py` : ajouter le champ `honesty_humility` dans les snapshots de seed
4. Mettre a jour `backend/app/engine/pe_fit/trait_extractor.py` : ajouter `extract_honesty_humility()`
5. Mettre a jour `backend/app/engine/pe_fit/pt_fit/f_team.py` : ajouter flag `jerk_potential_h_low` (non-compensatoire)
6. Tests : verifier que les 863 tests backend passent apres les modifications

### Phase P2 (apres N = 50 profils candidats)

1. Creer `seed_gca_series.py`, `seed_gca_matrices.py`, `seed_gca_rotation.py`
2. Aligner `ces_values.py` sur `Q5_values_items.md`
3. Aligner `maritime_tolerance.py` sur `Q7_ICE_physical_items.md`
4. Aligner `mobility_profile.py` sur `Q7_MMFS_mobility_items.md`
5. Creer `seed_management_pref.py` depuis `Q6_management_pref_items.md`

### Phase P3 (apres premier retrain OLS, N ≥ 150)

1. Evaluer VIF entre Q3 (SDT-6) et Q5 (valeurs) — si > 5, implementer Option B (H dans po_fit)
2. Evaluer contribution de H dans la prediction de performance (y_actual) — si significatif (p < 0.05), formaliser le role de H dans le modele

---

## 5. Tableau des statuts de validation — Vue consolidee

| Q | Instrument | N items | Alpha min attendu | Statut droits | Statut validation | Etalon population |
|---|---|---|---|---|---|---|
| Q1 | IPIP-HEXACO-60 | 60 | 0.71 (A) | Domaine public | Valide (multiples etudes, N > 10 000) | Population generale + travail |
| Q2 | HMR-24 (matrices) | 24 | N/A (exactitude) | Custom | ALPHA — non valide | Aucun |
| Q2 | GCA Series (a creer) | ~20 | N/A (exactitude) | Custom | En specification | Aucun |
| Q2 | GCA Rotation (a creer) | ~16 | N/A (exactitude) | Custom | En specification | Aucun |
| Q3 | SDT-6 custom maritime | 18 | 0.70 (cible) | Custom | ALPHA — non valide | Aucun |
| Q5 | CES maritime custom | 16 | 0.70 (cible) | Custom | ALPHA — non valide | Aucun |
| Q6 | Management Pref (a creer) | ~15 | 0.70 (cible) | Custom | En specification | Aucun |
| Q7 | METS (physique) | 15 | 0.70 (cible) | Custom | ALPHA — non valide | Aucun |
| Q7 | MMFS (mobilite) | 12 | 0.70 (cible) | Custom | ALPHA — non valide | Aucun |

**Seul Q1 (IPIP-HEXACO-60) dispose d'une validation psychometrique externe robuste.** Tous les instruments custom sont en statut ALPHA et ne doivent pas etre utilises comme critere de decision unique en contexte de recrutement jusqu'a leur validation empirique sur donnees reelles.

---

## References

- Ashton, M.C., Lee, K., & Goldberg, L.R. (2007). The IPIP-HEXACO scales: An alternative, public-domain measure of the personality constructs in the HEXACO model. *Personality and Individual Differences*, 42(8), 1515–1526.
- Bell, S.T. (2007). Deep-level composition variables as predictors of team performance: A meta-analysis. *Journal of Applied Psychology*, 92(3), 595–615.
- Carroll, J.B. (1993). *Human cognitive abilities: A survey of factor-analytic studies*. Cambridge University Press.
- Deci, E.L., & Ryan, R.M. (2000). The "what" and "why" of goal pursuits. *Psychological Inquiry*, 11(4), 227–268.
- Gagne, M., et al. (2010). The Motivation at Work Scale. *Educational and Psychological Measurement*, 70(4), 628–646.
- Goldberg, L.R., et al. (2006). The International Personality Item Pool and the future of public-domain personality measures. *Journal of Research in Personality*, 40, 84–96.
- Graen, G.B., & Uhl-Bien, M. (1995). Relationship-based approach to leadership: Development of leader-member exchange (LMX) theory. *The Leadership Quarterly*, 6(2), 219–247.
- Lee, K., Ashton, M.C., & de Vries, R.E. (2005). Predicting workplace delinquency and integrity with the HEXACO and Five-Factor Models. *Human Performance*, 18(2), 179–197.
- Maples, J.L., Guan, L., Carter, N.T., & Miller, J.D. (2014). A test of the IPIP as a measure of the FFM via IRT. *Psychological Assessment*, 26(4), 1255–1264.
- Ravlin, E.C., & Meglino, B.M. (1987). Effect of values on perception and decision making. *Journal of Applied Psychology*, 72(4), 666–673.
- Stuster, J. (2010). Behavioral issues associated with long-duration space expeditions. *NASA/TM-2010-216130*.
- Valcour, M., & Ladge, J.J. (2008). Family and career path characteristics as predictors of career success. *Journal of Vocational Behavior*, 73(2), 300–309.
