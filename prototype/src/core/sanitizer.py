"""Filtrage des entrées non fiables (prompt injection mitigation).

Gardes-fous mis en œuvre (cf. `02_Architecture_MultiAgents.md`, G1 + LLM01 OWASP) :
- 1. Séparation stricte : le document étudié est TOUJOURS présenté comme DONNÉE,
     jamais comme consigne (délimiteurs + bloc quote).
- 2. Détection de motifs d'injection connus : remplacement et signalement.
- 3. Toute détection est journalisée et transmise aux agents via `incertitudes`.
"""

from __future__ import annotations

import re

# Motifs d'injection de prompt typiques (OWASP LLM Top 10, LLM01), FR + EN.
_MOTIFS_INJECTION: list[tuple[str, re.Pattern[str]]] = [
    ("ignore_instructions", re.compile(r"ignores?\s+(your|the|all|previous|tes|vos|les|mes|toutes)\s+.{0,60}(instructions|consignes|règles|directives|rules|prompt)", re.I)),
    ("disable_securite", re.compile(r"(désactive|désactiver|oublie|oublier|forget|disregard|ignorer|ignores?|ne\s+tiens\s+pas\s+compte)\s+(tes|vos|les|all|your|previous|toutes|règles|consignes|rules|instructions|sécurité)", re.I)),
    ("override_system", re.compile(r"(system\s*prompt|new\s*system prompt|tu\s+es\s+maintenant|vous\s+êtes\s+désormais|you\s+are\s+now|act\s+as|pretend\s+to\s+be)", re.I)),
    ("nouvelle_persona", re.compile(r"(à partir de maintenant|désormais|dorénavant|from now on|fais\s+comme\s+si|pretend)", re.I)),
    ("delimiter_escape", re.compile(r"<<\s*SYS\s*>>|<\|im_start\|>|<\|system\|>|<\|user\|>", re.I)),
    ("data_as_instruction", re.compile(r"^\s*(instructions|consignes|directives|rules)\s*:?", re.M | re.I)),
    ("jailbreak_mot", re.compile(r"jail\s*break|désactive\s+(tes|vos)\s+(règles|consignes)|ignorer\s+(tes|vos)\s+instructions", re.I)),
    ("assistant_prefix", re.compile(r"(?m)^\s*(assistant|human)\s*:", re.I)),
    ("disclose_secrets", re.compile(r"(disclose|reveal|affiche|montre|dévoile|révèle)\s+(your|tes|vos|toutes)\s+(instructions|prompt|secrets|clefs|clés|system)", re.I)),
    ("replay_prompt", re.compile(r"(répète|repeat|resume|répète)\s*(tout |until now |ce qui précède |everything above )?\s*.{0,30}(prompt|instructions|consignes|contexte précédent)", re.I)),
]


class Detection:
    """Une inspection détectée dans le document."""

    __slots__ = ("motif", "extrait")

    def __init__(self, motif: str, extrait: str) -> None:
        self.motif = motif
        self.extrait = extrait[:120]

    def to_dict(self) -> dict[str, str]:
        return {"motif": self.motif, "extrait": self.extrait}


def detecter_injections(texte: str) -> list[Detection]:
    """Retourne la liste des détections (motif + extrait). Ne modifie rien."""
    detections: list[Detection] = []
    for motif, pattern in _MOTIFS_INJECTION:
        found = pattern.findall(texte)
        if found:
            # L'extrait retenu est la portion déclencheuse la plus courte.
            extrait = found[0] if isinstance(found[0], str) else " ".join(found[0])
            detections.append(Detection(motif, extrait))
    return detections


def neutraliser(texte: str) -> str:
    """Remplace les motifs détectés par un marqueur inoffensif.

    Le marqueur conserve la trace de la détection sans donner d'instruction au LLM.
    """
    resultat = texte
    for motif, pattern in _MOTIFS_INJECTION:
        resultat = pattern.sub("[[DONNEE-NON-EXECUTABLE]]", resultat)
    return resultat


def _entourer_comme_donnees(texte: str) -> str:
    """Enveloppe le document dans un bloc réservé aux données (séparation consigne/donnée)."""
    return f"<<<DONNEES-SYSTEME-A-ANALYSER>>>\n```text\n{texte}\n```\n<<<FIN-DONNEES>>>"


def sanctionner_document(texte: str) -> tuple[str, list[Detection]]:
    """Applique les trois protections et retourne le texte assaini + les détections.

    La sortie peut être injectée telle quelle dans un prompt : elle est neutralisée
    et balisée comme donnée, ce qui la rend inopérante comme instruction.
    """
    detections = detecter_injections(texte)
    assaini = neutraliser(texte)
    return _entourer_comme_donnees(assaini), detections