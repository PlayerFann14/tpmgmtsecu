"""Outil `calculer_niveau` : matrice probabilité × impact (déterministe, G7).

Le LLM ne détermine JAMAIS le niveau seul : l'orchestrateur applique cet outil
et la validation recalcule systématiquement (voir core/validation.py).
"""

from __future__ import annotations

from ..core.config import MATRICE_RISQUE


def calculer_niveau(probabilite: str, impact: str, **_: object) -> dict[str, str]:
    """Calcule le niveau de risque à partir de la probabilité et de l'impact."""
    p = probabilite.strip().lower()
    i = impact.strip().lower()
    if p not in MATRICE_RISQUE or i not in MATRICE_RISQUE[p]:
        raise ValueError(
            f"Probabilité/impact hors échelle : '{probabilite}' × '{impact}' "
            f"(échelles : {list(MATRICE_RISQUE)} × {list(MATRICE_RISQUE['faible'])})"
        )
    return {"probabilite": p, "impact": i, "niveau": MATRICE_RISQUE[p][i]}