# backend/services/sme_profiles.py

# Mapping des traits par catégorie
CATEGORY_MAPPING = {
    "personality": ["extraversion", "agreeableness", "openness", "neuroticism", "conscientiousness"],
    "motivation": ["intrinsic", "extrinsic_social", "extrinsic_material", "identified", "introjected", "amotivation"],
    "cognitive": ["numerical", "logical", "verbal"]
}

TRAIT_DEFINITIONS = {
    # Personnalité
    "extraversion": "Tendance à être sociable, énergique et orienté vers les interactions sociales. Une personne extravertie s'épanouit dans les échanges et les activités de groupe, tandis qu'une personne introvertie préfère la solitude et la réflexion.",
    "agreeableness": "Capacité à être coopératif, empathique et soucieux de l'harmonie sociale. Une personne agréable évite les conflits et privilégie la bienveillance, tandis qu'une personne moins agréable peut être plus directe ou compétitive.",
    "conscientiousness": "Niveau d'organisation, de persévérance et de fiabilité. Une personne consciencieuse est méthodique et ponctuelle, tandis qu'une personne moins consciencieuse peut être plus spontanée ou désorganisée.",
    "neuroticism": "Sensibilité aux émotions négatives comme l'anxiété, l'irritabilité ou la tristesse. Une personne avec un haut niveau de névrosisme réagit fortement au stress, tandis qu'une personne stable émotionnellement reste calme sous pression.",
    "openness": "Ouverture à la curiosité, à la créativité et aux nouvelles expériences. Une personne ouverte est imaginative et flexible, tandis qu'une personne moins ouverte préfère la routine et les solutions éprouvées.",

    # Cognitive
    "numerical": "Capacité à comprendre, analyser et manipuler des données numériques. Une personne avec une forte aptitude numérique excelle dans les calculs et l'analyse de données.",
    "logical": "Aptitude à analyser des problèmes complexes et à identifier des schémas logiques. Une personne logique excelle dans la résolution de problèmes structurés et la planification stratégique.",
    "verbal": "Capacité à comprendre et utiliser le langage de manière précise et efficace. Une personne avec une forte aptitude verbale s'exprime clairement et adapte son discours à son audience.",

    # Motivation
    "intrinsic": "Motivation interne liée au plaisir et à la satisfaction de réaliser une activité pour elle-même. Une personne intrinsèquement motivée agit par passion ou curiosité.",
    "extrinsic_social": "Motivation externe liée à la reconnaissance sociale, à l'appartenance ou au statut. Une personne motivée socialement cherche l'approbation et la collaboration avec les autres.",
    "extrinsic_material": "Motivation externe liée aux récompenses tangibles comme le salaire, les bonus ou la sécurité financière. Une personne motivée matériellement valorise les bénéfices concrets.",
    "identified": "Motivation où l'individu adopte une tâche parce qu'il la juge importante, même si elle n'est pas plaisante. Il agit en alignement avec ses valeurs ou objectifs personnels.",
    "introjected": "Motivation où l'individu agit pour éviter la culpabilité ou la honte, souvent en réponse à des attentes internes. Il se sent poussé par une pression personnelle plutôt que par le plaisir.",
    "amotivation": "Absence de motivation, caractérisée par un manque d'intention ou de raison d'agir. L'individu peut se sentir désengagé ou dépassé par les tâches."
}

# Configuration des polarités
TRAIT_POLARITY = {
    # Personnalité
    "extraversion": "high",          # Un niveau élevé favorise les interactions sociales et le leadership
    "agreeableness": "high",         # Un niveau élevé favorise la coopération et l'harmonie
    "conscientiousness": "high",     # Un niveau élevé favorise l'organisation et la fiabilité
    "openness": "high",              # Un niveau élevé favorise la créativité et l'adaptabilité
    "neuroticism": "low",            # Un niveau bas favorise la stabilité émotionnelle et la résilience

    # Cognitive
    "numerical": "high",             # Un niveau élevé favorise l'analyse et la gestion des données
    "logical": "high",               # Un niveau élevé favorise la résolution de problèmes complexes
    "verbal": "high",                # Un niveau élevé favorise la communication et la compréhension

    # Motivation
    "intrinsic": "high",             # Un niveau élevé favorise l'engagement et la satisfaction personnelle
    "extrinsic_social": "high",      # Un niveau élevé favorise la collaboration et la reconnaissance sociale
    "extrinsic_material": "moderate", # Un niveau modéré est idéal : trop élevé peut nuire à la qualité, trop bas peut réduire la motivation
    "identified": "high",             # Un niveau élevé favorise l'alignement avec les valeurs personnelles
    "introjected": "low",            # Un niveau bas réduit la pression interne et favorise un engagement sain
    "amotivation": "low",            # Un niveau bas est toujours préférable pour éviter le désengagement
}

