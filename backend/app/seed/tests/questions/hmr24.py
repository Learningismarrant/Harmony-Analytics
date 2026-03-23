# app/seed/tests/questions/hmr24.py
"""
Harmony Matrix Reasoning Test — HMR-24.

24 matrices visuospatiales QCM : induction (8), analogie (8),
raisonnement matriciel (8). Ancré sur le Gf de la théorie CHC
(Carroll-Horn-Cattell, 1993).

Difficulté progressive (order 1 = plus facile, order 24 = plus difficile).
Les traits alternent I/A/MR pour maintenir l'engagement cognitif.

Chaque item utilise question_type="raven" (renderer mobile dédié).
Le scorer backend est scoring_qcm.calculate_qcm_scores() — inchangé,
il lit correct_answer et trait, ignore question_type.

Attributs visuels :
  shape   : circle | square | triangle | diamond
  size    : 1 | 2 | 3
  fill    : empty | half | full
  count   : 1 | 2 | 3
  rotation: 0 | 90 | 180 | 270   (distracteur statique uniquement, jamais règle primaire)

Seuil vitesse : le scorer actuel utilise 2s/item (check_reliability).
TODO (v2) : abaisser à 0.5s pour question_type="raven" — les matrices
nécessitent une réflexion plus longue que des QCM textuels.

    seed_hmr24(db)   → idempotent, retourne le TestCatalogue
    delete_hmr24(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.hmr24
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question
from app.shared.models.Assessment import CatalogueDomain

# ---------------------------------------------------------------------------
# Banque de 24 matrices
# Convention grille :
#   matrix[row][col] — grille 3×3, case manquante = None à [2][2]
#   answer_options : 6 choix A–F, un seul correct
# ---------------------------------------------------------------------------

HMR24_QUESTIONS = [

    # ── order 1 — INDUCTION — diff=1 ────────────────────────────────────────
    # Règle : distribution 3 valeurs de shape sur chaque ligne ET colonne
    # (chaque ligne/colonne contient exactement 1 circle, 1 square, 1 triangle)
    {
        "order": 1,
        "trait": "induction",
        "correct_answer": "C",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                {"id": "B", "shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                {"id": "C", "shape": "square",   "size": 2, "fill": "empty", "count": 1},
                {"id": "D", "shape": "diamond",  "size": 2, "fill": "empty", "count": 1},
                {"id": "E", "shape": "square",   "size": 2, "fill": "half",  "count": 1},
                {"id": "F", "shape": "square",   "size": 1, "fill": "empty", "count": 1},
            ],
            "difficulty": 1,
            "rule": "shape_distribution_3_values",
        },
    },

    # ── order 2 — ANALOGY — diff=1 ──────────────────────────────────────────
    # Règle : size progresse de 1→2→3 sur chaque ligne ; shape constante par ligne
    {
        "order": 2,
        "trait": "analogy",
        "correct_answer": "B",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 3, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "square", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "square", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square", "size": 3, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                {"id": "B", "shape": "triangle", "size": 3, "fill": "empty", "count": 1},
                {"id": "C", "shape": "circle",   "size": 3, "fill": "empty", "count": 1},
                {"id": "D", "shape": "square",   "size": 3, "fill": "empty", "count": 1},
                {"id": "E", "shape": "triangle", "size": 3, "fill": "half",  "count": 1},
                {"id": "F", "shape": "diamond",  "size": 3, "fill": "empty", "count": 1},
            ],
            "difficulty": 1,
            "rule": "size_progression_shape_constant",
        },
    },

    # ── order 3 — MATRIX_REASONING — diff=2 ─────────────────────────────────
    # Règle : fill progresse empty→half→full sur chaque colonne ; shape constante
    {
        "order": 3,
        "trait": "matrix_reasoning",
        "correct_answer": "A",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "square", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "square", "size": 2, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 2, "fill": "full",  "count": 1},
                {"id": "B", "shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                {"id": "C", "shape": "circle",   "size": 2, "fill": "full",  "count": 1},
                {"id": "D", "shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                {"id": "E", "shape": "triangle", "size": 1, "fill": "full",  "count": 1},
                {"id": "F", "shape": "diamond",  "size": 2, "fill": "full",  "count": 1},
            ],
            "difficulty": 2,
            "rule": "fill_progression_column",
        },
    },

    # ── order 4 — INDUCTION — diff=1 ────────────────────────────────────────
    # Règle : count progresse 1→2→3 sur chaque ligne ; shape et fill constants
    {
        "order": 4,
        "trait": "induction",
        "correct_answer": "D",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 2},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 3},
                ],
                [
                    {"shape": "square", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "square", "size": 2, "fill": "half",  "count": 2},
                    {"shape": "square", "size": 2, "fill": "half",  "count": 3},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "full", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "full", "count": 2},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 2, "fill": "full", "count": 1},
                {"id": "B", "shape": "triangle", "size": 2, "fill": "full", "count": 2},
                {"id": "C", "shape": "triangle", "size": 2, "fill": "half", "count": 3},
                {"id": "D", "shape": "triangle", "size": 2, "fill": "full", "count": 3},
                {"id": "E", "shape": "circle",   "size": 2, "fill": "full", "count": 3},
                {"id": "F", "shape": "triangle", "size": 3, "fill": "full", "count": 3},
            ],
            "difficulty": 1,
            "rule": "count_progression_row",
        },
    },

    # ── order 5 — ANALOGY — diff=1 ──────────────────────────────────────────
    # Règle : fill distribué (empty/half/full) sur chaque ligne ET colonne
    {
        "order": 5,
        "trait": "analogy",
        "correct_answer": "E",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "full",  "count": 1},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle", "size": 2, "fill": "full",  "count": 1},
                {"id": "B", "shape": "circle", "size": 2, "fill": "empty", "count": 1},
                {"id": "C", "shape": "square", "size": 2, "fill": "half",  "count": 1},
                {"id": "D", "shape": "circle", "size": 1, "fill": "half",  "count": 1},
                {"id": "E", "shape": "circle", "size": 2, "fill": "half",  "count": 1},
                {"id": "F", "shape": "circle", "size": 3, "fill": "half",  "count": 1},
            ],
            "difficulty": 1,
            "rule": "fill_distribution_3_values",
        },
    },

    # ── order 6 — MATRIX_REASONING — diff=2 ─────────────────────────────────
    # Règle : size distribué (1/2/3) sur chaque ligne ET colonne
    {
        "order": 6,
        "trait": "matrix_reasoning",
        "correct_answer": "C",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "square", "size": 1, "fill": "half", "count": 1},
                    {"shape": "square", "size": 2, "fill": "half", "count": 1},
                    {"shape": "square", "size": 3, "fill": "half", "count": 1},
                ],
                [
                    {"shape": "square", "size": 2, "fill": "half", "count": 1},
                    {"shape": "square", "size": 3, "fill": "half", "count": 1},
                    {"shape": "square", "size": 1, "fill": "half", "count": 1},
                ],
                [
                    {"shape": "square", "size": 3, "fill": "half", "count": 1},
                    {"shape": "square", "size": 1, "fill": "half", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "square", "size": 1, "fill": "half",  "count": 1},
                {"id": "B", "shape": "square", "size": 3, "fill": "half",  "count": 1},
                {"id": "C", "shape": "square", "size": 2, "fill": "half",  "count": 1},
                {"id": "D", "shape": "circle", "size": 2, "fill": "half",  "count": 1},
                {"id": "E", "shape": "square", "size": 2, "fill": "empty", "count": 1},
                {"id": "F", "shape": "square", "size": 2, "fill": "full",  "count": 1},
            ],
            "difficulty": 2,
            "rule": "size_distribution_3_values",
        },
    },

    # ── order 7 — INDUCTION — diff=1 ────────────────────────────────────────
    # Règle : shape constante par ligne, fill constant par ligne (tout identique)
    # La règle cachée : chaque ligne a une shape ET un fill unique, la 3e case
    # doit correspondre à la même shape/fill que les deux premières de la ligne
    {
        "order": 7,
        "trait": "induction",
        "correct_answer": "F",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 1, "fill": "empty", "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle",   "size": 3, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "square",   "size": 1, "fill": "half",  "count": 1},
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 1},
                    {"shape": "square",   "size": 3, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "diamond",  "size": 1, "fill": "full",  "count": 1},
                    {"shape": "diamond",  "size": 2, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "diamond", "size": 3, "fill": "empty", "count": 1},
                {"id": "B", "shape": "circle",  "size": 3, "fill": "full",  "count": 1},
                {"id": "C", "shape": "diamond", "size": 3, "fill": "half",  "count": 1},
                {"id": "D", "shape": "square",  "size": 3, "fill": "full",  "count": 1},
                {"id": "E", "shape": "diamond", "size": 2, "fill": "full",  "count": 1},
                {"id": "F", "shape": "diamond", "size": 3, "fill": "full",  "count": 1},
            ],
            "difficulty": 1,
            "rule": "shape_and_fill_constant_per_row_size_progression",
        },
    },

    # ── order 8 — ANALOGY — diff=2 ──────────────────────────────────────────
    # Règle : count distribué (1/2/3) ET shape distribué — double règle
    {
        "order": 8,
        "trait": "analogy",
        "correct_answer": "A",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 3},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 3},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 2},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 2},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 3},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "square",   "size": 2, "fill": "empty", "count": 1},
                {"id": "B", "shape": "square",   "size": 2, "fill": "empty", "count": 2},
                {"id": "C", "shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                {"id": "D", "shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                {"id": "E", "shape": "square",   "size": 2, "fill": "half",  "count": 1},
                {"id": "F", "shape": "diamond",  "size": 2, "fill": "empty", "count": 1},
            ],
            "difficulty": 2,
            "rule": "shape_distribution_AND_count_distribution",
        },
    },

    # ── order 9 — MATRIX_REASONING — diff=2 ─────────────────────────────────
    # Règle : taille croît dans chaque ligne (1→2→3) ET fill croît par colonne
    # (empty→half→full par colonne)
    {
        "order": 9,
        "trait": "matrix_reasoning",
        "correct_answer": "D",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 3, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle", "size": 1, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 3, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "circle", "size": 1, "fill": "full",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle", "size": 2, "fill": "full",  "count": 1},
                {"id": "B", "shape": "circle", "size": 3, "fill": "half",  "count": 1},
                {"id": "C", "shape": "circle", "size": 3, "fill": "empty", "count": 1},
                {"id": "D", "shape": "circle", "size": 3, "fill": "full",  "count": 1},
                {"id": "E", "shape": "square", "size": 3, "fill": "full",  "count": 1},
                {"id": "F", "shape": "circle", "size": 3, "fill": "full",  "count": 2},
            ],
            "difficulty": 2,
            "rule": "size_progression_row_AND_fill_progression_column",
        },
    },

    # ── order 10 — INDUCTION — diff=2 ───────────────────────────────────────
    # Règle : count[ligne][col] = col_index + 1 ET shape distribué par colonne
    {
        "order": 10,
        "trait": "induction",
        "correct_answer": "B",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 3},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "half",  "count": 2},
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 3},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "full",  "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 2},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                {"id": "B", "shape": "circle",   "size": 2, "fill": "full",  "count": 3},
                {"id": "C", "shape": "square",   "size": 2, "fill": "full",  "count": 3},
                {"id": "D", "shape": "diamond",  "size": 2, "fill": "full",  "count": 3},
                {"id": "E", "shape": "circle",   "size": 2, "fill": "half",  "count": 3},
                {"id": "F", "shape": "circle",   "size": 2, "fill": "full",  "count": 2},
            ],
            "difficulty": 2,
            "rule": "count_constant_per_column_AND_shape_distribution",
        },
    },

    # ── order 11 — ANALOGY — diff=2 ─────────────────────────────────────────
    # Règle : size constant par colonne (col0=1, col1=2, col2=3)
    #         fill progresse sur la ligne (empty→half→full)
    {
        "order": 11,
        "trait": "analogy",
        "correct_answer": "C",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "diamond", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "diamond", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "diamond", "size": 3, "fill": "full",  "count": 1},
                ],
                [
                    {"shape": "diamond", "size": 1, "fill": "empty", "count": 2},
                    {"shape": "diamond", "size": 2, "fill": "half",  "count": 2},
                    {"shape": "diamond", "size": 3, "fill": "full",  "count": 2},
                ],
                [
                    {"shape": "diamond", "size": 1, "fill": "empty", "count": 3},
                    {"shape": "diamond", "size": 2, "fill": "half",  "count": 3},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "diamond", "size": 3, "fill": "half",  "count": 3},
                {"id": "B", "shape": "diamond", "size": 2, "fill": "full",  "count": 3},
                {"id": "C", "shape": "diamond", "size": 3, "fill": "full",  "count": 3},
                {"id": "D", "shape": "circle",  "size": 3, "fill": "full",  "count": 3},
                {"id": "E", "shape": "diamond", "size": 3, "fill": "full",  "count": 2},
                {"id": "F", "shape": "diamond", "size": 3, "fill": "empty", "count": 3},
            ],
            "difficulty": 2,
            "rule": "size_constant_per_column_AND_fill_progression_row",
        },
    },

    # ── order 12 — MATRIX_REASONING — diff=2 ────────────────────────────────
    # Règle : shape distribué par ligne ET count distribué par colonne (double)
    {
        "order": 12,
        "trait": "matrix_reasoning",
        "correct_answer": "E",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 3},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 2},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 3},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 3},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle",   "size": 2, "fill": "empty", "count": 2},
                {"id": "B", "shape": "square",   "size": 2, "fill": "empty", "count": 2},
                {"id": "C", "shape": "triangle", "size": 2, "fill": "half",  "count": 2},
                {"id": "D", "shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                {"id": "E", "shape": "circle",   "size": 2, "fill": "empty", "count": 2},
                {"id": "F", "shape": "diamond",  "size": 2, "fill": "empty", "count": 2},
            ],
            "difficulty": 2,
            "rule": "shape_distribution_row_AND_count_distribution_column",
        },
    },

    # ── order 13 — INDUCTION — diff=2 ───────────────────────────────────────
    # Règle : taille décroît de gauche à droite (3→2→1), fill distribué colonne
    {
        "order": 13,
        "trait": "induction",
        "correct_answer": "A",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 3, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 1, "fill": "full",  "count": 1},
                ],
                [
                    {"shape": "square", "size": 3, "fill": "half",  "count": 1},
                    {"shape": "square", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "square", "size": 1, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 3, "fill": "full", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 1, "fill": "half",  "count": 1},
                {"id": "B", "shape": "triangle", "size": 1, "fill": "full",  "count": 1},
                {"id": "C", "shape": "triangle", "size": 1, "fill": "empty", "count": 1},
                {"id": "D", "shape": "circle",   "size": 1, "fill": "half",  "count": 1},
                {"id": "E", "shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                {"id": "F", "shape": "triangle", "size": 1, "fill": "half",  "count": 2},
            ],
            "difficulty": 2,
            "rule": "size_decreasing_row_AND_fill_distribution_column",
        },
    },

    # ── order 14 — ANALOGY — diff=2 ─────────────────────────────────────────
    # Règle : shape change par colonne (distribution) + size progresse par ligne
    {
        "order": 14,
        "trait": "analogy",
        "correct_answer": "F",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 1, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "diamond",  "size": 1, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "diamond",  "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle",   "size": 3, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 3, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 3, "fill": "empty", "count": 1},
                {"id": "B", "shape": "circle",   "size": 3, "fill": "empty", "count": 1},
                {"id": "C", "shape": "diamond",  "size": 2, "fill": "empty", "count": 1},
                {"id": "D", "shape": "square",   "size": 3, "fill": "empty", "count": 1},
                {"id": "E", "shape": "diamond",  "size": 3, "fill": "half",  "count": 1},
                {"id": "F", "shape": "diamond",  "size": 3, "fill": "empty", "count": 1},
            ],
            "difficulty": 2,
            "rule": "shape_constant_per_column_AND_size_progression_row",
        },
    },

    # ── order 15 — MATRIX_REASONING — diff=2 ────────────────────────────────
    # Règle : count[row][col] = row_index + col_index + 1 (addition des indices)
    # row0+col0=1, row0+col1=2, row0+col2=3
    # row1+col0=2, row1+col1=3, row1+col2=4 → mais on cap à 3 → 3
    # Simplification : count = (row + col) mod 3 + 1
    # row=0: 1,2,3 | row=1: 2,3,1 | row=2: 3,1,? → col=2 → (2+2)%3+1=2
    {
        "order": 15,
        "trait": "matrix_reasoning",
        "correct_answer": "B",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 2, "fill": "half", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "half", "count": 2},
                    {"shape": "circle", "size": 2, "fill": "half", "count": 3},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "half", "count": 2},
                    {"shape": "circle", "size": 2, "fill": "half", "count": 3},
                    {"shape": "circle", "size": 2, "fill": "half", "count": 1},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "half", "count": 3},
                    {"shape": "circle", "size": 2, "fill": "half", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle", "size": 2, "fill": "half", "count": 3},
                {"id": "B", "shape": "circle", "size": 2, "fill": "half", "count": 2},
                {"id": "C", "shape": "circle", "size": 2, "fill": "half", "count": 1},
                {"id": "D", "shape": "square", "size": 2, "fill": "half", "count": 2},
                {"id": "E", "shape": "circle", "size": 1, "fill": "half", "count": 2},
                {"id": "F", "shape": "circle", "size": 2, "fill": "full", "count": 2},
            ],
            "difficulty": 2,
            "rule": "count_distribution_latin_square",
        },
    },

    # ── order 16 — INDUCTION — diff=2 ───────────────────────────────────────
    # Règle : shape constante dans chaque colonne + fill distribué sur lignes
    #         + size distribué sur colonnes (3 règles simultanées)
    {
        "order": 16,
        "trait": "induction",
        "correct_answer": "D",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 1, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 3, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle",   "size": 1, "fill": "half",  "count": 1},
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 1},
                    {"shape": "triangle", "size": 3, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "circle",   "size": 1, "fill": "full",  "count": 1},
                    {"shape": "square",   "size": 2, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 3, "fill": "empty", "count": 1},
                {"id": "B", "shape": "triangle", "size": 3, "fill": "half",  "count": 1},
                {"id": "C", "shape": "circle",   "size": 3, "fill": "full",  "count": 1},
                {"id": "D", "shape": "triangle", "size": 3, "fill": "full",  "count": 1},
                {"id": "E", "shape": "square",   "size": 3, "fill": "full",  "count": 1},
                {"id": "F", "shape": "triangle", "size": 2, "fill": "full",  "count": 1},
            ],
            "difficulty": 2,
            "rule": "shape_constant_column_AND_fill_constant_row_AND_size_constant_column",
        },
    },

    # ── order 17 — ANALOGY — diff=2 ─────────────────────────────────────────
    # Règle : count dans chaque ligne est additif (col0 + col1 = col2)
    # row0: 1+2=3, row1: 2+1=3, row2: 1+2=3
    {
        "order": 17,
        "trait": "analogy",
        "correct_answer": "A",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "square", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square", "size": 2, "fill": "empty", "count": 2},
                    {"shape": "square", "size": 2, "fill": "empty", "count": 3},
                ],
                [
                    {"shape": "square", "size": 2, "fill": "half",  "count": 2},
                    {"shape": "square", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "square", "size": 2, "fill": "half",  "count": 3},
                ],
                [
                    {"shape": "square", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "square", "size": 2, "fill": "full",  "count": 2},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "square", "size": 2, "fill": "full",  "count": 3},
                {"id": "B", "shape": "square", "size": 2, "fill": "full",  "count": 2},
                {"id": "C", "shape": "square", "size": 2, "fill": "full",  "count": 1},
                {"id": "D", "shape": "circle", "size": 2, "fill": "full",  "count": 3},
                {"id": "E", "shape": "square", "size": 2, "fill": "empty", "count": 3},
                {"id": "F", "shape": "square", "size": 1, "fill": "full",  "count": 3},
            ],
            "difficulty": 2,
            "rule": "count_additive_col0+col1=col2",
        },
    },

    # ── order 18 — MATRIX_REASONING — diff=3 ────────────────────────────────
    # Règle : shape de col2 = shape de col0 (constante par ligne)
    #         fill de col2 = inverse de fill de col0 (empty↔full, half=half)
    #         size de col2 = size de col1
    {
        "order": 18,
        "trait": "matrix_reasoning",
        "correct_answer": "C",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 1, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 3, "fill": "half",  "count": 1},
                    {"shape": "circle",   "size": 3, "fill": "full",  "count": 1},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "full",  "count": 1},
                    {"shape": "diamond",  "size": 1, "fill": "half",  "count": 1},
                    {"shape": "square",   "size": 1, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 3, "fill": "half",  "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 3, "fill": "full",  "count": 1},
                {"id": "B", "shape": "circle",   "size": 2, "fill": "full",  "count": 1},
                {"id": "C", "shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                {"id": "D", "shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                {"id": "E", "shape": "square",   "size": 2, "fill": "half",  "count": 1},
                {"id": "F", "shape": "triangle", "size": 1, "fill": "half",  "count": 1},
            ],
            "difficulty": 3,
            "rule": "shape_constant_row_AND_fill_complement_AND_size_from_col1",
        },
    },

    # ── order 19 — INDUCTION — diff=2 ───────────────────────────────────────
    # Règle : count croît par diagonale (diagonale principale = count constant,
    # décalage +1 par colonne au sein d'une ligne)
    # row0: 1,2,3 | row1: 2,3,1 | row2: 3,1,? → (3+2)%3=2 → 2
    {
        "order": 19,
        "trait": "induction",
        "correct_answer": "E",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 3},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "half",  "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "half",  "count": 3},
                    {"shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                {"id": "B", "shape": "triangle", "size": 2, "fill": "full",  "count": 1},
                {"id": "C", "shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                {"id": "D", "shape": "circle",   "size": 2, "fill": "full",  "count": 2},
                {"id": "E", "shape": "triangle", "size": 2, "fill": "full",  "count": 2},
                {"id": "F", "shape": "triangle", "size": 1, "fill": "full",  "count": 2},
            ],
            "difficulty": 2,
            "rule": "count_latin_square_diagonal",
        },
    },

    # ── order 20 — ANALOGY — diff=3 ─────────────────────────────────────────
    # Règle : double transposition — shape de [row][col] = shape de [col][row]
    # (matrice symétrique) + fill croît par ligne
    {
        "order": 20,
        "trait": "analogy",
        "correct_answer": "B",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 1},
                    {"shape": "diamond",  "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "circle",   "size": 2, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "square",   "size": 2, "fill": "full",  "count": 1},
                {"id": "B", "shape": "diamond",  "size": 2, "fill": "full",  "count": 1},
                {"id": "C", "shape": "triangle", "size": 2, "fill": "full",  "count": 1},
                {"id": "D", "shape": "diamond",  "size": 2, "fill": "half",  "count": 1},
                {"id": "E", "shape": "circle",   "size": 2, "fill": "full",  "count": 1},
                {"id": "F", "shape": "diamond",  "size": 1, "fill": "full",  "count": 1},
            ],
            "difficulty": 3,
            "rule": "symmetric_matrix_shape_AND_fill_progression_row",
        },
    },

    # ── order 21 — MATRIX_REASONING — diff=3 ────────────────────────────────
    # Règle : shape constante par colonne, fill = résultat d'une opération XOR
    # conceptuel (empty XOR half = full, empty XOR full = half, half XOR full = empty)
    # Ligne 2 (index=2): col0=empty, col1=half, col2=?
    # Règle : pour chaque ligne, les 3 fills sont empty/half/full dans ordre quelconque
    # mais la paire (row,col) suit : fill[row][2] = le fill manquant dans la ligne
    # row0: full, empty, ? → half
    # row1: half, full, ? → empty
    # row2: empty, half, ? → full
    {
        "order": 21,
        "trait": "matrix_reasoning",
        "correct_answer": "D",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "diamond", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "diamond", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "diamond", "size": 2, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "diamond", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "diamond", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "diamond", "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "diamond", "size": 2, "fill": "empty", "count": 1},
                    {"shape": "diamond", "size": 2, "fill": "half",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "diamond", "size": 2, "fill": "empty", "count": 1},
                {"id": "B", "shape": "diamond", "size": 2, "fill": "half",  "count": 1},
                {"id": "C", "shape": "circle",  "size": 2, "fill": "full",  "count": 1},
                {"id": "D", "shape": "diamond", "size": 2, "fill": "full",  "count": 1},
                {"id": "E", "shape": "diamond", "size": 1, "fill": "full",  "count": 1},
                {"id": "F", "shape": "square",  "size": 2, "fill": "full",  "count": 1},
            ],
            "difficulty": 3,
            "rule": "fill_latin_square_each_row_has_all_three_fills",
        },
    },

    # ── order 22 — INDUCTION — diff=2 ───────────────────────────────────────
    # Règle : size[row][2] = size[row][0] + size[row][1] (additive, capé à 3)
    # mais ici 1+1=2, 1+2=3, 2+1=3 — distracteurs avec valeurs proches
    {
        "order": 22,
        "trait": "induction",
        "correct_answer": "F",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 1, "fill": "empty", "count": 1},
                    {"shape": "circle", "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle", "size": 1, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 2, "fill": "half",  "count": 1},
                    {"shape": "circle", "size": 3, "fill": "half",  "count": 1},
                ],
                [
                    {"shape": "circle", "size": 2, "fill": "full",  "count": 1},
                    {"shape": "circle", "size": 1, "fill": "full",  "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle", "size": 1, "fill": "full",  "count": 1},
                {"id": "B", "shape": "circle", "size": 2, "fill": "full",  "count": 1},
                {"id": "C", "shape": "circle", "size": 2, "fill": "empty", "count": 1},
                {"id": "D", "shape": "square", "size": 3, "fill": "full",  "count": 1},
                {"id": "E", "shape": "circle", "size": 3, "fill": "half",  "count": 1},
                {"id": "F", "shape": "circle", "size": 3, "fill": "full",  "count": 1},
            ],
            "difficulty": 2,
            "rule": "size_additive_col0+col1=col2",
        },
    },

    # ── order 23 — ANALOGY — diff=3 ─────────────────────────────────────────
    # Règle : triple distribution simultanée — shape/fill/count tous distribués
    # sur chaque ligne ET chaque colonne (carré latin 3D)
    # shape: row0=[C,S,T] row1=[S,T,C] row2=[T,C,?→S]
    # fill:  row0=[e,h,f] row1=[h,f,e] row2=[f,e,?→h]
    # count: row0=[1,2,3] row1=[2,3,1] row2=[3,1,?→2]
    {
        "order": 23,
        "trait": "analogy",
        "correct_answer": "D",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                ],
                [
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 2},
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "triangle", "size": 2, "fill": "full",  "count": 3},
                    {"shape": "circle",   "size": 2, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "circle",   "size": 2, "fill": "half",  "count": 2},
                {"id": "B", "shape": "triangle", "size": 2, "fill": "half",  "count": 2},
                {"id": "C", "shape": "square",   "size": 2, "fill": "empty", "count": 2},
                {"id": "D", "shape": "square",   "size": 2, "fill": "half",  "count": 2},
                {"id": "E", "shape": "square",   "size": 2, "fill": "full",  "count": 2},
                {"id": "F", "shape": "diamond",  "size": 2, "fill": "half",  "count": 2},
            ],
            "difficulty": 3,
            "rule": "triple_latin_square_shape_fill_count",
        },
    },

    # ── order 24 — MATRIX_REASONING — diff=3 ────────────────────────────────
    # Règle complexe : 3 règles simultanées
    #   - shape constant par colonne : col0=circle, col1=square, col2=triangle
    #   - size = carré latin par ligne : row0=[1,2,3], row1=[2,3,1], row2=[3,1,?→2]
    #   - fill = carré latin par ligne : row0=[empty,half,full], row1=[half,full,empty],
    #            row2=[full,empty,?→half]
    # Donc [2][2]: shape=triangle, size=2, fill=half
    {
        "order": 24,
        "trait": "matrix_reasoning",
        "correct_answer": "E",
        "text": "Complete the matrix.",
        "options": {
            "matrix": [
                [
                    {"shape": "circle",   "size": 1, "fill": "empty", "count": 1},
                    {"shape": "square",   "size": 2, "fill": "half",  "count": 1},
                    {"shape": "triangle", "size": 3, "fill": "full",  "count": 1},
                ],
                [
                    {"shape": "circle",   "size": 2, "fill": "half",  "count": 1},
                    {"shape": "square",   "size": 3, "fill": "full",  "count": 1},
                    {"shape": "triangle", "size": 1, "fill": "empty", "count": 1},
                ],
                [
                    {"shape": "circle",   "size": 3, "fill": "full",  "count": 1},
                    {"shape": "square",   "size": 1, "fill": "empty", "count": 1},
                    None,
                ],
            ],
            "answer_options": [
                {"id": "A", "shape": "triangle", "size": 1, "fill": "full",  "count": 1},
                {"id": "B", "shape": "triangle", "size": 2, "fill": "empty", "count": 1},
                {"id": "C", "shape": "square",   "size": 2, "fill": "half",  "count": 1},
                {"id": "D", "shape": "triangle", "size": 2, "fill": "full",  "count": 2},
                {"id": "E", "shape": "triangle", "size": 2, "fill": "half",  "count": 1},
                {"id": "F", "shape": "circle",   "size": 2, "fill": "full",  "count": 1},
            ],
            "difficulty": 3,
            "rule": "shape_constant_column_AND_size_additive_mod3_AND_fill_progression_diagonal",
        },
    },
]

_CATALOGUE_NAME = "Harmony Matrix Reasoning Test (HMR-24)"


async def seed_hmr24(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent — retourne l'existant si déjà présent."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [hmr24] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Test de raisonnement fluide visuo-spatial — 24 matrices à compléter. "
            "Ancré sur le Gf de la théorie CHC (Carroll-Horn-Cattell). "
            "Mesure l'induction, le raisonnement analogique et l'intégration multi-règles. "
            "Durée estimée : 15-20 minutes."
        ),
        instructions=(
            "Chaque matrice présente une grille 3×3 avec une case manquante (en bas à droite). "
            "Identifiez la règle qui relie les cases et sélectionnez l'option qui complète la matrice. "
            "Il n'y a pas de limite de temps — prenez le temps nécessaire."
        ),
        test_type="qcm",
        max_score_per_question=1,
        n_questions=len(HMR24_QUESTIONS),
        is_active=True,
        status="ALPHA",
        license="CUSTOM_ALPHA",
        domain=CatalogueDomain.cognitive,
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA NON ÉTALONNÉ — PROTOTYPAGE UNIQUEMENT. "
            "Harmony Matrix Reasoning Test — 24 matrices visuospatiales construites ad hoc. "
            "Ancré conceptuellement sur le Gf CHC (Carroll-Horn-Cattell, 1993) et les "
            "Progressive Matrices (Raven, 1938). "
            "NON un test de résilience — mesure le raisonnement fluide (Gf). "
            "À intégrer dans le composite GCA (sous-test Gf) après validation. "
            "Difficulté progressive non étalonnée sur population de référence. "
            "Seuil de vitesse actuel (2s/item) trop bas pour matrices — "
            "TODO v2 : abaisser à 0.5s/item (voir docstring hmr24.py)."
        ),
        modules_config=[
            {"index": 0, "name": "Matrices — Niveau 1 (facile)",
             "items_range": [1, 8], "n_items": 8, "duration_min": 5, "priority": "STANDARD"},
            {"index": 1, "name": "Matrices — Niveau 2 (intermédiaire)",
             "items_range": [9, 16], "n_items": 8, "duration_min": 6, "priority": "STANDARD"},
            {"index": 2, "name": "Matrices — Niveau 3 (difficile)",
             "items_range": [17, 24], "n_items": 8, "duration_min": 8, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in HMR24_QUESTIONS:
        order = q["order"]
        if 1 <= order <= 8:
            module_index = 0
        elif 9 <= order <= 16:
            module_index = 1
        else:
            module_index = 2
        db.add(Question(
            test_id=catalogue.id,
            text=q["text"],
            question_type="raven",
            trait=q["trait"],
            reverse=False,
            order=order,
            correct_answer=q["correct_answer"],
            options=q["options"],
            module_index=module_index,
        ))
    await db.flush()
    print(f"  [hmr24] Créé (id={catalogue.id}, {len(HMR24_QUESTIONS)} questions)")
    return catalogue


async def delete_hmr24(db: AsyncSession) -> None:
    print("  [hmr24] Deleting...")
    result = await db.execute(
        select(TestCatalogue.id).where(TestCatalogue.name == _CATALOGUE_NAME)
    )
    cat_id = result.scalar_one_or_none()
    if cat_id:
        await db.execute(delete(Question).where(Question.test_id == cat_id))
        await db.execute(delete(TestCatalogue).where(TestCatalogue.id == cat_id))
    await db.commit()
    print("  [hmr24] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_hmr24(db)
        await seed_hmr24(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
