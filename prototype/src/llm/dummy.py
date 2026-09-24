"""Fournisseur simulé (dry-run) : sorties déterministes pour la démo et les tests.

⚠️ HONNÊTETÉ : ce simulateur REPRODUIT l'analyse de référence
(`03_Analyse_Manuelle_Reference.md`) pour pouvoir :
- exécuter toute la chaîne SANS clé API ni réseau (démo, tests) ;
- vérifier que le PIPELINE (validations, schémas, garde-fous) fonctionne.

Il ne PRÉTEND PAS produire une analyse : un « 10/10 réconcilié » en dry-run ne
prouve que la cohérence de la chaîne. La vraie comparaison agents ↔ analyse
manuelle ne prend un sens qu'avec un fournisseur RÉEL (`OpenAICompatProvider`,
mode `openai`) — cf. `04_Tests_Comparaison_Agents.md` et la checklist (p. 27).

Mode `fidele=False` : produit volontairement un registre VALIDE mais DIVERGENT
(risque oublié, risque inventé, écart de niveau) pour prouver — test à l'appui —
que `comparer_registres` sait détecter les écarts (comparaison non tautologique).
"""

from __future__ import annotations

import copy
import json

from .interface import extraire_json

_ACTIFS: list[dict[str, object]] = [
    {"id": "A-01", "nom": "Base de dossiers patients", "type": "donnée",
     "description": "Dossiers, comptes rendus et documents des patients (données de santé, catégorie particulière RGPD).",
     "criticite": ["C", "I"], "valeur": "critique", "proprietaire": "Direction médicale",
     "contraintes": ["RGPD-art9", "HDS"]},
    {"id": "A-02", "nom": "Comptes et identités (patients, médecins, admins)", "type": "donnée",
     "description": "Identités, MFA, sessions ; un compte médecin donne accès aux dossiers et aux ordonnances.",
     "criticite": ["C", "A"], "valeur": "critique", "proprietaire": "RSSI / IAM", "contraintes": []},
    {"id": "A-03", "nom": "Console d'administration", "type": "application",
     "description": "Console du secrétariat et de l'exploitation : privilèges élevés sur la plateforme.",
     "criticite": ["C", "I", "A"], "valeur": "critique", "proprietaire": "RSSI", "contraintes": []},
    {"id": "A-04", "nom": "Service de visioconférence", "type": "service",
     "description": "Visio WebRTC via prestataire externe ; indisponibilité = consultations annulées.",
     "criticite": ["A", "C"], "valeur": "élevée", "proprietaire": "Direction produit", "contraintes": ["HDS"]},
    {"id": "A-05", "nom": "Agenda / prise de rendez-vous", "type": "application",
     "description": "Gestion des rendez-vous patients-médecins.",
     "criticite": ["A", "I"], "valeur": "élevée", "proprietaire": "Direction produit", "contraintes": []},
    {"id": "A-06", "nom": "Messagerie sécurisée patient-médecin", "type": "service",
     "description": "Messages interpersonnels entre patients et soignants.",
     "criticite": ["C", "I"], "valeur": "élevée", "proprietaire": "Direction médicale", "contraintes": []},
    {"id": "A-07", "nom": "Comptes rendus et ordonnances", "type": "donnée",
     "description": "Documents médicaux ; leur altération présente un risque direct pour le patient.",
     "criticite": ["I", "C"], "valeur": "élevée", "proprietaire": "Direction médicale", "contraintes": ["RGPD-art9"]},
    {"id": "A-08", "nom": "Sauvegardes chiffrées", "type": "donnée",
     "description": "Sauvegardes hors ligne chiffrées, unique recours contre un rançongiciel.",
     "criticite": ["A", "C"], "valeur": "élevée", "proprietaire": "DSI", "contraintes": []},
    {"id": "A-09", "nom": "Journaux horodatés (auth, accès)", "type": "donnée",
     "description": "Traçabilité des accès aux dossiers (non-répudiation, audits).",
     "criticite": ["I", "A"], "valeur": "élevée", "proprietaire": "RSSI", "contraintes": []},
    {"id": "A-10", "nom": "Clés de chiffrement et certificats TLS", "type": "service",
     "description": "Confidentialité en transit et au repos.",
     "criticite": ["C", "I"], "valeur": "élevée", "proprietaire": "RSSI", "contraintes": []},
    {"id": "A-11", "nom": "Prestataires externes (visio, SMS, paiement, HDS)", "type": "tiers",
     "description": "Chaîne d'approvisionnement : accès sortants vers des tiers.",
     "criticite": ["A", "C"], "valeur": "élevée", "proprietaire": "Achats / DSI", "contraintes": ["HDS"]},
    {"id": "A-12", "nom": "Portail patient et application mobile", "type": "application",
     "description": "Surface publique, cible des premières attaques.",
     "criticite": ["A"], "valeur": "moyenne", "proprietaire": "Direction produit", "contraintes": []},
    {"id": "A-13", "nom": "Personnes (patients, médecins, secrétariat)", "type": "humain",
     "description": "Cible d'ingénierie sociale et de harponnage.",
     "criticite": ["C"], "valeur": "élevée", "proprietaire": "Direction", "contraintes": []},
    {"id": "A-14", "nom": "Réputation et conformité (RGPD, HDS)", "type": "intangible",
     "description": "Sanction CNIL jusqu'à 4 % du CA mondial, perte de confiance.",
     "criticite": ["C"], "valeur": "élevée", "proprietaire": "Direction générale", "contraintes": ["RGPD"]},
]

