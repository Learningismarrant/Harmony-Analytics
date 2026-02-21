#backend/services/feedback.py
def get_client_feedback(normative_score: float, relative_percentile: float) -> str:
    """
    Feedback pour le Recruteur : Direct, précis, aide à la décision.
    """
    if normative_score >= 85:
        fit = "Profil hautement compatible avec les exigences SME."
    elif normative_score >= 70:
        fit = "Profil équilibré pour le poste."
    else:
        fit = "Points de vigilance identifiés par rapport au profil cible."

    pool = f"Se situe dans le top {100 - relative_percentile:.0f}% du vivier." if relative_percentile > 75 else "Positionnement standard."
    
    return f"{fit} {pool}"