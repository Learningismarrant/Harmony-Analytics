# Roadmap — Radiant Analytics

> État d'avancement à jour. À mettre à jour après chaque milestone significatif.
>
> Dernière mise à jour : Mars 2026

---

## État actuel (snapshot Mars 2026)

### Tests
| Suite | Nb tests | Statut |
|-------|----------|--------|
| Backend (pytest) | 863 | ✅ 0 failures |
| Web (Jest + RTL) | 126 | ✅ 0 failures |
| Mobile (jest-expo) | 121 | ✅ 0 failures (dont tests T-IRT — **à supprimer**) |
| **Total** | **1110** | **✅** |

> ⚠️ Les 121 tests mobile incluent des tests liés au flow T-IRT (ForcedChoiceQuestion, TirtResultDetail, useLastResultStore) qui seront supprimés lors du P2.

### Engine P-E Fit — 7 questions
| Q | Question | Instrument alpha v1 | Score opérationnel |
|---|----------|--------------------|--------------------|
| Q1 | Personality profile | IPIP-50 (CTT) — à implémenter | ⚠️ Seedé manuellement (15 profils Big Five) |
| Q2 | Abilities for the job | Batterie GCA chronométrée — à implémenter | ✅ D-A Fit actif |
| Q3 | Motivation / N-S Fit | MWMS (CTT) — à implémenter | ⚠️ Indicatif (priors Temps 0) |
| Q4 | Team fit | Dérivé IPIP-50 — pas d'instrument | ⚠️ 11/15 candidats assignés |
| Q5 | Values / culture | CES 16 items (CTT) — à implémenter | ❌ Non seedé |
| Q6 | Supervisor fit | LMX-7 (CTT) — à implémenter | ⚠️ Score dégradé (dérivation Big Five) |
| Q7 | Physical / mobility | Échelle ICE perception (CTT) — à implémenter | ❌ Non seedé |

**Pipeline complet :** non — Q5 et Q7 bloquées. Instruments CTT à construire pour tous.

### Bugs backend bloquants
| Bug | Fichier | Impact |
|-----|---------|--------|
| Import mort `engine.recruitment.DNRE` | `recruitment/service.py:349` | `GET /impact` crash |
| `get_all_for_owner()` vs `get_all_for_employer()` | `vessel/router.py` | Toutes routes vessel crash |
| `SurveyTriggerIn` sans `yacht_id` | `survey/schemas.py` | `POST /surveys/trigger` crash 500 |

---

## Alpha v1 — Définition du livrable

> **Done = les 3 périmètres ci-dessous complétés et testés end-to-end.**

---

### Périmètre 1 — Instruments & Étalonnage (prérequis à tout)

> Objectif : avoir des instruments CTT validés (α ≥ 0.80) avant de déployer sur vrais candidats.

- [ ] Finaliser les items de chaque instrument avec head-of-science :
  - Q1 : IPIP-50 (50 items, 5 dimensions, Likert 5)
  - Q2 : Matrices abstraites (20i) + séries numériques (15i) + rotation spatiale (10i) — avec timer
  - Q3 : MWMS (18 items, Likert 7)
  - Q5 : CES adapté (16 items, 4 dimensions, Likert 6)
  - Q6 : LMX-7 (7 items, Likert 7)
  - Q7 : Échelle perception ICE (12 items) + MMFS mobilité (8 items)
- [ ] Pilote item wording (n = 10-15, Google Forms, validation clarté et compréhension)
- [ ] Backend : modèle `CalibratorUser` isolé des données commerciales
- [ ] App calibrateur (rôle `calibrator`) — passation tous instruments + stockage DB
- [ ] Collecte étalonnage : n = 200-300 par instrument (écoles maritimes, réseau)
- [ ] Analyse R (`psych`, `lavaan`) : α Cronbach, ACP, indices discrimination
- [ ] Intégrer scores CTT dans pe_fit engine (Q1 IPIP-50 → trait_extractor, Q2 GCA → demands_abilities, Q3 MWMS, Q5 CES, Q6 LMX-7, Q7 ICE)

---

### Périmètre 2 — Boucle candidat complète (app mobile)

> Objectif : un candidat peut passer tous les tests, construire son profil, rejoindre un bateau, postuler à une campagne et voir ses formations recommandées.

