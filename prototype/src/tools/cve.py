"""Outil `rechercher_cve` : snapshot local CVE/CVSS (lecture seule, G4).

⚠️ NE PAS utiliser comme source de vérité : il s'agit d'un instantané de démonstration
figé dans `data/cve_snapshot.json`. En production, interroger le NVD
(https://nvd.nist.gov) — et citer la référence dans `sources`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..core.config import DATA_DIR


def _charger_snapshot() -> list[dict[str, object]]:
    chemin = DATA_DIR / "cve_snapshot.json"
    with chemin.open(encoding="utf-8") as fh:
        return json.load(fh)


def rechercher_cve(mots: str = "", version: str = "", **_: object) -> dict[str, object]:
    """Retourne les CVE du snapshot dont les mots-clés (ou la version) correspondent."""
    termes = [m for m in re.findall(r"[a-z0-9]{3,}", (mots or "").lower())]
    if not termes and not version:
        return {
            "note": "critère de recherche vide : préciser des mots-clés (ex. 'vpn', 'exchange')",
            "cves": [],
        }
    cibles = [c for c in _charger_snapshot() if _correspond(c, termes, version)]

    if not cibles:
        return {
            "note": "aucune CVE correspondante dans le snapshot local — "
                    "ne pas en inventer, consulter le NVD en production",
            "cves": [],
        }
    return {"cves": cibles,
            "note": "snapshot local de démonstration — référence : NIST NVD / FIRST CVSS v4.0"}


def _correspond(cve: dict[str, object], termes: list[str], version: str) -> bool:
    texte = " ".join(str(v) for v in cve.values()).lower()
    if termes and not all(t in texte for t in termes):
        return False
    if version and version.lower() not in texte:
        return False
    return True