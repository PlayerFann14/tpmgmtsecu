"""Outil `chencher_connaissance` : recherche RAG dans la base de connaissances.

La base (`knowledge/*.md`) est en lecture seule, versionnée, et chaque extrait
renvoyé est accompagné de sa référence (fichier + en-tête) — les agents doivent
la recopier dans `sources` (contre-poisonning, G10).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..core.config import KNOWLEDGE_DIR


class BaseConnaissances:
    """Charge les fichiers de référence une seule fois et les indexe par mot-clé."""

    def __init__(self, repertoire: Path | None = None) -> None:
        self._repertoire = repertoire or KNOWLEDGE_DIR
        self._documents: dict[str, str] = {}
        self._charger()

    def _charger(self) -> None:
        for fichier in sorted(self._repertoire.glob("*.md")):
            self._documents[fichier.stem] = fichier.read_text(encoding="utf-8")

    def noms_documents(self) -> list[str]:
        return sorted(self._documents)

    def retrouver(self, requete: str, *, limite: int = 3, mots_min: int = 2) -> list[dict[str, str]]:
        """Renvoie les extraits les plus pertinents (mots-clés) + leur référence."""
        mots = {m for m in re.findall(r"[a-zà-ÿ0-9]{3,}", requete.lower()) if m not in _MOTS_VIDES}
        resultats: list[dict[str, str]] = []
        for nom_doc, contenu in self._documents.items():
            blocs = re.split(r"\n(?=#{1,3} )", contenu)
            for bloc in blocs:
                titre = bloc.splitlines()[0].strip(" #") if bloc.splitlines() else ""
                score = sum(1 for mot in mots if mot in bloc.lower())
                if score >= mots_min:
                    resultats.append({
                        "reference": f"knowledge/{nom_doc}.md · {titre}",
                        "extrait": bloc[:400].strip(),
                        "score": str(score),
                    })
        resultats.sort(key=lambda r: -int(r["score"]))
        return resultats[:limite]


_MOTS_VIDES = {
    "avec", "pour", "dans", "une", "des", "les", "est", "sont", "qui",
    "que", "quoi", "comment", "par", "sur", "vers", "entre", "mais", "donc",
    "question", "système", "systèmes", "chaque", "tous", "toutes", "quels",
}


def chercher_connaissance(requete: str, base_nom: str = "", **_: object) -> dict[str, object]:
    """Interface d'outil : recherche dans la base globale ou un fichier précis."""
    base = BaseConnaissances()
    if base_nom:
        if base_nom not in base.noms_documents():
            raise ValueError(f"document de connaissance inconnu : {base_nom}")
        cible = {base_nom: base._documents[base_nom]}
        extraits = _decouper(cible, requete)
    else:
        resultats = base.retrouver(requete)
        extraits = resultats
    return {"resultats": extraits, "documents_disponibles": base.noms_documents()}


def _decouper(documents: dict[str, str], requete: str) -> list[dict[str, str]]:
    import re as _re

    mots = {m for m in _re.findall(r"[a-zà-ÿ0-9]{3,}", requete.lower()) if m not in _MOTS_VIDES}
    resultats: list[dict[str, str]] = []
    for nom_doc, contenu in documents.items():
        for bloc in _re.split(r"\n(?=#{1,3} )", contenu):
            titre = bloc.splitlines()[0].strip(" #") if bloc.splitlines() else ""
            if sum(1 for mot in mots if mot in bloc.lower()) >= 1:
                resultats.append({
                    "reference": f"knowledge/{nom_doc}.md · {titre}",
                    "extrait": bloc[:400].strip(),
                })
    return resultats