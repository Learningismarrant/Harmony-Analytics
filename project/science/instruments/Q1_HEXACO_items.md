# Q1 — IPIP-HEXACO-60 Items

**Version :** 1.1 — Mars 2026 (wording vérifié sur ipip.ori.org/newHEXACO_PI_key.htm)
**Construct :** 6 dimensions de personnalité (modele HEXACO)
**Source :** IPIP — International Personality Item Pool (domaine public)
**Reference primaire :** Ashton, M.C., Lee, K., & Goldberg, L.R. (2007). The IPIP-HEXACO scales: An alternative, public-domain measure of the personality constructs in the HEXACO model. *Personality and Individual Differences*, 42(8), 1515–1526.
**Echelle :** Likert 5 — 1 = "Strongly Disagree" → 5 = "Strongly Agree"
**Format :** Items auto-rapportes, passation individuelle, ordre randomisable
**Droits :** Domaine public — IPIP. Utilisation libre sans restriction pour usage commercial ou non-commercial. Aucune autorisation requise.
**Clé de scoring :** ipip.ori.org/newHEXACO_PI_key.htm

---

## Justification du passage Big Five → HEXACO-60

### Pourquoi HEXACO plutot que Big Five (IPIP-120 / NEO) ?

Le modele Big Five a longtemps ete l'etalon de reference en psychologie de la personnalite (Barrick & Mount, 1991 ; Schmidt & Hunter, 1998). Cependant, trois arguments scientifiques justifient le passage au HEXACO dans le contexte Harmony :

**1. La dimension Honesty-Humility (H) comme facteur discriminant en environnement ICE**

La recherche lexicale multilingue de Lee & Ashton (2004, 2008) a identifie systematiquement un sixieme facteur de personnalite — Honesty-Humility — absent des modeles Big Five. Ce facteur capture la tendance a etre sincere, equitable, a eviter la cupidite et a faire preuve de modestie. Dans les environnements ICE (Isolated, Confined, Extreme — Stuster, 2010), les comportements antisociaux opportunistes sont la principale source de dysfonction d'equipe : un membre d'equipage faible en H peut saborder la cohesion par des comportements manipulateurs, de la cupidite ou de l'arrogance. Le Big Five Agreeableness ne capture pas cette variance de maniere suffisamment specifique (correlation H-A ≈ 0.30 seulement — Ashton & Lee, 2007).

**2. Meilleure couverture de construct pour Q4 (PT Fit) et Q5 (PO Fit)**

La formule Bell (2007) utilise Agreeableness, Conscientiousness et Emotional Stability. Dans HEXACO, l'Agreeableness est une variante rotationnelle de l'Agreeableness Big Five (en incluant des facettes de Patience et Gentleness plutot que de Tender-Mindedness), et l'Emotionality HEXACO recoupe partiellement le Neuroticism Big Five avec une surcharge de peur/dependance plus pertinente pour les environnements a risque. Ces precisions de construct ameliorent la validite de content de Q4.

**3. Validite discriminante amelioree et reduction de la variance partagee avec A**

Dans le Big Five, la variance liee au comportement malhonnete ou manipulateur est distribuee entre Agreeableness (bas) et Conscientiousness (bas). Le HEXACO isole cette variance dans H, reduisant la multicollinearite dans les modeles de prediction, ce qui est critique pour les regressions OLS du MLPSM (VIF < 5 requis).

### Limites a documenter

- La formule Bell (2007) a ete developpee sur Big Five — les mappings C et A sont transposables directement (correlations convergentes > 0.80), mais H n'a pas d'equivalent Bell direct. Son role dans le moteur est a definir (voir section "Implications pe_fit engine").
- L'invariance culturelle du HEXACO sur population maritime n'est pas encore validee — ce point s'appliquait egalement au CUTTY SARK T-IRT Big Five.
- La version IPIP (Ashton et al. 2007) montre des alphas legerement inferieurs a la version proprietary hexaco.org (environ 0.03 a 0.05 en dessous) du fait de l'absence d'items hautement discriminants protege par copyright — differentiel acceptable.

