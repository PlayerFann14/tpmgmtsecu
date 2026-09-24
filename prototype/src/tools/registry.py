"""Registre d'outils : lecture seule + liste blanche par agent (garde-fous G2, G3).

Trois propriétés exigées :
- lecture seule (aucun outil ne peut écrire/exécuter) ;
- liste blanche : chaque agent n'a accès qu'aux outils déclarés dans sa fiche ;
- journalisation de chaque appel.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..core.journal import Journal

# Signature d'un outil : (kwargs) -> dict résultat (JSON-serialisable).
Outil = Callable[..., dict[str, Any]]


class RegistreOutils:
    """Contient la liste des outils disponibles (nom → fonction)."""

    def __init__(self) -> None:
        self._outils: dict[str, Outil] = {}

    def enregistrer(self, nom: str, fonction: Outil) -> None:
        self._outils[nom] = fonction

    def noms(self) -> list[str]:
        return sorted(self._outils)


class SandboxOutils:
    """Vue restreinte pour un agent : ne propose QUE ses outils autorisés."""

    def __init__(self, registre: RegistreOutils, agent: str,
                 outils_autorises: list[str], journal: Journal) -> None:
        interdits = [o for o in outils_autorises if o not in registre._outils]
        if interdits:
            raise ValueError(f"Agent {agent} : outils inconnus {interdits}")
        self._registre = registre
        self._agent = agent
        self._autorises = set(outils_autorises)
        self._journal = journal

    def description_pour_prompt(self) -> str:
        return ", ".join(sorted(self._autorises))

    def appeler(self, nom: str, **kwargs: Any) -> dict[str, Any]:
        """Exécute un outil si autorisé (sinon erreur = moindre privilège)."""
        if nom not in self._autorises:
            raise PermissionError(
                f"Agent {self._agent} : outil '{nom}' non autorisé (moindre privilège)"
            )
        fonction = self._registre._outils[nom]
        resultat = fonction(**kwargs)
        self._journal.appels_agents(
            nom_agent=self._agent, tentative=0, statut="outil",
            outils=[nom], n_sortie=len(str(resultat)),
        )
        return resultat