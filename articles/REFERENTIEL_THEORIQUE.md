# Référentiel Théorique — Harmony P-E Fit Engine

**Version :** 1.0 — Mars 2026
**Domaine :** Psychologie industrielle et organisationnelle (I/O Psychology), psychométrie appliquée, talent management
**Périmètre :** Base théorique du moteur de matching Harmony — recrutement, management, formation, gestion des talents dans l'industrie du yachting de luxe (superyachts)

---

## Préambule

Ce document constitue le référentiel scientifique permanent du projet Harmony. Il documente les fondements théoriques de chaque composante du moteur P-E Fit, ancre chaque choix de modélisation dans la littérature empirique, et formalise les limites connues que chaque développement futur devra respecter.

L'industrie du superyacht présente des caractéristiques qui la rapprochent des environnements dits "confinés et isolés" (ICE — Isolated, Confined, and Extreme environments) étudiés en psychologie du travail : équipes de taille réduite (4 à 30 personnes), cohabitation permanente sur plusieurs mois, éloignement géographique, hiérarchie forte, forte charge émotionnelle en haute saison. Ces caractéristiques justifient à la fois l'importance accordée aux variables de personnalité et l'existence de barrières de sécurité non-compensatoires dans le modèle.

---

## 1. Cadre général : Person-Environment Fit

### 1.1 Définition fondatrice

Le concept de Person-Environment Fit (P-E Fit) désigne le degré de compatibilité ou de congruence entre une personne et son environnement de travail. Sa formalisation moderne est attribuée à Kristof (1996), qui en donne la définition de référence : "la compatibilité entre les individus et les organisations, qui se produit lorsque (a) au moins l'une des deux entités fournit ce dont l'autre a besoin, ou (b) elles partagent des caractéristiques fondamentales similaires, ou (c) les deux."

Cette définition bifurquée est fondamentale : elle distingue deux logiques de fit qui ne sont pas interchangeables.

- Le **fit par complémentarité** (needs-supplies, demands-abilities) : l'environnement fournit ce dont la personne a besoin (salaire, autonomie, challenge), ou la personne possède ce que l'environnement requiert (compétences, traits, valeurs).
- Le **fit par similarité** (supplementary fit) : la personne et l'environnement partagent des caractéristiques fondamentales comparables.

La méta-analyse de Kristof-Brown, Zimmerman & Johnson (2005), portant sur 172 études indépendantes et plus de 66 000 sujets, est la référence quantitative principale. Elle établit que les quatre dimensions du P-E Fit — P-J, P-O, P-T et P-S — prédisent de façon différentielle et complémentaire un ensemble d'outcomes (performance, satisfaction, turnover, wellbeing). Les corrélations avec les outcomes varient selon la dimension (ρ = 0.10 à 0.56 selon l'outcome considéré), ce qui valide l'architecture à quatre moteurs d'Harmony.

### 1.2 Les quatre dimensions : définitions et distinctions

**P-J Fit (Person-Job Fit)** : congruence entre les caractéristiques de la personne (aptitudes, compétences, traits) et les exigences du poste (demands-abilities) ou entre les besoins de la personne et les ressources offertes par le poste (needs-supplies). C'est la dimension la plus étudiée. Harmony l'opérationnalise via le score PJ Fit (DNRE/scorer.py) : score SME pondéré GCA × 0.60 + Conscientiousness × 0.40, complété par la barrière de sécurité non-compensatoire.

**P-O Fit (Person-Organization Fit)** : congruence entre les valeurs, objectifs et caractéristiques de la personne et ceux de l'organisation (Chatman, 1989 ; Kristof, 1996). Dans le contexte yacht, l'"organisation" est le yacht lui-même dans ses caractéristiques opérationnelles (rapport ressources/demandes). Harmony l'opérationnalise via F_env (f_env.py) : ratio JD-R (Ressources / Demandes) du yacht modulé par la résilience individuelle.

**P-T Fit (Person-Team Fit)** : congruence entre les caractéristiques d'un individu et celles de son équipe. Inclut la dimension de composition (propriétés agrégées de l'équipe) et de compatibilité interpersonnelle. Harmony l'opérationnalise via F_team (f_team.py) : min(Agréabilité) × 0.40 − σ(Conscientiousness_normé) × 0.30 + μ(Stabilité Emotionnelle) × 0.30.

**P-S Fit (Person-Supervisor Fit)** : congruence entre les préférences de management de l'individu et le style de leadership de son superviseur direct. Harmony l'opérationnalise via F_lmx (f_lmx.py) : distance euclidienne pondérée dans l'espace (autonomie, feedback, structure) entre le vecteur capitaine et les préférences du candidat.

### 1.3 Fit subjectif vs objectif, fit perçu vs réel

La littérature distingue classiquement (Cable & DeRue, 2002) :

- **Fit objectif** : mesure indépendante des deux profils (personne et environnement) par un observateur externe ou des instruments psychométriques standardisés. C'est le mode de mesure qu'Harmony implémente : traits mesurés par tests psychométriques, profils de poste définis par SME, vecteur capitaine renseigné par l'employeur.
- **Fit subjectif** : perception de congruence telle que rapportée par l'individu lui-même ("Je me sens à ma place"). Mesuré typiquement par des questionnaires de fit perçu.
- **Fit perçu par l'organisation** : évaluation par le manager ou le recruteur.

La méta-analyse de Kristof-Brown et al. (2005) montre que le fit subjectif prédit mieux les outcomes attitudinaux (satisfaction, intention de quitter), tandis que le fit objectif prédit mieux la performance. Cette distinction justifie l'architecture à deux niveaux d'Harmony : le pipeline DNRE (objectif, performance) est distinct du module de rétention/bien-être à terme.

### 1.4 Outcomes associés à chaque dimension

D'après Kristof-Brown et al. (2005) et De Cooman & Vleugels (2022) :

| Dimension | Outcome principal | ρ moyen (meta-analyse) |
|---|---|---|
| P-J Fit | Performance task | 0.20 à 0.25 |
| P-J Fit | Satisfaction professionnelle | 0.44 |
| P-O Fit | Engagement organisationnel | 0.48 |
| P-O Fit | Turnover intention | −0.35 |
| P-O Fit | OCB (Comportements citoyens) | 0.27 |
| P-T Fit | Satisfaction d'équipe | 0.50 |
| P-T Fit | Coopération et cohésion | 0.30 à 0.45 |
| P-S Fit | Performance contextuelle | 0.20 à 0.30 |
| P-S Fit | Bien-être au travail | 0.35 |

Ces chiffres sont indicatifs et issus de populations généralistes. Les effets peuvent être amplifiés en environnements confinés où les frictions interpersonnelles ne peuvent être évitées par la distance physique.

### 1.5 Mécanismes causaux

Trois familles de mécanismes ont été proposées dans la littérature pour expliquer pourquoi le P-E Fit prédit les outcomes :

