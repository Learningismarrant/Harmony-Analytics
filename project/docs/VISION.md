# Vision Produit — Radiant Analytics

> **Source unique de vérité produit.** Tout le code, tout l'engine, toutes les décisions UI doivent pouvoir être justifiés par ce document.
>
> Fondation Technologies — Mars 2026

---

## Ce qu'on construit

**Radiant Analytics** est un moteur de décision RH pour l'industrie maritime de luxe (superyachts). Il aide les employeurs à prendre des décisions d'embauche et de management d'équipage fondées sur des données psychométriques objectives.

Le contexte superyacht est un **environnement ICE** (Isolated, Confined, Extreme) : équipes de 4 à 30 personnes, cohabitation permanente sur plusieurs mois, hiérarchie forte, éloignement géographique. Dans ce contexte, une mauvaise décision d'embauche est beaucoup plus coûteuse qu'en entreprise classique — elle ne peut pas être "absorbée" par la distance physique entre collègues.

---

## Les 7 questions — North Star

Chaque feature, chaque endpoint, chaque composant UI sert à répondre à une ou plusieurs de ces 7 questions :

| # | Question (vue employeur) | Construct P-E Fit | Instrument alpha v1 | Statut |
|---|---|---|---|---|
| **Q1** | What is his personality profile? | Trait measure — *input universel* | **IPIP-50** (50 items Likert 5, 10 par dimension, libre de droit) | Actif CTT |
| **Q2** | Does he have the abilities for this job? | PJ D-A Fit | **Batterie GCA chronométrée** : matrices abstraites (20i/12min) + séries numériques (15i/8min) + rotation spatiale (10i/6min) | Actif CTT |
| **Q3** | Does this job match his motivations? | PJ N-S Fit | **MWMS** (18 items Likert 7, 6 régulations SDT) + JDR vessel_params | Actif *(Q3 indicatif — calibration Temps 2)* |
| **Q4** | Will he integrate into this crew? | PG/PT Fit | **Dérivé** — agrégation IPIP-50 de l'équipage. Bell (2007) : 0.30·min(A) + 0.30·μ(C) + 0.28·μ(ES) - 0.12·σ(C) | Actif — pas d'instrument séparé |
| **Q5** | Does he share our values and culture? | PO Fit | **CES adapté** — 16 items candidat (app) + profil organisationnel employeur (dashboard) | Actif simplifié *(OCP/Q-Sort Temps 2)* |
| **Q6** | Is he compatible with the captain's style? | PS Fit | **LMX-7** côté candidat (app) + captain_vector côté capitaine (dashboard) | Actif |
| **Q7** | Can he handle life aboard? | Physical + Mobility Fit *(ICE-spécifique)* | **Échelle perception ICE** (12 items auto-déclaration) + **MMFS** mobilité (8 items) | Actif — maritime uniquement |

**Fondement scientifique :** Kristof-Brown, Zimmerman & Johnson (2005) — méta-analyse P-E Fit, 172 études, n > 66 000. Voir [science/pe_fit_reference.md](../science/pe_fit_reference.md).

---

## Règles d'interprétation des 7 questions

Ces règles sont non-négociables. Tout agent ou développeur doit les respecter.

**Q1 est un input, pas un score de fit.** Le profil Big Five (IPIP-50) alimente Q2 à Q6 — il n'entre jamais directement dans le `global_score`.

**Q2 + Q3 = PJ Fit, deux constructs distincts.** Cable & DeRue (2002) établissent que D-A Fit et N-S Fit sont empiriquement distincts (r ~ 0.53). Les combiner en un seul score serait une perte d'information.

**Q4 n'a pas d'instrument propre.** Il est entièrement calculé depuis les scores IPIP-50 agrégés de l'équipage déjà assigné au yacht. Aucun survey spécifique pour Q4.

**Q4, Q5, Q6 mesurent trois niveaux différents :**
- Q4 = compatibilité avec l'*équipage* (dynamique collective)
- Q5 = congruence avec les *valeurs de l'armateur/organisation*
- Q6 = compatibilité avec le *style du capitaine* (relation dyadique)
Ne jamais les conflater.

**Q7 est non-compensatoire.** Un score élevé sur Q1-Q6 ne compense pas une incompatibilité physique ou de mobilité. C'est une barrière, pas un facteur. Q7 mesure la **self-efficacy perçue** (Bandura) en contexte ICE — pas la capacité physiologique réelle, qui est validée séparément par le certificat ENG1.

