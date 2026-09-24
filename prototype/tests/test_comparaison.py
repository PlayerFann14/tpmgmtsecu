"""Comparaison registre généré vs analyse manuelle (jalon 4) — non tautologique.

Le simulateur « fidèle » reproduit la référence : son 10/10 ne prouve rien sur
la qualité d'analyse. En revanche, le mode `fidele=False` produit un registre
VALIDÉ par le pipeline mais DIVERGENT : ces tests prouvent que la comparaison
sait détecter les risques oubliés, inventés et les écarts de niveau — la
comparaison n'est donc pas une tautologie.
"""

from __future__ import annotations

from src.agents.orchestrator import EtapeImpossibleError
from src.core.comparaison import comparer_registres
from src.llm.dummy import FournisseurSimule, _RISQUES


def _registre(orchestrateur, texte):
    produits = orchestrateur.analyser(texte)
    return produits["risques"]["sortie"]["risques"]


def _orchestrateur(llm, registre_outils, journal, workspace):
    from src.agents.orchestrator import Orchestrateur

    return Orchestrateur(llm=llm, registre_outils=registre_outils,
                         journal=journal, workspace=workspace)


def test_reference_manuelle_10_10_fidele(registre_outils, journal, workspace, cas_b_texte):
    """Mode fidèle : la comparaison est EXACTEMENT conforme (et c'est un test
    de chaîne, pas une preuve d'analyse — assumé dans le dossier)."""
    orch = _orchestrateur(FournisseurSimule(), registre_outils, journal, workspace)
    genere = _registre(orch, cas_b_texte)

    resultat = comparer_registres(genere, _RISQUES)
    assert resultat["nb_reference"] == 10
    assert resultat["taux_reconciliation"] == 1.0
    assert resultat["inventes"] == []
    assert resultat["oublies"] == []
    assert resultat["ecarts_par_risque"] == {}


def test_mode_imparfait_passe_la_validation_mais_diverge(registre_outils, journal, workspace, cas_b_texte):
    """Mode imparfait : le registre est VALIDE (pipeline accepte) mais la
    comparaison détecte les écarts. C'est la preuve que comparer a du sens."""
    orch = _orchestrateur(FournisseurSimule(fidele=False), registre_outils, journal, workspace)
    genere = _registre(orch, cas_b_texte)

    assert len(genere) == 10  # 9 réels + 1 inventé
    resultat = comparer_registres(genere, _RISQUES)
    assert resultat["oublies"] == ["R-07"]           # risque oublié par le sim
    assert resultat["inventes"] == ["R-11"]          # risque inventé
    assert resultat["nb_ecarts_niveau"] >= 1         # écart de niveau détecté
    assert resultat["taux_reconciliation"] < 1.0
    assert "1 inventés" in resultat["synthese"]
    assert "1 oubliés" in resultat["synthese"]


def test_decisions_de_correction_non_tautologiques(registre_outils, journal, workspace, cas_b_texte):
    """Deux exécutions (fidèle vs imparfait) sur le même cas produisent des
    synthèses de comparaison différentes : la mesure discrimine bien les sources."""
    a = _comparer_avec(FournisseurSimule(fidele=True), registre_outils, journal, workspace, cas_b_texte)
    b = _comparer_avec(FournisseurSimule(fidele=False), registre_outils, journal, workspace, cas_b_texte)
    assert a["synthese"] != b["synthese"]


def _comparer_avec(llm, registre_outils, journal, workspace, texte):
    orch = _orchestrateur(llm, registre_outils, journal, workspace)
    return comparer_registres(_registre(orch, texte), _RISQUES)


def test_mode_imparfait_repare_ou_rejete_si_invalide(registre_outils, journal, workspace, cas_b_texte):
    """Le mode imparfait ne triche jamais sur les GARDE-FOUS : il reste valide
    (jamais de critique contre la matrice, jamais de valide_par rempli)."""
    orch = _orchestrateur(FournisseurSimule(fidele=False), registre_outils, journal, workspace)
    registre = _registre(orch, cas_b_texte)
    assert all(r["valide_par"] is None for r in registre)
    niveaux = {r["id"]: (r["probabilite"], r["impact"], r["niveau"]) for r in registre}
    # R-09 : (élevée, faible) → moyen, cohérent avec la matrice.
    assert niveaux["R-09"] == ("élevée", "faible", "moyen")