**Réduction de la dissonance** (Festinger, 1957 ; adapté par Edwards & Cable, 2009) : l'incongruence personne-environnement génère un état de tension cognitivo-affective qui consomme des ressources attentionnelles et motivationnelles, réduisant la performance et le bien-être.

**Trait Activation Theory** (Tett & Burnett, 2003) : les traits de personnalité se manifestent en comportements observables uniquement lorsque l'environnement fournit des "signaux d'activation" pertinents. Un capitaine autocratique (faible autonomy_given) activera différemment les traits de Conscientiousness et d'Openness d'un marin selon son profil. Ce mécanisme justifie la décomposition F_lmx en dimensions séparées (autonomie, feedback, structure) plutôt qu'un score global de style.

**Modèle JD-R** (Bakker & Demerouti, 2007) : l'adéquation entre les ressources disponibles (salaire, repos, conditions) et les demandes (intensité charter, pression managériale) détermine le niveau d'activation et le risque de burnout. Ce mécanisme est la base directe du module F_env/PO Fit.

---

## 2. Big Five — Base psychométrique

### 2.1 Modèle à cinq facteurs

Le modèle des Big Five (ou Five Factor Model, FFM) est le modèle de personnalité le plus largement validé en psychologie scientifique. Il émerge de la tradition lexicale (Allport & Odbert, 1936) et est cristallisé dans sa forme moderne par Costa & McCrae (1992) avec le NEO-PI. Les cinq facteurs sont :

- **Openness to Experience (O)** : curiosité intellectuelle, imagination, ouverture esthétique, flexibilité cognitive.
- **Conscientiousness (C)** : autodiscipline, fiabilité, organisation, sens du devoir, orientation vers les objectifs.
- **Extraversion (E)** : sociabilité, affirmation de soi, énergie, émotions positives.
- **Agreeableness (A)** : coopération, confiance envers autrui, empathie, altruisme.
- **Neuroticism (N)** / Emotional Stability (ES = 100 − N) : anxiété, instabilité émotionnelle, tendance à éprouver des émotions négatives.

Ces cinq facteurs sont relativement orthogonaux (corrélations interfacteurs modestes, généralement r < 0.30), relativement stables à l'âge adulte, et retrouvés dans des dizaines de cultures différentes. La fidélité des instruments de mesure est généralement satisfaisante : α de Cronbach ≥ 0.75 pour les facteurs, avec des variations selon les facettes.

### 2.2 Validité prédictive sur la performance individuelle

La méta-analyse fondatrice de Barrick & Mount (1991) — 117 études, N = 23 994 — est la référence canonique sur la relation Big Five / performance au travail. Résultats principaux (corrélations corrigées pour l'atténuation) :

- **Conscientiousness** : ρ = 0.31 — prédicteur universel, significatif pour tous les groupes de professions et tous les critères de performance (task performance, training proficiency). C'est le seul facteur du Big Five à présenter une validité généralisable.
- **Extraversion** : ρ = 0.18 en moyenne, mais prédicteur valide spécifiquement pour les postes impliquant du management (ρ = 0.18) et des interactions sociales (ρ = 0.15 à 0.23).
- **Openness** : prédicteur de la performance en formation (ρ = 0.27), mais faible pour la performance générale (ρ = 0.10).
- **Agreeableness** : ρ = 0.07 pour la performance individuelle, mais ρ plus élevé pour les postes de service client et les tâches coopératives.
- **Neuroticism (inverse)** : ρ = 0.13 pour la performance en général, mais prédicteur plus fort pour les postes sous pression ou en environnement stressant.

La méta-analyse de Schmidt & Hunter (1998) complète ce tableau en montrant que le meilleur prédicteur composite de la performance au travail est la combinaison GCA (General Cognitive Ability) + Conscientiousness, avec une validité incrémentale respective d'environ ρ = 0.51 (GCA seul) et ρ = 0.31 (C seul). La combinaison atteint ρ ≈ 0.60, la validité incrémentale de C sur GCA étant de Δρ ≈ 0.18. C'est cet état de la littérature qui fonde les poids SME par défaut de Harmony : GCA × 0.60 + Conscientiousness × 0.40, normalisés pour une somme à 1.0.

**Note de mise à jour** : Sackett et al. (2022) ont recalibré ces estimations en corrigeant le problème de range restriction, suggérant des validités légèrement supérieures pour GCA (ρ ≈ 0.55 à 0.65 selon les corrections appliquées). Les pondérations Harmony sont cohérentes avec ces révisions.

### 2.3 Critiques et limites : Trait Activation Theory

La critique la plus importante du modèle Big Five appliqué à la prédiction de performance est formulée par Tett & Burnett (2003) dans leur Trait Activation Theory (TAT). L'argument central : les traits de personnalité ne se "manifestent" comportementalement que lorsque la situation contient des stimuli pertinents (trait-relevant cues). Un trait fort sans activation situationnelle ne produit pas de comportement observable.

Implications pour Harmony :

1. Les poids SME (GCA 0.60, C 0.40) sont valides comme priors généraux, mais doivent être recalibrés par poste (Captain vs Deckhand) car les signaux d'activation diffèrent fondamentalement.
2. Le module P-S Fit / F_lmx implémente implicitement la TAT : c'est le style du capitaine (les signaux situationnels) qui active différemment les traits de leadership, d'autonomie et de conformité du marin.
3. La TAT justifie que les weights SME soient injectables depuis `JobWeightConfig` sans modification du code : chaque poste requiert un profil d'activation différent.

### 2.4 Niveau facette vs facteur

Maples et al. (2014) analysent la structure facettielle des Big Five et montrent que la validité prédictive est souvent portée par des facettes spécifiques plutôt que par le facteur global. Par exemple, au sein de Conscientiousness : la facette "fiabilité/reliability" prédit mieux la performance de maintenance que la facette "ordre/orderliness". Au sein d'Agreeableness : la facette "confiance" (trust) prédit mieux la cohésion d'équipe que la facette "modestie".

Pour Harmony, ceci est une direction de développement futur (Temps 2) : les instruments actuels (HEXACO ou Big Five adapté) mesurent les facteurs globaux. L'intégration de facettes améliorerait la précision des poids SME, au prix d'une complexité de mesure accrue. La règle de Cronbach (α ≥ 0.70 par facette) doit rester respectée.

---

## 3. Big Five au niveau équipe (composition)

### 3.1 Bell (2007) : la méta-analyse de référence

La méta-analyse de Bell (2007) — 57 études indépendantes, N = 3 811 équipes — est la référence sur l'effet des traits de personnalité au niveau équipe. Elle distingue deux types d'effets de composition :

**Effets d'élévation moyenne (mean effects)** : la performance de l'équipe est une fonction du trait moyen du groupe. Le modèle est additif : chaque membre contribue proportionnellement.

**Effets de variance (minimum/maximum effects)** : certains traits suivent des modèles non-linéaires. Le modèle disjonctif (déterminé par le minimum) s'applique quand la performance de l'équipe est contrainte par son membre le plus faible sur ce trait. Le modèle conjonctif (déterminé par le maximum) s'applique quand un expert unique suffit à compenser les lacunes des autres.

Résultats de Bell (2007) pour les traits Big Five au niveau équipe (corrélations avec la performance d'équipe) :

- **Conscientiousness mean** : ρ = 0.27 — effet positif de la moyenne, robuste
- **Agreeableness mean** : ρ = 0.34 — effet positif, plus fort que Conscientiousness en équipe
- **Agreeableness minimum** : ρ = 0.27 — effet disjonctif validé
- **Emotional Stability mean** : ρ = 0.25 — effet significatif
- **Extraversion mean** : ρ = 0.18 — effet présent mais plus contextuel
- **Openness mean** : ρ = 0.12 — effet faible, variable selon la nature de la tâche

### 3.2 Le modèle disjonctif d'Agréabilité — fondement du "jerk filter"

L'effet disjonctif de l'Agréabilité minimum est l'un des résultats les plus robustes de la méta-analyse de Bell (2007). La logique théorique (Hackman, 2002 ; Lencioni, 2002) est la suivante : dans une équipe, un seul membre avec une Agréabilité très faible peut empoisonner la dynamique de groupe entière — ce que Harmony nomme le "jerk filter". La présence d'un profil hostile ou systématiquement non-coopératif (A très bas) dans un espace confiné dégrade la confiance, augmente les conflits relationnels, et réduit la cohésion de toute l'équipe, indépendamment des niveaux des autres membres.

Dans l'implémentation Harmony (f_team.py), ce principe est formalisé par :
- Le terme `min(A_i)` dans la formule F_team, pondéré à 0.40 (terme dominant)
- Le seuil de danger `JERK_FILTER_DANGER = 35.0` : en dessous, un flag de risque est levé
- Les vetos de la safety barrier : A < 15 → DISQUALIFIED (veto HARD), A < 30 → HIGH_RISK (veto SOFT)

Ces seuils sont cohérents avec la littérature sur les environnements ICE (Sandal et al., 2006) qui montrent qu'en environnements confinés, les problèmes interpersonnels constituent la première source de dysfonctionnement d'équipe.

### 3.3 Variance de Conscientiousness — risque de faultline

Lau & Murnighan (1998) introduisent le concept de "faultlines" : des fractures virtuelles au sein d'une équipe, qui peuvent s'activer sous pression. Jehn, Northcraft & Neale (1999) montrent empiriquement que la variance des valeurs (dont Conscientiousness est un proxy) prédit les conflits de tâche et de relation.

Dans Harmony, la variance de Conscientiousness (`σ(C)`) entre membres de l'équipage est interprétée comme un risque de faultline : une forte divergence des standards de travail (certains membres très consciencieux, d'autres non) génère de la friction autour de la qualité d'exécution, du respect des procédures, et de la ponctualité. Le terme `−σ(C_normé) × 0.30` dans la formule F_team est une pénalité : plus la variance est élevée, plus le score F_team est réduit. Le seuil `FAULTLINE_DANGER = 20.0` (écart-type en points sur l'échelle 0-100) correspond approximativement au percentile 75 de variance observée dans les équipes fonctionnelles.

