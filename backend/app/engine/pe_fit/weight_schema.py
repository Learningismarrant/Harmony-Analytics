from __future__ import annotations

from typing import Dict


def validate_weights(weights: Dict[str, float], context: str = "") -> None:
    """
    Valide un dictionnaire de poids SME.
    Lève ValueError si les contraintes ne sont pas respectées.

    Contraintes :
    - Le dict ne doit pas être vide
    - Chaque poids w_t doit être > 0 et <= 1.0
    - La somme Σw_t doit être > 0
    """
    prefix = f"[{context}] " if context else ""

    if not weights:
        raise ValueError(f"{prefix}weights dict must not be empty")

    for trait, value in weights.items():
        if value <= 0:
            raise ValueError(
                f"{prefix}weight for trait '{trait}' must be > 0, got {value}"
            )
        if value > 1.0:
            raise ValueError(
                f"{prefix}weight for trait '{trait}' must be <= 1.0, got {value}"
            )

    total = sum(weights.values())
    if total <= 0:
        raise ValueError(
            f"{prefix}sum of weights must be > 0, got {total}"
        )
