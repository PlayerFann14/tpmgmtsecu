"""Les 5 agents concrets (une étape de la méthode chacun, cf. sujet p. 21)."""

from __future__ import annotations

import json
from typing import Any

from .base import Agent
from .prompts import AG1_PROMPT, AG2_PROMPT, AG3_PROMPT, AG4_PROMPT, AG5_PROMPT


class AgentInventaire(Agent):
    nom = "AG1"
    marqueur = "__AGENT_1_INVENTAIRE__"
    outils_autorises = ["lire_fichier", "chercher_connaissance"]
    role_prompt = AG1_PROMPT

    def donnees(self, contexte: dict[str, Any]) -> str:
        description = contexte.get("description_assainie", "")
        metier = contexte.get("contexte_metier", "")
        retour = f"<<<DONNEES-SYSTEME-A-ANALYSER>>>\n{description}\n<<<FIN-DONNEES>>>"
        if metier:
            # Le contexte métier est lui aussi une donnée non fiable (G1).
            retour += f"\n\n<<<DONNEES-METIER>>>\n{metier}\n<<<FIN-DONNEES>>>"
        return retour

    def schema_rappel(self) -> str:
        return """{"agent":"AG1","resume":"...","sortie":{"actifs":[
  {"id":"A-nn","nom":"...","type":"donnée|application|service|tiers|humain|intangible",
   "description":"...","criticite":["C","I","A"],"valeur":"critique|élevée|moyenne|faible",
   "proprietaire":"...","contraintes":["RGPD-art9","HDS"]}]},"sources":["..."],"incertitudes":[]}"""


class AgentModele(Agent):
    nom = "AG2"
    marqueur = "__AGENT_2_MODELE__"
    outils_autorises = ["chercher_connaissance"]
    role_prompt = AG2_PROMPT

    def donnees(self, contexte: dict[str, Any]) -> str:
        actifs = contexte.get("actifs", [])
        actifs_json = json.dumps(actifs, ensure_ascii=False, indent=1)
        return f"ACTIFS\n{actifs_json}"

    def schema_rappel(self) -> str:
        return """{"agent":"AG2","resume":"...","sortie":{
  "modele_retenu":"STRIDE","modeles_complementaires":["LINDDUN"],
  "justification":"...","criteres":{...},"grille_evaluation":"matrice_PxI",
  "echelle_probabilite":["faible","moyenne","élevée"],
  "echelle_impact":["faible","moyen","élevé"]},"sources":["..."],"incertitudes":[]}"""


class AgentMenaces(Agent):
    nom = "AG3"
    marqueur = "__AGENT_3_MENACES__"
    outils_autorises = ["chercher_connaissance", "rechercher_cve"]
    role_prompt = AG3_PROMPT

    def donnees(self, contexte: dict[str, Any]) -> str:
        actifs = json.dumps(contexte.get("actifs", []), ensure_ascii=False)
        modele = json.dumps(contexte.get("modele", {}), ensure_ascii=False)
        description = contexte.get("description_assainie", "")
        cve = contexte.get("cve", [])
        cve_bloc = json.dumps(cve, ensure_ascii=False) if cve else "Aucune CVE pré-recherchée."
        return (
            f"ACTIFS\n{actifs}\n\nMODELE\n{modele}\n\n"
            f"<<<DONNEES-SYSTEME-A-ANALYSER>>>\n{description}\n<<<FIN-DONNEES>>>\n\n"
            f"REFERENCES CVE (snapshot local)\n{cve_bloc}"
        )

    def schema_rappel(self) -> str:
        return """{"agent":"AG3","resume":"...","sortie":{"menaces":[
  {"id_menace":"M-nn","actif":"A-nn","frontiere":"1|2|3|4|5|6",
   "description":"...","categorie":"STRIDE-I|LINDDUN-DD",
   "vulnerabilite":"...","source_menace":"..."}]},"sources":["..."],"incertitudes":[]}"""


class AgentEvaluation(Agent):
    nom = "AG4"
    marqueur = "__AGENT_4_EVALUATION__"
    outils_autorises = ["calculer_niveau"]
    role_prompt = AG4_PROMPT

    def donnees(self, contexte: dict[str, Any]) -> str:
        menaces = json.dumps(contexte.get("menaces", []), ensure_ascii=False)
        echelles = json.dumps(contexte.get("echelles", {}), ensure_ascii=False)
        return f"MENACES\n{menaces}\n\nECHELLES (Agent 2)\n{echelles}"

    def schema_rappel(self) -> str:
        return """{"agent":"AG4","resume":"...","sortie":{"evaluations":[
  {"id_menace":"M-nn","probabilite":"faible|moyenne|élevée",
   "impact":"faible|moyen|élevé","niveau":"<laisse vide ou faux : vérifié>",
   "justification":"..."}]},"sources":["..."],"incertitudes":[]}"""


class AgentTraitement(Agent):
    nom = "AG5"
    marqueur = "__AGENT_5_TRAITEMENT__"
    outils_autorises = ["chercher_connaissance", "calculer_niveau"]
    role_prompt = AG5_PROMPT

    def donnees(self, contexte: dict[str, Any]) -> str:
        evaluations = json.dumps(contexte.get("evaluations", []), ensure_ascii=False)
        actifs = json.dumps(contexte.get("actifs", []), ensure_ascii=False)
        menaces = json.dumps(contexte.get("menaces", []), ensure_ascii=False)
        return f"EVALUATIONS (étage 4)\n{evaluations}\n\nACTIFS\n{actifs}\n\nMENACES\n{menaces}"

    def schema_rappel(self) -> str:
        return """{"agent":"AG5","resume":"...","sortie":{"risques":[
  {"id":"R-nn","actif":"...","menace_id":"M-nn","menace":"...",
   "categorie":"...","probabilite":"...","impact":"...","niveau":"...",
   "traitement":"réduire|transférer|éviter|accepter",
   "mesures":["<mesure> (catégorie/fonction)"],
   "justification":"...","sources":["..."],"risque_residuel":"...",
   "proprietaire":"...","valide_par":null}]},"sources":["..."],"incertitudes":[]}"""


AGENTS: dict[str, type[Agent]] = {
    "AG1": AgentInventaire,
    "AG2": AgentModele,
    "AG3": AgentMenaces,
    "AG4": AgentEvaluation,
    "AG5": AgentTraitement,
}

ORDRE = ["AG1", "AG2", "AG3", "AG4", "AG5"]