### 3.4 Diversité cognitive (Openness)

La littérature sur la diversité cognitive (van Knippenberg & Schippers, 2007) montre un effet de modération : la diversité en Openness est bénéfique pour les tâches créatives et les problèmes non-routiniers, mais neutre voire légèrement négative pour les tâches répétitives et procédurales. Dans l'industrie yacht, la majorité des tâches sont procédurales (maintenance, service, manœuvres), ce qui justifie de ne pas inclure la variance d'Openness dans F_team. Openness est conservée pour d'autres usages : dérivation des préférences de leadership (F_lmx) et plan de développement.

### 3.5 Implications pour le P-T Fit dans Harmony

La formule F_team implémentée dans Harmony combine trois des effets les mieux documentés par Bell (2007) :

```
F_team = min(A) × 0.40  −  σ(C_norm) × 0.30  +  μ(ES) × 0.30
```

- `min(A) × 0.40` : effet disjonctif dominant de l'Agréabilité minimale
- `σ(C_norm) × 0.30` : pénalité variance Conscientiousness (faultline risk)
- `μ(ES) × 0.30` : buffer de résilience collective (Emotional Stability moyenne)

La somme arithmétique des poids n'est pas normalisée à 1.0 car le terme faultline est une pénalité (coefficient négatif), non un terme additif. Ce choix modélise fidèlement la nature différente des trois effets.

---

## 4. P-J Fit — Adéquation personne-poste

### 4.1 Définition et dimensions

Edwards (1991) formalise deux sous-dimensions du P-J Fit :

- **Demands-Abilities (D-A) Fit** : adéquation entre les exigences objectives du poste et les capacités/compétences de la personne. C'est la dimension "suis-je assez bon pour ce poste ?". Harmony la mesure principalement via le score SME (GCA, Conscientiousness).
- **Needs-Supplies (N-S) Fit** : adéquation entre les besoins de la personne (intérêts, valeurs, préférences) et ce que le poste offre. "Ce poste me convient-il ?" Harmony anticipe cette dimension via le module F_env (ressources vs besoins) et le module F_lmx (style souhaité vs style proposé).

Kristof-Brown (2000) montre dans une étude expérimentale que les recruteurs opèrent intuitivement une distinction entre les deux, valorisant davantage le D-A Fit dans les phases initiales de sélection. C'est pourquoi dans le pipeline Harmony, le PJ Fit (D-A centré) est calculé en premier et constitue le filtre d'entrée obligatoire (Étage 1 / DNRE).

### 4.2 Score SME et calibration des poids

Les poids SME (Subject Matter Expert) implémentés dans Harmony correspondent à un panel d'experts maritimes appliqué à la définition de la compétence C1 (Individual Performance). Les valeurs par défaut (GCA = 0.60, C = 0.40) sont ancrées dans deux méta-analyses :

- Schmidt & Hunter (1998) : GCA est le meilleur prédicteur unique de performance, ρ ≈ 0.51. La validité incrémentale de C sur GCA est ρ ≈ +0.18. Le ratio de pondération GCA/C ≈ 3/2 traduit cette différence de validité relative.
- Sackett et al. (2022) : corrections plus rigoureuses de la restriction de l'étendue confirment la supériorité de GCA, avec validités révisées légèrement à la hausse.

Ces poids sont des priors (Phase 0 du panel SME). Ils doivent être recalibrés poste par poste via `JobWeightConfig` en DB — les poids du Capitaine incluront E et LMX-leadership, ceux du Steward incluront A et O, etc. La structure du code (`sme_weights` injectable) rend ce recalibrage possible sans modification de la logique du moteur.