# Profils idéaux par poste (exemples fictifs)
SME_PROFILES = {
    "Captain": {
        "personality": {"conscientiousness": 95, "neuroticism": 15, "extraversion": 75, "agreeableness": 70, "openness": 80},
        "motivation": {"intrinsic": 90, "identified": 85, "extrinsic_material": 60, "amotivation": 0},
        "cognitive": {"logical": 90, "verbal": 85, "numerical": 80}
    },
    "First Mate": {
        "personality": {"conscientiousness": 90, "neuroticism": 20, "extraversion": 70, "agreeableness": 75, "openness": 75},
        "motivation": {"intrinsic": 85, "identified": 80, "extrinsic_material": 65, "amotivation": 0},
        "cognitive": {"logical": 85, "verbal": 80, "numerical": 85}
    },
    "Bosun": {
        "personality": {"conscientiousness": 85, "neuroticism": 25, "extraversion": 65, "agreeableness": 80, "openness": 60},
        "motivation": {"intrinsic": 80, "identified": 85, "extrinsic_material": 70, "amotivation": 0},
        "cognitive": {"logical": 75, "verbal": 60, "numerical": 70}
    },
    "Deckhand": {
        "personality": {"conscientiousness": 80, "neuroticism": 30, "extraversion": 60, "agreeableness": 85, "openness": 50},
        "motivation": {"identified": 90, "extrinsic_social": 80, "extrinsic_material": 75, "amotivation": 0},
        "cognitive": {"logical": 65, "verbal": 60, "numerical": 60}
    },
    "Chief Engineer": {
        "personality": {"conscientiousness": 98, "neuroticism": 10, "extraversion": 40, "agreeableness": 65, "openness": 70},
        "motivation": {"intrinsic": 95, "identified": 80, "extrinsic_material": 60, "amotivation": 0},
        "cognitive": {"logical": 95, "numerical": 95, "verbal": 70}
    },
    "2nd Engineer": {
        "personality": {"conscientiousness": 90, "neuroticism": 15, "extraversion": 45, "agreeableness": 70, "openness": 70},
        "motivation": {"intrinsic": 90, "identified": 85, "extrinsic_material": 65, "amotivation": 0},
        "cognitive": {"logical": 90, "numerical": 90, "verbal": 65}
    },
    "Chief Stewardess": {
        "personality": {"conscientiousness": 95, "neuroticism": 20, "extraversion": 85, "agreeableness": 90, "openness": 80},
        "motivation": {"intrinsic": 85, "identified": 90, "extrinsic_social": 90, "amotivation": 0},
        "cognitive": {"verbal": 90, "logical": 75, "numerical": 70}
    },
    "Stewardess": {
        "personality": {"conscientiousness": 85, "neuroticism": 25, "extraversion": 80, "agreeableness": 95, "openness": 75},
        "motivation": {"extrinsic_social": 95, "identified": 80, "extrinsic_material": 70, "amotivation": 0},
        "cognitive": {"verbal": 85, "logical": 60, "numerical": 60}
    },
    "Chef": {
        "personality": {"conscientiousness": 90, "neuroticism": 35, "extraversion": 50, "agreeableness": 60, "openness": 95},
        "motivation": {"intrinsic": 98, "identified": 70, "extrinsic_material": 60, "amotivation": 0},
        "cognitive": {"logical": 80, "verbal": 70, "numerical": 75}
    }
}

# Version normalisée (minuscules) pour faciliter la recherche
JOB_PROFILES_NORM = {k.lower(): v for k, v in SME_PROFILES.items()}