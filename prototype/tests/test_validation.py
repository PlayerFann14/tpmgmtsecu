"""Tests des garde-fous de validation (sources, valide_par, traitements, échelles)."""

from __future__ import annotations

import pytest

from src.core.validation import (
    calculer_niveau,
    toutes_les_erreurs,
    valider_schema,
    verifier_niveaux_agent4,
    verifier_niveaux_agent5,
    verifier_sources,
    verifier_traitements,
    verifier_valide_par,
)

from src.core.schemas import SCHEMAS_SORTIE


def _enveloppe(agent: str, sortie: object, sources: list[str] | None = None) -> dict:
    return {
        "agent": agent,
        "resume": "résumé",
        "sortie": sortie,
        "sources": sources if sources is not None else ["STRIDE"],
        "incertitudes": [],
    }


def test_schema_agent5_valide():
    sortie = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01", "menace_id": "M-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
        "traitement": "réduire", "mesures": ["MFA (technique/préventif)"],
        "justification": "justification suffisante", "sources": ["STRIDE"],
        "risque_residuel": "moyen", "proprietaire": "RSSI", "valide_par": None,
    }]})
    assert toutes_les_erreurs("AG5", sortie) == []


def test_schema_rejette_json_incomplet():
    sortie = _enveloppe("AG1", {"actifs": [{"id": "A-01"}]})
    erreurs = valider_schema("AG1", sortie)
    assert any("required" in e for e in erreurs)


def test_sources_vides_rejetees():
    sortie = _enveloppe("AG1", {"actifs": []}, sources=[])
    assert verifier_sources(sortie) != []


def test_valide_par_reserve_a_l_humain():
    sortie = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01", "menace_id": "M-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
        "traitement": "réduire", "mesures": ["MFA"], "justification": "justif",
        "sources": ["STRIDE"], "risque_residuel": "moyen",
        "proprietaire": "RSSI", "valide_par": "agent",
    }]})
    assert verifier_valide_par(sortie) != []


def test_traitement_ignorer_interdit():
    sortie = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01", "menace_id": "M-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
        "traitement": "ignorer", "mesures": [], "justification": "justif",
        "sources": ["STRIDE"], "risque_residuel": "moyen",
        "proprietaire": "RSSI", "valide_par": None,
    }]})
    assert verifier_traitements(sortie) != []


def test_traitement_inconnu_rejete():
    sortie = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01", "menace_id": "M-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
        "traitement": "peut-être", "mesures": ["MFA"], "justification": "justif",
        "sources": ["STRIDE"], "risque_residuel": "moyen",
        "proprietaire": "RSSI", "valide_par": None,
    }]})
    assert verifier_traitements(sortie) != []


def test_niveau_incoherent_detecte():
    sortie = _enveloppe("AG4", {"evaluations": [
        {"id_menace": "M-01", "probabilite": "moyenne", "impact": "élevé",
         "niveau": "faible", "justification": "justification suffisante"},
    ]})
    erreurs = verifier_niveaux_agent4(sortie)
    assert any("niveau" in e for e in erreurs)


def test_niveau_coherent_passe():
    sortie = _enveloppe("AG4", {"evaluations": [
        {"id_menace": "M-01", "probabilite": "moyenne", "impact": "élevé",
         "niveau": calculer_niveau("moyenne", "élevé"), "justification": "justification"},
    ]})
    assert verifier_niveaux_agent4(sortie) == []


def test_echelle_hors_borne_rejetee():
    sortie = _enveloppe("AG4", {"evaluations": [
        {"id_menace": "M-01", "probabilite": "très probable", "impact": "élevé",
         "niveau": "critique", "justification": "justification suffisante"},
    ]})
    erreurs = toutes_les_erreurs("AG4", sortie)
    assert any("hors échelle" in e for e in erreurs)


# --- Contournements issus de la revue QA (à ne pas faire repasser) -----------

def test_valide_par_chainage_null_rejete():
    """La chaîne JSON 'null' n'est PAS acceptée (seul null réel l'est)."""
    sortie = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01", "menace_id": "M-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
        "traitement": "réduire", "mesures": ["MFA"], "justification": "justif",
        "sources": ["STRIDE"], "risque_residuel": "moyen",
        "proprietaire": "RSSI", "valide_par": "null",
    }]})
    assert verifier_valide_par(sortie) != []


def test_agent5_menace_id_requis_par_schema():
    """Sans menace_id, le risque ne peut pas être rattaché à l'étape 4 : bloquant."""
    sans_lien = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
        "traitement": "réduire", "mesures": ["MFA"], "justification": "justif",
        "sources": ["STRIDE"], "risque_residuel": "moyen",
        "proprietaire": "RSSI", "valide_par": None,
    }]})
    assert "menace_id" in SCHEMAS_SORTIE["AG5"]["properties"]["risques"]["items"]["required"]
    erreurs = valider_schema("AG5", sans_lien)
    assert any("menace_id" in e for e in erreurs)


def test_agent5_niveau_non_matriciel_bloque():
    """G7 étendu au registre final : un niveau que la matrice ne produit pas est rejeté."""
    sortie = _enveloppe("AG5", {"risques": [{
        "id": "R-01", "actif": "A-01", "menace_id": "M-01",
        "menace": "une menace concrète assez longue", "categorie": "STRIDE-I",
        "probabilite": "faible", "impact": "faible", "niveau": "critique",
        "traitement": "réduire", "mesures": ["MFA"], "justification": "justif",
        "sources": ["STRIDE"], "risque_residuel": "moyen",
        "proprietaire": "RSSI", "valide_par": None,
    }]})
    erreurs = verifier_niveaux_agent5(sortie)
    assert any("critique" in e and "faible" in e for e in erreurs)


def test_agent4_echo_echelle_inventee_rejete():
    """Une échelle inventée par AG4 dans sa sortie ne doit jamais autoriser P hors matrice."""
    sortie = _enveloppe("AG4", {"evaluations": [
        {"id_menace": "M-01", "probabilite": "très probable", "impact": "élevé",
         "niveau": "critique", "justification": "justification suffisante"},
    ], "echelle_probabilite": ["très probable", "moyenne", "faible"],
        "echelle_impact": ["faible", "moyen", "élevé"]})
    erreurs = toutes_les_erreurs("AG4", sortie)
    # L'écho ne doit pas sauver l'évaluation : 'très probable' reste hors échelle.
    assert any("très probable" in e for e in erreurs)