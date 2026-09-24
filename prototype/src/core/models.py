"""Modèles de données partagés entre agents et orchestrateur."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Actif:
    """Actif identifié par l'Agent 1."""

    id: str
    nom: str
    type: str
    description: str
    criticite: list[str]
    valeur: str
    proprietaire: str
    contraintes: list[str] = field(default_factory=list)


@dataclass
class Menace:
    """Menace identifiée par l'Agent 3."""

    id_menace: str
    actif: str
    frontiere: str
    description: str
    categorie: str
    vulnerabilite: str
    source_menace: str


@dataclass
class Evaluation:
    """Évaluation probabilité × impact (Agent 4)."""

    id_menace: str
    probabilite: str
    impact: str
    niveau: str
    justification: str


@dataclass
class Risque:
    """Ligne du registre des risques (Agent 5 + validation humaine)."""

    id: str
    actif: str
    menace: str
    categorie: str
    probabilite: str
    impact: str
    niveau: str
    traitement: str
    mesures: list[str]
    justification: str
    sources: list[str]
    risque_residuel: str
    proprietaire: str
    valide_par: str | None = None


def as_dict(obj: Any) -> dict[str, Any]:
    """Convertisseur simple dataclass → dict (JSON-serialisable)."""
    import dataclasses

    return dataclasses.asdict(obj)