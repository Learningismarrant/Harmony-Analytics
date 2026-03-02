# seeds/seed_tests_surveys.py
"""
Seed tests & surveys — données psychométriques complètes.

Dépendance : seed_environment.py doit être exécuté en premier.
Ce seed lit les crew_profile_id créés par seed_environment.

Contenu :
    2 TestCatalogue :
        #1 — Big Five Personality Inventory (Likert 1-5, 30 questions)
        #2 — General Cognitive Ability / GCA (Cognitif, 20 questions)

    50 Questions réalistes (30 Big Five + 20 GCA)

    15 TestResult :
        → Tous les membres assignés ont passé les 2 tests
        → Résultats cohérents avec leur psychometric_snapshot
        → 3 candidats non-assignés : Tom Bradley (2 tests), Aisha Nkosi (2 tests),
          Carlos Mendez (1 test — abandonne en cours), Sam Adler (1 test partiel)

    3 Surveys (trigger_type : post_charter | monthly_pulse) :
        #1 — post_charter Lady Aurora (fermé, 4/4 réponses)
        #2 — monthly_pulse Nomad Spirit (ouvert, 2/3 réponses — Lena absente)
        #3 — post_charter Stella Maris (ouvert, 0/3 — test is_open sans réponses)

    6 SurveyResponse — champs Float scalaires alignés sur le modèle :
        team_cohesion_observed / workload_felt / leadership_fit_felt /
        individual_performance_self / intent_to_stay (Y_actual ML)

    120 DailyPulse :
        → 30 jours × ~4 membres Lady Aurora (profils stables → scores 3.5-5)
        → 20 jours × 3 membres Nomad Spirit (profils mixtes → variance)
        → 15 jours × 3 membres Stella Maris
        → 10 jours × 1 membre Blue Horizon (Dimitri — scores bas)

Usage :
    python -m seeds.seed_tests_surveys
    (après seed_environment)
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.shared.models import DailyPulse, Yacht, CrewAssignment,CrewProfile, User, Survey, SurveyResponse, TestCatalogue, Question, TestResult

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

random.seed(42)   # Reproductible


# ── Helpers temporels ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _ago(days: int, hours: int = 0) -> datetime:
    return _now() - timedelta(days=days, hours=hours)

def _ago_date(days: int) -> datetime:
    d = _now() - timedelta(days=days)
    return d.replace(hour=9, minute=0, second=0, microsecond=0)


# ── Questions Big Five (Likert 1-5) ────────────────────────────────────────────
# Chaque trait : 6 questions (3 normales + 3 inversées)
# Traits : agreeableness (A), conscientiousness (C), neuroticism (N),
#          openness (O), extraversion (E)

BIG_FIVE_QUESTIONS = [
    # ── AGREEABLENESS ──────────────────────────────────────────────────────────
    {"order": 1,  "trait": "agreeableness", "reverse": False,
     "text": "Je prends facilement en compte les besoins des autres avant de prendre une décision."},
    {"order": 2,  "trait": "agreeableness", "reverse": False,
     "text": "Je fais des efforts pour maintenir une atmosphère harmonieuse dans l'équipe."},
    {"order": 3,  "trait": "agreeableness", "reverse": False,
     "text": "Je suis à l'écoute de mes collègues même lorsque je ne partage pas leur point de vue."},
    {"order": 4,  "trait": "agreeableness", "reverse": True,
     "text": "J'ai tendance à critiquer ouvertement le travail de mes collègues."},
    {"order": 5,  "trait": "agreeableness", "reverse": True,
     "text": "Je pense que mes intérêts passent avant ceux du groupe."},
    {"order": 6,  "trait": "agreeableness", "reverse": True,
     "text": "Je n'hésite pas à contredire mes collègues en public lorsque j'estime qu'ils ont tort."},

    # ── CONSCIENTIOUSNESS ──────────────────────────────────────────────────────
    {"order": 7,  "trait": "conscientiousness", "reverse": False,
     "text": "Je planifie mes tâches à l'avance pour éviter les imprévus de dernière minute."},
    {"order": 8,  "trait": "conscientiousness", "reverse": False,
     "text": "Je m'assure que mon poste de travail est rangé et organisé avant de partir."},
    {"order": 9,  "trait": "conscientiousness", "reverse": False,
     "text": "Je respecte systématiquement les délais qui me sont fixés."},
    {"order": 10, "trait": "conscientiousness", "reverse": True,
     "text": "Il m'arrive souvent de remettre à plus tard des tâches que je devrais accomplir maintenant."},
    {"order": 11, "trait": "conscientiousness", "reverse": True,
     "text": "Je travaille par à-coups plutôt que de manière régulière et méthodique."},
    {"order": 12, "trait": "conscientiousness", "reverse": True,
     "text": "Je trouve difficile de maintenir une routine de travail stable sur le long terme."},

    # ── NEUROTICISM ────────────────────────────────────────────────────────────
    {"order": 13, "trait": "neuroticism", "reverse": False,
     "text": "Je me sens souvent anxieux ou tendu sans raison apparente."},
    {"order": 14, "trait": "neuroticism", "reverse": False,
     "text": "Les situations stressantes me déstabilisent facilement et durablement."},
    {"order": 15, "trait": "neuroticism", "reverse": False,
     "text": "Mon humeur varie de façon marquée en fonction des événements de la journée."},
    {"order": 16, "trait": "neuroticism", "reverse": True,
     "text": "Je reste calme et posé même dans les situations de pression intense."},
    {"order": 17, "trait": "neuroticism", "reverse": True,
     "text": "Je récupère rapidement après un moment de stress ou de contrariété."},
    {"order": 18, "trait": "neuroticism", "reverse": True,
     "text": "Je parviens à garder le contrôle de mes émotions même lorsque les choses ne se passent pas comme prévu."},

    # ── OPENNESS ──────────────────────────────────────────────────────────────
    {"order": 19, "trait": "openness", "reverse": False,
     "text": "Je suis curieux des nouvelles méthodes de travail, même si les anciennes fonctionnent bien."},
    {"order": 20, "trait": "openness", "reverse": False,
     "text": "J'apprécie les discussions sur des idées complexes ou abstraites."},
    {"order": 21, "trait": "openness", "reverse": False,
     "text": "Je m'intéresse à des cultures, des pratiques ou des points de vue très différents des miens."},
    {"order": 22, "trait": "openness", "reverse": True,
     "text": "Je préfère m'en tenir à des méthodes éprouvées plutôt qu'expérimenter."},
    {"order": 23, "trait": "openness", "reverse": True,
     "text": "Je trouve les débats philosophiques ou théoriques peu utiles dans la vie réelle."},
    {"order": 24, "trait": "openness", "reverse": True,
     "text": "Les changements fréquents dans mon environnement de travail me dérangent."},

    # ── EXTRAVERSION ──────────────────────────────────────────────────────────
    {"order": 25, "trait": "extraversion", "reverse": False,
     "text": "Je prends facilement l'initiative dans les conversations de groupe."},
    {"order": 26, "trait": "extraversion", "reverse": False,
     "text": "Je me sens énergisé après des interactions sociales prolongées."},
    {"order": 27, "trait": "extraversion", "reverse": False,
     "text": "Je suis à l'aise pour m'exprimer devant des personnes que je ne connais pas encore."},
    {"order": 28, "trait": "extraversion", "reverse": True,
     "text": "Je trouve les longues réunions ou interactions de groupe épuisantes."},
    {"order": 29, "trait": "extraversion", "reverse": True,
     "text": "Je préfère travailler seul plutôt qu'en équipe lorsque j'en ai le choix."},
    {"order": 30, "trait": "extraversion", "reverse": True,
     "text": "Je me sens mal à l'aise quand je dois prendre la parole en public."},
]


# ── Questions GCA — Cognitif (réponse correcte parmi A/B/C/D) ─────────────────

GCA_QUESTIONS = [
    # ── Raisonnement verbal ────────────────────────────────────────────────────
    {"order": 1, "trait": "verbal_reasoning", "reverse": False,
     "correct_answer": "C",
     "text": "RAPIDE est à LENT ce que LUMIÈRE est à ___",
     "options": {"A": "Soleil", "B": "Lampe", "C": "Obscurité", "D": "Vitesse"}},
    {"order": 2, "trait": "verbal_reasoning", "reverse": False,
     "correct_answer": "B",
     "text": "Quel mot complète la série : Chêne, Hêtre, Sapin, ___ ?",
     "options": {"A": "Rose", "B": "Bouleau", "C": "Lierre", "D": "Algue"}},
    {"order": 3, "trait": "verbal_reasoning", "reverse": False,
     "correct_answer": "A",
     "text": "Capitaine est à navire ce que pilote est à ___",
     "options": {"A": "Avion", "B": "Route", "C": "Train", "D": "Port"}},
    {"order": 4, "trait": "verbal_reasoning", "reverse": False,
     "correct_answer": "D",
     "text": "Parmi les mots suivants, lequel est l'antonyme de PRÉCIS ?",
     "options": {"A": "Exact", "B": "Juste", "C": "Correct", "D": "Vague"}},
    {"order": 5, "trait": "verbal_reasoning", "reverse": False,
     "correct_answer": "B",
     "text": "Un équipage de 6 personnes est divisé en 2 groupes égaux. Chaque groupe comprend ___",
     "options": {"A": "2 personnes", "B": "3 personnes", "C": "4 personnes", "D": "6 personnes"}},

    # ── Raisonnement numérique ─────────────────────────────────────────────────
    {"order": 6, "trait": "numerical_reasoning", "reverse": False,
     "correct_answer": "C",
     "text": "Quelle est la prochaine valeur de la suite : 2, 4, 8, 16, ___ ?",
     "options": {"A": "18", "B": "24", "C": "32", "D": "64"}},
    {"order": 7, "trait": "numerical_reasoning", "reverse": False,
     "correct_answer": "A",
     "text": "Un yacht parcourt 120 milles nautiques en 8 heures. Quelle est sa vitesse moyenne ?",
     "options": {"A": "15 nœuds", "B": "12 nœuds", "C": "20 nœuds", "D": "960 nœuds"}},
    {"order": 8, "trait": "numerical_reasoning", "reverse": False,
     "correct_answer": "D",
     "text": "Si 3 marins font une tâche en 6 heures, combien d'heures 1 marin seul mettra-t-il ?",
     "options": {"A": "2h", "B": "6h", "C": "9h", "D": "18h"}},
    {"order": 9, "trait": "numerical_reasoning", "reverse": False,
     "correct_answer": "B",
     "text": "Quelle est la prochaine valeur de la suite : 100, 90, 81, 73, ___ ?",
     "options": {"A": "64", "B": "66", "C": "68", "D": "70"}},
    {"order": 10, "trait": "numerical_reasoning", "reverse": False,
     "correct_answer": "C",
     "text": "Un réservoir de 450 litres se remplit à 30L/min. En combien de minutes est-il plein ?",
     "options": {"A": "10 min", "B": "12 min", "C": "15 min", "D": "20 min"}},

    # ── Raisonnement logique ───────────────────────────────────────────────────
    {"order": 11, "trait": "logical_reasoning", "reverse": False,
     "correct_answer": "A",
     "text": "Tous les capitaines sont des marins. Jean est capitaine. Donc ___",
     "options": {"A": "Jean est marin", "B": "Jean est ingénieur", "C": "Tous les marins sont capitaines", "D": "Jean n'est pas marin"}},
    {"order": 12, "trait": "logical_reasoning", "reverse": False,
     "correct_answer": "D",
     "text": "Si A > B et B > C, alors ___",
     "options": {"A": "C > A", "B": "B = A", "C": "A < C", "D": "A > C"}},
    {"order": 13, "trait": "logical_reasoning", "reverse": False,
     "correct_answer": "B",
     "text": "Quelle figure complète la série : ○ □ △ ○ □ ___ ?",
     "options": {"A": "○", "B": "△", "C": "□", "D": "◇"}},
    {"order": 14, "trait": "logical_reasoning", "reverse": False,
     "correct_answer": "A",
     "text": "Sur 10 candidats, 6 ont passé le test A et 5 le test B. 3 ont passé les deux. Combien n'ont passé aucun test ?",
     "options": {"A": "2", "B": "3", "C": "4", "D": "5"}},
    {"order": 15, "trait": "logical_reasoning", "reverse": False,
     "correct_answer": "C",
     "text": "Lundi → Mercredi → Vendredi → ___ ?",
     "options": {"A": "Samedi", "B": "Jeudi", "C": "Dimanche", "D": "Mardi"}},

    # ── Mémoire de travail ─────────────────────────────────────────────────────
    {"order": 16, "trait": "working_memory", "reverse": False,
     "correct_answer": "B",
     "text": "Lisez la séquence une fois : 7-3-9-1-4. Quelle est la valeur du 3ème chiffre ?",
     "options": {"A": "3", "B": "9", "C": "1", "D": "7"}},
    {"order": 17, "trait": "working_memory", "reverse": False,
     "correct_answer": "D",
     "text": "Séquence : Foxtrot-Alpha-Tango-Sierra. Quel est le 2ème mot ?",
     "options": {"A": "Foxtrot", "B": "Tango", "C": "Sierra", "D": "Alpha"}},
    {"order": 18, "trait": "working_memory", "reverse": False,
     "correct_answer": "A",
     "text": "Séquence de couleurs : Rouge-Bleu-Vert-Bleu-Rouge. La couleur qui n'apparaît qu'une fois est ___",
     "options": {"A": "Vert", "B": "Bleu", "C": "Rouge", "D": "Aucune"}},

    # ── Vitesse de traitement ──────────────────────────────────────────────────
    {"order": 19, "trait": "processing_speed", "reverse": False,
     "correct_answer": "C",
     "text": "Combien de fois la lettre 'a' apparaît-elle dans 'paramètre de navigation avancée' ?",
     "options": {"A": "3", "B": "4", "C": "5", "D": "6"}},
    {"order": 20, "trait": "processing_speed", "reverse": False,
     "correct_answer": "B",
     "text": "Parmi ces 4 paires, laquelle est identique ? (A) 7823/7832 (B) 4591/4591 (C) 3367/3376 (D) 8814/8841",
     "options": {"A": "A", "B": "B", "C": "C", "D": "D"}},
]


# ── Scores GCA par profil (correct_answers / 20 → gca_score 0-100) ────────────
# Cohérent avec les snapshots du seed_environment

GCA_CORRECT_BY_PROFILE = {
    "marcus_webb":    17,   # gca=80 → 17/20
    "isabelle_moreau": 16,  # gca=77
    "tom_bradley":    16,   # gca=78
    "sofia_reyes":    15,   # gca=74
    "emma_larsen":    12,   # gca=58
    "mei_zhang":      13,   # gca=61
    "clara_dumont":   11,   # gca=56
    "aisha_nkosi":    15,   # gca=75
    "niko_papadis":   13,   # gca=65
    "jake_torres":    14,   # gca=70
    "lena_kovacs":    11,   # gca=52
    "ryan_okafor":    11,   # gca=55
    "dimitri_volkov":  9,   # gca=48
    "carlos_mendez":  10,   # gca=49
    "sam_adler":       9,   # gca=44
}

# Scores Big Five Likert par profil — structure {trait: score_brut / score_normalise}
# Score brut = somme des réponses (6 questions × 1-5 = 6-30)
# Score normalisé = (brut-6)/(30-6) × 100

def _bf_score_from_normalised(normalised: float) -> float:
    """normalised 0-100 → brut Likert 6-30."""
    return round(6 + (normalised / 100) * 24, 1)

BIG_FIVE_SCORES_BY_PROFILE = {
    "marcus_webb":    {"agreeableness": 72, "conscientiousness": 82, "neuroticism": 22, "openness": 68, "extraversion": 74},
    "isabelle_moreau":{"agreeableness": 70, "conscientiousness": 85, "neuroticism": 25, "openness": 72, "extraversion": 66},
    "tom_bradley":    {"agreeableness": 74, "conscientiousness": 81, "neuroticism": 21, "openness": 70, "extraversion": 71},
    "sofia_reyes":    {"agreeableness": 68, "conscientiousness": 79, "neuroticism": 29, "openness": 65, "extraversion": 60},
    "emma_larsen":    {"agreeableness": 80, "conscientiousness": 68, "neuroticism": 34, "openness": 74, "extraversion": 78},
    "mei_zhang":      {"agreeableness": 76, "conscientiousness": 65, "neuroticism": 31, "openness": 71, "extraversion": 69},
    "clara_dumont":   {"agreeableness": 82, "conscientiousness": 62, "neuroticism": 27, "openness": 68, "extraversion": 76},
    "aisha_nkosi":    {"agreeableness": 66, "conscientiousness": 77, "neuroticism": 32, "openness": 74, "extraversion": 62},
    "niko_papadis":   {"agreeableness": 74, "conscientiousness": 71, "neuroticism": 38, "openness": 62, "extraversion": 58},
    "jake_torres":    {"agreeableness": 58, "conscientiousness": 73, "neuroticism": 45, "openness": 60, "extraversion": 52},
    "lena_kovacs":    {"agreeableness": 62, "conscientiousness": 60, "neuroticism": 52, "openness": 58, "extraversion": 61},
    "ryan_okafor":    {"agreeableness": 52, "conscientiousness": 64, "neuroticism": 56, "openness": 55, "extraversion": 55},
    "dimitri_volkov": {"agreeableness": 35, "conscientiousness": 55, "neuroticism": 78, "openness": 45, "extraversion": 48},
    "carlos_mendez":  {"agreeableness": 40, "conscientiousness": 52, "neuroticism": 82, "openness": 42, "extraversion": 44},
    "sam_adler":      {"agreeableness": 45, "conscientiousness": 50, "neuroticism": 90, "openness": 40, "extraversion": 42},
}

# Pulse patterns par équipage (mean, std) — pour générer des séries réalistes
PULSE_PATTERNS = {
    # Lady Aurora — équipe ELITE, très stable → scores hauts, faible variance
    "marcus_webb":    (4.4, 0.4),
    "sofia_reyes":    (4.2, 0.5),
    "niko_papadis":   (3.8, 0.7),
    "emma_larsen":    (4.1, 0.5),
    # Nomad Spirit — équipe mixte, quelques tensions
    "isabelle_moreau":(4.0, 0.6),
    "jake_torres":    (3.2, 1.0),   # ES modéré → plus variable
    "lena_kovacs":    (3.0, 1.1),   # ES faible → variance élevée
    # Stella Maris — profils moyens
    "mei_zhang":      (3.7, 0.6),
    "ryan_okafor":    (3.2, 0.9),
    "clara_dumont":   (3.9, 0.5),
    # Blue Horizon — Dimitri HIGH_RISK → scores bas et volatils
    "dimitri_volkov": (2.4, 1.2),
}


# ── Générateur de scores SurveyResponse réalistes ────────────────────────────
#
# SurveyResponse ne stocke pas un dict answers — elle stocke 5 scores numériques
# qui sont les proxies des composantes MLPSM et la variable dépendante ML.
#
# Mapping :
#   team_cohesion_observed      ← proxy F_team (agréabilité + ES perçue)
#   workload_felt               ← proxy F_env (charge ressentie)
#   leadership_fit_felt         ← proxy F_lmx (fit perçu avec le capitaine)
#   individual_performance_self ← proxy P_ind (auto-évaluation performance)
#   intent_to_stay              ← Y_actual ML (0="je pars" / 100="je reste")

def _survey_response_scores(profile_key: str, trigger_type: str) -> dict:
    """
    Génère des scores cohérents avec le profil Big Five du marin.

    Logique psychométrique :
        team_cohesion   ← A (agréabilité projective) + ES + bruit
        workload_felt   ← inverse de ES (névrosisme élevé = charge perçue plus lourde)
                          + C (consciencieux = gère mieux la charge)
        leadership_fit  ← A + ES (profils stables s'adaptent mieux au leadership)
        perf_self       ← C + GCA (consciencieux + cognitif = auto-évaluation réaliste haute)
        intent_to_stay  ← ES + A + C − workload (variable cible principale)
    """
    bf = BIG_FIVE_SCORES_BY_PROFILE[profile_key]
    es  = 100 - bf["neuroticism"]
    a   = bf["agreeableness"]
    c   = bf["conscientiousness"]
    gca = GCA_CORRECT_BY_PROFILE.get(profile_key, 10) / 20 * 100

    def _jitter(base: float, scale: float = 8.0) -> float:
        return round(max(0.0, min(100.0, base + random.gauss(0, scale))), 1)

    team_cohesion   = _jitter((a * 0.5 + es * 0.5))
    workload_felt   = _jitter(100 - (es * 0.4 + c * 0.3 + 30), scale=10)  # inversé
    leadership_fit  = _jitter((es * 0.45 + a * 0.35 + c * 0.2))
    perf_self       = _jitter((c * 0.5 + gca * 0.3 + es * 0.2))

    # intent_to_stay : composite positif ES+A+C, pénalisé par workload perçu élevé
    raw_intent = (es * 0.35 + a * 0.25 + c * 0.20 + (100 - workload_felt) * 0.20)
    # Trigger exit_interview → intention de rester systématiquement basse
    if trigger_type == "exit_interview":
        raw_intent = raw_intent * 0.35
    intent_to_stay  = _jitter(raw_intent, scale=6.0)

    free_texts = {
        "high":   ["RAS, très satisfait de cette saison.", "Super ambiance à bord, je recommande."],
        "medium": ["Quelques tensions mais globalement positif.", "La charge est parfois lourde mais gérable."],
        "low":    ["Je ressens une fatigue accumulée.", "La communication s'est dégradée ces dernières semaines."],
    }
    if intent_to_stay >= 70:   bucket = "high"
    elif intent_to_stay >= 40: bucket = "medium"
    else:                      bucket = "low"

    return {
        "team_cohesion_observed":      team_cohesion,
        "workload_felt":               workload_felt,
        "leadership_fit_felt":         leadership_fit,
        "individual_performance_self": perf_self,
        "intent_to_stay":              intent_to_stay,
        "free_text":                   random.choice(free_texts[bucket]),
    }


# ── Générateur de réponses GCA ─────────────────────────────────────────────────

def _gca_responses(profile_key: str, questions: list) -> list:
    """Génère les réponses GCA avec le bon nombre de bonnes réponses."""
    n_correct = GCA_CORRECT_BY_PROFILE.get(profile_key, 10)
    all_q_ids = [q["order"] for q in questions]
    correct_ids = set(random.sample(all_q_ids, min(n_correct, len(all_q_ids))))
    responses = []
    for q in questions:
        if q["order"] in correct_ids:
            answer = q["correct_answer"]
        else:
            wrong = [k for k in ["A", "B", "C", "D"] if k != q["correct_answer"]]
            answer = random.choice(wrong)
        responses.append({
            "question_order": q["order"],
            "valeur_choisie": answer,
            "seconds_spent": round(random.uniform(8, 45)),
        })
    return responses


def _gca_scores(profile_key: str, questions: list) -> dict:
    """Calcule les scores GCA par trait pour TestResult.scores."""
    traits = set(q["trait"] for q in questions)
    n_correct = GCA_CORRECT_BY_PROFILE.get(profile_key, 10)
    trait_q_count = {t: sum(1 for q in questions if q["trait"] == t) for t in traits}
    # Distribuer les bonnes réponses proportionnellement
    scores = {}
    total_q = len(questions)
    for trait in traits:
        trait_n = trait_q_count[trait]
        expected_correct = round((n_correct / total_q) * trait_n)
        score = (expected_correct / trait_n) * 100 if trait_n else 50
        scores[trait] = {"score": round(score, 1), "n_correct": expected_correct, "n_total": trait_n}
    gca_raw = (n_correct / total_q) * 100
    scores["gca_score"] = round(gca_raw, 1)
    return scores


# ── Seed principal ─────────────────────────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    print("🧪 Seed tests & surveys démarré...")

    # ── CUTTY SARK T-IRT (idempotent, commit interne) ─────────────────────────
    from app.seed.CUTTY_SARK import seed_cutty_sark
    await seed_cutty_sark(db)

    # ── Récupérer les crew_profiles depuis la DB ───────────────────────────────
    r = await db.execute(
        select(CrewProfile, User)
        .join(User, User.id == CrewProfile.user_id)
    )
    rows = r.all()
    profiles_by_name: Dict[str, CrewProfile] = {}
    for cp, u in rows:
        # Matcher par email suffix (ex: marcus.webb@gmail.com → marcus_webb)
        key = u.email.split("@")[0].replace(".", "_")
        profiles_by_name[key] = cp

    # Mapper les yachts
    r = await db.execute(select(Yacht))
    yachts_list = r.scalars().all()
    yachts_by_name = {y.name: y for y in yachts_list}

    aurora = yachts_by_name.get("Lady Aurora")
    nomad  = yachts_by_name.get("Nomad Spirit")
    stella = yachts_by_name.get("Stella Maris")
    blue   = yachts_by_name.get("Blue Horizon")

    print(f"  ✓ {len(profiles_by_name)} crew profiles trouvés")

    # ────────────────────────────────────────────────────────────────────────────
    # 1. TestCatalogue
    # ────────────────────────────────────────────────────────────────────────────
    test_big_five = TestCatalogue(
        name="Harmony Big Five Inventory (HBF-30)",
        description=(
            "Évaluation des 5 grands traits de personnalité adaptée au contexte maritime. "
            "30 items Likert 1-5. Durée estimée : 12-15 minutes. "
            "Traits mesurés : Agréabilité, Conscienciosité, Névrosisme, "
            "Ouverture à l'expérience, Extraversion."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=30,
        is_active=True,
        
    )
    db.add(test_big_five)

    test_gca = TestCatalogue(
        name="General Cognitive Ability Assessment (GCA-20)",
        description=(
            "Test d'aptitude cognitive générale — raisonnement verbal, numérique, "
            "logique, mémoire de travail et vitesse de traitement. "
            "20 items à choix multiples. Durée estimée : 25-30 minutes."
        ),
        test_type="cognitive",
        max_score_per_question=1,
        n_questions=20,
        is_active=True,
        
    )
    db.add(test_gca)
    await db.flush()

    print(f"  ✓ TestCatalogue : HBF-30 (id={test_big_five.id}), GCA-20 (id={test_gca.id})")

    # ────────────────────────────────────────────────────────────────────────────
    # 2. Questions
    # ────────────────────────────────────────────────────────────────────────────
    q_objects_bf  = []
    q_objects_gca = []

    for q_data in BIG_FIVE_QUESTIONS:
        q = Question(
            test_id=test_big_five.id,
            text=q_data["text"],
            question_type="likert",
            trait=q_data["trait"],
            reverse=q_data["reverse"],
            order=q_data["order"],
            correct_answer=None,
            options=None,
        )
        db.add(q)
        q_objects_bf.append(q)

    for q_data in GCA_QUESTIONS:
        q = Question(
            test_id=test_gca.id,
            text=q_data["text"],
            question_type="qcm",
            trait=q_data["trait"],
            reverse=False,
            order=q_data["order"],
            correct_answer=q_data["correct_answer"],
            options=q_data.get("options"),
        )
        db.add(q)
        q_objects_gca.append(q)

    await db.flush()
    print(f"  ✓ Questions : {len(q_objects_bf)} Big Five + {len(q_objects_gca)} GCA")

    # ────────────────────────────────────────────────────────────────────────────
    # 3. TestResults
    # ────────────────────────────────────────────────────────────────────────────
    # Membres assignés — ont tous passé les 2 tests (passé lointain)
    assigned_profiles = [
        ("marcus_webb",    42, 40),
        ("sofia_reyes",    38, 36),
        ("niko_papadis",   35, 33),
        ("emma_larsen",    30, 28),
        ("isabelle_moreau",32, 30),
        ("jake_torres",    28, 26),
        ("lena_kovacs",    25, 23),
        ("mei_zhang",      27, 25),
        ("ryan_okafor",    24, 22),
        ("clara_dumont",   22, 20),
        ("dimitri_volkov", 18, 16),
    ]

    # Candidats — ont passé récemment
    candidate_profiles = [
        ("tom_bradley",    7, 5),
        ("aisha_nkosi",    9, 7),
        ("carlos_mendez",  6, None),  # GCA non complété
        ("sam_adler",      5, None),  # GCA non complété
    ]

    n_results = 0
    for key, days_bf, days_gca in assigned_profiles + candidate_profiles:
        cp = profiles_by_name.get(key)
        if not cp:
            continue

        bf_scores_raw = BIG_FIVE_SCORES_BY_PROFILE[key]

        # ── Big Five result ────────────────────────────────────────────────────
        bf_trait_scores = {}
        for trait, normalised in bf_scores_raw.items():
            brut = _bf_score_from_normalised(normalised)
            bf_trait_scores[trait] = {
                "score": round(normalised, 1),
                "raw_score": brut,
                "reliable": True,
            }
        bf_trait_scores["emotional_stability"] = {
            "score": round(100 - bf_scores_raw["neuroticism"], 1),
            "reliable": True,
        }

        tr_bf = TestResult(
            crew_profile_id=cp.id,
            test_id=test_big_five.id,
            scores=bf_trait_scores,
            global_score=round(sum(bf_scores_raw.values()) / len(bf_scores_raw), 1),
            
            created_at=_ago(days_bf),
        )
        db.add(tr_bf)
        n_results += 1

        # ── GCA result ─────────────────────────────────────────────────────────
        if days_gca is not None:
            gca_scores = _gca_scores(key, GCA_QUESTIONS)
            n_correct = GCA_CORRECT_BY_PROFILE.get(key, 10)
            tr_gca = TestResult(
                crew_profile_id=cp.id,
                test_id=test_gca.id,
                scores=gca_scores,
                global_score=round((n_correct / 20) * 100, 1),
                
                created_at=_ago(days_gca),
            )
            db.add(tr_gca)
            n_results += 1

    await db.flush()
    print(f"  ✓ TestResults : {n_results} résultats créés")

    # ────────────────────────────────────────────────────────────────────────────
    # 4. Surveys
    # ────────────────────────────────────────────────────────────────────────────
    # Récupérer les employer_profile_id depuis les yachts
    aurora_employer_id = aurora.employer_profile_id if aurora else None
    stella_employer_id = stella.employer_profile_id if stella else None

    aurora_crew_ids = [
        profiles_by_name[k].id
        for k in ["marcus_webb", "sofia_reyes", "niko_papadis", "emma_larsen"]
        if k in profiles_by_name
    ]
    nomad_crew_ids = [
        profiles_by_name[k].id
        for k in ["isabelle_moreau", "jake_torres", "lena_kovacs"]
        if k in profiles_by_name
    ]
    stella_crew_ids = [
        profiles_by_name[k].id
        for k in ["mei_zhang", "ryan_okafor", "clara_dumont"]
        if k in profiles_by_name
    ]

    # Survey 1 — Post-charter Lady Aurora (fermé, 4/4 réponses)
    # trigger_type "post_charter" → déclenché à la fin d'une charte
    # Parfait pour alimenter le pipeline ML : y_actual = intent_to_stay
    survey_aurora_mid = Survey(
        yacht_id=aurora.id if aurora else None,
        triggered_by_id=aurora_employer_id,
        title="Post-charter — Lady Aurora / Été 2025",
        trigger_type="post_charter",
        target_crew_ids=aurora_crew_ids,
        is_open=False,
        created_at=_ago(20),
        closed_at=_ago(13),
    )
    db.add(survey_aurora_mid)

    # Survey 2 — Monthly pulse Nomad Spirit (ouvert, 2/3 réponses)
    # trigger_type "monthly_pulse" → envoi automatique chaque mois
    survey_nomad_checkin = Survey(
        yacht_id=nomad.id if nomad else None,
        triggered_by_id=aurora_employer_id,
        title="Pulse mensuel — Nomad Spirit / Juillet 2025",
        trigger_type="monthly_pulse",
        target_crew_ids=nomad_crew_ids,
        is_open=True,
        created_at=_ago(5),
        closed_at=None,
    )
    db.add(survey_nomad_checkin)

    # Survey 3 — Post-charter Stella Maris (ouvert, 0 réponse)
    # Teste le cas is_open=True sans aucune réponse — attend les marins
    survey_stella_onboarding = Survey(
        yacht_id=stella.id if stella else None,
        triggered_by_id=stella_employer_id,
        title="Post-charter — Stella Maris / Juillet 2025",
        trigger_type="post_charter",
        target_crew_ids=stella_crew_ids,
        is_open=True,
        created_at=_ago(2),
        closed_at=None,
    )
    db.add(survey_stella_onboarding)
    await db.flush()

    print(f"  ✓ Surveys : post-charter Aurora (fermé), monthly_pulse Nomad (ouvert), post-charter Stella (ouvert)")

    # ────────────────────────────────────────────────────────────────────────────
    # 5. SurveyResponses
    # ────────────────────────────────────────────────────────────────────────────
    # SurveyResponse stocke 5 scores numériques (proxies MLPSM) + intent_to_stay
    # (variable dépendante ML — alimente RecruitmentEvent.y_actual).
    # Pas de dict answers — chaque dimension est une colonne Float distincte.
    n_responses = 0

    # Survey 1 — Post-charter Aurora : 4/4 réponses
    # Ces scores seront utilisés pour valider les prédictions MLPSM a posteriori
    for key, days_offset in [
        ("marcus_webb",  19), ("sofia_reyes", 18),
        ("niko_papadis", 17), ("emma_larsen", 16),
    ]:
        cp = profiles_by_name.get(key)
        if not cp:
            continue
        scores = _survey_response_scores(key, "post_charter")
        sr = SurveyResponse(
            survey_id=survey_aurora_mid.id,
            crew_profile_id=cp.id,
            yacht_id=aurora.id,
            trigger_type="post_charter",
            team_cohesion_observed=      scores["team_cohesion_observed"],
            workload_felt=               scores["workload_felt"],
            leadership_fit_felt=         scores["leadership_fit_felt"],
            individual_performance_self= scores["individual_performance_self"],
            intent_to_stay=              scores["intent_to_stay"],
            free_text=                   scores["free_text"],
            submitted_at=_ago(days_offset),
        )
        db.add(sr)
        n_responses += 1

    # Survey 2 — Monthly pulse Nomad : 2/3 réponses (Lena n'a pas répondu)
    # Jake Torres (ES modéré, A=58) → scores plus bas, intent_to_stay plus faible
    for key, days_offset in [("isabelle_moreau", 4), ("jake_torres", 3)]:
        cp = profiles_by_name.get(key)
        if not cp:
            continue
        scores = _survey_response_scores(key, "monthly_pulse")
        sr = SurveyResponse(
            survey_id=survey_nomad_checkin.id,
            crew_profile_id=cp.id,
            yacht_id=nomad.id,
            trigger_type="monthly_pulse",
            team_cohesion_observed=      scores["team_cohesion_observed"],
            workload_felt=               scores["workload_felt"],
            leadership_fit_felt=         scores["leadership_fit_felt"],
            individual_performance_self= scores["individual_performance_self"],
            intent_to_stay=              scores["intent_to_stay"],
            free_text=                   scores["free_text"],
            submitted_at=_ago(days_offset),
        )
        db.add(sr)
        n_responses += 1

    # Survey 3 — Post-charter Stella : 0 réponse
    # État is_open=True sans réponses — pour tester get_pending_for_crew()
    await db.flush()
    print(f"  ✓ SurveyResponses : {n_responses} réponses (Stella 0/3 — test is_open sans réponses)")

    # ────────────────────────────────────────────────────────────────────────────
    # 6. DailyPulses
    # ────────────────────────────────────────────────────────────────────────────
    n_pulses = 0

    pulse_schedule = [
        # (profile_key, yacht, n_days, skip_days — pour simuler des jours sans pulse)
        # Lady Aurora — 30 jours, très régulier
        ("marcus_webb",    aurora, 30, {5, 12, 20}),
        ("sofia_reyes",    aurora, 30, {3, 11, 25}),
        ("niko_papadis",   aurora, 28, {7, 15}),
        ("emma_larsen",    aurora, 27, {2, 18, 26}),
        # Nomad Spirit — 20 jours, quelques trous
        ("isabelle_moreau",nomad,  20, {4, 13}),
        ("jake_torres",    nomad,  18, {1, 9, 16}),
        ("lena_kovacs",    nomad,  15, {5, 12}),
        # Stella Maris — 15 jours
        ("mei_zhang",      stella, 15, {3}),
        ("ryan_okafor",    stella, 14, {7}),
        ("clara_dumont",   stella, 13, set()),
        # Blue Horizon — 10 jours, scores bas
        ("dimitri_volkov", blue,   10, {4, 8}),
    ]

    for key, yacht, n_days, skip in pulse_schedule:
        cp = profiles_by_name.get(key)
        if not cp or not yacht:
            continue

        mean, std = PULSE_PATTERNS.get(key, (3.5, 0.7))

        for day_offset in range(1, n_days + 1):
            if day_offset in skip:
                continue

            raw_score = random.gauss(mean, std)
            score = max(1, min(5, round(raw_score)))

            comment = None
            if score <= 2:
                comment = random.choice([
                    "Journée difficile, fatigue accumulée.",
                    "Tensions ressenties à bord.",
                    "Pas au mieux de ma forme.",
                ])
            elif score == 5 and random.random() < 0.3:
                comment = random.choice([
                    "Excellente journée, super ambiance.",
                    "Tout s'est très bien passé aujourd'hui.",
                ])

            pulse = DailyPulse(
                crew_profile_id=cp.id,
                yacht_id=yacht.id,
                score=score,
                comment=comment,
                created_at=_ago(n_days - day_offset, hours=random.randint(0, 8)),
            )
            db.add(pulse)
            n_pulses += 1

    await db.commit()
    print(f"  ✓ DailyPulses : {n_pulses} entrées générées")
    print()
    print("✅ Seed tests & surveys terminé.")
    print()
    print("📋 Résumé pour les tests :")
    print(f"   Big Five HBF-30  : id={test_big_five.id}")
    print(f"   GCA-20           : id={test_gca.id}")
    print(f"   Survey Aurora    : id={survey_aurora_mid.id} (fermé, 4/4)")
    print(f"   Survey Nomad     : id={survey_nomad_checkin.id} (ouvert, 2/3)")
    print(f"   Survey Stella    : id={survey_stella_onboarding.id} (ouvert, 0/3)")
    print(f"   DailyPulses      : {n_pulses} entrées sur {len(pulse_schedule)} membres")
    print()
    print("⚠️  Cas de test couverts :")
    print("   · Carlos Mendez  : Big Five OK, GCA absent → snapshot partiel")
    print("   · Sam Adler      : Big Five OK, GCA absent + ES=10 → DISQUALIFIED")
    print("   · Lena Kovacs    : Survey check-in ouvert sans réponse")
    print("   · Dimitri Volkov : Pulses bas (μ=2.4) + HIGH_RISK → TVI élevé")
    print("   · Blue Horizon   : 1 seul membre → dashboard incomplet attendu")


async def main():
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())