### 4.3 P_ind — terme d'interaction GCA × Conscientiousness

La formule P_ind implémentée dans le scorer PJ Fit est :

```
P_ind = 0.55 × GCA + 0.35 × C + 0.10 × (GCA × C / 100)
```

Le terme d'interaction (ω = 0.10) est ancré dans Roberts et al. (2007) et des travaux sur la synergieaptitudes × traits (Ackerman & Heggestad, 1997) : les individus qui combinent forte aptitude cognitive et haute Conscientiousness sur-performent au-delà de ce que chaque facteur prédit séparément. Le terme d'interaction est volontairement faible (0.10) pour rester conservateur : la littérature empirique directe sur cet effet est moins robuste que pour les effets principaux.

### 4.4 Barrière de sécurité non-compensatoire

La barrière de sécurité de Harmony est un mécanisme non-compensatoire : certains déficits psychométriques ne peuvent pas être "compensés" par des forces sur d'autres dimensions. Ce principe est ancré dans la littérature sur les contre-indicateurs de recrutement (Hogan & Hogan, 2001) et est particulièrement justifié pour les environnements ICE (Sandal et al., 2006).

L'implémentation utilise une pénalité logistique continue plutôt qu'un seuil binaire dur, ce qui préserve la gradualité pour les décisions marginales :

```
penalty(x, s, k) = σ(k × (x − s)) = 1 / (1 + e^{−k × (x − s)})
adjusted_score = g_fit × Π(penalty_i)
```

Les quatre niveaux de sécurité correspondent à des seuils théoriquement justifiés :
- **DISQUALIFIED** (veto HARD) : ES < 15 ou A < 15 — risque de sécurité aiguë en environnement confiné
- **HIGH_RISK** (veto SOFT) : ES < 30, A < 30, ou C < 25 — risque de burnout ou friction équipe
- **ADVISORY** : C < 35 ou Résilience < 35 — point de vigilance sans exclusion
- **CLEAR** : aucun seuil activé

### 4.5 Centile dynamique

Le calcul de centile (formule de Tukey, implémenté dans `centile_rank.py`) permet de positionner chaque candidat relativement à un pool dynamique. Contrairement à un centile normatif sur population générale, ce centile est calculé sur le pool de candidats actifs pour cette campagne — il répond à la question "parmi les candidats qui ont postulé, où se situe ce profil ?". Cette approche est cohérente avec le principe de classement relatif dans les processus de sélection (Cascio & Aguinis, 2011).

---

## 5. P-O Fit — Adéquation personne-organisation

### 5.1 Définition et modèles de mesure

Chatman (1989) introduit le P-O Fit comme la congruence entre les valeurs individuelles et les valeurs organisationnelles. Sa définition est fondée sur le modèle des valeurs : une organisation a une "personnalité" (culture, valeurs dominantes) et les individus qui partagent ces valeurs seront plus engagés, plus performants, et resteront plus longtemps.