_MODELE: dict[str, object] = {
    "modele_retenu": "STRIDE",
    "modeles_complementaires": ["LINDDUN"],
    "justification": (
        "STRIDE convient car le cas B est décrit par son architecture et ses flux "
        "(approche software-centric), en phase de conception, avec un effort faible. "
        "LINDDUN est ajouté car le système traite des données de santé (catégorie "
        "particulière RGPD) : les menaces vie privée (liaison, identification, "
        "divulgation, méconnaissance) sont directement pertinentes."
    ),
    "critiques": {
        "question": "quelles menaces pèsent sur cette application ?",
        "donnees_sensibles": True,
        "phase": "conception",
        "moyens": "faibles",
    },
    "grille_evaluation": "matrice_PxI",
    "echelle_probabilite": ["faible", "moyenne", "élevée"],
    "echelle_impact": ["faible", "moyen", "élevé"],
}

_MENACES: list[dict[str, object]] = [
    {"id_menace": "M-01", "actif": "A-02", "frontiere": "2",
     "description": "Vol d'identifiants d'un médecin par harponnage ciblé puis connexion à la console d'administration.",
     "categorie": "STRIDE-S", "vulnerabilite": "absence de MFA résistant au phishing, formation insuffisante",
     "source_menace": "cybercriminel motivé (revente de dossiers)"},
    {"id_menace": "M-02", "actif": "A-01", "frontiere": "4",
     "description": "Consultation non autorisée d'un dossier patient par un compte interne compromis ou trop privilégié.",
     "categorie": "STRIDE-E", "vulnerabilite": "droits excessifs, pas de revue régulière des accès",
     "source_menace": "compte légitime détourné / salarié malveillant"},
    {"id_menace": "M-03", "actif": "A-01", "frontiere": "2",
     "description": "Exfiltration massive des dossiers via une API d'accès exposée sur Internet (contrôle d'autorisation défaillant).",
     "categorie": "STRIDE-I", "vulnerabilite": "défaut de contrôle d'accès côté serveur (BOLA)",
     "source_menace": "attaquant externe exploitant l'API"},
    {"id_menace": "M-04", "actif": "A-08", "frontiere": "6",
     "description": "Rançongiciel chiffre la production et efface les sauvegardes : perte irrémédiable des dossiers.",
     "categorie": "STRIDE-D", "vulnerabilite": "sauvegardes connectées, pas de test de restauration",
     "source_menace": "gang de rançongiciels"},
    {"id_menace": "M-05", "actif": "A-07", "frontiere": "4",
     "description": "Altération d'un compte rendu ou d'une ordonnance en transit ou au stockage : risque direct pour le patient.",
     "categorie": "STRIDE-T", "vulnerabilite": "absence de contrôle d'intégrité sur les documents",
     "source_menace": "interception ou accès interne non autorisé"},
    {"id_menace": "M-06", "actif": "A-04", "frontiere": "1",
     "description": "Indisponibilité prolongée du service de visio ou de l'agenda (panne, DDoS) : consultations annulées.",
     "categorie": "STRIDE-D", "vulnerabilite": "point unique de dépendance au prestataire, pas de bascule",
     "source_menace": "panne, DDoS"},
    {"id_menace": "M-07", "actif": "A-09", "frontiere": "6",
     "description": "Absence ou non-horodatage des journaux d'accès : une consultation de dossier ne peut être prouvée ni niée (répudiation).",
     "categorie": "STRIDE-R", "vulnerabilite": "journalisation incomplète, horloges non synchronisées (NTP)",
     "source_menace": "défaut d'exploitation / acteur interne"},
    {"id_menace": "M-08", "actif": "A-11", "frontiere": "5",
     "description": "Compromission d'un prestataire externe (visio, SMS, hébergeur) : porte d'entrée via une mise à jour ou une intégration.",
     "categorie": "STRIDE-T", "vulnerabilite": "dépendance sèche à des tiers, pas d'exigence SBOM",
     "source_menace": "attaquant ciblant la chaîne d'approvisionnement (cf. SolarWinds, 3CX)"},
    {"id_menace": "M-09", "actif": "A-13", "frontiere": "2",
     "description": "Ingénierie sociale sur le secrétariat (faux appui technique, urgence) pour obtenir un accès ou faire valider un changement.",
     "categorie": "STRIDE-S", "vulnerabilite": "sensibilisation insuffisante, pas de procédure de vérification en second canal",
     "source_menace": "attaquant social"},
    {"id_menace": "M-10", "actif": "A-01", "frontiere": "6",
     "description": "Données de santé en clair dans les journaux d'application ou d'analyse : divulgation et non-conformité RGPD.",
     "categorie": "LINDDUN-DD", "vulnerabilite": "défaut de minimisation et de masquage dans les journaux",
     "source_menace": "défaut de conception / opérateur privilégié"},
]

