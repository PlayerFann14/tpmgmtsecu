"""Validation des sorties d'agents : schéma JSON + règles métier.

Garde-fous appliqués ici (cf. `02`, §6) :
- G4  : `sources` non vide (parade à l'hallucination).
- G6  : `valide_par` reste null (écrit uniquement par l'humain).
- G7  : `niveau` = résultat déterministe de la matrice P×I (le LLM ne décide pas).
- Règles métier : échelles respectées, identifiants uniques, « ignorer » interdit.
"""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from . import config
from .config import MATRICE_RISQUE


def valider_schema(nom_agent: str, sortie: Any) -> list[str]:
    """Valide le JSON produit par un agent contre son schéma. Retourne les erreurs."""
    from .schemas import schema_agent

    erreurs: list[str] = []
    validateur = Draft202012Validator(schema_agent(nom_agent))
    for error in sorted(validateur.iter_errors(sortie), key=lambda e: list(e.path)):
        position = "/".join(str(p) for p in error.path) or "$"
        erreurs.append(f"{nom_agent}: {position}: {error.message}")
    return erreurs


def calculer_niveau(probabilite: str, impact: str) -> str:
    """Outil déterministe : matrice probabilité × impact (sujet p. 8)."""
    p = probabilite.strip().lower()
    i = impact.strip().lower()
    if p not in MATRICE_RISQUE or i not in MATRICE_RISQUE[p]:
        raise ValueError(f"Probabilité/impact hors échelle : '{probabilite}' × '{impact}'")
    return MATRICE_RISQUE[p][i]


def _niveau_est_coherent(niveau: str, probabilite: str, impact: str) -> bool:
    try:
        return calculer_niveau(probabilite, impact) == niveau.strip().lower()
    except ValueError:
        return False


_SOURCES_INVALIDES = {"aucune", "neant", "néant", "none", "n/a", "na", "inconnue",
                      "inconnu", "?", "sans objet", "sans-objet", "x"}


def verifier_sources(sortie: Any) -> list[str]:
    """G4 — toute sortie doit citer au moins une source VALIDE.

    Ne se limite pas à la présence : on rejette aussi les valeurs vides, les
    chaînes « aucune / néant / n/a », et les longueurs hors bornes (une référence
    réelle a un format identifiable). La validité sémantique (vraie page, vrai
    contrôle) reste vérifiée à la relecture humaine.
    """
    sources = sortie.get("sources", []) if isinstance(sortie, dict) else []
    if not isinstance(sources, list) or len(sources) == 0:
        return ["sources vide : sortie rejetée (parade anti-hallucination, G4)"]
    problemes: list[str] = []
    for source in sources:
        if not isinstance(source, str) or not source.strip():
            problemes.append("source vide (liste non vide mais entrée illisible)")
            continue
        source = source.strip()
        if source.lower() in _SOURCES_INVALIDES:
            problemes.append(f"source invalide (refusée) : {source!r}")
        elif len(source) > 120:
            problemes.append(f"source trop longue (>120 caractères) : {source[:40]!r}…")
        elif len(source) < 3:
            problemes.append(f"source trop courte pour être une référence : {source!r}")
    return problemes


def verifier_valide_par(sortie: Any) -> list[str]:
    """G6 — aucun agent ne peut renseigner la validation humaine.

    NB : seul `None` (JSON null) est accepté. La chaîne `"null"` est elle aussi
    rejetée : elle serait interprétée comme « validé » par les consommateurs.
    """
    risques = []
    if isinstance(sortie, dict):
        sortie_interne = sortie.get("sortie", {})
        if isinstance(sortie_interne, dict):
            risques = sortie_interne.get("risques", [])
    problemes = []
    for r in risques:
        if isinstance(r, dict) and r.get("valide_par") is not None:
            problemes.append(f"valide_par doit rester null (JSON) — réservé à l'humain (G6)")
    return problemes


def verifier_echelles(probabilite: str, impact: str, echelle_p: list[str], echelle_i: list[str]) -> list[str]:
    """L'Agent 4 doit rester dans les échelles fixées par l'Agent 2."""
    erreurs = []
    if probabilite.strip().lower() not in echelle_p:
        erreurs.append(f"probabilité '{probabilite}' hors échelle {echelle_p}")
    if impact.strip().lower() not in echelle_i:
        erreurs.append(f"impact '{impact}' hors échelle {echelle_i}")
    return erreurs


def verifier_niveaux_agent4(sortie: Any) -> list[str]:
    """G7 — recalcule chaque niveau via la matrice (déterministe)."""
    erreurs: list[str] = []
    sortie_interne = sortie.get("sortie", {})
    evaluations = sortie_interne.get("evaluations", []) if isinstance(sortie_interne, dict) else []
    for ev in evaluations:
        p = ev.get("probabilite", "").strip().lower()
        i = ev.get("impact", "").strip().lower()
        niveau = ev.get("niveau")
        if not _niveau_est_coherent(niveau or "", p, i):
            attendu = calculer_niveau(p, i) if p in MATRICE_RISQUE and i in MATRICE_RISQUE.get(p, {}) else "?"
            erreurs.append(
                f"{ev.get('id_menace')}: niveau '{niveau}' ≠ matrice ({attendu}) — le LLM ne décide pas du niveau (G7)"
            )
    return erreurs


