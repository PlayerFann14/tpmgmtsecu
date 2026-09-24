"""Interface abstraite des fournisseurs de LLM (garde-fou G9 : modèle remplaçable)."""

from __future__ import annotations

from typing import Protocol


class FournisseurLLM(Protocol):
    """Contrat minimal : produire un texte à partir de deux blocs de prompt."""

    nom_produit: str

    def complete(self, systeme: str, utilisateur: str) -> str:
        """Retourne la réponse brute (doit être un objet JSON)."""
        ...


def extraire_json(reponse: str) -> str:
    """Extrait la portion JSON d'une réponse bavarde (délimiteurs de code, texte)."""
    debut = reponse.find("{")
    fin = reponse.rfind("}")
    if debut == -1 or fin == -1 or fin <= debut:
        raise ValueError("aucun objet JSON trouvé dans la réponse du LLM")
    return reponse[debut : fin + 1]