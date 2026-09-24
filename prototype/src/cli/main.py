"""Point d'entrée CLI : exécute la chaîne d'agents sur un cas d'étude.

Usage :
  python src/cli/main.py run --case cases/casB_mediconsult.md \
      [--provider dummy|openai] [--no-human] [--analyste NAME]
  python src/cli/main.py test-injection --case cases/casB_injecte.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Permet d'importer src/ comme paquet depuis la racine du prototype.
RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from src.core.config import RUNS_DIR  # noqa: E402
from src.core.journal import Journal  # noqa: E402
from src.core.workspace import Workspace  # noqa: E402


def _nom_analyste(analyste: str) -> str:
    return analyste or "analyste-humain"


def _fournisseur(nom: str) -> object:
    from src.llm.dummy import FournisseurSimule
    from src.llm.openai_compat import OpenAICompatProvider

    if nom == "dummy":
        return FournisseurSimule()
    if nom == "openai":
        return OpenAICompatProvider()
    raise ValueError(f"fournisseur inconnu : {nom} (dummy|openai)")


def _lire_cas(chemin: str) -> str:
    from src.tools.file_reader import lire_fichier

    contenu = lire_fichier(chemin)["contenu"]
    return str(contenu)


def _sauver_registre(repertoire: Path, registre: list[dict[str, object]]) -> Path:
    chemin = repertoire / "registre_final.json"
    with chemin.open("w", encoding="utf-8") as fh:
        json.dump(registre, fh, ensure_ascii=False, indent=2)
    return chemin


def _afficher_synthese(registre: list[dict[str, object]]) -> None:
    from collections import Counter

    niveaux = Counter(str(r.get("niveau")) for r in registre)
    valides = sum(1 for r in registre if r.get("valide_par"))
    print("\n=== SYNTHÈSE ===")
    for niveau in ("critique", "élevé", "moyen", "faible"):
        print(f"  {niveau:<9} : {niveaux.get(niveau, 0)}")
    print(f"  risques validés par l'humain : {valides}/{len(registre)}")


def commande_run(args: argparse.Namespace) -> int:
    from src.agents.orchestrator import EtapeImpossibleError, Orchestrateur, construire_registre_outils

    # Répertoire de session.
    from datetime import datetime, timezone

    horodatage = datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S")
    repertoire = RUNS_DIR / horodatage
    repertoire.mkdir(parents=True, exist_ok=True)

    journal = Journal(repertoire / "journal.jsonl")
    description = _lire_cas(args.case)

    workspace = Workspace(
        cas=f"B · MediConsult ({args.case})",
        description_systeme=description,
        repertoire=repertoire,
    )

    try:
        llm = _fournisseur(args.provider)
    except ValueError as exc:
        print(f"[erreur] {exc}")
        return 1

    registre_outils = construire_registre_outils()
    orchestrateur = Orchestrateur(llm=llm, registre_outils=registre_outils,
                                  journal=journal, workspace=workspace)

    print(f"Fournisseur LLM : {llm.nom_produit}")
    print(f"Chaîne : AG1 → AG2 → AG3 → AG4 → AG5 (proposition) → validation humaine\n")

    try:
        produits = orchestrateur.analyser(description)
    except EtapeImpossibleError as exc:
        # G8 : arrêt explicite, aucune sortie n'est publiée.
        print(f"\n[arrêt bavard] {exc}")
        journal.ecrire({"type": "session_fin", "statut": "echec_arrêt_bavard"})
        journal.ecrire({"type": "session_fin_motif", "motif": str(exc)})
        return 1

    metamorphoses = {
        "actifs": lambda s: len(s.get("actifs", [])),
        "modele": lambda s: s.get("modele_retenu", "?"),
        "menaces": lambda s: len(s.get("menaces", [])),
        "evaluations": lambda s: len(s.get("evaluations", [])),
        "risques": lambda s: len(s.get("risques", [])),
    }
    for nom, extraire in metamorphoses.items():
        sortie = produits[nom].get("sortie", {}) or {}
        print(f"  [ok] étape {nom} : {extraire(sortie)}")

    # Étape humaine dans la boucle (G6) — optionnelle pour la démo.
    if args.no_human:
        registre = orchestrateur.registre_provisoire()
        print("\n[--no-human] validation humaine désactivée (demo).\n")
    else:
        registre = orchestrateur.valider_humainement(
            orchestrateur.registre_provisoire(),
            analyste=_nom_analyste(args.analyste),
        )

    workspace.set_final(registre)
    workspace.sauvegarder()

    chemin_registre = _sauver_registre(repertoire, [dict(r) for r in registre])
    journal.ecrire({"type": "session_fin", "statut": "ok",
                    "nb_risques": len(registre)})
    print(f"Registre écrit : {chemin_registre}")
    print(f"Workspace      : {repertoire / 'workspace.json'}")
    print(f"Journal        : {repertoire / 'journal.jsonl'}")
    _afficher_synthese(registre)
    return 0


def commande_test_injection(args: argparse.Namespace) -> int:
    """Démo : un document contenant une consigne piégée est neutralisé et signalé."""
    from src.core.sanitizer import detecter_injections, neutraliser

    document = _lire_cas(args.case)
    detections = detecter_injections(document)
    print(f"Document : {args.case}")
    if not detections:
        print("  Aucune injection détectée.")
        return 0
    for d in detections:
        print(f"  [détectée] motif={d.motif} extrait={d.extrait!r}")
    assaini = neutraliser(document)
    print(f"\n  Document neutralisé : {len(document)} → {len(assaini)} caractères")
    print("  (les motifs piégés ont été remplacés par [[DONNEE-NON-EXECUTABLE]])")
    return 0


def construit_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(prog="agents-risques",
                                      description="Multi-agents d'analyse de risques (E21)")
    sous = parseur.add_subparsers(dest="commande", required=True)

    run = sous.add_parser("run", help="exécuter la chaîne complète sur un cas")
    run.add_argument("--case", required=True, help="chemin du fichier (dans cases/)")
    run.add_argument("--provider", choices=["dummy", "openai"], default="dummy",
                     help="fournisseur LLM (dummy = déterministe, sans clé)")
    run.add_argument("--no-human", action="store_true",
                     help="désactiver la validation humaine interactive (démo)")
    run.add_argument("--analyste", default="analyste-humain",
                     help="nom de l'analyste qui valide")
    run.set_defaults(fonction=commande_run)

    inj = sous.add_parser("test-injection", help="tester la neutralisation d'une consigne piégée")
    inj.add_argument("--case", required=True)
    inj.set_defaults(fonction=commande_test_injection)

    return parseur


def main(argv: list[str] | None = None) -> int:
    args = construit_parseur().parse_args(argv)
    return args.fonction(args)


if __name__ == "__main__":
    raise SystemExit(main())