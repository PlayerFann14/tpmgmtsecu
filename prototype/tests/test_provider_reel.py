"""Garde-fous du fournisseur réel (`openai_compat.py`) — transport et secrets.

Vérifie, sans réseau :
- qu'aucun secret requis n'est codé en dur (ValueError si variables absentes) ;
- que le timeout par appel est surchargeable par `OPENAI_TIMEOUT` (modèles lents) ;
- que la clé API n'apparaît JAMAIS dans la ligne de commande curl (fichier de
  config éphémère 0600, corps sur stdin) — propriété documentée au § 7 du guide.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from src.llm.openai_compat import OpenAICompatProvider


def _environner(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "https://exemple.invalid/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "cle-test-secrete")
    monkeypatch.setenv("OPENAI_MODEL", "modele-test")


def test_secret_non_defini_leve_erreur(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://exemple.invalid/v1")
    with pytest.raises(ValueError):
        OpenAICompatProvider()


def test_timeout_surchargeable_par_environnement(monkeypatch) -> None:
    _environner(monkeypatch)
    monkeypatch.setenv("OPENAI_TIMEOUT", "300")
    assert OpenAICompatProvider().timeout == 300


def test_timeout_defaut_sans_surcharge(monkeypatch) -> None:
    _environner(monkeypatch)
    monkeypatch.delenv("OPENAI_TIMEOUT", raising=False)
    assert OpenAICompatProvider().timeout == 120


def test_cle_api_jamais_dans_argv(monkeypatch) -> None:
    """La clé doit rester hors de la ligne de commande (invisible dans /proc)."""
    _environner(monkeypatch)
    monkeypatch.setattr("src.llm.openai_compat.shutil.which", lambda _nom: "/usr/bin/curl")

    commandes: list[list[str]] = []

    def faux_run(commande, **_kwargs):  # type: ignore[no-untyped-def]
        commandes.append(list(commande))
        contenu = json.dumps({
            "choices": [{"message": {"role": "assistant",
                                     "content": '{"risques": []}'}}]
        })
        return subprocess.CompletedProcess(commande, 0, stdout=contenu.encode())

    monkeypatch.setattr("src.llm.openai_compat.subprocess.run", faux_run)

    fournisseur = OpenAICompatProvider()
    sortie = fournisseur.complete("système", "utilisateur")

    assert json.loads(sortie) == {"risques": []}
    assert commandes, "une commande curl doit avoir été construite"
    for commande in commandes:
        assert not any("cle-test-secrete" in str(arg) for arg in commande), \
            "la clé API ne doit jamais apparaître dans la ligne de commande"