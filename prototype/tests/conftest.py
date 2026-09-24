"""Fixtures partagées pour les tests."""

from __future__ import annotations

import pytest

from src.agents.orchestrator import construire_registre_outils
from src.core.journal import Journal
from src.core.workspace import Workspace
from src.llm.dummy import FournisseurSimule


@pytest.fixture
def registre_outils():
    return construire_registre_outils()


@pytest.fixture
def journal(tmp_path):
    return Journal(tmp_path / "journal.jsonl")


@pytest.fixture
def workspace(tmp_path):
    return Workspace(cas="B·test", description_systeme="desc", repertoire=tmp_path)


@pytest.fixture
def llm_dummy():
    return FournisseurSimule()


@pytest.fixture
def cas_b_path():
    return "cases/casB_mediconsult.md"


@pytest.fixture
def cas_b_texte(cas_b_path):
    from src.tools.file_reader import lire_fichier

    return lire_fichier(cas_b_path)["contenu"]