"""Schémas JSON des échanges inter-agents (cf. `02_Architecture_MultiAgents.md`, §3)."""

from __future__ import annotations

from typing import Any

# Enveloppe commune à tous les agents : resume + sortie + sources + incertitudes.
ENVELOPPE: dict[str, Any] = {
    "type": "object",
    "required": ["agent", "resume", "sortie", "sources"],
    "properties": {
        "agent": {"type": "string"},
        "resume": {"type": "string", "maxLength": 500},
        "sortie": {"type": "object"},
        "sources": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "incertitudes": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


def _enveloppe(sortie_schema: dict[str, Any]) -> dict[str, Any]:
    """Construit le schéma complet d'un agent à partir du schéma de sa `sortie`."""
    schema: dict[str, Any] = {
        "type": "object",
        "required": list(ENVELOPPE["required"]),
        "properties": {**ENVELOPPE["properties"], "sortie": sortie_schema},
        "additionalProperties": False,
    }
    return schema


# --- Schémas de sortie par agent -------------------------------------------
AG1_SORTIE: dict[str, Any] = {
    "type": "object",
    "required": ["actifs"],
    "properties": {
        "actifs": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id", "nom", "type", "description",
                    "criticite", "valeur", "proprietaire",
                ],
                "properties": {
                    "id": {"type": "string", "pattern": "^A-\\d{2}$"},
                    "nom": {"type": "string", "minLength": 2},
                    "type": {"enum": ["donnée", "application", "service", "tiers", "humain", "intangible"]},
                    "description": {"type": "string"},
                    "criticite": {"type": "array", "items": {"enum": ["C", "I", "A"]}},
                    "valeur": {"enum": ["critique", "élevée", "moyenne", "faible"]},
                    "proprietaire": {"type": "string", "minLength": 2},
                    "contraintes": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": True,
            },
        }
    },
    "additionalProperties": True,
}

AG2_SORTIE: dict[str, Any] = {
    "type": "object",
    "required": [
        "modele_retenu", "modeles_complementaires", "justification",
        "grille_evaluation", "echelle_probabilite", "echelle_impact",
    ],
    "properties": {
        "modele_retenu": {"type": "string", "minLength": 1},
        "modeles_complementaires": {"type": "array", "items": {"type": "string"}},
        "justification": {"type": "string", "minLength": 20},
        "criteres": {"type": "object"},
        "grille_evaluation": {"type": "string", "minLength": 1},
        "echelle_probabilite": {"type": "array", "minItems": 3, "items": {"type": "string"}},
        "echelle_impact": {"type": "array", "minItems": 3, "items": {"type": "string"}},
    },
    "additionalProperties": True,
}

AG3_SORTIE: dict[str, Any] = {
    "type": "object",
    "required": ["menaces"],
    "properties": {
        "menaces": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id_menace", "actif", "frontiere", "description",
                    "categorie", "vulnerabilite", "source_menace",
                ],
                "properties": {
                    "id_menace": {"type": "string", "pattern": "^M-\\d{2}$"},
                    "actif": {"type": "string"},
                    "frontiere": {"type": "string", "pattern": "^[1-6]$"},
                    "description": {"type": "string", "minLength": 10},
                    "categorie": {"type": "string", "pattern": "^(STRIDE|LINDDUN)-[A-Za-z-]+$"},
                    "vulnerabilite": {"type": "string", "minLength": 5},
                    "source_menace": {"type": "string"},
                },
                "additionalProperties": True,
            },
        }
    },
    "additionalProperties": True,
}

AG4_SORTIE: dict[str, Any] = {
    "type": "object",
    "required": ["evaluations"],
    "properties": {
        "evaluations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id_menace", "probabilite", "impact"],
                "properties": {
                    "id_menace": {"type": "string", "pattern": "^M-\\d{2}$"},
                    "probabilite": {"type": "string"},
                    "impact": {"type": "string"},
                    "niveau": {"type": "string"},
                    "justification": {"type": "string", "minLength": 10},
                },
                "additionalProperties": True,
            },
        }
    },
    "additionalProperties": True,
}

AG5_SORTIE: dict[str, Any] = {
    "type": "object",
    "required": ["risques"],
    "properties": {
        "risques": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id", "actif", "menace_id", "menace", "categorie", "probabilite",
                    "impact", "niveau", "traitement", "mesures",
                    "justification", "sources", "risque_residuel", "proprietaire",
                ],
                "properties": {
                    "id": {"type": "string", "pattern": "^R-\\d{2}$"},
                    "actif": {"type": "string"},
                    "menace_id": {"type": "string", "pattern": "^M-\\d{2}$"},
                    "menace": {"type": "string", "minLength": 10},
                    "categorie": {"type": "string"},
                    "probabilite": {"type": "string"},
                    "impact": {"type": "string"},
                    "niveau": {"type": "string"},
                    "traitement": {"type": "string"},
                    "mesures": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                    "justification": {"type": "string", "minLength": 10},
                    "sources": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                    "risque_residuel": {"type": "string"},
                    "proprietaire": {"type": "string"},
                    "valide_par": {"type": "null"},
                },
                "additionalProperties": True,
            },
        },
        "synthèse": {"type": "object"},
    },
    "additionalProperties": True,
}

# Map agent → schéma de la sortie.
SCHEMAS_SORTIE: dict[str, dict[str, Any]] = {
    "AG1": AG1_SORTIE,
    "AG2": AG2_SORTIE,
    "AG3": AG3_SORTIE,
    "AG4": AG4_SORTIE,
    "AG5": AG5_SORTIE,
}


def schema_agent(nom_agent: str) -> dict[str, Any]:
    """Retourne le schéma complet (enveloppe + sortie) d'un agent."""
    return _enveloppe(SCHEMAS_SORTIE[nom_agent])