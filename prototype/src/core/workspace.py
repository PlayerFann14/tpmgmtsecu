"""Espace de travail partagé (mémoire) : orchestrateur → workspace.json.

Seul l'orchestrateur écrit cet espace. Les agents renvoient leurs sorties ;
l'orchestrateur les valide, les normalise et les stocke.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Workspace:
    """Mémoire partagée de la session d'analyse."""

    def __init__(self, *, cas: str, description_systeme: str, repertoire: Path) -> None:
        self._repertoire = repertoire
        self._repertoire.mkdir(parents=True, exist_ok=True)
        self._donnees: dict[str, Any] = {
            "session": datetime.now(timezone.utc).strftime("CAS-B-%Y%m%d-%H%M%S"),
            "cas": cas,
            "statuts": {},           # étape -> {"statut", "tentatives", "erreurs"}
            "produits": {},          # étape -> sortie normalisée
            "journal": {},
        }
        self.description_systeme = description_systeme

    # --- écriture (orchestrateur uniquement) --------------------------------
    def set_etape(self, nom_etape: str, produit: Any, *, tentatives: int,
                  erreurs: list[str] | None = None) -> None:
        self._donnees["produits"][nom_etape] = produit
        self._donnees["statuts"][nom_etape] = {
            "statut": "ok" if not erreurs else "reparé",
            "tentatives": tentatives,
            "erreurs": erreurs or [],
        }

    def set_final(self, registre: list[dict[str, Any]]) -> None:
        self._donnees["registre_final"] = registre

    # --- lecture -------------------------------------------------------------
    def produit(self, nom_etape: str) -> Any:
        return self._donnees["produits"].get(nom_etape)

    def produits(self) -> dict[str, Any]:
        return dict(self._donnees["produits"])

    def statuts(self) -> dict[str, Any]:
        return self._donnees["statuts"]

    def registre(self) -> list[dict[str, Any]]:
        return self._donnees.get("registre_final", [])

    def chemin_workspace(self) -> Path:
        return self._repertoire / "workspace.json"

    # --- persistance ----------------------------------------------------------
    def sauvegarder(self) -> Path:
        chemin = self._repertoire / "workspace.json"
        with chemin.open("w", encoding="utf-8") as fh:
            json.dump(self._donnees, fh, ensure_ascii=False, indent=2)
        return chemin


def charger_registre(chemin: Path) -> list[dict[str, Any]]:
    """Recharge un registre depuis un workspace sauvegardé (pour validation humaine)."""
    with chemin.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("registre_final") or []