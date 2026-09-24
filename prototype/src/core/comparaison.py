"""Comparaison registre généré vs analyse manuelle de référence (jalon 4).

⚠️ Sémantique, assumée dans le dossier (04) :
- le simulateur (`FournisseurSimule`, mode `fidele=True`) REPRODUIT la référence
  pour tester la chaîne : son 10/10 ne prouve RIEN sur la qualité de l'analyse ;
- une vraie comparaison n'a de sens qu'avec un fournisseur RÉEL (mode `openai`) ;
- pour prouver que la comparaison n'est pas tautologique, le simulateur dispose
  d'un mode `fidele=False` qui produit un registre différent : on vérifie alors
  (test) que `comparer_registres` détecte bien les risques inventés, oubliés,
  et les écarts de niveau.
"""

from __future__ import annotations

from typing import Any

CHAMPS_COMPARES = ("actif", "probabilite", "impact", "niveau", "traitement")


def comparer_registres(genere: list[dict[str, Any]],
                       reference: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare deux registres par identifiant (`R-nn`). Ne mute aucun argument.

    Retourne : retrouves / inventes / oublies / ecarts_par_risque /
    nb_ecarts_niveau et une synthèse prête à afficher.
    """
    ref = {r["id"]: r for r in reference}
    gen = {r["id"]: r for r in genere}

    retrouves = sorted(set(ref) & set(gen))
    inventes = sorted(set(gen) - set(ref))
    oublies = sorted(set(ref) - set(gen))

    ecarts: dict[str, dict[str, tuple[Any, Any]]] = {}
    for identifiant in retrouves:
        differences = {
            champ: (ref[identifiant].get(champ), gen[identifiant].get(champ))
            for champ in CHAMPS_COMPARES
            if str(ref[identifiant].get(champ, "")).strip().lower()
            != str(gen[identifiant].get(champ, "")).strip().lower()
        }
        if differences:
            ecarts[identifiant] = differences

    nb_ecarts_niveau = sum(
        1 for diff in ecarts.values() if "niveau" in diff
    )

    return {
        "nb_reference": len(ref),
        "nb_genere": len(gen),
        "retrouves": retrouves,
        "inventes": inventes,
        "oublies": oublies,
        "ecarts_par_risque": ecarts,
        "nb_ecarts_niveau": nb_ecarts_niveau,
        "taux_reconciliation": round(len(retrouves) / len(ref), 2) if ref else 0.0,
        "synthese": (
            f"{len(retrouves)}/{len(ref)} risques retrouvés · "
            f"{len(inventes)} inventés · {len(oublies)} oubliés · "
            f"{nb_ecarts_niveau} écart(s) de niveau"
        ),
    }