Les instruments classiques de mesure incluent :
- **OCP (Organizational Culture Profile)** : Q-Sort de 54 items de valeurs, appliqué à la fois à la personne et à l'organisation, mesurant l'adéquation par corrélation de profil (O'Reilly, Chatman & Caldwell, 1991)
- **ASA Model** (Schneider, 1987) : cycle d'Attraction-Sélection-Attrition — les organisations tendent naturellement vers l'homogénéité des valeurs par les mécanismes de recrutement et de départ volontaire

### 5.2 Opérationnalisation dans Harmony : F_env comme proxy JD-R

Dans l'implémentation Harmony, le P-O Fit est opérationnalisé via le modèle JD-R (Bakker & Demerouti, 2007) plutôt que via un instrument OCP. Ce choix pragmatique est justifié par plusieurs raisons :

1. Dans l'industrie yacht, les "valeurs organisationnelles" sont difficilement codifiables à court terme — ce qui varie réellement d'un yacht à l'autre, c'est le ratio demandes/ressources (intensité de la saison charter, conditions de vie à bord, pression managériale).
2. Le JD-R est le modèle le mieux validé pour prédire le burnout et le bien-être en environnements de travail exigeants (Bakker & Demerouti, 2007 ; revue méta-analytique de Schaufeli & Taris, 2014).
3. Les paramètres nécessaires (salary_index, rest_days_ratio, private_cabin_ratio, charter_intensity, management_pressure) sont des données objectives récoltables sans instruments psychométriques.

La formule implémentée est :
```
F_env = (R_yacht / D_yacht) × Résilience_norm × 100  (cappé à 100)
```

La modulation par la résilience individuelle est une innovation propre à Harmony : le même yacht à haut JD-R (exigeant) sera vécu différemment par un marin à haute résilience (ES = 80) et par un marin fragile (ES = 35). Cette interaction est cohérente avec le concept de "fit modéré par les ressources personnelles" dans le modèle JD-R étendu.

### 5.3 Outcomes et direction de causalité

Kristof-Brown et al. (2005) rapportent pour le P-O Fit : ρ = 0.48 avec l'engagement organisationnel, ρ = −0.35 avec le turnover intention, ρ = 0.27 avec l'OCB (comportements de citoyenneté organisationnelle). Ces effets sont les plus forts parmi les quatre dimensions du P-E Fit pour les variables d'attitudes et de rétention.

Dans le contexte yacht, ces effets sont amplifiés par l'impossibilité de "sortir" de l'organisation en dehors des ports. Un marin dont le P-O Fit est faible (yacht exigeant, résilience basse) ne peut pas réduire son exposition aux stresseurs en rentrant chez lui le soir — il vit et dort dans l'environnement de travail. Ceci justifie que F_env soit inclus comme dimension à part entière dans le score global PE Fit.

---

## 6. P-T Fit — Adéquation personne-équipe

### 6.1 Définition et distinction composition vs compatibilité

Kristof-Brown & Stevens (2001) formalisent le P-T Fit en distinguant deux dimensions complémentaires :

- **Fit de composition** : propriétés agrégées de l'équipe (moyenne, variance, minimum) et leur relation avec la performance collective. C'est la dimension mesurée par Bell (2007) et implémentée dans F_team.
- **Compatibilité interpersonnelle** : adéquation entre paires de membres (dyadique). C'est la dimension mesurée dans le sociogramme Harmony via la matrice de compatibilité pairwise (matrice.py).

Ces deux dimensions sont complémentaires : le F_team score mesure la santé de l'équipe en tant que système, la matrice de compatibilité identifie les paires à risque de friction ou de synergie au sein de ce système.

### 6.2 La matrice de compatibilité pairwise du sociogramme

La formule de compatibilité dyadique implémentée dans `matrice.py` est :

```
D_ij = 0.55 × (1 − |C_i − C_j| / 100) + 0.25 × (A_i + A_j) / 200 + 0.20 × (ES_i + ES_j) / 200
```

Les pondérations reflètent les effets documentés :

- **α = 0.55 (Conscientiousness, similarité)** : terme dominant. La divergence des standards de travail est la source de friction la plus fréquente dans les équipes de maintenance et d'opérations (Bell, 2007 ; Jehn et al., 1999). Le terme est basé sur la similarité (1 − distance) car un marin très consciencieux et un marin peu consciencieux s'opposeront systématiquement sur les standards de qualité.
- **β = 0.25 (Agréabilité, additif)** : terme social. L'Agréabilité est modélisée de façon additive (cumulative), non par similarité : deux membres à haute Agréabilité créent une énergie sociale cumulative positive, mais une paire basse A / haute A n'est pas pénalisée autant que si les deux étaient bas. Ce choix est cohérent avec la modélisation de l'Agréabilité comme ressource sociale (Mount, Barrick & Stewart, 1998).
- **γ = 0.20 (Stabilité émotionnelle, additive)** : buffer de résilience collective. La moyenne des ES de la paire est préférée au produit pour éviter de trop pénaliser les paires où un seul membre est fragile — la résilience collective d'une paire est mieux représentée par sa moyenne que par son produit.

L'application principale de la matrice est le sociogramme 3D : chaque paire devient une arête dont le poids = compatibilité, la couleur et l'épaisseur encodant visuellement la dynamique. L'affectation des cabines peut utiliser ce score : paires avec D_ij > 0.70 = synergiques (cabine partagée recommandable), paires avec D_ij < 0.30 = friction (à séparer).

### 6.3 Diversité, faultlines et performance

Van Knippenberg, De Dreu & Homan (2004) proposent le modèle catégorisation-élaboration (CEM) qui formalise la tension entre diversité et cohésion : la diversité en valeurs et personnalité (deep-level diversity) tend à réduire la cohésion et augmenter les conflits relationnels, même si elle peut bénéficier aux tâches créatives. Dans un contexte d'opérations maritimes — tâches largement procédurales, sécurité critique — la réduction de la diversité en Conscientiousness (homogénéité des standards) est donc un objectif légitime, tandis que la diversité en Openness peut être tolérée voire encouragée pour les postes impliquant de la résolution de problèmes.

---

## 7. P-S Fit — Adéquation personne-superviseur (LMX)

### 7.1 Théorie LMX et fondements du P-S Fit

La Leader-Member Exchange Theory (Graen & Uhl-Bien, 1995) postule que les relations superviseur-subordonné ne sont pas uniformes au sein d'une équipe : chaque dyade superviseur-subordonné développe une relation unique, qualifiée de "haute LMX" (confiance, soutien, délégation) ou "basse LMX" (surveillance, faible investissement relationnel). La qualité de la LMX prédit la performance contextuelle, la satisfaction, et la rétention du subordonné (méta-analyse de Dulebohn et al., 2012 : ρ = 0.27 pour la performance, ρ = 0.46 pour la satisfaction).

Le lien entre P-S Fit et LMX est bi-directionnel : la congruence entre les préférences du subordonné et le style du superviseur prédit la qualité de la LMX, qui à son tour prédit les outcomes. Harmony modélise la dimension antécédente (congruence des préférences) plutôt que la LMX développée (qui n'est observable qu'après une période d'interaction).

### 7.2 Les trois dimensions du vecteur leadership

L'implémentation Harmony décompose le style de leadership en trois dimensions dont les préférences peuvent être mesurées avant l'embauche :

- **Autonomie** (autonomy_given / autonomy_preference) : degré de délégation et d'indépendance dans l'exécution des tâches. Ancré dans le continuum du "leadership directif vs participatif" (House, 1971).
- **Feedback** (feedback_style / feedback_preference) : fréquence et style du retour d'information. Préférence pour le coaching vs l'évaluation formelle.
- **Structure** (structure_imposed / structure_preference) : degré de formalisation des procédures et des attentes. Ancré dans la notion de "structure d'initiating structure" (Halpin & Winer, 1957).

Ces trois dimensions couvrent les deux facteurs classiques du leadership (considération et initiating structure), décomposés de façon à permettre un profiling opérationnel sans instrument spécialisé. En l'absence de mesure directe des préférences du candidat, Harmony dérive ces préférences depuis le Big Five via des heuristiques théoriquement motivées :
- `autonomy_pref ≈ O × 0.6 + (1 − A/100) × 0.4` : les individus ouverts et moins dociles préfèrent plus d'autonomie
- `feedback_pref ≈ O` : les personnes ouvertes sont plus receptives au développement
- `structure_pref ≈ C` : les personnes consciencieuses préfèrent des environnements structurés

### 7.3 Calcul de la distance et interprétation

La distance euclidienne pondérée dans l'espace à trois dimensions du leadership est :

```
F_lmx = (1 − ‖L_capt − V_crew‖ / d_max) × 100
```

Les poids sont uniformes (1/3 chacun) en Temps 1. Dulebohn et al. (2012) montrent que les trois dimensions ont des effets comparables sur la qualité LMX perçue, ce qui justifie l'égalité des poids en absence de données empiriques propres à Harmony.

Les seuils d'alerte (distance normalisée > 0.70 → CRITICAL, > 0.50 → TENSION) sont calibrés de sorte que :
- **EXCELLENT** (< 0.25) : profils compatibles sur les trois dimensions — relation LMX haute probable
- **GOOD** (0.25 à 0.45) : écarts acceptables — relation LMX fonctionnelle
- **TENSION** (0.45 à 0.70) : friction probable sur au moins une dimension
- **CRITICAL** (> 0.70) : incompatibilité structurelle — risque de conflit managérial répété

### 7.4 Application spécifique yacht : le contexte capitaine-équipage

Dans l'industrie yacht, la relation capitaine-équipage présente des caractéristiques qui amplifient les effets du P-S Fit : le capitaine est à la fois superviseur direct, responsable légal du navire, et cohabitant. L'impossibilité de "sortir" de la relation (sauf à quitter le navire) rend les désaccords de style de leadership particulièrement coûteux. Ceci justifie que le P-S Fit soit une dimension à part entière dans le score global, et non un facteur secondaire.

---

## 8. Psychosocial Risks (RPS) — Extension naturelle du P-E Fit

### 8.1 Modèle JD-R

Le Job Demands-Resources model (Bakker & Demerouti, 2007) postule que les exigences professionnelles (demands) mobilisent des ressources cognitives et émotionnelles, conduisant à l'épuisement (burnout pathway), tandis que les ressources disponibles (resources) soutiennent la motivation et l'engagement (motivation pathway). L'équilibre R/D détermine le risque de burnout et le niveau d'engagement.

La robustesse du modèle JD-R est attestée par plusieurs centaines d'études dans des secteurs variés. La méta-analyse de Schaufeli & Taris (2014) confirme la validité des deux pathways, avec des validités moyennes pour les demandes → burnout (ρ = 0.40) et ressources → engagement (ρ = 0.43).

Dans Harmony, les ressources yacht (salaire, repos, cabine privée) et les demandes (intensité charter, pression managériale) sont les inputs du module F_env. Le ratio R/D < 0.7 est le seuil de déclenchement du flag `BURNOUT_RISK`, calibré de façon conservatrice.

### 8.2 P-T Fit comme prédicteur de burnout

Andela & Van der Doef (2018) montrent dans une étude longitudinale sur des professionnels de santé que le P-T Fit (congruence avec l'équipe) est un prédicteur significatif du burnout émotionnel, indépendamment des variables JD-R. La logique est intuitive : une équipe discordante (faultlines, jerk, ES faible) constitue en elle-même une demand qui consomme des ressources émotionnelles.

Pour Harmony, ceci implique que F_team est un prédicteur des RPS au-delà de son rôle dans la performance : un score F_team bas n'est pas seulement un signal de performance collective réduite, mais aussi un signal de risque de burnout accru. Cette dualité doit être documentée dans les rapports employeur.

### 8.3 Signaux précoces dans le moteur Harmony

Le moteur peut détecter proactivement les combinaisons à risque suivant la convergence des trois dimensions :

- **ES (Stabilité Emotionnelle) individuelle basse** (< 35) : flag `LOW_RESILIENCE` dans F_env — le candidat est vulnérable aux demandes.
- **Agréabilité minimum de l'équipe basse** (< 35) : flag `JERK_RISK` dans F_team — l'équipe génère des demandes relationnelles supplémentaires.
- **Divergence P-T sur Conscientiousness** élevée : flag `FAULTLINE_RISK` dans F_team — l'équipe est fragmentée sur les standards, source de stress chronique.

La conjonction de ces trois signaux constitue un profil de risque psychosocial élevé qui mérite une alerte spécifique à l'employeur, indépendamment du score global PE Fit. Cette logique d'alerte combinatoire est à implémenter dans les futures versions du module de diagnostic (diagnosis.py).

---

## 9. Formation et développement — P-E Fit comme diagnostic

### 9.1 Gap analysis P-J : plan de développement individuel

Le score PJ Fit peut être décomposé en contributions par trait (TraitContribution dans SMEScoreResult), ce qui permet de construire directement un plan de développement : les traits sous-performants relativement aux poids SME sont les axes de développement prioritaires.

Par exemple, pour un Deckhand présentant GCA = 65 (contribution satisfaisante) et C = 42 (contribution insuffisante avec poids 0.40), la recommandation de développement portera prioritairement sur la Conscientiousness : organisation, gestion des priorités, régularité dans les tâches de maintenance. Cette recommandation est plus actionnable qu'un score global insuffisant.

Le module `benchmarking/gap.py` (existence confirmée dans l'arborescence du projet) est la surface naturelle pour cette analyse. Son articulation avec les poids SME par poste permettra, à terme, de générer des plans de développement différenciés par rôle.

### 9.2 Potentiel de leadership : trajectoire P-S → P-J (Capitaine)

La littérature sur le développement du leadership (Day, 2001 ; Judge et al., 2002) identifie plusieurs prédicteurs du potentiel de leadership : Extraversion (ρ = 0.31 avec leadership emergence), GCA, et certaines facettes de Conscientiousness (ambition, drive). Le modèle LMX suggère une trajectoire naturelle : un marin qui développe des relations LMX haute avec ses supérieurs successifs est un candidat au rôle de capitaine — il "apprend" les codes de la relation superviseur en les vivant du côté subordonné.

Pour Harmony, cette trajectoire peut être modélisée à moyen terme : les candidats dont le profil PS Fit est excellent avec les capitaines actuels et dont le profil GCA + E + C est fort constituent un vivier de leadership à identifier.

### 9.3 Stabilité longitudinale des Big Five

Roberts & Mroczek (2008), et Roberts et al. (2006) documentent la stabilité des Big Five sur des périodes de 4 à 6 ans : les corrélations test-retest à 4 ans sont de l'ordre de 0.55 à 0.70 selon les traits, avec une tendance à l'augmentation de Conscientiousness et à la diminution de Neuroticism avec l'âge adulte.

Pour Harmony, ceci a deux implications :

1. Les snapshots psychométriques doivent être rechargés par une nouvelle passation de tests tous les 3 à 4 ans maximum pour rester prédictifs.
2. Les Big Five ne sont pas entièrement immuables : des interventions de développement (coaching, formation) peuvent produire des changements mesurables sur certains traits, notamment C et ES. Les plans de développement du module formation ont donc un ancrage scientifique réel.

---

## 10. Limites et précautions

### 10.1 Biais de méthode commune (Common Method Variance)

En sciences du comportement, le CMV (Podsakoff et al., 2003) est une source d'inflation artificielle des corrélations lorsque les variables indépendantes et dépendantes sont mesurées par le même instrument, au même moment, par la même personne. Dans Harmony, ce risque est limité car :
- Les traits sont mesurés par des tests psychométriques standardisés (objectif)
- Les profils de poste sont définis par des SME (source différente)
- Les vecteurs capitaine sont renseignés par l'employeur (source différente du candidat)

Le risque résiduel concerne la validation du modèle (Section OLS) : si `y_actual` est mesuré via des évaluations managériales, et si les managers connaissent les scores du moteur, un CMV de confirmation pourrait biaiser la mesure de critère.

### 10.2 Fit vs diversité : la tension créative

Milliken & Martins (1996) documentent la tension fondamentale entre fit et diversité : l'homogénéité d'une équipe favorise la cohésion mais réduit la créativité et la capacité d'adaptation. Pour Harmony, ce trade-off est central dans la pondération de la variance de Conscientiousness (pénalisée dans F_team) vs la variance d'Openness (non pénalisée). À mesure que la base de données Harmony croît, il sera possible de tester empiriquement si certaines configurations de diversité prédisent mieux la performance à long terme dans le contexte yacht.

### 10.3 Prédiction vs équité : risques de discrimination

L'utilisation de tests psychométriques et de modèles de matching à l'embauche expose à des risques de discrimination indirecte si les instruments ou les poids introduisent des disparités selon le genre, l'âge ou l'origine ethnique. Points de vigilance spécifiques pour Harmony :

- **GCA et biais culturel** : les tests cognitifs présentent des biais interculturels documentés. Les scores GCA d'individus non francophones natifs testés en français sont susceptibles de sous-estimer l'aptitude réelle.
- **Big Five et genre** : des différences de moyennes de genre existent pour A et N dans les études cross-culturelles. Le fait de pondérer fortement ces traits dans le score global pourrait introduire des biais.
- **Safety barrier et équité** : les vetos doivent être documentés avec une justification objective liée aux exigences de sécurité réelles du poste (pas seulement de convenance).

La conformité au standard ISO 10667 (évaluation en contexte professionnel) requiert que chaque outil utilisé soit validé sur la population cible, que les conditions de passation soient standardisées, et que les candidats soient informés des méthodes de mesure.

### 10.4 Données manquantes : fallback à 50.0 vs veto

La règle de fallback à 50.0 (médiane) pour les traits non mesurés est une décision conservatrice : en l'absence de mesure, le candidat est traité comme "dans la moyenne". Ce choix est justifiable du point de vue des droits du candidat (bénéfice du doute), mais introduit une perte d'information.

Pour la barrière de sécurité spécifiquement, Harmony applique la règle inverse pour les vetos : `extract_strict()` est utilisé (pas de fallback), ce qui signifie qu'un veto ne peut être déclenché que sur un trait réellement mesuré. Ce choix est scientifiquement plus défendable : déclencher un veto HARD sur un profil fictif (fallback) serait injuste.

La tension entre ces deux règles (fallback pour les scores, pas de fallback pour les vetos) doit être documentée explicitement pour chaque revue scientifique.

### 10.5 Recalibration périodique des profils SME

Les poids SME Phase 0 sont des priors fondés sur la littérature générale. Ils doivent être recalibrés périodiquement en deux étapes :

- **Temps 1 (court terme)** : Q-Sort auprès d'un panel d'employeurs et capitaines Harmony pour valider les poids par poste. Cette procédure est conforme à la norme ISO 10667.
- **Temps 2 (à partir de 150 événements de recrutement)** : OLS sur les données réelles Harmony pour calibrer les βs du modèle prédictif. Le critère de succès (`y_actual`) doit être défini précisément avant toute collecte : rétention à 6 mois, note d'évaluation managériale, absence de conflit signalé ? Le choix du critère détermine ce que le modèle optimise.

Pour l'OLS Temps 2, les conditions de validité des hypothèses (linéarité, homoscédasticité, indépendance des résidus, VIF < 5) doivent être vérifiées, et un hold-out set (20% des données) doit être conservé pour la validation croisée.

---

## 11. Bibliographie complète

### Big Five et performance individuelle

Barrick, M.R., & Mount, M.K. (1991). The Big Five personality dimensions and job performance: A meta-analysis. *Personnel Psychology*, 44(1), 1–26.

Costa, P.T., & McCrae, R.R. (1992). *Revised NEO Personality Inventory (NEO-PI-R) and NEO Five-Factor Inventory (NEO-FFI) professional manual*. Psychological Assessment Resources.

Judge, T.A., Bono, J.E., Ilies, R., & Gerhardt, M.W. (2002). Personality and leadership: A qualitative and quantitative review. *Journal of Applied Psychology*, 87(4), 765–780.

Maples, J.L., Carter, N.T., Few, L.R., Crego, C., Gore, W.L., Samuel, D.B., Williamson, R.L., Lynam, D.R., Widiger, T.A., Markon, K.E., Krueger, R.F., & Miller, J.D. (2014). Testing whether the DSM-5 personality disorder trait model can be measured with a reduced set of items: An item response theory investigation of the Personality Inventory for DSM-5. *Psychological Assessment*, 27(4), 1–15.

Mount, M.K., Barrick, M.R., & Stewart, G.L. (1998). Five-factor model of personality and performance in jobs involving interpersonal interactions. *Human Performance*, 11(2–3), 145–165.

Roberts, B.W., & Mroczek, D. (2008). Personality trait change in adulthood. *Current Directions in Psychological Science*, 17(1), 31–35.

Roberts, B.W., Walton, K.E., & Viechtbauer, W. (2006). Patterns of mean-level change in personality traits across the life course: A meta-analysis of longitudinal studies. *Psychological Bulletin*, 132(1), 1–25.

Roberts, B.W., Kuncel, N.R., Shiner, R., Caspi, A., & Goldberg, L.R. (2007). The power of personality: The comparative validity of personality traits, socioeconomic status, and cognitive ability for predicting important life outcomes. *Perspectives on Psychological Science*, 2(4), 313–345.

Tett, R.P., & Burnett, D.D. (2003). A personality trait-based interactionist model of job performance. *Journal of Applied Psychology*, 88(3), 500–517.

### Prédiction de performance et méthodes de sélection

Schmidt, F.L., & Hunter, J.E. (1998). The validity and utility of selection methods in personnel psychology: Practical and theoretical implications of 85 years of research findings. *Psychological Bulletin*, 124(2), 262–274.

Schmidt, F.L. (2016). The validity and utility of selection methods in personnel psychology: Practical and theoretical implications of 100 years of research findings. *Fox School of Business Research Paper*.

Sackett, P.R., Zhang, C., Berry, C.M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology*, 107(10), 2040–2068.

Cascio, W.F., & Aguinis, H. (2011). *Applied Psychology in Human Resource Management* (7th ed.). Prentice Hall.

### P-E Fit — Cadre général et méta-analyses

Kristof, A.L. (1996). Person-organization fit: An integrative review of its conceptualizations, measurement, and implications. *Personnel Psychology*, 49(1), 1–49.

Kristof-Brown, A.L., Zimmerman, R.D., & Johnson, E.C. (2005). Consequences of individuals' fit at work: A meta-analysis of person-job, person-organization, person-group, and person-supervisor fit. *Personnel Psychology*, 58(2), 281–342.

Kristof-Brown, A.L., & Stevens, C.K. (2001). Goal congruence in project teams: Does the fit between members' personal mastery and performance goals matter? *Journal of Applied Psychology*, 86(6), 1083–1095.

De Cooman, R., & Vleugels, W. (2022). Person–environment fit conceptualization and misalignment: A review. *Annual Review of Organizational Psychology and Organizational Behavior*, 9, 183–209.

Chuang, A., Shen, C.T., & Judge, T.A. (2016). Development of a multidimensional instrument of person-environment fit: The Perceived Person-Environment Fit Scale (PPEFS). *Applied Psychology: An International Review*, 65(1), 66–98.

Andela, M., & Van der Doef, M. (2018). A comprehensive assessment of the person-environment fit dimensions and their relationships with work-related outcomes. *Journal of Career Development*, 46(5), 567–584.

Cable, D.M., & DeRue, D.S. (2002). The convergent and discriminant validity of subjective fit perceptions. *Journal of Applied Psychology*, 87(5), 875–884.

Edwards, J.R. (1991). Person-job fit: A conceptual integration, literature review, and methodological critique. In C.L. Cooper & I.T. Robertson (Eds.), *International Review of Industrial and Organizational Psychology* (vol. 6, pp. 283–357). Wiley.

Chatman, J.A. (1989). Improving interactional organizational research: A model of person-organization fit. *Academy of Management Review*, 14(3), 333–349.

### Dynamiques d'équipe et composition

Bell, S.T. (2007). Deep-level composition variables as predictors of team performance: A meta-analysis. *Journal of Applied Psychology*, 92(3), 595–615.

Hackman, J.R. (2002). *Leading Teams: Setting the Stage for Great Performances*. Harvard Business School Press.

Jehn, K.A. (1995). A multimethod examination of the benefits and detriments of intragroup conflict. *Administrative Science Quarterly*, 40(2), 256–282.

Jehn, K.A., Northcraft, G.B., & Neale, M.A. (1999). Why differences make a difference: A field study of diversity, conflict, and performance in workgroups. *Administrative Science Quarterly*, 44(4), 741–763.

Lau, D.C., & Murnighan, J.K. (1998). Demographic diversity and faultlines: The compositional dynamics of organizational groups. *Academy of Management Review*, 23(2), 325–340.

Milliken, F.J., & Martins, L.L. (1996). Searching for common threads: Understanding the multiple effects of diversity in organizational groups. *Academy of Management Review*, 21(2), 402–433.

Van Knippenberg, D., De Dreu, C.K.W., & Homan, A.C. (2004). Work group diversity and group performance: An integrative model and research agenda. *Journal of Applied Psychology*, 89(6), 1008–1022.

Jordan, P.J., Ashkanasy, N.M., Härtel, C.E.J., & Hooper, G.S. (2002). Workgroup emotional intelligence: Scale development and relationship to team process effectiveness and goal focus. *Human Resource Management Review*, 12(2), 195–214.

### Leadership, LMX et P-S Fit

Graen, G.B., & Uhl-Bien, M. (1995). Relationship-based approach to leadership: Development of leader-member exchange (LMX) theory of leadership over 25 years. *The Leadership Quarterly*, 6(2), 219–247.

Dulebohn, J.H., Bommer, W.H., Liden, R.C., Brouer, R.L., & Ferris, G.R. (2012). A meta-analysis of antecedents and consequences of leader-member exchange: Integrating the past with an eye toward the future. *Journal of Management*, 38(6), 1715–1759.

House, R.J. (1971). A path goal theory of leader effectiveness. *Administrative Science Quarterly*, 16(3), 321–339.

Day, D.V. (2001). Leadership development: A review in context. *The Leadership Quarterly*, 11(4), 581–613.

### JD-R et risques psychosociaux

Bakker, A.B., & Demerouti, E. (2007). The job demands-resources model: State of the art. *Journal of Managerial Psychology*, 22(3), 309–328.

Schaufeli, W.B., & Taris, T.W. (2014). A critical review of the job demands-resources model: Implications for improving work and health. In G.F. Bauer & O. Hämmig (Eds.), *Bridging Occupational, Organizational and Public Health* (pp. 43–68). Springer.

Borman, W.C., & Motowidlo, S.J. (1993). Expanding the criterion domain to include elements of contextual performance. In N. Schmitt & W.C. Borman (Eds.), *Personnel Selection in Organizations* (pp. 71–98). Jossey-Bass.

### Environnements confinés et isolés

Sandal, G.M., Leon, G.R., & Larsen, E. (2006). Human challenges in polar and space environments. *Reviews in Environmental Science and Bio/Technology*, 5(2–3), 281–296.

Hogan, R., & Hogan, J. (2001). Assessing leadership: A view from the dark side. *International Journal of Selection and Assessment*, 9(1–2), 40–51.

### Psychométrie et méthodes

Cronbach, L.J. (1951). Coefficient alpha and the internal structure of tests. *Psychometrika*, 16(3), 297–334.

Podsakoff, P.M., MacKenzie, S.B., Lee, J.Y., & Podsakoff, N.P. (2003). Common method biases in behavioral research: A critical review of the literature and recommended remedies. *Journal of Applied Psychology*, 88(5), 879–903.

O'Reilly, C.A., Chatman, J., & Caldwell, D.F. (1991). People and organizational culture: A profile comparison approach to assessing person-organization fit. *Academy of Management Journal*, 34(3), 487–516.

Schneider, B. (1987). The people make the place. *Personnel Psychology*, 40(3), 437–453.

ISO 10667-1:2011. *Assessment service delivery — Procedures and methods to assess people in work and organizational settings*. International Organization for Standardization.

---

## Annexe A — Correspondance formules / fichiers d'implémentation

| Formule / Concept | Fichier Harmony | Paramètres clés |
|---|---|---|
| Score SME C1 = Σ(w_t × x_it) / Σ(w_t) | `pe_fit/pj_fit/scorer.py` | DEFAULT_PJ_WEIGHTS : GCA=0.60, C=0.40 |
| P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA×C/100) | `pe_fit/pj_fit/scorer.py` | ω₁=0.55, ω₂=0.35, ω₃=0.10 |
| Safety barrier non-compensatoire | `pe_fit/pj_fit/safety_barrier.py` | HARD: ES<15, A<15 ; SOFT: ES<30, A<30, C<25 |
| F_team = min(A)×α − σ(C_norm)×β + μ(ES)×γ | `pe_fit/pt_fit/f_team.py` | α=0.40, β=0.30, γ=0.30 |
| F_env = (R/D) × Résilience × 100 | `pe_fit/po_fit/f_env.py` | seuils : BURNOUT_RISK < 0.7, COMFORT ≥ 1.3 |
| F_lmx = (1 − ‖L − V‖ / d_max) × 100 | `pe_fit/ps_fit/f_lmx.py` | W_A=W_F=W_S=1/3, CRITICAL > 0.70 |
| D_ij (matrice pairwise) | `benchmarking/matrice.py` | α=0.55, β=0.25, γ=0.20 |
| Global PE Fit = moyenne dimensions disponibles | `pe_fit/master.py` | Architecture graceful degradation |
| Pipeline DNRE → MLPSM | `engine/recruitment/pipeline.py` | Filtre HARD : DISQUALIFIED → exclu stage 2 |

---

## Annexe B — Signaux de risque psychosocial combinatoires

Le tableau suivant formalise les combinaisons de flags qui déclenchent une alerte RPS dans les rapports employeur (à implémenter en Temps 2) :

| Combinaison | Signal | Recommandation |
|---|---|---|
| ES_ind < 35 + BURNOUT_RISK (F_env) | Risque d'épuisement aigu | Reconsidérer l'affectation sur ce yacht ; prioriser un yacht COMFORTABLE |
| JERK_RISK (F_team) + ES_ind < 40 | Double vulnérabilité émotionnelle | Accompagnement managérial renforcé requis |
| FAULTLINE_RISK (F_team) + LMX_TENSION (F_lmx) | Environnement systémiquement conflictuel | Risque de départ anticipé élevé (ρ ≈ −0.35, P-O Fit Kristof-Brown et al.) |
| Safety HIGH_RISK + F_team score < 40 | Candidat fragile dans une équipe déjà difficile | Non recommandé — orienter vers une équipe à F_team ≥ 60 |

---

*Document de référence Harmony — Responsable scientifique. Toute modification de formule dans les moteurs PJ/PO/PT/PS Fit doit être soumise à validation scientifique en référence à ce document avant implémentation.*
