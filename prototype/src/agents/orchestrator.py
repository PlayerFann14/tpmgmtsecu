"""Orchestrateur : enchaîne AG1 → AG5, valide, répare, mémorise, journalise.

Responsabilités (cf. `02`, §5.6) :
- entrée = donnée (sanitizer) ;
- enchaînement dans l'ordre ; max 3 tentatives par étape ;
- validation complète (schéma + sources + échelles + niveau matrice + traitement) ;
- application DÉTERMINISTE de `calculer_niveau` sur l'étape 4 ;
- RAG : pré-extraire les connaissances utiles par agent et les injecter ;
- CVE : pré-recherche pour l'étape 3 ;
- journalisation de chaque appel ; arrêt bavard si étape impossible (G8) ;
- `valide_par` reste null — la validation humaine est une étape à part (CLI).
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from ..core import config
from ..core.config import MAX_TENTATIVES
from ..core.journal import Journal
from ..core.sanitizer import neutraliser, sanctionner_document
from ..core.validation import calculer_niveau, toutes_les_erreurs
from ..core.workspace import Workspace
from ..llm.interface import FournisseurLLM
from ..tools.cve import rechercher_cve
from ..tools.knowledge import chercher_connaissance
from ..tools.registry import RegistreOutils
from .agents import ORDRE, Agent
from .prompts import BLOC_SYSTEME, OUTILS_DECLARES, REQUETES_RAG


class EtapeImpossibleError(Exception):
    """Levée quand un agent échoue après MAX_TENTATIVES (arrêt bavard, G8)."""


def _tronquer(erreurs: list[str], *, max_car: int = 160) -> list[str]:
    """Limite la longueur des erreurs journalisées (pas de fuite de contenu LLM)."""
    return [e if len(e) <= max_car else e[:max_car] + "…" for e in erreurs]


class Orchestrateur:
    def __init__(
        self,
        *,
        llm: FournisseurLLM,
        registre_outils: RegistreOutils,
        journal: Journal,
        workspace: Workspace,
    ) -> None:
        self.llm = llm
        self.registre_outils = registre_outils
        self.journal = journal
        self.workspace = workspace
        self.agents: dict[str, Agent] = {}
        for nom in ORDRE:
            agent = self._construire_agent(nom)
            agent.definir_contexte({})
            self.agents[nom] = agent

    def _construire_agent(self, nom: str) -> Agent:
        from .agents import AGENTS

        classe = AGENTS[nom]
        return classe(llm=self.llm, registre_outils=self.registre_outils,
                      systeme=BLOC_SYSTEME, journal=self.journal)

    # ------------------------------------------------------------------ outils
    def _preparer_rag(self, agent_nom: str) -> list[dict[str, str]]:
        extraits: list[dict[str, str]] = []
        for requete in REQUETES_RAG.get(agent_nom, []):
            try:
                resultat = chercher_connaissance(requete)
            except Exception as exc:  # la connaissance ne doit jamais bloquer l'analyse
                self.journal.ecrire({"type": "rag_echec", "agent": agent_nom,
                                     "erreur": str(exc)})
                continue
            extraits.extend(resultat.get("resultats", []))
        # Dédoublonnage par référence.
        vus: set[str] = set()
        uniques = []
        for e in extraits:
            ref = e["reference"]
            if ref not in vus:
                vus.add(ref)
                uniques.append(e)
        return uniques[:6]

    def _preparer_cve_ag3(self) -> list[dict[str, object]]:
        try:
            resultat = rechercher_cve(mots="webrtc tls api")  # technologies du cas B
        except Exception:
            return []
        return resultat.get("cves", [])

    # ------------------------------------------------------------------- flux
    def analyser(self, description_systeme: str, *, contexte_metier: str = "") -> dict[str, Any]:
        """Exécute la chaîne complète et retourne les produits par étape."""
        # 1) Entrée = donnée non fiable → assainissement + détection d'injections.
        description_assainie, detections = sanctionner_document(description_systeme)
        if detections:
            self.journal.injection_detectee([d.to_dict() for d in detections])

        # Le contexte métier est lui aussi une donnée non fiable (G1).
        if contexte_metier:
            _, detections_metier = sanctionner_document(contexte_metier)
            if detections_metier:
                self.journal.injection_detectee([d.to_dict() for d in detections_metier])
            contexte_metier = neutraliser(contexte_metier)

        # 2) Boucle sur les 5 agents.
        contexte = {
            "description_assainie": description_assainie,
            "contexte_metier": contexte_metier,
        }

        for nom in ORDRE:
            agent = self.agents[nom]
            contexte["rag"] = self._preparer_rag(nom)
            if nom == "AG3":
                contexte["cve"] = self._preparer_cve_ag3()
            agent.definir_contexte(contexte)

            produit = self._executer_avec_reprises(nom, agent, contexte)
            nom_etape = {
                "AG1": "actifs", "AG2": "modele", "AG3": "menaces",
                "AG4": "evaluations", "AG5": "risques",
            }[nom]
            self.workspace.set_etape(nom_etape, produit, tentatives=agent._tentatives,
                                     erreurs=agent._erreurs)
            contexte.update({nom_etape: produit, **self._injecter_etape(nom, produit)})

        return self.workspace.produits()

    def _injecter_etape(self, nom: str, produit: Any) -> dict[str, Any]:
        """Rend les sorties normalisées disponibles pour l'étape suivante."""
        sortie = produit.get("sortie", {}) if isinstance(produit, dict) else {}
        carte = {
            "AG1": {"actifs": sortie.get("actifs", [])},
            "AG2": {"modele": sortie, "echelles": {
                "echelle_probabilite": sortie.get("echelle_probabilite", config.ECHELLE_PROBABILITE),
                "echelle_impact": sortie.get("echelle_impact", config.ECHELLE_IMPACT),
            }},
            "AG3": {"menaces": sortie.get("menaces", [])},
            "AG4": {"evaluations": sortie.get("evaluations", [])},
            "AG5": {},
        }
        return carte.get(nom, {})

    def _executer_avec_reprises(self, nom: str, agent: Agent,
                                contexte: dict[str, Any]) -> dict[str, Any]:
        dernier_erreurs: list[str] = []
        for tentative in range(1, MAX_TENTATIVES + 1):
            try:
                brut = agent.produire()
            except Exception as exc:
                dernier_erreurs = _tronquer([f"échec appel LLM : {exc}"])
                self.journal.appels_agents(nom_agent=nom, tentative=tentative,
                                           statut="echec_llm", erreurs=dernier_erreurs)
                agent.definir_contexte({**contexte, "erreurs_reparation": dernier_erreurs})
                continue

            try:
                sortie = json.loads(brut)
            except json.JSONDecodeError as exc:
                dernier_erreurs = _tronquer([f"JSON invalide : {exc}"])
                self.journal.appels_agents(nom_agent=nom, tentative=tentative,
                                           statut="echec_json", n_sortie=len(brut),
                                           erreurs=dernier_erreurs)
                # Réparation : signaler la cause au prochain essai.
                agent.definir_contexte({**contexte, "erreurs_reparation": dernier_erreurs})
                continue

            erreurs = toutes_les_erreurs(
                nom, sortie,
                evaluations_etape4=contexte.get("evaluations", []) if nom == "AG5" else None,
            )

            # Étape 4 : normalisation déterministe des niveaux (G7).
            if nom == "AG4" and not erreurs:
                erreurs += _tronquer(self._appliquer_niveaux_deterministes(sortie))

            agent._tentatives = tentative
            agent._erreurs = _tronquer(erreurs)
            if not erreurs:
                self.journal.appels_agents(nom_agent=nom, tentative=tentative,
                                           statut="ok", n_sortie=len(brut))
                return sortie

            dernier_erreurs = agent._erreurs
            self.journal.appels_agents(nom_agent=nom, tentative=tentative,
                                       statut="echec_schema", n_sortie=len(brut),
                                       erreurs=dernier_erreurs)
            # Réparation : réinjecter les erreurs dans le contexte du prochain essai.
            agent.definir_contexte({**contexte, "erreurs_reparation": dernier_erreurs})

        raise EtapeImpossibleError(
            f"étape {nom} impossible après {MAX_TENTATIVES} tentatives : "
            f"{'; '.join(dernier_erreurs[:5])} — arrêt explicite, pas de remplissage (G8)"
        )

    def _appliquer_niveaux_deterministes(self, sortie: dict[str, Any]) -> list[str]:
        """Recalcule et écrase `niveau` avec la matrice (le LLM ne décide pas, G7).

        Retourne les erreurs (probabilité/impact hors matrice) : l'étape est alors
        considérée en échec et rejouée — jamais de valeur silencieusement ignorée.
        """
        echecs: list[str] = []
        evaluations = (sortie.get("sortie", {}) or {}).get("evaluations", [])
        for ev in evaluations:
            try:
                ev["niveau"] = calculer_niveau(ev.get("probabilite", ""), ev.get("impact", ""))
            except ValueError as exc:
                echecs.append(f"{ev.get('id_menace')}: {_tronquer([str(exc)])[0]}")
        return echecs

    # ------------------------------------------------- validation humaine ----
    def registre_provisoire(self) -> list[dict[str, Any]]:
        """Registre tel que proposé par l'Agent 5 (copie, rien de validé)."""
        produits = self.workspace.produits()
        risques = (produits.get("risques", {}).get("sortie", {}) or {}).get("risques", [])
        copie = deepcopy(risques)
        for r in copie:
            r["valide_par"] = None
        return copie

    def valider_humainement(self, registre: list[dict[str, Any]], *, analyste: str) -> list[dict[str, Any]]:
        """Étape d'humain dans la boucle : écrit `valide_par` (garde-fou G6).

        Appelée par le CLI, jamais par un agent. Pour chaque risque, l'analyste
        accepte (a), diffère (d, reste null) ou corrige (c, édite le champ).
        NB : travaille sur une copie, le produit de l'Agent 5 reste intact.
        """
        registre = deepcopy(registre)
        for r in registre:
            decision = input(
                f"[{r['id']}] {r['menace'][:80]}…\n"
                f"  niveau={r['niveau']} · traitement={r['traitement']} "
                f"(proposé par AG5)\n"
                f"  valider ? (a)ccepter / (d)ifférer / (c)orriger : "
            ).strip().lower()
            if decision == "a":
                r["valide_par"] = analyste
                self.journal.validation_humaine(r["id"], analyste, "accepte")
            elif decision == "c":
                r["valide_par"] = analyste
                correction = input("  correction ? ")
                if correction:
                    r["menace"] = correction
                self.journal.validation_humaine(r["id"], analyste, "corrige")
            else:
                r["valide_par"] = None
                self.journal.validation_humaine(r["id"], analyste, "differe")
        return registre


def construire_registre_outils() -> RegistreOutils:
    """Enregistre les outils du système (lecture seule)."""
    from ..tools.file_reader import lire_fichier
    from ..tools.knowledge import chercher_connaissance as outil_knowledge
    from ..tools.matrice import calculer_niveau as outil_matrice

    registre = RegistreOutils()
    registre.enregistrer("lire_fichier", lire_fichier)
    registre.enregistrer("chercher_connaissance", outil_knowledge)
    registre.enregistrer("calculer_niveau", outil_matrice)
    try:
        from ..tools.cve import rechercher_cve as outil_cve

        registre.enregistrer("rechercher_cve", outil_cve)
    except Exception:
        pass
    return registre