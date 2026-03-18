# backend/app/content/advice/advice_candidate.py
"""
Conseils gap analysis pour le candidat — affichage post-test sur mobile.

Structure par trait et par bande de gap :
  - "strength"   : score >= sme_target − 10 (aligné ou au-dessus du profil cible)
  - "developing" : écart modéré de −10 à −25 pts sous la cible
  - "gap"        : écart important > −25 pts sous la cible
  - "too_high"   : score > sme_target + 15 pts (nettement au-dessus)

Ancrage scientifique :
  - Barrick & Mount (1991) — Big Five et performance au travail
  - Deci & Ryan (2000) — Self-Determination Theory, continuum motivationnel
  - Judge & Bono (2001) — Core self-evaluations et stabilité émotionnelle
  - Cattell-Horn-Carroll — Raisonnement fluide (Gf) et performance en situation nouvelle
  - Van Vianen & De Dreu (2001) — Agreeableness et cohésion d'équipe
"""

CANDIDATE_GAP_ADVICE: dict[str, dict[str, str]] = {

    # =========================================================================
    # BIG FIVE — PERSONNALITE
    # =========================================================================

    "conscientiousness": {
        # Barrick & Mount (1991) : premier prédicteur universel de la performance
        # dans tous les métiers, y compris ceux à forte contrainte opérationnelle.
        "strength": (
            "Votre niveau de rigueur et de fiabilité correspond pleinement aux attentes "
            "de ce poste. À bord, cette constance se traduit directement en sécurité "
            "pour l'équipage et en confiance pour l'armateur. Continuez à ancrer "
            "vos routines opérationnelles dans vos quarts."
        ),
        "developing": (
            "Ce poste exige une persistance comportementale soutenue, notamment sur les "
            "procédures de maintenance préventive et les checklists de sécurité. "
            "Adoptez un carnet de bord personnel pour tracer vos engagements quotidiens "
            "et fermer chaque tâche avant de passer à la suivante — c'est un réflexe "
            "que les meilleurs officiers construisent délibérément."
        ),
        "gap": (
            "La rigueur opérationnelle est non-négociable en mer : un équipement "
            "non vérifié ou une procédure sautée peut engager la sécurité du navire. "
            "Commencez par systématiser une chose : terminez chaque quart avec une "
            "checklist complétée et signée. Cette habitude seule, ancrée sur 21 jours, "
            "reconfigure durablement votre rapport à la rigueur."
        ),
        "too_high": (
            "Votre niveau d'organisation est un atout opérationnel majeur. "
            "En situation de haute pression ou de décision rapide, assurez-vous que "
            "votre exigence de complétude ne freine pas la fluidité collective — "
            "en mer, une décision bonne et rapide vaut souvent mieux qu'une décision "
            "parfaite et tardive."
        ),
    },

    "agreeableness": {
        # Van Vianen & De Dreu (2001) : l'agreeableness prédit la cohésion d'équipe
        # et la réduction des conflits relationnels dans les groupes de travail restreints.
        "strength": (
            "Votre capacité à coopérer et à maintenir l'harmonie correspond bien "
            "au profil attendu. À bord, cela se traduit par une communication fluide "
            "lors des rotations de quart et une intégration rapide dans tout équipage. "
            "Cet atout est particulièrement visible dans les interactions avec les guests."
        ),
        "developing": (
            "La vie à bord repose sur une interdépendance forte : l'irritabilité ou "
            "le retrait dans un espace confiné s'amplifient vite. Entraînez-vous à "
            "reformuler les désaccords sur les faits plutôt que sur les personnes, "
            "et à proposer une solution concrète dans le même souffle. "
            "C'est la base de la communication non-violente en situation de quart."
        ),
        "gap": (
            "Dans un équipage de 8 à 20 personnes en espace restreint, les tensions "
            "relationnelles non gérées escaladent rapidement. Concentrez-vous sur un "
            "comportement observable : terminez chaque interaction tendue par une "
            "question ouverte vers l'autre. Cette posture d'écoute active rompt "
            "les cycles de friction et restaure la coopération opérationnelle."
        ),
        "too_high": (
            "Votre bienveillance est un vrai levier de cohésion d'équipage. "
            "Veillez cependant à ne pas absorber les conflits au détriment de vos "
            "propres limites : en mer, savoir refuser une demande inappropriée — "
            "avec calme et fermeté — est aussi une compétence professionnelle. "
            "L'assertivité protège autant l'équipe que vous-même."
        ),
    },

    "extraversion": {
        "strength": (
            "Votre aisance relationnelle correspond aux exigences du poste, "
            "que ce soit pour coordonner l'équipe pendant une manœuvre ou assurer "
            "une présence rassurante auprès des guests. Cette énergie sociale "
            "est un accélérateur d'intégration dans tout nouvel équipage."
        ),
        "developing": (
            "Ce poste implique des interactions régulières — briefings d'équipage, "
            "accueil des passagers, coordination de pont. Si vous fonctionnez mieux "
            "en retrait, préparez deux ou trois points précis avant chaque briefing "
            "pour prendre la parole avec intention. L'extraversion opérationnelle "
            "s'entraîne par des rituels, pas par la personnalité."
        ),
        "gap": (
            "À bord, l'isolement relationnel devient visible très rapidement dans "
            "un équipage de taille réduite. Fixez-vous un objectif concret : "
            "initier au moins un échange non-opérationnel par quart avec un collègue "
            "ou un guest. Ce geste simple renforce le lien d'équipage et votre "
            "visibilité professionnelle sans forcer une sociabilité qui ne vous "
            "est pas naturelle."
        ),
        "too_high": (
            "Votre énergie sociale dynamisera l'équipage. Cultivez aussi les moments "
            "de silence actif : écouter jusqu'au bout avant de répondre, "
            "laisser les autres terminer leurs briefings, gérer les guests en "
            "laissant des silences. Dans les espaces confinés, savoir occuper moins "
            "d'espace sonore est une compétence à part entière."
        ),
    },

    "neuroticism": {
        # Score brut : haut = instable. Les conseils ci-dessous sont formulés
        # en termes de stabilité émotionnelle pour le candidat.
        # "too_low" sur neuroticism = très stable = bon signal.
        # "too_high" sur neuroticism = instabilité = le problème principal.
        "strength": (
            "Votre stabilité émotionnelle est solide. En situation d'urgence à bord "
            "— avarie moteur, météo dégradée, guest difficile — vous resterez "
            "un point d'ancrage pour l'équipage. C'est une ressource rare "
            "que les capitaines et les chefs de service reconnaissent immédiatement."
        ),
        "developing": (
            "Sous pression soutenue (longue traversée, quart de nuit, conflit à bord), "
            "une légère réactivité émotionnelle peut affecter vos décisions et "
            "l'ambiance d'équipe. Intégrez une routine de régulation simple : "
            "trois respirations diaphragmatiques avant de répondre à une situation "
            "stressante. Ce micro-rituel ancre la réponse choisie plutôt que "
            "la réaction automatique."
        ),
        "gap": (
            "À bord, la gestion des émotions sous contrainte est une compétence "
            "critique : un quart de 12 heures en mer agitée ou un guest exigeant "
            "peut épuiser les ressources d'un profil très réactif. "
            "Travaillez en priorité sur la distinction entre signal (information "
            "utile du stress) et bruit (rumination, escalade émotionnelle). "
            "Une pratique de débrief quotidien — noter 3 faits, 1 émotion, "
            "1 action — restructure durablement cette réactivité."
        ),
        "too_high": (
            "Votre sens de l'anticipation émotionnelle peut être un atout "
            "si vous l'orientez vers la détection des risques plutôt que vers "
            "la rumination. Veillez à ne pas suranalyser les situations avant "
            "qu'elles n'arrivent — en mer, l'action juste et rapide prime souvent "
            "sur l'analyse exhaustive."
        ),
    },

    "emotional_stability": {
        # Clé utilisée dans le snapshot (= 100 − neuroticism).
        # Conseils formulés directement en termes positifs de stabilité.
        # Judge & Bono (2001) : emotional stability corrèle avec la performance
        # et la satisfaction au travail dans des environnements à forte pression.
        "strength": (
            "Votre stabilité émotionnelle correspond pleinement au profil attendu. "
            "Elle vous permet d'absorber la pression opérationnelle à bord "
            "sans la retransmettre à l'équipe — une qualité que les capitaines "
            "et armateurs valorisent au premier chef pour les postes à responsabilité."
        ),
        "developing": (
            "Un niveau de stabilité légèrement inférieur à la cible signifie que "
            "certains contextes — manque de sommeil, décision rapide, conflict "
            "avec un collègue — peuvent affecter temporairement votre régulation. "
            "Identifiez vos déclencheurs personnels et préparez une réponse "
            "comportementale prédéfinie pour chacun. La stabilité émotionnelle "
            "opérationnelle est une compétence entraînable."
        ),
        "gap": (
            "En environnement maritime confiné, la stabilité émotionnelle est "
            "un prérequis de sécurité : une régulation fragile affecte la prise "
            "de décision, la cohésion d'équipe et la relation aux guests. "
            "Commencez par un journal de bord émotionnel — deux lignes par quart, "
            "sur 30 jours. Cette pratique développe la conscience de soi qui est "
            "le premier levier de régulation durable."
        ),
        "too_high": (
            "Une stabilité émotionnelle très élevée est un atout solide. "
            "Assurez-vous qu'elle ne masque pas une déconnexion des signaux "
            "d'alerte de l'équipe : rester attentif aux tensions des autres, "
            "même quand vous-même restez calme, est une composante clé "
            "de l'intelligence émotionnelle en leadership."
        ),
    },

    "openness": {
        "strength": (
            "Votre curiosité et votre adaptabilité correspondent bien à un métier "
            "où chaque destination, chaque équipage et chaque armateur redéfinissent "
            "les attentes. Cette ouverture est un moteur d'apprentissage continu "
            "— une ressource précieuse pour évoluer rapidement dans la hiérarchie "
            "maritime."
        ),
        "developing": (
            "Ce poste exige une capacité d'adaptation aux protocoles variés "
            "(standards d'armateur, nationalités d'équipage, routes inédites). "
            "Exposez-vous délibérément à des contextes nouveaux entre deux contrats : "
            "un stage dans un département différent, une formation technique inédite. "
            "L'adaptabilité s'entretient par la pratique de la nouveauté."
        ),
        "gap": (
            "L'industrie du yachting de luxe est en mutation permanente — "
            "nouvelles technologies de navigation, normes environnementales, "
            "attentes guests en évolution. Si vous préférez fortement les "
            "méthodes éprouvées, commencez par adopter une nouveauté opérationnelle "
            "par contrat : un nouvel outil de navigation, une procédure révisée. "
            "Ce rythme progressif développe la flexibilité sans déstabiliser "
            "vos routines."
        ),
        "too_high": (
            "Votre créativité est un moteur d'innovation à bord. "
            "Veillez à la canaliser dans les marges autorisées : en mer, "
            "les procédures de sécurité et les protocoles de l'armateur "
            "ne sont pas des suggestions. Distinguez les espaces où innover "
            "est un atout (service, itinéraire, convivialité) de ceux "
            "où la conformité protège l'équipage."
        ),
    },

    # =========================================================================
    # MOTIVATION — R-MAWS (Self-Determination Theory, Deci & Ryan 2000)
    # =========================================================================

    "intrinsic": {
        # Deci & Ryan (2000) : la motivation intrinsèque prédit la persistance,
        # l'engagement et la performance dans les environnements autonomes.
        "strength": (
            "Vous trouvez un intérêt et un plaisir réels dans votre métier — "
            "c'est le moteur de motivation le plus durable selon la théorie de "
            "l'autodétermination. En mer, lors des longues traversées ou des "
            "contrats exigeants, cette flamme intrinsèque maintient votre niveau "
            "d'engagement quand les récompenses externes s'estompent."
        ),
        "developing": (
            "Si votre motivation intrinsèque est en dessous du profil cible, "
            "recentrez-vous sur ce qui vous a amené à ce métier. "
            "Identifiez deux ou trois tâches du poste qui vous engagent vraiment "
            "— naviguer de nuit, maîtriser un système technique, servir un dîner "
            "d'excellence — et cherchez à les réaliser avec un niveau de maîtrise "
            "croissant. La compétence nourrit l'intérêt."
        ),
        "gap": (
            "Un niveau d'engagement intrinsèque faible dans un métier aussi "
            "exigeant que le yachting de luxe rend les longues missions difficiles "
            "à tenir. Posez-vous la question directement : qu'est-ce qui, "
            "dans ce secteur ou ce type de poste, pourrait réellement vous captiver ? "
            "Chercher ce point d'ancrage — même étroit — est la première étape "
            "pour construire une motivation durable."
        ),
        "too_high": (
            "Votre engagement profond est un atout remarquable. "
            "Assurez-vous que cette passion ne vous isole pas des contraintes "
            "collectives : à bord, l'excellence individuelle passe toujours "
            "par la synchronisation avec l'équipe. Distribuez votre énergie "
            "entre votre domaine de passion et les tâches de soutien collectif."
        ),
    },

    "identified": {
        # Deci & Ryan (2000) : la régulation identifiée = adhésion aux valeurs
        # de l'activité sans pression externe. Prédicteur fort de persistance.
        "strength": (
            "Vous agissez parce que vous croyez à ce que vous faites — "
            "pas seulement pour le salaire ou la reconnaissance. "
            "Cette régulation autonome est un prédicteur fort de persistance "
            "dans les contrats longs et les environnements isolés. "
            "C'est la marque des marins qui font carrière."
        ),
        "developing": (
            "Clarifiez le lien entre vos tâches quotidiennes et vos valeurs "
            "professionnelles profondes. Exemple concret : si la sécurité maritime "
            "compte pour vous, chaque checklist effectuée n'est plus une contrainte "
            "administrative — c'est un acte de responsabilité. "
            "Ce cadrage transforme les tâches répétitives en engagement."
        ),
        "gap": (
            "Sans connexion claire entre votre travail et ce qui compte pour vous, "
            "les contrats longs deviennent une épreuve d'endurance pure. "
            "Listez par écrit trois valeurs qui guident votre vie professionnelle, "
            "puis identifiez comment chacune se manifeste — même partiellement — "
            "dans le poste visé. Ce travail de sens est le fondement "
            "d'un engagement qui tient sur la durée."
        ),
        "too_high": (
            "Votre fort alignement avec vos valeurs est une force de caractère. "
            "Veillez à ce qu'il ne génère pas une rigidité dans les contextes "
            "où les règles de l'armateur ou les attentes de l'équipe "
            "divergent légèrement de vos convictions. "
            "La flexibilité dans l'expression de vos valeurs est aussi une maturité."
        ),
    },

    "extrinsic_social": {
        "strength": (
            "Votre sensibilité à la reconnaissance et à l'appartenance "
            "correspond au profil attendu. À bord, cet ancrage social favorise "
            "une intégration rapide dans l'équipage et une attention naturelle "
            "au moral collectif — des atouts précieux sur les contrats longs."
        ),
        "developing": (
            "La dynamique sociale d'un équipage est une ressource motivationnelle "
            "forte, surtout lors des traversées isolées. Investissez dans les "
            "rituels collectifs à bord : repas d'équipage, débriefs informels, "
            "célébration des petites victoires. Ce lien social nourrit "
            "votre énergie sur la durée."
        ),
        "gap": (
            "Si la reconnaissance sociale ne vous importe pas, "
            "assurez-vous que vous avez d'autres sources de motivation stables "
            "pour les contrats de longue durée en milieu isolé. "
            "L'absence de retour social peut, à terme, éroder l'engagement. "
            "Identifiez une source de feedback — même auto-évaluation hebdomadaire "
            "— pour maintenir votre cap."
        ),
        "too_high": (
            "Un fort besoin de validation sociale peut rendre les périodes "
            "sans retour explicite (traversées isolées, capitaine peu expressif) "
            "difficiles à tenir. Développez votre capacité à vous auto-évaluer : "
            "définissez vos propres critères de réussite pour chaque quart "
            "et évaluez-vous vous-même à la fin. "
            "L'autonomie de jugement est une protection en environnement confiné."
        ),
    },

    "extrinsic_material": {
        "strength": (
            "Votre rapport équilibré aux récompenses matérielles correspond "
            "au profil cible. Vous pouvez vous engager pleinement dans le travail "
            "sans que la variable financière ne prenne le dessus sur la qualité "
            "ou la cohésion d'équipe."
        ),
        "developing": (
            "Si les récompenses tangibles ne constituent pas un levier naturel, "
            "appuyez-vous sur d'autres moteurs — maîtrise technique, impact visible, "
            "progression de carrière. Discutez avec votre capitaine ou armateur "
            "des opportunités de développement pour relier votre engagement "
            "à une progression concrète au-delà du salaire."
        ),
        "gap": (
            "Un faible ancrage dans les récompenses matérielles peut fragiliser "
            "l'engagement dans les phases moins stimulantes (hivernage, maintenance). "
            "Identifiez les bénéfices non-financiers du poste qui vous motivent "
            "réellement — destinations, formation, réseau — et utilisez-les "
            "comme ancre pendant les périodes creuses."
        ),
        "too_high": (
            "Une forte orientation vers les récompenses matérielles peut orienter "
            "les décisions vers le gain à court terme au détriment de la qualité "
            "de service ou de la cohésion d'équipe. "
            "À bord d'un superyacht, la réputation professionnelle est votre "
            "capital long terme — elle se construit sur la qualité du travail, "
            "pas sur l'optimisation des tips."
        ),
    },

    "introjected": {
        # Deci & Ryan (2000) : régulation introjectée = pression interne,
        # culpabilité, ego — forme de motivation contrôlée, non autonome.
        # Score idéal : bas à modéré. Score élevé = problème.
        "strength": (
            "Votre niveau de pression interne se situe dans une plage saine : "
            "vous êtes exigeant envers vous-même sans que cette exigence "
            "ne se transforme en source d'anxiété chronique. "
            "Cet équilibre favorise la performance durable en mission longue."
        ),
        "developing": (
            "Une pression interne modérément élevée peut être canalisée "
            "en énergie de performance si elle reste orientée vers l'action "
            "plutôt que la rumination. Distinguez ce que vous pouvez contrôler "
            "(votre préparation, votre comportement) de ce que vous ne pouvez pas "
            "(la météo, les guests, les décisions du capitaine). "
            "Agissez sur le premier, lâchez le second."
        ),
        "gap": (
            "Un niveau d'autocontrainte élevé — agir par culpabilité ou pour "
            "éviter la honte — est épuisant en mission longue et nuit "
            "à la qualité des décisions sous pression. "
            "Remplacez progressivement les 'je dois' par des 'je choisis' : "
            "ce glissement lexical reflète et renforce un rapport plus autonome "
            "à vos responsabilités, avec moins de charge émotionnelle résiduelle."
        ),
        "too_high": (
            "Cette section ne s'applique pas dans ce sens pour ce trait — "
            "voir la logique inversée de 'introjected' dans la documentation moteur."
        ),
    },

    "amotivation": {
        # Score idéal SME : proche de 0. Un score élevé est le problème.
        # Les bandes gap/developing/too_high correspondent à un score TROP ÉLEVÉ.
        "strength": (
            "Votre niveau d'amotivation est très bas — c'est exactement "
            "ce qu'on attend. Vous abordez vos missions avec une intention "
            "claire et un engagement de fond. En mer, lors des longues traversées, "
            "c'est cette boussole interne qui fait la différence."
        ),
        "developing": (
            "Un niveau d'amotivation légèrement présent signifie que certains "
            "aspects du poste vous semblent peu porteurs de sens. "
            "Identifiez ces zones précisément et cherchez à les relier "
            "à un résultat concret qui compte pour vous ou pour l'équipe. "
            "Même une tâche ingrate prend du sens si son lien à la sécurité "
            "ou à la qualité collective est rendu visible."
        ),
        "gap": (
            "Un score d'amotivation élevé est un signal sérieux : "
            "il indique une absence d'intention d'agir, ce qui ne tient pas "
            "dans les conditions exigeantes du yachting de luxe. "
            "Avant de vous engager dans un contrat long, prenez le temps "
            "d'identifier ce qui, dans ce secteur ou ce poste, peut "
            "réellement vous engager. Accepter une mission sans ancrage "
            "motivationnel clair est risqué pour vous et pour l'équipe."
        ),
        "too_high": (
            "Voir 'gap' — pour ce trait, 'too_high' et 'gap' renvoient "
            "au même problème : un score élevé d'amotivation est toujours "
            "un signal d'alerte, quelle que soit la magnitude."
        ),
    },

    # =========================================================================
    # COGNITIF — COG-IQ (IPIP-120 cognitive subscores)
    # =========================================================================

    "numerical": {
        "strength": (
            "Vos capacités numériques sont au niveau attendu pour ce poste. "
            "En navigation, gestion du carburant, calcul de marges de sécurité "
            "ou lecture de bilans financiers de navire — vous opérez avec "
            "la précision que ce type de poste requiert."
        ),
        "developing": (
            "Une marge de progression numérique reste à combler. "
            "Entraînez-vous sur des cas concrets du métier : calcul de consommation "
            "carburant, gestion budgétaire de provisions, lecture de courbes "
            "météo numériques. L'application directe au contexte maritime "
            "est plus efficace que les exercices abstraits."
        ),
        "gap": (
            "Ce poste implique une manipulation régulière de données numériques "
            "avec un seuil d'erreur faible. Structurez un plan d'entraînement "
            "progressif : commencez par des calculs maritimes simples "
            "(vitesse/distance/temps), montez vers la gestion de budget de navire. "
            "Utilisez des feuilles de calcul pour automatiser la vérification "
            "et gagner en confiance sur les grandes décimales."
        ),
        "too_high": (
            "Votre aisance numérique est un atout opérationnel réel. "
            "Veillez à rendre vos analyses accessibles à l'équipage : "
            "en contexte de quart ou de briefing, un résultat clair "
            "et formulé simplement vaut mieux qu'une démonstration complète "
            "que seul vous comprenez."
        ),
    },

    "logical": {
        # Cattell-Horn-Carroll : le raisonnement logique (Gc/Gf) prédit
        # la performance dans les environnements à problèmes complexes et nouveaux.
        "strength": (
            "Votre raisonnement logique est aligné avec les exigences du poste. "
            "En navigation, résolution d'avarie ou planification de route, "
            "vous structurez les problèmes avec la précision qu'on attend "
            "à ce niveau de responsabilité."
        ),
        "developing": (
            "Renforcez votre raisonnement structuré sur des scénarios proches "
            "du terrain : que feriez-vous face à une avarie électrique à "
            "50 milles des côtes ? Entraînez-vous à décomposer chaque problème "
            "en hypothèses, preuves et décision. La méthode prime sur l'intuition "
            "dans les situations à enjeux élevés."
        ),
        "gap": (
            "En situation d'urgence à bord, la pensée logique rapide est "
            "une compétence de sécurité. Commencez par pratiquer des résolutions "
            "de problèmes step-by-step sur des cas maritimes simulés : "
            "avarie de gouvernail, panne de propulsion, situation météo dégradée. "
            "L'entraînement explicite de la pensée déductive améliore "
            "la performance en situation réelle dans des délais de quelques semaines."
        ),
        "too_high": (
            "Votre capacité analytique est un levier stratégique fort. "
            "En équipe, intégrez la dimension humaine dans vos raisonnements : "
            "l'état de fatigue de l'équipage, le niveau de stress du capitaine "
            "ou les limites techniques d'un collègue font partie des données "
            "du problème, au même titre que les paramètres techniques."
        ),
    },

    "verbal": {
        "strength": (
            "Votre aisance à comprendre et formuler des informations complexes "
            "est au niveau attendu. À bord, cela se traduit par des briefings "
            "clairs, une communication efficace avec les guests et "
            "une transmission fiable des consignes de quart."
        ),
        "developing": (
            "Renforcez votre précision verbale sur les contextes critiques "
            "du métier : rédaction de rapports d'incident, communication radio "
            "standardisée (phraséologie SMDSM), briefings de sécurité guests. "
            "Ces formats exigeants, pratiqués régulièrement, élèvent "
            "la qualité de votre communication opérationnelle."
        ),
        "gap": (
            "La communication claire est une compétence de sécurité maritime. "
            "Un ordre ambigu lors d'une manœuvre ou un briefing d'urgence "
            "mal formulé peut avoir des conséquences directes. "
            "Entraînez-vous à la phraséologie radio maritime et "
            "à la rédaction de rapports structurés. La rigueur de la forme "
            "protège la clarté du fond."
        ),
        "too_high": (
            "Votre maîtrise du langage est un levier de coordination d'équipe "
            "et de relation guests. Adaptez systématiquement votre registre : "
            "les instructions techniques à l'équipage ne sont pas les mêmes "
            "que l'accueil d'un propriétaire. La précision lexicale n'est "
            "utile que si elle reste accessible à votre interlocuteur."
        ),
    },

    # =========================================================================
    # COGNITIF — HMR-24 (Raisonnement fluide, Cattell-Horn-Carroll Gf theory)
    # =========================================================================

    "fluid_reasoning": {
        # Cattell-Horn-Carroll : Gf = capacité à raisonner dans des situations
        # nouvelles, sans recours aux connaissances cristallisées. Prédicteur
        # de performance dans les environnements changeants et les situations
        # d'urgence non-routinières.
        "strength": (
            "Votre raisonnement fluide vous permet d'opérer efficacement "
            "dans des situations nouvelles — avarie inédite, route non planifiée, "
            "configuration d'équipage inhabituelle. C'est l'une des capacités "
            "cognitives les plus précieuses en navigation hauturière."
        ),
        "developing": (
            "Le raisonnement fluide s'améliore par l'exposition à des problèmes "
            "nouveaux et non-routiniers. Variez vos registres de pratique : "
            "simulation d'urgence, puzzles de navigation à bord, "
            "jeux de stratégie. Chaque nouveau contexte entraîne "
            "votre cerveau à construire des solutions sans filet."
        ),
        "gap": (
            "Ce score indique une difficulté à résoudre des situations "
            "inédites en temps réel. En mer, les situations non-protocollaires "
            "surviennent sans prévenir. Entraînez-vous régulièrement "
            "sur des scénarios d'urgence simulés : la répétition de la nouveauté "
            "est paradoxalement le meilleur entraînement du raisonnement fluide."
        ),
        "too_high": (
            "Votre capacité à improviser des solutions dans l'inconnu est "
            "un atout majeur en navigation. Veillez à documenter vos solutions "
            "pour en faire bénéficier l'équipage — un bon raisonnement fluide "
            "partagé devient une procédure collective."
        ),
    },

    "hfr_induction": {
        "strength": (
            "Votre capacité à identifier des régularités et à induire des règles "
            "à partir d'observations concrètes est solide. À bord, cela se traduit "
            "par une lecture rapide des patterns météo, mécaniques ou comportementaux."
        ),
        "developing": (
            "Entraînez-vous à l'observation systématique : après chaque quart, "
            "notez une régularité que vous avez observée (comportement machine, "
            "pattern météo, réaction d'équipage). Ce réflexe d'induction "
            "renforce progressivement votre capacité à anticiper."
        ),
        "gap": (
            "L'induction — identifier le principe général derrière des cas "
            "particuliers — est centrale en navigation préventive. "
            "Commencez par des exercices de lecture de séries numériques "
            "ou de schémas logiques, puis appliquez la même méthode "
            "à des données maritimes réelles (courbes de consommation, "
            "patterns de vent)."
        ),
        "too_high": (
            "Votre sens de la détection de patterns est un atout de navigation. "
            "Vérifiez vos inductions par des données concrètes avant d'agir "
            "— en mer, une règle induite trop vite peut être une fausse corrélation."
        ),
    },

    "hfr_analogy": {
        "strength": (
            "Votre raisonnement par analogie vous permet de transférer rapidement "
            "des solutions d'un contexte à un autre. C'est un levier d'adaptation "
            "précieux quand chaque navire et chaque équipage redéfinissent le terrain."
        ),
        "developing": (
            "Exercez le transfert analogique : face à un problème nouveau, "
            "demandez-vous explicitement 'à quelle situation déjà vécue "
            "cela ressemble-t-il ?' et identifiez ce qui se transpose et "
            "ce qui ne se transpose pas. Ce questionnement structure "
            "une compétence souvent intuitive."
        ),
        "gap": (
            "Le raisonnement par analogie permet de résoudre le nouveau "
            "à partir de l'acquis. Pratiquez des exercices d'analogie formelle "
            "(matrices de Raven, tests d'aptitude) mais appliquez-les aussi "
            "au terrain maritime : quelle procédure connue s'applique "
            "à cette avarie inédite ?"
        ),
        "too_high": (
            "Votre raisonnement analogique est rapide et puissant. "
            "Contrôlez la validité du transfert : deux situations analogues "
            "ne sont jamais identiques, et les différences peuvent être "
            "décisives en situation d'urgence. La rapidité d'analogie "
            "doit s'accompagner d'une validation rapide des limites du transfert."
        ),
    },

    "hfr_matrix_reasoning": {
        "strength": (
            "Votre capacité à raisonner sur des structures abstraites complexes "
            "est au niveau attendu. En navigation, gestion de systèmes "
            "ou planification logistique, vous identifiez les relations "
            "structurelles sans effort particulier."
        ),
        "developing": (
            "Entraînez-vous sur des matrices progressives (type Raven) "
            "et appliquez ce type de raisonnement à des schémas techniques "
            "maritimes : plans électriques, synoptiques de propulsion, "
            "organigrammes de quart. La lecture de structure abstraite "
            "s'améliore par la pratique régulière."
        ),
        "gap": (
            "Le raisonnement matriciel — identifier des relations complexes "
            "dans un système — est sollicité en ingénierie de bord "
            "et en navigation avancée. Commencez par des exercices visuels "
            "progressifs (matrices 2x2, puis 3x3), avant de transférer "
            "cette logique aux systèmes techniques de votre domaine."
        ),
        "too_high": (
            "Votre capacité à traiter des structures complexes est un atout "
            "pour les postes techniques et de commandement. "
            "Pensez à simplifier vos analyses pour les communiquer à l'équipage : "
            "la complexité bien maîtrisée se traduit en instructions claires, "
            "pas en exposés techniques."
        ),
    },

    # =========================================================================
    # FALLBACK GENERIQUE
    # =========================================================================

    "default": {
        "strength": (
            "Ce trait est bien aligné avec le profil attendu pour ce poste. "
            "Continuez à le développer dans les contextes opérationnels "
            "qui vous sont accessibles."
        ),
        "developing": (
            "Ce trait présente un écart modéré avec le profil cible. "
            "Identifiez une action concrète et observable pour le renforcer "
            "dans les prochains mois, idéalement ancrée dans votre pratique "
            "quotidienne à bord ou en préparation de contrat."
        ),
        "gap": (
            "Ce trait est significativement en dessous des attentes du poste. "
            "Un plan de développement ciblé — formation, mentorat, pratique "
            "délibérée — est recommandé avant de postuler à ce niveau "
            "de responsabilité."
        ),
        "too_high": (
            "Ce trait dépasse nettement le profil cible. "
            "Assurez-vous que cette sur-représentation ne devient pas "
            "une source de rigidité ou de friction avec les attentes "
            "de l'équipe et de l'armateur."
        ),
    },
}