**Suppression T-IRT :**
- [ ] Supprimer `ForcedChoiceQuestion`, `TirtResultDetail`, `useLastResultStore`
- [ ] Supprimer les tests Jest associés
- [ ] Supprimer le backend CUTTY SARK survey type et ses seeds

**Tests CTT (nouveaux écrans) :**
- [ ] Écran passation Likert (Q1, Q3, Q5, Q6, Q7) — composant générique réutilisable
- [ ] Écran passation GCA chronométré (Q2) — matrices + séries + rotation avec timer visible
- [ ] Résultats Q1 : profil Big Five CTT (barres normalisées)
- [ ] Résultats Q2 : score GCA descriptif (sans percentile avant étalonnage)
- [ ] Résultats Q3 : profil motivationnel descriptif (6 régulations SDT)

**Profil candidat :**
- [ ] Profil persistant : photo, expérience (postes + durée), certifications (STCW, ENG1, etc.)
- [ ] Modification du profil depuis l'app

**Invitation & onboarding :**
- [ ] Rejoindre un bateau via QR code ou lien `/join/vessel/{token}`
- [ ] Postuler à une campagne via QR code ou lien `/join/campaign/{token}`
- [ ] Backend : génération de tokens d'invitation (employeur) + assignation à la réception

**Training :**
- [ ] Section "Formations recommandées" basée sur règles statiques v1 :
  - Poste visé + niveau d'expérience + score Q2 (GCA) + profil Q1 (Big Five)
- [ ] Fiches formation : titre, description, durée, ressources externes
- [ ] Marquage "complété" par le candidat

**Rôle capitaine (app mobile) :**
- [ ] Vue unique bateau assigné : composition équipage + scores TEAM_HEALTH + alertes RPS
- [ ] Fiches candidats en cours de recrutement sur son yacht
- [ ] Scan QR pour accueillir un nouveau membre d'équipage

---

### Périmètre 3 — Dashboard employeur + API analytics

> Objectif : l'employeur voit les scores de fit réels pour son équipage et ses campagnes, et peut prendre des décisions de recrutement et de management fondées sur les données.

**Bugs backend à corriger en priorité :**
- [ ] Fix import mort DNRE → pe_fit dans `recruitment/service.py`
- [ ] Aligner `vessel/router.py` sur `get_all_for_employer()` / `create(employer=...)`
- [ ] Ajouter `yacht_id: int` à `SurveyTriggerIn`
- [ ] Vérifier 0 régression sur 863 tests

**Seeding complet :**
- [ ] Seeds Q5 (CES) pour 15 candidats + `org_values` pour 4 yachts
- [ ] Seeds Q7 (ICE perception + MMFS) pour 15 candidats + `maritime_conditions` / `mobility_requirements` yachts
- [ ] Assigner les 4 candidats orphelins (sam_adler, tom_bradley, aisha_nkosi, carlos_mendez)

**API analytics (module `analytics/`) :**
- [ ] `GET /recruitment/campaigns/{id}/matching?detail=full` → `pe_fit_breakdown` (7 scores)
- [ ] `RecruitmentImpactOut` → `PEFitResult.to_impact_report()`
- [ ] `GET /analytics/vessels/{id}/management` (TEAM_HEALTH)
- [ ] `GET /analytics/vessels/{id}/rps` (RISK_LEVEL)
- [ ] `GET /analytics/vessels/{id}/team-fit`
- [ ] `GET /analytics/crew/{id}/training` (GAP_ANALYSIS)
- [ ] `GET /analytics/crew/{id}/talent` (READINESS)
- [ ] `GET /crew/me/fit-profile` (vue candidat — scores agrégés uniquement)
- [ ] `POST /vessels/{id}/invite` → génération token QR/lien (employeur)
- [ ] Migration Alembic : `fit_score_cache` sur `CampaignCandidate`
- [ ] Syncer `@harmony/types` pour tous les nouveaux schémas
- [ ] Security review : ownership checks, rate limits

**Frontend web :**
- [ ] Panel recrutement : HIRE / CONDITIONAL / DISQUALIFY avec `pe_fit_breakdown` visible
- [ ] Sociogramme modulable par dimension de fit (Q2→Q6 sélectionnable)
- [ ] Sociogramme sur vraies données dyadiques (endpoint `/crew/{yacht_id}/sociogram`)
- [ ] `TeamHealthPanel` : score + alertes + recommandations actionables
- [ ] `RPSPanel` : niveau risque psychosocial + facteurs déclencheurs
- [ ] `ReadinessPanel` : maturité équipage pour postes supérieurs
- [ ] `GapAnalysisPanel` : lacunes prioritaires par membre
- [ ] Génération QR codes / liens d'invitation depuis le dashboard