_EVALUATIONS: list[dict[str, object]] = [
    {"id_menace": "M-01", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "justification": "Le harponnage des professionnels de santé est un vecteur fréquent ; l'impact touche le secret médical."},
    {"id_menace": "M-02", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "justification": "Accès à tous les dossiers d'un médecin : divulgation massive possible."},
    {"id_menace": "M-03", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "justification": "Les API exposées sont régulièrement ciblées (OWASP API Top 10 BOLA)."},
    {"id_menace": "M-04", "probabilite": "faible", "impact": "élevé", "niveau": "moyen",
     "justification": "Événement rare mais à l'impact maximal si les sauvegardes sont emportées."},
    {"id_menace": "M-05", "probabilite": "faible", "impact": "élevé", "niveau": "moyen",
     "justification": "Nécessite un accès déjà acquis ; conséquences directes sur le patient."},
    {"id_menace": "M-06", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "justification": "Panne/DDoS du prestataire plausible ; indisponibilité = soins retardés."},
    {"id_menace": "M-07", "probabilite": "moyenne", "impact": "moyen", "niveau": "moyen",
     "justification": "Défaut d'exploitation fréquent ; conséquence sur la traçabilité et les audits."},
    {"id_menace": "M-08", "probabilite": "faible", "impact": "élevé", "niveau": "moyen",
     "justification": "Compromission tierce rare mais à très fort impact (SCM)."},
    {"id_menace": "M-09", "probabilite": "élevée", "impact": "moyen", "niveau": "élevé",
     "justification": "L'ingénierie sociale est le vecteur le plus couramment exploité."},
    {"id_menace": "M-10", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "justification": "Non-minimisation des journaux = infraction RGPD + fuite de santé."},
]

