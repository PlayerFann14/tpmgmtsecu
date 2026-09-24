"""Fournisseur réel : API compatible OpenAI (chat/completions).

Transport : curl système lorsque disponible — vérification TLS RÉELLE (bundle
système), et la clé API n'apparaît jamais dans la ligne de commande : elle est
injectée par une variable d'environnement développée dans un fichier de config
curl éphémère (mode 0600), le corps JSON étant envoyé sur stdin. Aucun secret
en dur dans le code (garde-fou : clé en variable d'environnement uniquement).
Repli urllib si curl est absent du système. Modèle remplaçable via la config (G9).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
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
        # Timeout surchargeable par environnement (modèles lents : free tier).
        self.timeout = int(os.environ.get("OPENAI_TIMEOUT", str(timeout)))
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
        if shutil.which("curl"):
            contenu = self._appel_avec_curl(corps)
        else:
            contenu = self._appel_avec_urllib(corps)
        # Le modèle doit produire du JSON : on l'extrait, sinon on échoue (G8).
        return extraire_json(contenu)

    # ---------------------------------------------------------------- transport
    def _appel_avec_curl(self, corps: dict[str, Any]) -> str:
        """POST via curl. La clé API n'apparaît jamais dans la ligne de commande
        (donc jamais dans /proc) : elle est écrite dans un fichier de config curl
        éphémère en mode 0600, supprimé immédiatement après l'appel. Le corps JSON
        passe par stdin. TLS VÉRIFIÉ avec le bundle de CA système (curl), repli
        urllib strict si curl est absent."""
        corps_texte = json.dumps(corps, ensure_ascii=False, separators=(",", ":"))
        configuration = "\n".join([
            f'url = "{self.base_url}/chat/completions"',
            f'header = "Authorization: Bearer {self.api_key}"',
            'header = "Content-Type: application/json"',
        ])

        descripteur, chemin = tempfile.mkstemp(prefix="opencode-curl-", suffix=".conf")
        try:
            with os.fdopen(descripteur, "w", encoding="utf-8") as fh:
                fh.write(configuration)
            os.chmod(chemin, 0o600)
            tache = subprocess.run(
                ["curl", "--silent", "--show-error", "--fail-with-body",
                 "-m", str(self.timeout), "-K", chemin, "--data-binary", "@-"],
                input=corps_texte.encode("utf-8"),
                capture_output=True, timeout=self.timeout + 10,
            )
        finally:
            try:
                os.unlink(chemin)
            except OSError:
                pass

        if tache.returncode != 0:
            detail = tache.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"erreur curl (code {tache.returncode}) : {detail[:300]}")

        try:
            payload = json.loads(tache.stdout.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"réponse API non JSON : {tache.stdout.decode('utf-8', errors='replace')[:300]}"
            ) from exc
        return self._extraire_contenu(payload)

    def _appel_avec_urllib(self, corps: dict[str, Any]) -> str:
        """Repli sans curl (urllib standard). Sans curl, aucune clé du secret
        n'apparaît non plus ; la vérification TLS dépend alors du contexte
        ssl par défaut de l'interpréteur."""
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
        return self._extraire_contenu(payload)

    @staticmethod
    def _extraire_contenu(payload: dict[str, Any]) -> str:
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"réponse API inattendue : {str(payload)[:300]}") from exc