def verifier_niveaux_agent5(sortie: Any) -> list[str]:
    """G7 sur le registre final — chaque risque doit respecter la matrice P×I.

    L'Agent 5 recopie P/I/niveau de l'étape 4 ; il ne les recalcule jamais. Un
    niveau qui ne correspond pas à la matrice est un signal d'altération : bloquant.
    """
    erreurs: list[str] = []
    risques = (sortie.get("sortie", {}) or {}).get("risques", [])
    for r in risques:
        p = (r.get("probabilite") or "").strip().lower()
        i = (r.get("impact") or "").strip().lower()
        niveau = (r.get("niveau") or "").strip().lower()
        if p not in MATRICE_RISQUE or i not in MATRICE_RISQUE.get(p, {}):
            erreurs.append(
                f"{r.get('id')}: P/I hors échelle ('{r.get('probabilite')}' × '{r.get('impact')}')"
            )
            continue
        attendu = MATRICE_RISQUE[p][i]
        if niveau != attendu:
            erreurs.append(
                f"{r.get('id')}: niveau '{r.get('niveau')}' ≠ matrice ({attendu}) "
                "— le niveau vient de la matrice déterministe (G7)"
            )
    return erreurs


def verifier_traitements(sortie: Any) -> list[str]:
    """Règle métier : traitement parmi les 4 réponses, « ignorer » interdit."""
    erreurs: list[str] = []
    sortie_interne = sortie.get("sortie", {})
    risques = sortie_interne.get("risques", []) if isinstance(sortie_interne, dict) else []
    for r in risques:
        traitement = (r.get("traitement") or "").strip().lower()
        if traitement in {t.strip().lower() for t in config.TRAITEMENTS_INTERDITS}:
            erreurs.append(f"{r.get('id')}: traitement '{traitement}' interdit (ignorer ≠ réponse)")
        elif traitement not in config.TRAITEMENTS_AUTORISES:
            erreurs.append(
                f"{r.get('id')}: traitement '{traitement}' inconnu — 4 réponses possibles : "
                "réduire, transférer, éviter, accepter"
            )
    return erreurs


def verifier_coherence_agent5(sortie: Any, evaluations: list[dict[str, Any]]) -> list[str]:
    """L'Agent 5 doit recopier P/I/niveau de l'étape précédente, jamais recalculer."""
    erreurs: list[str] = []
    ev_par_menace = {ev["id_menace"]: ev for ev in evaluations}
    risques = (sortie.get("sortie", {}) or {}).get("risques", [])
    for r in risques:
        # On exige `menace_id` (maintenant requis par le schéma AG5) : sans lien
        # avec l'étape 4, l'évaluation ne peut pas être vérifiée → bloquant.
        mid = r.get("menace_id")
        if not mid or mid not in ev_par_menace:
            erreurs.append(
                f"{r.get('id')}: menace_id '{mid}' absent ou inconnu — "
                "impossible de vérifier la recopie de l'étape 4"
            )
            continue
        ev = ev_par_menace[mid]
        for champ in ("probabilite", "impact", "niveau"):
            if str(r.get(champ, "")).strip().lower() != str(ev.get(champ, "")).strip().lower():
                erreurs.append(
                    f"{r.get('id')}: {champ} '{r.get(champ)}' ≠ étape 4 ('{ev.get(champ)}') "
                    "— recopie interdite de recalculer"
                )
    return erreurs


def verifier_ids_uniques(sortie: Any, champ: str) -> list[str]:
    """Les identifiants doivent être uniques dans la sortie."""
    sortie_interne = sortie.get("sortie", {})
    elements = sortie_interne.get(champ, []) if isinstance(sortie_interne, dict) else []
    vus: set[str] = set()
    doublons = []
    for el in elements:
        identite = el.get("id") if champ == "risques" else el.get("id_menace", el.get("id"))
        if identite in vus:
            doublons.append(str(identite))
        vus.add(identite)
    return [f"identifiant dupliqué : {d}" for d in doublons]


def toutes_les_erreurs(
    nom_agent: str,
    sortie: Any,
    *,
    evaluations_etape4: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Applique la pile complète de validation pour un agent donné."""
    erreurs = valider_schema(nom_agent, sortie)
    erreurs += verifier_sources(sortie)
    erreurs += verifier_valide_par(sortie)

    if nom_agent == "AG1":
        erreurs += verifier_ids_uniques(sortie, "actifs")
    elif nom_agent == "AG2":
        echelle_p = (sortie.get("sortie", {}) or {}).get("echelle_probabilite", [])
        echelle_i = (sortie.get("sortie", {}) or {}).get("echelle_impact", [])
        if len(echelle_p) != len(set(echelle_p)):
            erreurs.append("AG2: échelle de probabilité avec doublons")
        if len(echelle_i) != len(set(echelle_i)):
            erreurs.append("AG2: échelle d'impact avec doublons")
    elif nom_agent == "AG3":
        erreurs += verifier_ids_uniques(sortie, "menaces")
    elif nom_agent == "AG4":
        erreurs += verifier_ids_uniques(sortie, "evaluations")
        # Échelles : TOUJOURS celles de configuration — l'écho renvoyé par l'agent
        # n'est jamais utilisé (contre l'auto-autorisation d'une échelle inventée).
        echelle_p = config.ECHELLE_PROBABILITE
        echelle_i = config.ECHELLE_IMPACT
        evaluations = (sortie.get("sortie", {}) or {}).get("evaluations", [])
        for ev in evaluations:
            erreurs += verifier_echelles(ev.get("probabilite", ""), ev.get("impact", ""), echelle_p, echelle_i)
        # NB : le `niveau` d'AG4 n'est pas vérifié ici : il est recalculé de façon
        # déterministe par l'orchestrateur (G7). `verifier_niveaux_agent4` sert aux tests.
    elif nom_agent == "AG5":
        erreurs += verifier_ids_uniques(sortie, "risques")
        erreurs += verifier_traitements(sortie)
        erreurs += verifier_niveaux_agent5(sortie)
        if evaluations_etape4:
            erreurs += verifier_coherence_agent5(sortie, evaluations_etape4)
    return erreurs