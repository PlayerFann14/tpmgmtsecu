"""Tests de l'espace de travail (workspace) et du registre."""

from __future__ import annotations

from src.core.workspace import Workspace, charger_registre


def test_workspace_cycle_complet(tmp_path):
    ws = Workspace(cas="B", description_systeme="contenu", repertoire=tmp_path)
    ws.set_etape("actifs", {"sortie": {"actifs": [{"id": "A-01"}]}}, tentatives=1)
    ws.set_final([{"id": "R-01", "valide_par": None}])
    chemin = ws.sauvegarder()

    assert chemin.exists()
    assert ws.produit("actifs")["sortie"]["actifs"][0]["id"] == "A-01"

    registre = charger_registre(chemin)
    assert registre[0]["id"] == "R-01"
    assert registre[0]["valide_par"] is None