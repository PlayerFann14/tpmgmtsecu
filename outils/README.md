# outils/ — Génération des PDF des livrables

Ce dossier contient le script de conversion **Markdown → PDF** utilisé pour produire
les livrables PDF du projet E21.

## Script : `md_to_pdf.py`

Convertit un ou plusieurs documents Markdown en PDF **A4** (même nom, extension `.pdf`).

```bash
# Depuis la racine du projet
/tmp/opencode/venv/bin/python outils/md_to_pdf.py 05_Dossier_Ecrit.md 06_Slides_Soutenance.md
```

Moteurs utilisés (dans l'ordre) :
1. **WeasyPrint** — meilleur rendu (page numbers, styles complets) ; nécessite les
   bibliothèques système `libpango` (`apt-get install libpango-1.0-0 libpangocairo-1.0-0`).
2. **xhtml2pdf** — repli **100 % Python** (aucune dépendance système), automatique.

Dépendances Python (à installer dans le venv) :
```bash
/tmp/opencode/venv/bin/pip install markdown weasyprint xhtml2pdf
```

## PDF générés (2026-09-23)

| Fichier | Pages | Rôle |
|---|---|---|
| `01_Cadrage_CasB_Teleconsultation.pdf` | — | description du cas (jalon 1) |
| `02_Architecture_MultiAgents.pdf` | — | conception (jalon 2) |
| `03_Analyse_Manuelle_Reference.pdf` | — | référence manuelle (jalon 1/3) |
| `04_Tests_Comparaison_Agents.pdf` | 8 | tests + grille C1→C10 (jalon 4) |
| `05_Dossier_Ecrit.pdf` | 13 | **dossier écrit (livrable principal)** |
| `06_Slides_Soutenance.pdf` | 6 | support de soutenance 45 min |

> ⚠️ Relancer la conversion **après toute modification** des `.md` (ex. compléter le
> § 9 « Outils d'IA utilisés » du dossier).