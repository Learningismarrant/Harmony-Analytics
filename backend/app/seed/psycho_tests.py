# seed.py
from app.database import SessionLocal, engine
from app import models

def seed_data():
    db = SessionLocal()
    
    # ATTENTION : Supprime toutes les tables existantes
    print("🗑️ Nettoyage de la base de données...")
    models.Base.metadata.drop_all(bind=engine) 
    
    # Recrée les tables proprement avec les nouveaux champs
    print("🏗️ Création des nouvelles tables...")
    models.Base.metadata.create_all(bind=engine)

    # 1. CATALOGUES DES TESTS AVEC TYPES ET INSTRUCTIONS
    tests = [
        {
            "nom": "NEO-60", 
            "desc": "Inventaire de personnalité Big Five", 
            "max": 5, 
            "type": "likert",
            "instructions": "Pour chaque affirmation, choisissez l'option qui vous décrit le mieux. Il n'y a pas de bonne ou de mauvaise réponse. Soyez le plus honnête possible."
        },
        {
            "nom": "R-MAWS", 
            "desc": "Échelle de motivation au travail", 
            "max": 7, 
            "type": "likert",
            "instructions": "Indiquez à quel point les énoncés suivants correspondent aux raisons pour lesquelles vous faites des efforts dans votre travail actuel ou visé. (1 = Pas du tout, 7 = Exactement)."
        },
        {
            "nom": "COG-IQ", 
            "desc": "Évaluation des aptitudes cognitives", 
            "max": 1, 
            "type": "cognitive",
            "instructions": "Ce test mesure vos capacités de raisonnement. Vous disposez d'un temps limité pour chaque question. Choisissez la réponse qui vous semble la plus logique."
        }
    ]

    test_objs = {}
    for t in tests:
        obj = db.query(models.TestCatalogue).filter_by(nom_du_test=t["nom"]).first()
        if not obj:
            obj = models.TestCatalogue(
                nom_du_test=t["nom"], 
                description_courte=t["desc"], 
                instructions=t["instructions"],
                max_score_per_question=t["max"],
                test_type=t["type"]
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
        test_objs[t["nom"]] = obj

    # 2. QUESTIONS COGNITIVES (Type multiple_choice)
    if db.query(models.Question).filter_by(test_id=test_objs["COG-IQ"].id).count() == 0:
        cog_qs =  [
            # NUMERICAL
            {
                "text": "4, 9, 16, 25, ... What is next?",
                "options": ["30", "34", "36", "49"],
                "correct_answer": "36",
                "trait": "numerical",
                "question_type": "multiple_choice"
            },
            {
                "text": "3, 6, 11, 18, ... What is next?",
                "options": ["25", "27", "29", "31"],
                "correct_answer": "27",
                "trait": "numerical",
                "question_type": "multiple_choice"
            },
            {
                "text": "120, 60, 30, 15, ... What is next?",
                "options": ["7.5", "5", "10", "8"],
                "correct_answer": "7.5",
                "trait": "numerical",
                "question_type": "multiple_choice"
            },
            {
                "text": "1, 1, 2, 3, 5, 8, ... What is next?",
                "options": ["10", "11", "12", "13"],
                "correct_answer": "13",
                "trait": "numerical",
                "question_type": "multiple_choice"
            },
            {
                "text": "If 3 widgets cost $4.50, how much for 7?",
                "options": ["$10.50", "$9", "$11", "$12"],
                "correct_answer": "$10.50",
                "trait": "numerical",
                "question_type": "multiple_choice"
            },
            {
                "text": "A bat and ball cost $1.10. The bat costs $1 more than the ball. How much is the ball?",
                "options": ["$0.10", "$0.05", "$0.15", "$0.55"],
                "correct_answer": "$0.05",
                "trait": "numerical",
                "question_type": "multiple_choice"
            },

            # LOGICAL
            {
                "text": "All A are B. All B are C. Are all A also C?",
                "options": ["Yes", "No", "Maybe"],
                "correct_answer": "Yes",
                "trait": "logical",
                "question_type": "multiple_choice"
            },
            {
                "text": "If North is South and East is West, what is Northwest?",
                "options": ["Northeast", "Southeast", "Southwest"],
                "correct_answer": "Southeast",
                "trait": "logical",
                "question_type": "multiple_choice"
            },
            {
                "text": "Find the odd one out: Circle, Square, Sphere, Triangle.",
                "options": ["Circle", "Square", "Sphere", "Triangle"],
                "correct_answer": "Sphere",
                "trait": "logical",
                "question_type": "multiple_choice"
            },
            {
                "text": "Book is to Reading as Fork is to...",
                "options": ["Cooking", "Eating", "Spoon", "Silver"],
                "correct_answer": "Eating",
                "trait": "logical",
                "question_type": "multiple_choice"
            },
            {
                "text": "If 'CAKE' is 'DBLF', what is 'BREAD'?",
                "options": ["CSFBG", "CSFBE", "DSFBG", "CTFBG"],
                "correct_answer": "CSFBG",
                "trait": "logical",
                "question_type": "multiple_choice"
            },
            {
                "text": "John is taller than Sam. Sam is shorter than Alex. Is John taller than Alex?",
                "options": ["Yes", "No", "Uncertain"],
                "correct_answer": "Uncertain",
                "trait": "logical",
                "question_type": "multiple_choice"
            },
            {
                "text": "If 2 days ago was Friday, what day is 3 days from now?",
                "options": ["Tuesday", "Wednesday", "Thursday", "Friday"],
                "correct_answer": "Thursday",
                "trait": "logical",
                "question_type": "multiple_choice"
            },

            # VERBAL
            {
                "text": "Which word is a synonym for 'Meticulous'?",
                "options": ["Messy", "Careful", "Fast", "Angry"],
                "correct_answer": "Careful",
                "trait": "verbal",
                "question_type": "multiple_choice"
            },
            {
                "text": "Which word is the antonym of 'Ambiguous'?",
                "options": ["Clear", "Vague", "Large", "Rare"],
                "correct_answer": "Clear",
                "trait": "verbal",
                "question_type": "multiple_choice"
            },
            {
                "text": "'Prudence' is to 'Caution' as 'Efficiency' is to...",
                "options": ["Speed", "Productivity", "Laziness", "Waste"],
                "correct_answer": "Productivity",
                "trait": "verbal",
                "question_type": "multiple_choice"
            },
            {
                "text": "Rearrange 'R-A-I-N-T' to form a common word.",
                "options": ["Train", "Rain", "Star", "Trainy"],
                "correct_answer": "Train",
                "trait": "verbal",
                "question_type": "multiple_choice"
            },
            {
                "text": "Which word does not belong?",
                "options": ["Apple", "Banana", "Carrot", "Grape"],
                "correct_answer": "Carrot",
                "trait": "verbal",
                "question_type": "multiple_choice"
            },
            {
                "text": "A 'Prolific' writer produces...",
                "options": ["High quality", "Much work", "Bad work", "No work"],
                "correct_answer": "Much work",
                "trait": "verbal",
                "question_type": "multiple_choice"
            },
            {
                "text": "Sentence: 'The plan was __ due to lack of funds.'",
                "options": ["Cancelled", "Promoted", "Written", "Sold"],
                "correct_answer": "Cancelled",
                "trait": "verbal",
                "question_type": "multiple_choice"
            }
        ]
        for q in cog_qs:
            db.add(models.Question(**q, test_id=test_objs["COG-IQ"].id))

    # 3. QUESTIONS DE MOTIVATION (R-MAWS) - Type likert_7
    if db.query(models.Question).filter_by(test_id=test_objs["R-MAWS"].id).count() == 0:
        rmaws_qs = [
            {"text": "To get others’ approval.", "trait": "extrinsic_social", "reverse": False, "question_type": "likert_7"},
            {"text": "Because others will respect me more.", "trait": "extrinsic_social", "reverse": False, "question_type": "likert_7"},
            {"text": "To avoid being criticized by others.", "trait": "extrinsic_social", "reverse": False, "question_type": "likert_7"},
            {"text": "Because others will reward me financially only if I put enough effort.", "trait": "extrinsic_material", "reverse": False, "question_type": "likert_7"},
            {"text": "Because others offer me greater job security.", "trait": "extrinsic_material", "reverse": False, "question_type": "likert_7"},
            {"text": "Because I risk losing my job if I don’t put enough effort in it.", "trait": "extrinsic_material", "reverse": False, "question_type": "likert_7"},
            {"text": "Because I have to prove to myself that I can.", "trait": "introjected", "reverse": False, "question_type": "likert_7"},
            {"text": "Because it makes me feel proud of myself.", "trait": "introjected", "reverse": False, "question_type": "likert_7"},
            {"text": "Because otherwise I will feel ashamed of myself.", "trait": "introjected", "reverse": False, "question_type": "likert_7"},
            {"text": "Because otherwise I will feel bad about myself.", "trait": "introjected", "reverse": False, "question_type": "likert_7"},
            {"text": "Because I personally consider it important to put efforts in this job.", "trait": "identified", "reverse": False, "question_type": "likert_7"},
            {"text": "Because putting efforts in this job aligns with my personal values.", "trait": "identified", "reverse": False, "question_type": "likert_7"},
            {"text": "Because putting efforts in this job has personal significance to me.", "trait": "identified", "reverse": False, "question_type": "likert_7"},
            {"text": "Because I have fun doing my job.", "trait": "intrinsic", "reverse": False, "question_type": "likert_7"},
            {"text": "Because what I do in my work is exciting.", "trait": "intrinsic", "reverse": False, "question_type": "likert_7"},
            {"text": "Because the work I do is interesting.", "trait": "intrinsic", "reverse": False, "question_type": "likert_7"},
            {"text": "I don't, because I really feel that I'm wasting my time at work.", "trait": "amotivation", "reverse": False, "question_type": "likert_7"},
            {"text": "I do little because I don’t think this work is worth putting efforts into.", "trait": "amotivation", "reverse": False, "question_type": "likert_7"},
            {"text": "I don’t know why I’m doing this job, it’s pointless work.", "trait": "amotivation", "reverse": False, "question_type": "likert_7"},
        ]
        for q in rmaws_qs:
            db.add(models.Question(**q, test_id=test_objs["R-MAWS"].id))

    # 4. QUESTIONS DE PERSONNALITÉ (NEO-60) - Type likert_5
    if db.query(models.Question).filter_by(test_id=test_objs["NEO-60"].id).count() == 0:
        neo_qs = [
            {"text": "Am the life of the party", "trait": "extraversion", "reverse": False, "question_type": "likert_5"},
            {"text": "Feel little concern for others", "trait": "agreeableness", "reverse": True, "question_type": "likert_5"},
            {"text": "Am always prepared", "trait": "conscientiousness", "reverse": False, "question_type": "likert_5"},
            {"text": "Get stressed out easily", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Have a rich vocabulary", "trait": "openness", "reverse": False, "question_type": "likert_5"},
            {"text": "Don't talk a lot", "trait": "extraversion", "reverse": True, "question_type": "likert_5"},
            {"text": "Am interested in people", "trait": "agreeableness", "reverse": False, "question_type": "likert_5"},
            {"text": "Leave my belongings around", "trait": "conscientiousness", "reverse": True, "question_type": "likert_5"},
            {"text": "Am relaxed most of the time", "trait": "neuroticism", "reverse": True, "question_type": "likert_5"},
            {"text": "Have difficulty understanding abstract ideas", "trait": "openness", "reverse": True, "question_type": "likert_5"},
            {"text": "Feel comfortable around people", "trait": "extraversion", "reverse": False, "question_type": "likert_5"},
            {"text": "Insult people", "trait": "agreeableness", "reverse": True, "question_type": "likert_5"},
            {"text": "Pay attention to details", "trait": "conscientiousness", "reverse": False, "question_type": "likert_5"},
            {"text": "Worry about things", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Have a vivid imagination", "trait": "openness", "reverse": False, "question_type": "likert_5"},
            {"text": "Keep in the background", "trait": "extraversion", "reverse": True, "question_type": "likert_5"},
            {"text": "Sympathize with others' feelings", "trait": "agreeableness", "reverse": False, "question_type": "likert_5"},
            {"text": "Make a mess of things", "trait": "conscientiousness", "reverse": True, "question_type": "likert_5"},
            {"text": "Seldom feel blue", "trait": "neuroticism", "reverse": True, "question_type": "likert_5"},
            {"text": "Am not interested in abstract ideas", "trait": "openness", "reverse": True, "question_type": "likert_5"},
            {"text": "Start conversations", "trait": "extraversion", "reverse": False, "question_type": "likert_5"},
            {"text": "Am not interested in other people's problems", "trait": "agreeableness", "reverse": True, "question_type": "likert_5"},
            {"text": "Get chores done right away", "trait": "conscientiousness", "reverse": False, "question_type": "likert_5"},
            {"text": "Am easily disturbed", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Have excellent ideas", "trait": "openness", "reverse": False, "question_type": "likert_5"},
            {"text": "Have little to say", "trait": "extraversion", "reverse": True, "question_type": "likert_5"},
            {"text": "Have a soft heart", "trait": "agreeableness", "reverse": False, "question_type": "likert_5"},
            {"text": "Often forget to put things back in their proper place", "trait": "conscientiousness", "reverse": True, "question_type": "likert_5"},
            {"text": "Get upset easily", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Do not have a good imagination", "trait": "openness", "reverse": True, "question_type": "likert_5"},
            {"text": "Talk to a lot of different people at parties", "trait": "extraversion", "reverse": False, "question_type": "likert_5"},
            {"text": "Am not really interested in others", "trait": "agreeableness", "reverse": True, "question_type": "likert_5"},
            {"text": "Like order", "trait": "conscientiousness", "reverse": False, "question_type": "likert_5"},
            {"text": "Change my mood a lot", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Am quick to understand things", "trait": "openness", "reverse": False, "question_type": "likert_5"},
            {"text": "Don't like to draw attention to myself", "trait": "extraversion", "reverse": True, "question_type": "likert_5"},
            {"text": "Take time out for others", "trait": "agreeableness", "reverse": False, "question_type": "likert_5"},
            {"text": "Shirk my duties", "trait": "conscientiousness", "reverse": True, "question_type": "likert_5"},
            {"text": "Have frequent mood swings", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Use difficult words", "trait": "openness", "reverse": False, "question_type": "likert_5"},
            {"text": "Don't mind being the center of attention", "trait": "extraversion", "reverse": False, "question_type": "likert_5"},
            {"text": "Feel others' emotions", "trait": "agreeableness", "reverse": False, "question_type": "likert_5"},
            {"text": "Follow a schedule", "trait": "conscientiousness", "reverse": False, "question_type": "likert_5"},
            {"text": "Get irritated easily", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Spend time reflecting on things", "trait": "openness", "reverse": False, "question_type": "likert_5"},
            {"text": "Am quiet around strangers", "trait": "extraversion", "reverse": True, "question_type": "likert_5"},
            {"text": "Make people feel at ease", "trait": "agreeableness", "reverse": False, "question_type": "likert_5"},
            {"text": "Am exacting in my work", "trait": "conscientiousness", "reverse": False, "question_type": "likert_5"},
            {"text": "Often feel blue", "trait": "neuroticism", "reverse": False, "question_type": "likert_5"},
            {"text": "Am full of ideas", "trait": "openness", "reverse": False, "question_type": "likert_5"},
    ]
        for q in neo_qs:
            db.add(models.Question(**q, test_id=test_objs["NEO-60"].id))

    db.commit()
    print("✅ Données métier avec TYPES et INSTRUCTIONS injectées !")
    db.close()

if __name__ == "__main__":
    seed_data()