---

## Temps 2 — Après alpha stable

### Calibration & instruments avancés
- Validation fidélité et validité de contenu post-collecte (n ≥ 200)
- Migration Q3 : retirer le statut "indicatif" après calibration SDT sur données réelles
- Migration Q6 : remplacer dérivation Big Five → LMX preferences par items LP-3 directs
- Migration Q5 : CES (4 dims) → OCP/Q-Sort (54 items, 8 dimensions)

### Sociogramme complet
- Backend : endpoint `GET /crew/{yacht_id}/sociogram` → `SociogramOut` (scores dyadiques)
- Calcul dyadique de compatibilité pour toutes les paires de l'équipage

### Training — Contenus partenaires
- Partenariats avec Yachting Concept, Yacht Club de Monaco, INSEIT, Bluewater
- Modules de contenu certifiant brandés au nom des partenaires
- Déclenchement dynamique post-surveys (vie à bord)

### Migration IRT
- Une fois n ≥ 500 par instrument → migration vers modèles IRT (2PL ou 3PL)
- Estimation des paramètres d'item, scoring adaptatif envisageable à T3

---

## Temps 3 — Vision long terme

- **Validation empirique** : collecte de données réelles (turnover, performance, satisfaction) pour valider les pondérations du moteur
- **Retrain OLS** : calibration des poids PJ/PO/PG/PS sur données empiriques (actuellement : Kristof-Brown 2005)
- **Fit dynamique** : score de fit qui évolue dans le temps (re-test périodique, feedback post-embarquement)
- **IRT adaptatif** : scoring adaptatif (CAT) sur Q1 et Q2 une fois les banques d'items étalonnées
- **Multi-secteur** : adapter le moteur à d'autres environnements ICE (santé, construction offshore, exploration)
- **CI/CD** : pipeline de déploiement automatisé
- **GDPR / compliance** : audit conformité données psychométriques

---

## Dépendances critiques

```
Étalonnage instruments (P1)
    ↓
Suppression T-IRT + implémentation CTT (P2 + engine)
    ↓
Boucle candidat complète (P2 mobile)
    ↓
Fix bugs + seeding Q5/Q7 + API analytics (P3 backend)
    ↓
Dashboard employeur + app capitaine (P3 frontend)
    ↓
Alpha livré
    ↓
Temps 2 (calibration + contenus + sociogramme)
```

---

## Décisions prises (non-révisables sans discussion)

| Décision | Raison | Date |
|----------|--------|------|
| CTT en alpha (abandonne T-IRT) | IRT nécessite n ≥ 500 étalonnés — impraticable avant commercialisation | Mars 2026 |
| CUTTY SARK T-IRT caduc | Remplacé par IPIP-50 (Q1) + batterie GCA (Q2) en CTT | Mars 2026 |
| Q4 sans instrument propre | Entièrement dérivé des IPIP-50 agrégés de l'équipage (Bell 2007) | Mars 2026 |
| Q7 = self-efficacy perçue (Bandura) | Capacité physiologique réelle validée par ENG1 — Q7 mesure l'adéquation perçue | Mars 2026 |
| 1 app mobile, 3 rôles (candidate / captain / calibrator) | Maintenance simplifiée, branding unifié, déploiement unique | Mars 2026 |
| CalibratorUser = modèle isolé | Données d'étalonnage ne doivent pas contaminer les données commerciales | Mars 2026 |
| Training v1 = règles statiques | Partenariats contenus (Temps 2) nécessitent validations externes | Mars 2026 |
| Q3 profils SDT = indicatif Temps 0 | Priors non validés empiriquement | Mars 2026 |
| Q7 non-compensatoire | ICE context — incompatibilité physique = bloquant | Mars 2026 |
| Q1 = input uniquement (hors global_score) | Big Five ne se somme pas avec un score de fit | Mars 2026 |
| Renommage Harmony → Radiant Analytics | Rebranding Fondation Technologies | Antérieur |
| engine/recruitment → engine/pe_fit | DNRE/MLPSM supprimés, remplacement par cadre P-E Fit | Antérieur |
