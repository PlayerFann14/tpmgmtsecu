"""Verrouillage des correctifs d'audit : reprises utiles, octets réels,
correction humaine complète, format des sources, recherche CVE dynamique.
"""

from __future__ import annotations

import json

from src.agents.orchestrator import Orchestrateur, extraire_technologies
from src.core.validation import verifier_sources
from src.llm.dummy import FournisseurSimule


def _orchestrateur(llm, registre_outils, journal, workspace) -> Orchestrateur:
    return Orchestrateur(llm=llm, registre_outils=registre_outils,
                         journal=journal, workspace=workspace)


class FournisseurQuiRateUneFois:
    """Rate une fois l'Agent 1 (JSON corrompu) puis sert le fournisseur cible."""

    nom_produit = "test-reprises"

    def __init__(self, cible: FournisseurSimule) -> None:
        self.cible = cible
        self.prompts: list[str] = []
        self._ag1_echecs = 0

    def complete(self, systeme: str, utilisateur: str) -> str:
        self.prompts.append(utilisateur)
        if "AGENT_1_INVENTAIRE" in utilisateur and self._ag1_echecs == 0:
            self._ag1_echecs += 1
            return "{ json corrompu"
        return self.cible.complete(systeme, utilisateur)


# ---------------------------------------------------------------- reprises
def test_reprise_reinjecte_les_erreurs(registre_outils, journal, workspace, cas_b_texte):
    """Après un échec de l'Agent 1, le SECOND prompt contient les erreurs de la
    tentative précédente : la reprise n'est jamais un simple doublon."""
    cible = FournisseurSimule()
    fournisseur = FournisseurQuiRateUneFois(cible)
    orch = _orchestrateur(fournisseur, registre_outils, journal, workspace)
    produits = orch.analyser(cas_b_texte)  # ne doit PAS lever d'erreur

    prompts_ag1 = [p for p in fournisseur.prompts if "AGENT_1_INVENTAIRE" in p]
    assert len(prompts_ag1) == 2
    assert prompts_ag1[0] != prompts_ag1[1]
    assert "ERREURS DE LA TENTATIVE PRÉCÉDENTE" in prompts_ag1[1]
    assert "JSON invalide" in prompts_ag1[1]
    assert len(produits["actifs"]["sortie"]["actifs"]) >= 10


# --------------------------------------------------------------- octets réels
def test_journal_enregistre_les_octets_entree(registre_outils, journal, workspace, cas_b_texte):
    """`octets_entree` du journal = taille réelle du prompt envoyé au fournisseur
    (plus jamais 0) : la preuve « aucune donnée sensible » devient vérifiable."""
    orch = _orchestrateur(FournisseurSimule(), registre_outils, journal, workspace)
    orch.analyser(cas_b_texte)

    lignes = journal._fichier.read_text(encoding="utf-8").strip().splitlines()
    appels_ok = [l for l in lignes if '"appel_agent"' in l and '"statut": "ok"' in l]
    assert len(appels_ok) == 5  # AG1…AG5
    tous_non_nuls = all(json.loads(l)["octets_entree"] > 0 for l in appels_ok)
    assert tous_non_nuls, "tout appel doit journaliser la taille réelle d'entrée"


# --------------------------------------------------------- correction humaine
def test_correction_humaine_tous_champs(registre_outils, journal, workspace,
                                        cas_b_texte, monkeypatch):
    """La correction (c) permet de modifier actif, probabilité, impact (niveau
    recalculé), traitement et sources — pas seulement le texte de la menace."""
    orch = _orchestrateur(FournisseurSimule(), registre_outils, journal, workspace)
    produits = orch.analyser(cas_b_texte)
    registre = produits["risques"]["sortie"]["risques"]

    # R-01 : corriger (impact → faible => niveau recalculé « moyen ») puis a×9.
    entrees = iter(["c", "", "", "élevée", "faible", "", "ANSSI — test supplémentaire"]
                   + ["a"] * 9)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(entrees))

    valide = orch.valider_humainement(registre, analyste="Dr Dupont")

    r01 = next(r for r in valide if r["id"] == "R-01")
    assert r01["valide_par"] == "Dr Dupont"
    assert r01["probabilite"] == "élevée"
    assert r01["impact"] == "faible"
    assert r01["niveau"] == "moyen"          # matrice : élevée × faible → moyen
    assert "ANSSI — test supplémentaire" in r01["sources"]
    assert all(r["valide_par"] == "Dr Dupont" for r in valide if r["id"] != "R-02")

    lignes = journal._fichier.read_text(encoding="utf-8").strip().splitlines()
    assert any('"correction_humaine"' in l and '"champs"' in l for l in lignes)


def test_differe_laisse_valide_par_null(registre_outils, journal, workspace,
                                        cas_b_texte, monkeypatch):
    orch = _orchestrateur(FournisseurSimule(), registre_outils, journal, workspace)
    produits = orch.analyser(cas_b_texte)
    registre = produits["risques"]["sortie"]["risques"]

    entrees = iter(["d"] + ["a"] * 9)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(entrees))
    valide = orch.valider_humainement(registre, analyste="Dr Dupont")
    assert valide[0]["valide_par"] is None   # différé : reste null (G6 respecté)


# ------------------------------------------------------------------- sources
def test_verifier_sources_rejette_formats_invalides():
    assert verifier_sources({"sources": []}) != []
    assert verifier_sources({"sources": ["aucune"]}) != []
    assert verifier_sources({"sources": ["néant"]}) != []
    assert verifier_sources({"sources": ["x"]}) != []
    assert verifier_sources({"sources": ["s" * 121]}) != []
    assert verifier_sources({"sources": [""]}) != []
    assert verifier_sources({"sources": ["STRIDE-S"]}) == []
    assert verifier_sources({"sources": ["ANSSI (MFA)", "ISO/IEC 27002 A.5.15"]}) == []


# ------------------------------------------------------------------- CVE / techno
def test_extraire_technologies_depuis_document():
    texte = "Service WebRTC avec TLS, API et visio sécurisée."
    assert extraire_technologies(texte) == ["webrtc", "tls", "api", "visio"]


def test_preparer_cve_repli_decentralise():
    """Document sans mot-clé technologique : repli documenté, jamais d'erreur."""
    orch = _orchestrateur(FournisseurSimule(), *_minimales())
    resultat = orch._preparer_cve_ag3("Un document sans technologie identifiée.")
    assert isinstance(resultat, list)


def _minimales():
    from pathlib import Path
    import tempfile

    from src.agents.orchestrator import construire_registre_outils
    from src.core.journal import Journal
    from src.core.workspace import Workspace

    tmp = Path(tempfile.mkdtemp())
    return (construire_registre_outils(), Journal(tmp / "j.jsonl"),
            Workspace(cas="B·test", description_systeme="desc", repertoire=tmp))


# ------------------------------------------------------- cas piégé : 14 = 14
def test_cas_injecte_exactement_14_detections():
    """Garde-fou de cohérence : le fichier piégé annonce 14 instructions et le
    filtre doit en détecter exactement 14 (une par occurrence)."""
    from src.core.sanitizer import detecter_injections
    from src.tools.file_reader import lire_fichier

    texte = lire_fichier("cases/casB_injecte.md")["contenu"]
    detections = detecter_injections(texte)
    assert len(detections) == 14
    assert any("[détectée]" for _ in detections)