_RISQUES: list[dict[str, object]] = [
    {"id": "R-01", "actif": "Comptes et identités (médecins)", "menace_id": "M-01",
     "menace": "Vol d'identifiants d'un médecin par harponnage puis connexion à la console d'administration.",
     "categorie": "STRIDE-S", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "traitement": "réduire",
     "mesures": ["MFA FIDO2 résistant au phishing (technique/préventif)",
                 "Sensibilisation + simulations de phishing (administratif/préventif)",
                 "Alerte sur connexion inhabituelle (technique/détectif)"],
     "justification": "Ancré dans le cas : un compte médecin donne accès aux dossiers et aux ordonnances.",
     "sources": ["STRIDE-S", "ANSSI (MFA)", "OWASP ASVS V2"],
     "risque_residuel": "moyen", "proprietaire": "RSSI", "valide_par": None},
    {"id": "R-02", "actif": "Base de dossiers patients", "menace_id": "M-02",
     "menace": "Consultation non autorisée d'un dossier patient par un compte interne compromis ou trop privilégié.",
     "categorie": "STRIDE-E", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "traitement": "réduire",
     "mesures": ["Moindre privilège + revue trimestrielle des droits (administratif/préventif)",
                 "Contrôle d'accès par besoin d'en connaître (technique/préventif)",
                 "Journal d'accès aux dossiers (technique/détectif)"],
     "justification": "Le cas prévoit des accès nominatifs au dossier ; l'écart permis/réel est ici la menace.",
     "sources": ["STRIDE-E", "ISO/IEC 27002 A.5.15", "RGPD art. 32"],
     "risque_residuel": "moyen", "proprietaire": "Direction médicale", "valide_par": None},
    {"id": "R-03", "actif": "Base de dossiers patients", "menace_id": "M-03",
     "menace": "Exfiltration massive des dossiers via une API d'accès exposée sur Internet (contrôle d'autorisation défaillant).",
     "categorie": "STRIDE-I", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "traitement": "réduire",
     "mesures": ["Contrôle d'autorisation systématique côté serveur (technique/préventif)",
                 "Tests d'intrusion avant mise en production (administratif/préventif)",
                 "Détection d'exfiltration volumineuse (technique/détectif)"],
     "justification": "L'API Gateway est en frontière de confiance 2, exposée sur Internet.",
     "sources": ["STRIDE-I", "OWASP API Top 10 (BOLA)", "ISO/IEC 27002 A.8.24"],
     "risque_residuel": "moyen", "proprietaire": "RSSI", "valide_par": None},
    {"id": "R-04", "actif": "Sauvegardes chiffrées", "menace_id": "M-04",
     "menace": "Rançongiciel chiffre la production et efface les sauvegardes : perte irrémédiable.",
     "categorie": "STRIDE-D", "probabilite": "faible", "impact": "élevé", "niveau": "moyen",
     "traitement": "réduire",
     "mesures": ["Sauvegardes hors ligne immuables, règle 3-2-1 (technique/préventif)",
                 "Test de restauration mensuel (administratif/détectif)",
                 "Segmentation réseau + EDR (technique/préventif)"],
     "justification": "Le cas place les sauvegardes chiffrées comme unique recours ; leur isolation est critique.",
     "sources": ["STRIDE-D", "ANSSI (sauvegardes)", "ISO/IEC 27002 A.8.13"],
     "risque_residuel": "faible", "proprietaire": "DSI", "valide_par": None},
    {"id": "R-05", "actif": "Comptes rendus et ordonnances", "menace_id": "M-05",
     "menace": "Altération d'un compte rendu ou d'une ordonnance en transit ou au stockage.",
     "categorie": "STRIDE-T", "probabilite": "faible", "impact": "élevé", "niveau": "moyen",
     "traitement": "réduire",
     "mesures": ["TLS 1.3 obligatoire (technique/préventif)",
                 "Hachage + signature des documents (technique/préventif)",
                 "Contrôle des versions (technique/détectif)"],
     "justification": "L'intégrité des documents médicaux conditionne l'acte de soin.",
     "sources": ["STRIDE-T", "ISO/IEC 27002 A.8.24", "RGPD art. 32"],
     "risque_residuel": "faible", "proprietaire": "Direction médicale", "valide_par": None},
    {"id": "R-06", "actif": "Service de visioconférence", "menace_id": "M-06",
     "menace": "Indisponibilité prolongée du service de visio ou de l'agenda (panne, DDoS).",
     "categorie": "STRIDE-D", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "traitement": "transférer",
     "mesures": ["Redondance multi-zone + bascule (technique/préventif)",
                 "Protection anti-DDoS (technique/préventif)",
                 "SLA contractuel avec le prestataire + cyber-assurance (administratif/compensatoire)"],
     "justification": "Dépendance au prestataire visio (frontière 5) : le risque est partiellement transférable.",
     "sources": ["STRIDE-D", "ISO/IEC 27002 A.8.14", "cours ch. 09 (RTO/RPO)"],
     "risque_residuel": "moyen", "proprietaire": "Direction produit", "valide_par": None},
    {"id": "R-07", "actif": "Journaux horodatés", "menace_id": "M-07",
     "menace": "Absence ou non-horodatage des journaux : une consultation ne peut être prouvée ni niée (répudiation).",
     "categorie": "STRIDE-R", "probabilite": "moyenne", "impact": "moyen", "niveau": "moyen",
     "traitement": "réduire",
     "mesures": ["Journaux centralisés + NTP + conservation 12 mois (technique/préventif)",
                 "Revue mensuelle des accès administrateurs (administratif/détectif)"],
     "justification": "La traçabilité est exigée par le contexte (secret médical, audits).",
     "sources": ["STRIDE-R", "ISO/IEC 27002 A.8.15/A.8.16"],
     "risque_residuel": "faible", "proprietaire": "RSSI", "valide_par": None},
    {"id": "R-08", "actif": "Prestataires externes", "menace_id": "M-08",
     "menace": "Compromission d'un prestataire externe (visio, SMS, hébergeur) ouvrant une porte d'entrée dans la plateforme.",
     "categorie": "STRIDE-T", "probabilite": "faible", "impact": "élevé", "niveau": "moyen",
     "traitement": "transférer",
     "mesures": ["Évaluation précontractuelle + clause de notification (administratif/préventif)",
                 "Exigence SBOM (administratif/préventif)",
                 "Revue trimestrielle des accès tiers (technique/préventif)"],
     "justification": "Le cas déclare des flux sortants vers des tiers (frontière 5) : SCRM.",
     "sources": ["STRIDE-T", "cours ch. 07 (SCRM, SolarWinds/3CX/XZ)", "ISO/IEC 27002 A.5.19"],
     "risque_residuel": "moyen", "proprietaire": "Achats / DSI", "valide_par": None},
    {"id": "R-09", "actif": "Personnes (secrétariat)", "menace_id": "M-09",
     "menace": "Ingénierie sociale sur le secrétariat pour obtenir un accès ou faire valider un changement.",
     "categorie": "STRIDE-S", "probabilite": "élevée", "impact": "moyen", "niveau": "élevé",
     "traitement": "réduire",
     "mesures": ["Sensibilisation trimestrielle + simulations (administratif/préventif)",
                 "Procédure de vérification en second canal (administratif/directif)"],
     "justification": "Vecteur le plus exploité ; le secrétariat manipule l'agenda et la facturation.",
     "sources": ["STRIDE-S", "cours ch. 08 (ingénierie sociale)"],
     "risque_residuel": "moyen", "proprietaire": "Direction", "valide_par": None},
    {"id": "R-10", "actif": "Base de dossiers patients", "menace_id": "M-10",
     "menace": "Données de santé en clair dans les journaux d'application ou d'analyse : divulgation et non-conformité.",
     "categorie": "LINDDUN-DD", "probabilite": "moyenne", "impact": "élevé", "niveau": "élevé",
     "traitement": "réduire",
     "mesures": ["Masquage et chiffrement des journaux (technique/préventif)",
                 "Minimisation + purge à 90 jours (administratif/préventif)",
                 "Revue de conformité AIPD (administratif/détectif)"],
     "justification": "Menace vie privée typique du cas : données de santé dans les journaux.",
     "sources": ["LINDDUN-DD", "RGPD art. 5, 9, 25"],
     "risque_residuel": "moyen", "proprietaire": "DPO", "valide_par": None},
]


