"""Fournisseur réel : API compatible OpenAI (chat/completions), via urllib standard.

Aucune dépendance externe, aucun secret codé en dur (garde-fou : clé en variable
d'environnement uniquement). Modèle remplaçable via la config (G9).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .interface import extraire_json


class OpenAICompatProvider:
    """Appelle une API style OpenAI (base_url + clé + modèle)."""

    nom_produit = "openai-compatible (configurable)"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        modele: str | None = None,
        temperature: float = 0.2,
        timeout: int = 120,
    ) -> None:
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.modele = modele or os.environ.get("OPENAI_MODEL", "")
        self.temperature = temperature
        self.timeout = timeout
        self.nom_produit = f"openai-compatible : {self.modele or 'modèle non défini'}"

        if not self.api_key or not self.modele:
            raise ValueError(
                "OPENAI_API_KEY et OPENAI_MODEL (ou OPENAI_BASE_URL) doivent être définis "
                "pour utiliser le fournisseur réel. Sinon : --provider dummy."
            )

    def complete(self, systeme: str, utilisateur: str) -> str:
        corps: dict[str, Any] = {
            "model": self.modele,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": systeme},
                {"role": "user", "content": utilisateur},
            ],
        }
        requete = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(corps).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(requete, timeout=self.timeout) as reponse:
                payload = json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            corps_erreur = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"erreur API {exc.code} : {corps_erreur[:300]}") from exc

        try:
            contenu = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"réponse API inattendue : {str(payload)[:300]}") from exc

        # Le modèle doit produire du JSON : on l'extrait, sinon on échoue (G8).
        return extraire_json(contenu)