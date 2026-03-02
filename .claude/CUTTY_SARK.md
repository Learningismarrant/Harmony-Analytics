Spécifications Techniques : Implémentation de l'Assessment CUTTY SARK (T-IRT)
1. Contexte du Projet
Projet : Harmony Analytics

Objectif : Évaluation psychométrique Big Five pour le recrutement dans le Yachting.

Méthodologie : Modèle de Choix Forcé (Ipsatif) utilisant la Théorie de Réponse aux Items Thurstonienne (T-IRT) pour générer des scores normatifs (Z-scores).

2. Architecture des Données (Input)
L'IA doit utiliser le JSON des 60 paires généré précédemment. Chaque paire oppose deux items de domaines différents du Big Five (O, C, E, A, N).

Structure d'un item de réponse :

interface AssessmentResponse {
  pair_id: string;      // ID de la paire (P01 à P60)
  chosen_side: 'left' | 'right';
  timestamp: number;
}
3. Paramètres Psychométriques (Calibration)Pour le scoring, l'IA doit intégrer une table de paramètres d'ancrage (basée sur Maples et al., 2014). Chaque affirmation de l'IPIP-120 possède :$\lambda$ (Loading/Poids) : Sensibilité de l'item vis-à-vis de son trait latent (généralement entre 0.5 et 1.5).$\mu$ (Intercept/Difficulté) : Niveau de désirabilité sociale intrinsèque de l'item.Trait : Le domaine associé (O, C, E, A ou N).4. Algorithme de Scoring : Thurstonian IRT (T-IRT)L'objectif est de trouver le vecteur de traits latents $\theta = [\theta_O, \theta_C, \theta_E, \theta_A, \theta_N]$ qui maximise la vraisemblance des réponses observées.Étape A : Fonction de probabilité ProbitPour chaque paire $l$ opposant l'item $i$ et l'item $j$, la probabilité que le candidat choisisse $i$ est :$$P(y_l = 1 | \theta_i, \theta_j) = \Phi \left( \frac{(\mu_i - \mu_j) + (\lambda_i \theta_i - \lambda_j \theta_j)}{\sqrt{\psi_i^2 + \psi_j^2}} \right)$$Où $\Phi$ est la fonction de répartition de la loi normale centrée réduite, et $\psi$ est la variance résiduelle.Étape B : Estimation par Maximum a Posteriori (MAP)L'algorithme doit implémenter une fonction d'optimisation (type Newton-Raphson ou BFGS) pour maximiser la fonction de log-vraisemblance :$$\log L(\theta) = \sum_{l=1}^{60} \ln P(y_l | \theta) + \log P(\theta)$$Note : $P(\theta)$ est une distribution a priori normale $N(0,1)$ pour chaque trait.5. Instructions d'implémentation (Pseudo-code)Classe TirtScoringEngineInitialize : Charger les paramètres d'items ($\mu, \lambda$) pour les 120 affirmations.Pre-process : Transformer les AssessmentResponse[] en un vecteur de résultats binaires.Optimize : - Utiliser une bibliothèque de calcul numérique (ex: mathjs en TS ou scipy.optimize en Python).Définir la fonction de coût (Log-Likelihood négative).Lancer l'optimisation à partir de $\theta = [0, 0, 0, 0, 0]$.Normalize : Convertir les valeurs finales de $\theta$ en Z-scores standardisés et en Centiles pour l'affichage UI.6. Sortie attendue (Output API)Le moteur de scoring doit renvoyer un objet structuré pour alimenter le sociogramme Harmony :
{
  "candidate_id": "uuid",
  "scores": {
    "O": { "z_score": 0.45, "percentile": 67 },
    "C": { "z_score": 1.2, "percentile": 88 },
    "E": { "z_score": -0.3, "percentile": 38 },
    "A": { "z_score": 0.8, "percentile": 79 },
    "N": { "z_score": -1.1, "percentile": 13 }
  },
  "reliability_index": 0.94, // Basé sur l'erreur standard de mesure
  "test_duration_seconds": 285
}

