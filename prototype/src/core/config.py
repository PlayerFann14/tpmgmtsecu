"""Configuration globale du système (constantes partagées)."""

from __future__ import annotations

from pathlib import Path

# --- Chemins ---------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]          # prototype/
SRC_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
CASES_DIR = PROJECT_ROOT / "cases"
DATA_DIR = PROJECT_ROOT / "data"
RUNS_DIR = PROJECT_ROOT / "runs"

# --- Échelles (fixées par l'Agent 2, vérifiées par l'orchestrateur) -------
ECHELLE_PROBABILITE = ["faible", "moyenne", "élevée"]
ECHELLE_IMPACT = ["faible", "moyen", "élevé"]
NIVEAUX = ["faible", "moyen", "élevé", "critique"]

# Matrice probabilité × impact — sujet p. 8 du projet E21.
# Probabilité (ligne) × Impact (colonne) → niveau de risque.
MATRICE_RISQUE: dict[str, dict[str, str]] = {
    "élevée": {"faible": "moyen", "moyen": "élevé", "élevé": "critique"},
    "moyenne": {"faible": "faible", "moyen": "moyen", "élevé": "élevé"},
    "faible": {"faible": "faible", "moyen": "faible", "élevé": "moyen"},
}

TRAITEMENTS_AUTORISES = {"réduire", "transférer", "éviter", "accepter"}

# Réponses JAIS (litiges) interdites : « ignorer » n'est jamais un traitement.
TRAITEMENTS_INTERDITS = {"ignorer", "aucun", "rien", "néant", "ne rien faire"}

# Nombre maximal de tentatives (exécution + réparations) par agent.
MAX_TENTATIVES = 3

# Taille maximale d'un document d'entrée (anti-DoS du modèle).
MAX_DOCUMENT_OCTETS = 100_000
MAX_PROMPT_OCTETS = 25_000