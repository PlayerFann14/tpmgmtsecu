"""Tests de la matrice probabilité × impact (sujet p. 8)."""

from __future__ import annotations

import pytest

from src.core.validation import calculer_niveau

CAS_EXPECTES = {
    ("élevée", "faible"): "moyen",
    ("élevée", "moyen"): "élevé",
    ("élevée", "élevé"): "critique",
    ("moyenne", "faible"): "faible",
    ("moyenne", "moyen"): "moyen",
    ("moyenne", "élevé"): "élevé",
    ("faible", "faible"): "faible",
    ("faible", "moyen"): "faible",
    ("faible", "élevé"): "moyen",
}


@pytest.mark.parametrize("p,i,attendu", [
    (p, i, attendu) for (p, i), attendu in CAS_EXPECTES.items()
])
def test_calculer_niveau(p, i, attendu):
    assert calculer_niveau(p, i) == attendu


def test_calculer_niveau_hors_echelle():
    with pytest.raises(ValueError):
        calculer_niveau("très probable", "élevé")


def test_calculer_niveau_insensible_a_la_casse():
    assert calculer_niveau("ÉLEVÉE", "ÉLEVÉ") == "critique"