class FournisseurSimule:
    """Fournisseur déterministe : reproduit la référence (test de chaîne).

    `fidele=False` : sortie volontairement divergente (voir docstring).
    """

    nom_produit = "dummy-deterministic (test de chaîne — n'est PAS une analyse)"

    def __init__(self, *, troubler: bool = False, fidele: bool = True) -> None:
        self.troubler = troubler
        self.fidele = fidele

    def complete(self, systeme: str, utilisateur: str) -> str:
        """Retourne une sortie de référence selon l'agent attendu dans le prompt."""
        if "AGENT_1_INVENTAIRE" in utilisateur:
            return self._enveloppe("AG1", {"actifs": copy.deepcopy(_ACTIFS)},
                                   sources=["cas B (01_Cadrage)", "ISO/IEC 27005"])
        if "AGENT_2_MODELE" in utilisateur:
            return self._enveloppe("AG2", _MODELE, sources=["cours E21 ch. 06/10", "sujet p. 11-12"])
        if "AGENT_3_MENACES" in utilisateur:
            return self._enveloppe("AG3", {"menaces": copy.deepcopy(_MENACES)},
                                   sources=["STRIDE", "LINDDUN", "01_Cadrage (frontières)"])
        if "AGENT_4_EVALUATION" in utilisateur:
            evaluations = copy.deepcopy(_EVALUATIONS)
            if not self.fidele:
                # Écart volontaire mais VALIDE (matrice) : M-09 évalué (élevée, faible) → moyen.
                for ev in evaluations:
                    if ev["id_menace"] == "M-09":
                        ev["probabilite"] = "élevée"
                        ev["impact"] = "faible"
                        ev["niveau"] = "moyen"
            return self._enveloppe("AG4", {"evaluations": evaluations},
                                   sources=["matrice P×I (sujet p. 8)", "01_Cadrage (contexte)"])
        if "AGENT_5_TRAITEMENT" in utilisateur:
            risques = [dict(r) for r in _RISQUES]
            if not self.fidele:
                # Registre valide mais divergent : R-07 oublié, R-11 inventé,
                # R-09 avec un écart de niveau, R-08 avec un autre traitement,
                # R-04 avec un texte de menace modifié.
                risques = [r for r in risques if r["id"] != "R-07"]
                for r in risques:
                    if r["id"] == "R-09":
                        r["probabilite"] = "élevée"
                        r["impact"] = "faible"
                        r["niveau"] = "moyen"
                        r["mesures"] = ["Sensibilisation annuelle"]
                    if r["id"] == "R-08":
                        r["traitement"] = "réduire"
                    if r["id"] == "R-04":
                        r["menace"] = "Perte des sauvegardes lors d'une panne datacenter."
                risques.append({
                    "id": "R-11", "actif": "Portail patient", "menace_id": "M-05",
                    "menace": "Risque inventé : dégradation du portail patient pendant les pics.",
                    "categorie": "STRIDE-D", "probabilite": "faible", "impact": "élevé",
                    "niveau": "moyen", "traitement": "accepter",
                    "mesures": ["Aucune"], "justification": "Risque fictif du mode imparfait.",
                    "sources": ["matrice P×I"], "risque_residuel": "faible",
                    "proprietaire": "DSI", "valide_par": None,
                })
            if self.troubler:
                # Mode dégradé pour les tests de garde-fous.
                risques[0]["valide_par"] = "agent"
                risques[1]["sources"] = []
                risques[2]["traitement"] = "ignorer"
                risques[3]["niveau"] = "critique"
            return self._enveloppe("AG5", {"risques": risques},
                                   sources=["ISO/IEC 27002", "ANSSI", "cours ch. 05"])
        raise ValueError("prompt inconnu : aucune sortie simulée")

    def _enveloppe(self, agent: str, sortie: object, sources: list[str]) -> str:
        return json.dumps({
            "agent": agent,
            "resume": f"sortie simulée pour {agent}",
            "sortie": sortie,
            "sources": sources,
            "incertitudes": [],
        }, ensure_ascii=False)