**Q3 est indicatif jusqu'au Temps 2.** Les profils idéaux SDT (`MOTIVATION_PROFILES`) sont des priors SME non validés empiriquement. Ne pas les utiliser comme base décisionnelle critique avant calibration.

---

## Approche psychométrique — Théorie Classique des Tests (CTT)

Tous les instruments sont en **CTT** (somme des items, α de Cronbach, normalisation sur population collectée). L'approche IRT (T-IRT, réponses forcées) a été abandonnée en alpha : elle nécessite un étalonnage préalable sur n ≥ 500 sujets, impraticable avant la commercialisation.

**Protocole d'étalonnage :**
1. Pilote wording (n = 10-15, Google Forms, validation item clarity)
2. Collecte via app calibrateur interne (n = 200-300 par instrument)
3. Analyse R (`psych`, `lavaan`) : α ≥ 0.80, ACP, indices de discrimination
4. Migration vers IRT (Temps 2-3) une fois les normes stables

---

## Use cases — Ce que l'employeur peut faire

| Use Case | Questions mobilisées | Output |
|----------|---------------------|--------|
| **HIRE / CONDITIONAL / DISQUALIFY** | Q1 → Q7 (pipeline complet) | Décision recrutement + rapport détaillé |
| **TEAM_HEALTH** | Q4 + Q6 (entrée = Q1 de l'équipage) | Score santé équipe + alertes + recommandations |
| **GAP_ANALYSIS / Formation** | Q2 + Q3 | Lacunes prioritaires + plan de développement |
| **READINESS** | Q1 + Q2 + Q4 | Maturité pour un niveau de poste supérieur |
| **RISK_LEVEL psychosocial** | Q3 + Q4 + Q6 | Niveau de risque RPS + facteurs déclencheurs |

---

## Utilisateurs

**Employeur (web dashboard)** : armateur, gestionnaire de flotte. Prend les décisions de recrutement et management. Voit les scores de fit *contextuels* (relatifs à son yacht/équipage spécifique). Génère les QR codes / liens d'invitation pour les candidats et l'équipage.

**Candidat (app mobile — rôle `candidate`)** : marin cherchant un poste. Passe les tests psychométriques. Voit son profil descriptif (Q1, Q2 descriptif, Q3 descriptif) — pas les scores de fit relatifs à un employeur. Peut rejoindre un bateau et postuler à une campagne via QR code ou lien.

**Capitaine (app mobile — rôle `captain`)** : accès limité à son propre yacht. Voit les alertes TEAM_HEALTH et RPS, les candidats en cours, peut accueillir un nouveau membre (QR scan). Actions similaires à l'employeur mais périmètre restreint à son équipage.

**Calibrateur (app mobile — rôle `calibrator`)** : utilisateur interne Radiant Analytics. Passe les instruments pour construire les étalons normatifs. **Modèle utilisateur isolé des données commerciales** — les réponses calibrateur ne contaminent pas les données candidats.

---

## Module training (alpha v1)

Les formations sont déclenchées par des règles prédéfinies statiques basées sur : le poste visé, l'expérience déclarée, les scores Q2 (GCA) et Q1 (Big Five), et les scores Q3 (motivation). En vie à bord, les surveys périodiques peuvent déclencher des modules additionnels (Temps 2+).

Le contenu en v1 est intégré (fiches texte + ressources). À Temps 2-3, des partenariats avec des organismes de formation maritime (Yachting Concept, Yacht Club de Monaco, INSEIT, Bluewater) permettront de brancher du contenu certifiant.

---

## Ce qu'on ne construit pas (garde-fous)

- Pas de scoring "global candidat" sans contexte yacht — un candidat n'a pas de score absolu, uniquement des scores de fit relatifs à un poste/équipage
- Pas de décision automatique — l'engine produit des recommandations, l'humain décide
- Pas de profiling clinique — on mesure des traits professionnels, pas des pathologies
- Pas de ranking inter-candidats sans même poste/yacht de référence
- Pas d'IRT en alpha — CTT uniquement jusqu'à n ≥ 200-300 par instrument étalonnés

---

## Références

- [science/pe_fit_reference.md](../science/pe_fit_reference.md) — Fondement théorique complet
- [science/pe_fit_technical.md](../science/pe_fit_technical.md) — Formules et spécifications techniques
- [ROADMAP.md](ROADMAP.md) — État d'avancement et prochaines étapes
