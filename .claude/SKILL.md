# YACHT HARMONY : MOTEUR PSYCHOMÉTRIQUE & DATA SCIENCE
**Rôle de l'Agent Assistant :** Vous êtes le Data Scientist et Ingénieur Backend en charge d'implémenter l'architecture algorithmique de Yacht Harmony. L'objectif est de coder un Système d'Aide à la Décision (DSS) probabiliste pour le recrutement et le management d'équipages confinés.

## 1. VISION GLOBALE DE L'ARCHITECTURE
Le système ne fait pas de la simple addition de scores. Il modélise la thermodynamique sociale d'un équipage confiné à travers 3 modules :
1. **DNRE** : Mesure le potentiel brut et l'adéquation métier (Filtre).
2. **MLPSM** : Prédit la probabilité de survie saisonnière (Simulateur de Charge Systémique).
3. **DYADE** : Calcule l'alchimie interpersonnelle (Graphe Sociométrique).

---

## 2. SPÉCIFICATIONS MATHÉMATIQUES ET RÈGLES D'IMPLÉMENTATION (V1)

### MODULE 1 : DNRE (Dynamic Normative-Relative Engine)
**Objectif :** Évaluer le Job Fit ($S_{i,c}$) et la rareté ($Percentile$) du candidat par rapport au marché.

**Équations de base :**
* Score Expert (SME Fit) : $$S_{i,c} = \frac{\sum_{t=1}^{n} w_t \cdot x_{i,t}}{\sum_{t=1}^{n} w_t}$$
* Percentile Dynamique : $$\Pi_{i,c} = \left( \frac{cf_i + 0.5 \cdot f_i}{N} \right) \times 100$$

> ⚠️ **DIRECTIVE DE CODE V1 (CORRECTION DU FILTRE DE SÉCURITÉ)** : 
> Ne **PAS** utiliser de fonction indicatrice binaire ($\mathbb{1}$) pour éliminer les candidats sous le seuil critique (effet couperet instable). 
> **À coder :** Remplacer le produit binaire par une **fonction de pénalité continue** (courbe logistique ou spline) pour l'Indice Global Ajusté ($G_{fit\_adjusted}$). Le score doit s'effondrer progressivement à l'approche du seuil de sécurité ($S_{min}$).
### DIRECTIVE D'ÉVOLUTION FUTURE : ML POUR LE DNRE
**Vision V2 :** Les poids experts ($w_t$) du DNRE ont vocation à être remplacés par des coefficients $\beta$ appris par Machine Learning (Validité Prédictive).
> ⚠️ **DIRECTIVE D'ARCHITECTURE V1** : 
> L'architecture de la base de données DOIT séparer le dictionnaire des poids (`JOB_PROFILES_NORM`) du code de calcul. Les poids $w_t$ ne doivent jamais être "hardcodés" dans les fonctions. Ils doivent être appelés dynamiquement depuis la base de données. 
> Cela permettra, en V2, à un script de Machine Learning de mettre à jour ces valeurs de poids automatiquement la nuit sans toucher au code backend de l'API.

### MODULE 2 : MLPSM (Multi-Level Predictive Stability Model)
**Objectif :** Prédire la probabilité de rétention (Régression Logistique) en évitant la sur-paramétrisation lors du "Cold Start" (démarrage à froid < 500 cas).

**Équation Maîtresse :**
$$Y_{success} = \beta_1 P_{ind} + \beta_2 F_{team} + \beta_3 F_{env} + \beta_4 F_{lmx} + \beta_5 (F_{env} \times TypeYacht) + \epsilon$$
$$P(success) = \frac{1}{1 + e^{-Y}}$$

**Composantes & Directives V1 :**
* **Individu ($P_{ind}$) :** $$P_{ind} = \omega_1 GCA + \omega_2 C + \omega_3 (GCA \times C)$$
* **Équipe ($F_{team}$) :** > ⚠️ **DIRECTIVE DE CODE V1** : Désactiver le calcul du $Faultline_{index}$ pour la V1 afin d'éviter l'overfitting. L'équation simplifiée à coder est : $$F_{team} = w_a \min(A_i) - w_c \sigma(C_i) + w_e \mu(ES_i)$$
* **Environnement ($F_{env}$) :** $$F_{env} = \frac{R_{yacht}}{D_{yacht}} \times Resilience_{ind}$$
    *Note technique : Dans notre modèle, le ratio est Ressources/Demandes (mesure du confort) et non Demandes/Ressources.*
* **Leadership ($F_{lmx}$) :** Distance Euclidienne entre le style du capitaine et les valeurs du marin. $$F_{lmx} = 1 - \frac{||L_{capt} - V_{crew}||_2}{d_{max}}$$

### MODULE 3 : L'ÉQUATION DE LA DYADE
**Objectif :** Gérer l'affectation des cabines et des quarts en mesurant l'alchimie entre deux marins.

> ⚠️ **DIRECTIVE DE CODE V1 (AJOUT DE PONDÉRATION)** :
> L'addition simple n'est pas réaliste (50/50). L'implémentation doit intégrer des coefficients de pondération ($\alpha$ et $\beta$) pour donner plus de poids à la similitude des valeurs qu'à la complémentarité sociale.
> **À coder :** $$D_{ij} = \alpha \underbrace{\left( 1 - \frac{|C_i - C_j|}{max\_diff} \right)}_{\text{Similitude (Valeurs)}} + \beta \underbrace{f(E_i + E_j)}_{\text{Complémentarité (Énergie)}}$$

---

## 3. PRINCIPES DE DÉVELOPPEMENT POUR L'AGENT
1. **Évolutivité (Scalability) :** Le code doit permettre de mettre à jour les poids ($\beta$, $\omega$, $\alpha$) facilement via une base de données ou un fichier de configuration, car ils seront calibrés par Machine Learning une fois les 500 premiers recrutements atteints.
2. **Modularité :** Séparer le calcul du DNRE (Sourcing) du MLPSM (Simulation Équipe) dans des services distincts.
3. **Robustesse :** Gérer correctement les divisions par zéro ou les vecteurs vides dans les calculs de distance euclidienne ou de variance.