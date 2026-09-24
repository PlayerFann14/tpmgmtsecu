"""Tests de l'outil lecture de fichier (dossier restreint, read-only)."""

from __future__ import annotations

import pytest

from src.tools.file_reader import LectureInterditeError, lire_fichier


def test_lire_fichier_existant(cas_b_path):
    resultat = lire_fichier(cas_b_path)
    assert "contenu" in resultat
    assert "MediConsult" in resultat["contenu"]


def test_lire_fichier_hors_perimetre_rejete():
    with pytest.raises(LectureInterditeError):
        lire_fichier("/etc/passwd")


def test_traverse_de_chemin_rejetee():
    with pytest.raises(LectureInterditeError):
        lire_fichier("../data/cve_snapshot.json")