---

## Structure de la clé de scoring HEXACO-60

Chaque dimension = 10 items (4 facettes, 2-3 items chacune).
Items marques [R] = items inverses (reponse recodee avant calcul : 5→1, 4→2, 3→3, 2→4, 1→5).

Source de la cle : ipip.ori.org/newHEXACO_PI_key.htm + Ashton et al. (2007) Appendix.

**Note sur le wording :** Les items ci-dessous sont les items exacts de l'IPIP public domain (première personne, style descriptif court). Ils diffèrent délibérément du wording plus élaboré de la version proprietary hexaco.org — les deux mesurent les mêmes constructs (corrélations convergentes r = 0.75–0.84) mais seule la version IPIP est librement utilisable en produit commercial.

---

## Dimension 1 — Honesty-Humility (H)

**Construct :** Tendance a etre sincere et non-manipulateur dans les relations interpersonnelles, a se conformer aux regles sociales et ethiques meme en l'absence de surveillance, a ne pas etre motive par les richesses et le statut social, et a avoir une vision modeste de soi-meme.

**Facettes :** Sincerity (H:Sinc) α=.81 | Fairness (H:Fair) α=.77 | Greed-Avoidance (H:Gree) α=.69 | Modesty (H:Mode) α=.81

**Alpha attendu (dimension) :** α ≈ 0.74–0.79 (Ashton & Lee, 2009 ; Lee et al., 2018)

---

**Item Q1-H-01** | Facette: Sincerity (H:Sinc) | Inversé: Non
EN: "Don't pretend to be more than I am."

**Item Q1-H-02** | Facette: Sincerity (H:Sinc) | Inversé: Oui [R]
EN: "Use flattery to get ahead."

**Item Q1-H-03** | Facette: Sincerity (H:Sinc) | Inversé: Oui [R]
EN: "Put on a show to impress people."

**Item Q1-H-04** | Facette: Fairness (H:Fair) | Inversé: Non
EN: "Would never take things that aren't mine."

**Item Q1-H-05** | Facette: Fairness (H:Fair) | Inversé: Oui [R]
EN: "Cheat to get ahead."

**Item Q1-H-06** | Facette: Fairness (H:Fair) | Inversé: Non
EN: "Try to follow the rules."

**Item Q1-H-07** | Facette: Greed-Avoidance (H:Gree) | Inversé: Oui [R]
EN: "Love luxury."

**Item Q1-H-08** | Facette: Greed-Avoidance (H:Gree) | Inversé: Oui [R]
EN: "Am mainly interested in money."

**Item Q1-H-09** | Facette: Modesty (H:Mode) | Inversé: Non
EN: "Don't think that I'm better than other people."

**Item Q1-H-10** | Facette: Modesty (H:Mode) | Inversé: Oui [R]
EN: "Believe that I am better than others."

---

## Dimension 2 — Emotionality (E)

**Construct :** Tendance a ressentir de la peur, de l'anxiete, a avoir besoin de soutien emotionnel, et a ressentir de l'empathie. Dans HEXACO, l'Emotionality inclut des facettes de Peur et Dependance qui la distinguent du Neuroticism Big Five — elle est davantage orientee "vulnerable" que "instable emotionnellement". Les individus faibles en E sont peu affectes par le danger, emotionnellement autosuffisants et peu empathiques.

**Facettes :** Fearfulness (E:Fear) α=.84 | Anxiety (E:Anxi) α=.85 | Dependence (E:Depe) α=.73 | Sentimentality (E:Sent) α=.79

**Alpha attendu (dimension) :** α ≈ 0.78–0.83 (Ashton & Lee, 2009)

**Note maritime ICE :** E modere est optimal en environnement ICE — une E tres faible indique un manque d'empathie et une prise de risque excessive (pertinent pour Q7), une E tres haute peut signaler une vulnerabilite a l'isolement prolonge.

---

**Item Q1-E-01** | Facette: Fearfulness (E:Fear) | Inversé: Non
EN: "Am a physical coward."

