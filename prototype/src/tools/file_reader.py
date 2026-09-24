"""Outil `lire_fichier` : lecture seule, restreinte au dossier `cases/`.

Garanties : pas d'écriture, pas de traverse de chemin (..), taille maximale.
Le contenu lu est traité comme DONNÉE non fiable (à passer par le sanitizer).
"""

from __future__ import annotations

from pathlib import Path

from ..core.config import CASES_DIR, MAX_DOCUMENT_OCTETS


class LectureInterditeError(Exception):
    """Levée quand le chemin demandé n'est pas autorisé."""


def lire_fichier(path: str, **_: object) -> dict[str, object]:
    """Lit un fichier de description de système (uniquement dans cases/)."""
    demande = Path(path).resolve()
    racine = CASES_DIR.resolve()

    if not demande.is_relative_to(racine):
        raise LectureInterditeError(f"chemin hors du répertoire autorisé : {path}")

    if not demande.is_file():
        raise FileNotFoundError(f"fichier introuvable : {path}")

    octets = demande.stat().st_size
    if octets > MAX_DOCUMENT_OCTETS:
        raise ValueError(f"document trop volumineux pour l'analyse : {octets} octets")

    contenu = demande.read_text(encoding="utf-8")
    return {
        "chemin": str(demande.relative_to(racine)),
        "octets": octets,
        "contenu": contenu,
    }