"""Journalisation horodatée de toutes les actions (garde-fou G5, STRIDE-R).

Chaque événement est écrit en JSON-lines : agent, tentative, statut, outils,
tailles, erreurs. Conservé dans `runs/<session>/journal.jsonl`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Journal:
    """Journal séquentiel horodaté, écriture append-only."""

    def __init__(self, chemin: Path) -> None:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        self._fichier = chemin
        # Entêtes standard (afin de tracer l'ouverture de session).
        self.ecrire({"type": "session_debut", "chemin": str(chemin)})

    def ecrire(self, evenement: dict[str, Any]) -> None:
        ligne = {"ts": _iso_now(), **evenement}
        with self._fichier.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(ligne, ensure_ascii=False) + "\n")

    def appels_agents(self, *, nom_agent: str, tentative: int, statut: str,
                      outils: list[str] | None = None, n_entree: int = 0,
                      n_sortie: int = 0, erreurs: list[str] | None = None) -> None:
        self.ecrire({
            "type": "appel_agent",
            "agent": nom_agent,
            "tentative": tentative,
            "statut": statut,
            "outils": outils or [],
            "octets_entree": n_entree,
            "octets_sortie": n_sortie,
            "erreurs": erreurs or [],
        })

    def injection_detectee(self, detections: list[dict[str, str]]) -> None:
        self.ecrire({"type": "injection_detectee", "detections": detections})

    def validation_humaine(self, risque_id: str, valide_par: str, decision: str) -> None:
        self.ecrire({"type": "validation_humaine", "risque": risque_id,
                     "valide_par": valide_par, "decision": decision})