**Item Q1-E-02** | Facette: Fearfulness (E:Fear) | Inversé: Non
EN: "Begin to panic when there is danger."

**Item Q1-E-03** | Facette: Fearfulness (E:Fear) | Inversé: Oui [R]
EN: "Like to do frightening things."

**Item Q1-E-04** | Facette: Anxiety (E:Anxi) | Inversé: Non
EN: "Worry about things."

**Item Q1-E-05** | Facette: Anxiety (E:Anxi) | Inversé: Oui [R]
EN: "Rarely worry."

**Item Q1-E-06** | Facette: Dependence (E:Depe) | Inversé: Non
EN: "Need reassurance."

**Item Q1-E-07** | Facette: Dependence (E:Depe) | Inversé: Non
EN: "Need the approval of others."

**Item Q1-E-08** | Facette: Sentimentality (E:Sent) | Inversé: Non
EN: "Feel others' emotions."

**Item Q1-E-09** | Facette: Sentimentality (E:Sent) | Inversé: Non
EN: "Immediately feel sad when hearing of an unhappy event."

**Item Q1-E-10** | Facette: Sentimentality (E:Sent) | Inversé: Oui [R]
EN: "Seldom get emotional."

---

## Dimension 3 — eXtraversion (X)

**Construct :** Tendance a avoir une expression sociale active, a se sentir a l'aise dans les interactions sociales, a prendre la parole facilement et a etre energique. La version IPIP de l'Extraversion comprend une facette Expressiveness (tendance a parler et a s'exprimer) là où la version proprietary hexaco.org utilise Social Self-Esteem — les deux mesurent des aspects de l'extraversion sociale mais par des items distincts.

**Facettes :** Expressiveness (X:Expr) α=.84 | Social Boldness (X:SocB) α=.86 | Sociability (X:Soci) α=.85 | Liveliness (X:Live) α=.82

**Alpha attendu (dimension) :** α ≈ 0.76–0.82 (Ashton & Lee, 2009)

---

**Item Q1-X-01** | Facette: Expressiveness (X:Expr) | Inversé: Non
EN: "Talk a lot."

**Item Q1-X-02** | Facette: Expressiveness (X:Expr) | Inversé: Oui [R]
EN: "Don't talk a lot."

**Item Q1-X-03** | Facette: Expressiveness (X:Expr) | Inversé: Oui [R]
EN: "Say little."

**Item Q1-X-04** | Facette: Social Boldness (X:SocB) | Inversé: Non
EN: "Am good at making impromptu speeches."

**Item Q1-X-05** | Facette: Social Boldness (X:SocB) | Inversé: Oui [R]
EN: "Would be afraid to give a speech in public."

**Item Q1-X-06** | Facette: Sociability (X:Soci) | Inversé: Non
EN: "Usually like to spend my free time with people."

**Item Q1-X-07** | Facette: Sociability (X:Soci) | Inversé: Oui [R]
EN: "Rarely enjoy being with people."

**Item Q1-X-08** | Facette: Liveliness (X:Live) | Inversé: Non
EN: "Am usually active and full of energy."

**Item Q1-X-09** | Facette: Liveliness (X:Live) | Inversé: Oui [R]
EN: "Tire out quickly."

**Item Q1-X-10** | Facette: Liveliness (X:Live) | Inversé: Non
EN: "Smile a lot."

---

## Dimension 4 — Agreeableness (A)

**Construct :** Dans HEXACO, l'Agreeableness capture la tendance a pardonner les offenses, a etre doux et patient plutot que susceptible et colereux. Cette dimension differe du Big Five Agreeableness : la variance liee a la sincerite et l'equite est capturee par H, pas A. L'A HEXACO est davantage une mesure de "tolerance interpersonnelle et de paix sociale" que de conformite ou de compliance.

**Facettes :** Forgiveness (A:Forg) α=.78 | Gentleness (A:Gent) α=.81 | Flexibility (A:Flex) α=.73 | Patience (A:Pati) α=.88

**Alpha attendu (dimension) :** α ≈ 0.71–0.76 (Ashton & Lee, 2009)

**Note Bell (2007) :** La formule utilise min(A) comme indicateur de la personne la plus difficile de l'equipe. Le A HEXACO est directement utilisable avec cette formule, avec une note de vigilance : la variance "cooperative" portee par H dans HEXACO n'est plus dans A — voir implications engine ci-dessous.

---

**Item Q1-A-01** | Facette: Forgiveness (A:Forg) | Inversé: Non
EN: "Am inclined to forgive others."

**Item Q1-A-02** | Facette: Forgiveness (A:Forg) | Inversé: Oui [R]
EN: "Hold a grudge."

**Item Q1-A-03** | Facette: Forgiveness (A:Forg) | Inversé: Oui [R]
EN: "Get back at people who insult me."

**Item Q1-A-04** | Facette: Gentleness (A:Gent) | Inversé: Non
EN: "Accept people as they are."

**Item Q1-A-05** | Facette: Gentleness (A:Gent) | Inversé: Oui [R]
EN: "Find fault with everything."

**Item Q1-A-06** | Facette: Flexibility (A:Flex) | Inversé: Non
EN: "Adjust easily."

**Item Q1-A-07** | Facette: Flexibility (A:Flex) | Inversé: Oui [R]
EN: "React strongly to criticism."

**Item Q1-A-08** | Facette: Flexibility (A:Flex) | Inversé: Oui [R]
EN: "Am hard to reason with."

**Item Q1-A-09** | Facette: Patience (A:Pati) | Inversé: Non
EN: "Am usually a patient person."

**Item Q1-A-10** | Facette: Patience (A:Pati) | Inversé: Oui [R]
EN: "Get angry easily."

---

## Dimension 5 — Conscientiousness (C)

**Construct :** Tendance a etre organise, diligent, perfectionniste et prudent. Le C HEXACO est hautement convergent avec le C Big Five (r ≈ 0.82–0.88 — Ashton & Lee, 2009). C est le meilleur predicteur de la performance contextuelle (Borman & Motowidlo, 1993) et de l'observance des regles de securite, particulierement critique en environnement maritime.

**Facettes :** Organization (C:Orga) α=.85 | Diligence (C:Dili) α=.81 | Perfectionism (C:Perf) α=.80 | Prudence (C:Prud) α=.80

**Alpha attendu (dimension) :** α ≈ 0.77–0.82 (Ashton & Lee, 2009)

---

**Item Q1-C-01** | Facette: Organization (C:Orga) | Inversé: Non
EN: "Keep things tidy."

**Item Q1-C-02** | Facette: Organization (C:Orga) | Inversé: Oui [R]
EN: "Leave a mess in my room."

**Item Q1-C-03** | Facette: Diligence (C:Dili) | Inversé: Non
EN: "Work hard."

**Item Q1-C-04** | Facette: Diligence (C:Dili) | Inversé: Non
EN: "Get started quickly on doing a job."

**Item Q1-C-05** | Facette: Diligence (C:Dili) | Inversé: Oui [R]
EN: "Do just enough work to get by."

**Item Q1-C-06** | Facette: Perfectionism (C:Perf) | Inversé: Non
EN: "Pay attention to details."

**Item Q1-C-07** | Facette: Perfectionism (C:Perf) | Inversé: Non
EN: "Continue until everything is perfect."

**Item Q1-C-08** | Facette: Perfectionism (C:Perf) | Inversé: Oui [R]
EN: "Pay too little attention to details."

**Item Q1-C-09** | Facette: Prudence (C:Prud) | Inversé: Non
EN: "Make plans and stick to them."

**Item Q1-C-10** | Facette: Prudence (C:Prud) | Inversé: Oui [R]
EN: "Jump into things without thinking."

---

## Dimension 6 — Openness to Experience (O)

**Construct :** Tendance a s'interesser a la nature, a l'art, aux idees abstraites, a la creativite et aux experiences non-conventionnelles. L'O HEXACO est similaire au O/Intellect Big Five, avec une facette Unconventionality (tendance a avoir des convictions inhabituelles) plus prononcee. Dans un contexte professionnel maritime, O modere est associe a l'adaptabilite, a la flexibilite cognitive et a la resolution de problemes en mer.

**Facettes :** Aesthetic Appreciation (O:AesA) α=.83 | Inquisitiveness (O:Inqu) α=.78 | Creativity (O:Crea) α=.85 | Unconventionality (O:Unco) α=.84

**Alpha attendu (dimension) :** α ≈ 0.75–0.80 (Ashton & Lee, 2009)

---

**Item Q1-O-01** | Facette: Aesthetic Appreciation (O:AesA) | Inversé: Non
EN: "Believe in the importance of art."

**Item Q1-O-02** | Facette: Aesthetic Appreciation (O:AesA) | Inversé: Non
EN: "See beauty in things that others might not notice."

**Item Q1-O-03** | Facette: Aesthetic Appreciation (O:AesA) | Inversé: Oui [R]
EN: "Do not like art."

**Item Q1-O-04** | Facette: Inquisitiveness (O:Inqu) | Inversé: Non
EN: "Am interested in science."

**Item Q1-O-05** | Facette: Inquisitiveness (O:Inqu) | Inversé: Non
EN: "Love to read challenging material."

**Item Q1-O-06** | Facette: Creativity (O:Crea) | Inversé: Non
EN: "Have a vivid imagination."

**Item Q1-O-07** | Facette: Creativity (O:Crea) | Inversé: Non
EN: "Am full of ideas."

**Item Q1-O-08** | Facette: Creativity (O:Crea) | Inversé: Oui [R]
EN: "Do not have a good imagination."

**Item Q1-O-09** | Facette: Unconventionality (O:Unco) | Inversé: Non
EN: "Am considered to be kind of eccentric."

**Item Q1-O-10** | Facette: Unconventionality (O:Unco) | Inversé: Oui [R]
EN: "Would hate to be considered odd or strange."

---

## Notes psychometriques

### Fidélité (consistance interne)

| Dimension | Alpha attendu (dimension, 10 items) | Alphas facettes (pool complet) | Source |
|---|---|---|---|
| Honesty-Humility (H) | 0.74–0.79 | Sinc=.81, Fair=.77, Gree=.69, Mode=.81 | Ashton & Lee (2009), ipip.ori.org |
| Emotionality (E) | 0.78–0.83 | Fear=.84, Anxi=.85, Depe=.73, Sent=.79 | Ashton & Lee (2009), ipip.ori.org |
| eXtraversion (X) | 0.76–0.82 | Expr=.84, SocB=.86, Soci=.85, Live=.82 | Ashton & Lee (2009), ipip.ori.org |
| Agreeableness (A) | 0.71–0.76 | Forg=.78, Gent=.81, Flex=.73, Pati=.88 | Ashton & Lee (2009), ipip.ori.org |
| Conscientiousness (C) | 0.77–0.82 | Orga=.85, Dili=.81, Perf=.80, Prud=.80 | Ashton & Lee (2009), ipip.ori.org |
| Openness (O) | 0.75–0.80 | AesA=.83, Inqu=.78, Crea=.85, Unco=.84 | Ashton & Lee (2009), ipip.ori.org |

Tous les alphas dimension sont au-dessus du seuil minimal de 0.70 requis pour les sous-echelles. Le seuil recommande pour les scores globaux (≥ 0.80) n'est atteint que pour E et C — acceptable pour un instrument de 10 items par dimension.

### Validite convergente (IPIP-HEXACO vs HEXACO-PI-R proprietary)

Ashton, Lee & Goldberg (2007) rapportent des correlations convergentes dimension-par-dimension entre l'IPIP-HEXACO et le HEXACO-PI original :
- H : r = 0.79 | E : r = 0.83 | X : r = 0.84 | A : r = 0.75 | C : r = 0.82 | O : r = 0.77

Ces correlations indiquent que la version IPIP mesure les memes constructs que la version proprietary avec une perte de validite limitee (variance partagee ≈ 59–71 %).

### Validite predictive

- C → performance au travail : r = 0.22 (meta-analyse Barrick & Mount, 1991) ; r = 0.31 (Roberts et al., 2007)
- H → reduction des comportements contre-productifs (CWB) : r = -0.43 (Lee et al., 2005)
- E (faible) → prise de risque excessive en environment ICE : reference Stuster (2010)
- X → performance contextuelle en equipes soudees : r = 0.18 (Mount et al., 1998)

### Administration

- **Format :** Likert 5 points — 1 "Strongly Disagree" a 5 "Strongly Agree"
- **Temps :** 8–12 minutes
- **Randomisation :** Randomiser l'ordre des items au sein de chaque dimension pour controler les effets d'ordre. Ne pas randomiser les dimensions entre elles sans valider l'equivalence de mesure.
- **Langue :** Items EN — traduction FR disponible mais non incluse dans ce fichier. Validite de la traduction FR non encore verifiee sur population maritime.
- **Score :** Moyenne des items par dimension apres recodage des items [R]. Score 0–100 par rescaling : `(mean - 1) / 4 * 100`.

### Droits et conditions d'utilisation

Les items IPIP sont dans le **domaine public** (Goldberg, 1999). Aucune autorisation, attribution formelle ou paiement n'est requis. La citation academique recommandee est :

> Goldberg, L.R., Johnson, J.A., Eber, H.W., Hogan, R., Ashton, M.C., Cloninger, C.R., & Gough, H.G. (2006). The International Personality Item Pool and the future of public-domain personality measures. *Journal of Research in Personality*, 40, 84–96.

Ces items IPIP sont distincts des items du HEXACO-PI-R proprietary (Ashton & Lee, hexaco.org) qui sont soumis a une licence restrictive pour usage commercial.

---

## Implications pour le pe_fit engine

### Q4 — PT Fit (Bell, 2007) : ajustements requis

La formule Bell (2007) est : `0.30 * min(A) + 0.30 * mean(C) + 0.28 * mean(ES) - 0.12 * std(C)`

Avec le passage au HEXACO, trois ajustements sont necessaires :

**A (Agreeableness) :** L'A HEXACO est directement utilisable dans la formule Bell comme proxy de l'A Big Five (r convergent ≈ 0.75). Point de vigilance : la variance liee a la sincerite/equite est maintenant dans H et non plus dans A. Le `min(A)` Bell identifie la personne la plus "abrasive" — avec HEXACO, un individu tres bas en H (manipulateur, cupide) mais moyen en A ne sera pas detecte par cette formule seule. Recommandation : ajouter un terme `min(H)` comme facteur de detection des comportements contre-productifs (`f_team.py`).

**ES (Emotional Stability) :** Big Five ES = inverse du Neuroticism. HEXACO Emotionality (E) n'est pas l'inverse exact de ES Big Five — la correlation est r ≈ -0.59 (Ashton & Lee, 2009). L'ES Big Five capture l'instabilite emotionnelle generale, l'E HEXACO capture specifiquement la peur et la dependance. Pour Bell (2007), utiliser `mean(100 - E_HEXACO)` comme proxy de ES, avec une note de vigilance sur la loss of variance.

**C (Conscientiousness) :** C HEXACO ≈ C Big Five (r ≈ 0.85). Utilisation directe, aucun ajustement requis.

**Recommandation head-of-science :** Implementer dans `pt_fit/f_team.py` :
```python
# Ajout post-HEXACO : detection comportements contre-productifs
jerk_h_flag = any(profile.H < H_THRESHOLD for profile in team_profiles)
# H_THRESHOLD = 25 (centile bas — a calibrer sur donnees)
```

### H (Honesty-Humility) : nouveau facteur sans equivalent Bell

H est la principale innovation du HEXACO vs Big Five. Sans reference empirique directe dans Bell (2007), son integration dans le moteur doit etre prudente :

**Role dans Q4 (PT Fit) :** H bas dans un membre de l'equipage est un facteur de risque de conflit (Lee et al., 2005 ; Chirumbolo et al., 2022). Recommandation : H < seuil → activer flag `jerk_potential` dans `f_team.py` (non-compensatoire, similaire au filtre "jerk" existant).

**Role dans Q5 (PO Fit) :** Les facettes Sincerity et Fairness de H sont tres proches des valeurs `honesty` et `fairness` du CES (Ravlin & Meglino, 1987). H peut servir de **predicteur trait** de l'adherence aux valeurs de l'entreprise, complementaire au questionnaire de valeurs Q5. Formule suggeree : `f_values_honesty = 0.6 * H_score + 0.4 * CES_honesty_score`.

**Role dans Q6 (PS Fit / LMX) :** Un capitaine fort en H (sincere, equitable) peut creer une friction avec un marin faible en H (manipulateur). La distance H entre capitaine et marin peut etre integree dans le vecteur LMX comme composante supplementaire. A experimenter lors du Temps 2 (phase empirique).

### Q1 comme input (pas un score de fit)

Conformement a la regle architecturale du projet : Q1 (HEXACO-60) est un **input descriptif** (`psychometric_snapshot.big_five` + `psychometric_snapshot.honesty_humility`), jamais agregee dans le `global_score`. Les 6 dimensions alimentent Q2-Q6 comme variables predictives mais ne constituent pas elles-memes une mesure de fit.

Le snapshot devra etre etendu pour inclure `H` comme 7eme dimension au cote des Big Five existants :
```python
psychometric_snapshot = {
    "big_five": {"O": 62, "C": 78, "E": 55, "A": 70, "N": 35},
    "honesty_humility": 68,  # nouveau champ HEXACO
    ...
}
```

---

## References bibliographiques

- Ashton, M.C., & Lee, K. (2007). Empirical, theoretical, and practical advantages of the HEXACO model of personality structure. *Personality and Social Psychology Review*, 11(2), 150–166.
- Ashton, M.C., Lee, K., & Goldberg, L.R. (2007). The IPIP-HEXACO scales: An alternative, public-domain measure of the personality constructs in the HEXACO model. *Personality and Individual Differences*, 42(8), 1515–1526.
- Ashton, M.C., & Lee, K. (2009). The HEXACO-60: A short measure of the major dimensions of personality. *Journal of Personality Assessment*, 91(4), 340–345.
- Barrick, M.R., & Mount, M.K. (1991). The Big Five personality dimensions and job performance: A meta-analysis. *Personnel Psychology*, 44, 1–26.
- Bell, S.T. (2007). Deep-level composition variables as predictors of team performance: A meta-analysis. *Journal of Applied Psychology*, 92(3), 595–615.
- Borman, W.C., & Motowidlo, S.J. (1993). Expanding the criterion domain to include elements of contextual performance. In N. Schmitt & W.C. Borman (Eds.), *Personnel selection in organizations* (pp. 71–98).
- Chirumbolo, A., Piccolo, A., & Mastroianni, I. (2022). Honesty-Humility and dark triad traits as predictors of counterproductive workplace behaviors. *Frontiers in Psychology*, 13.
- Goldberg, L.R., et al. (2006). The International Personality Item Pool and the future of public-domain personality measures. *Journal of Research in Personality*, 40, 84–96.
- Lee, K., Ashton, M.C., & de Vries, R.E. (2005). Predicting workplace delinquency and integrity with the HEXACO and Five-Factor Models of personality structure. *Human Performance*, 18(2), 179–197.
- Lee, K., et al. (2018). Psychometric properties of the HEXACO-100. *Assessment*, 25(5), 543–556.
- Mount, M.K., Barrick, M.R., & Stewart, G.L. (1998). Personality Five Factor Model and job performance: A meta-analytic review. *Journal of Organizational Behavior*, 19, 445–461.
- Roberts, B.W., Kuncel, N.R., Shiner, R., Caspi, A., & Goldberg, L.R. (2007). The power of personality. *Perspectives on Psychological Science*, 2(4), 313–345.
- Stuster, J. (2010). Behavioral issues associated with long-duration space expeditions. *NASA/TM-2010-216130*.
