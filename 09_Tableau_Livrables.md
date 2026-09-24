# 09 · Tableau des livrables — quoi rendre, quoi montrer, quoi garder

> Récapitulatif des documents du projet E21, classés en **3 catégories** :
> **A. À rendre** (dépôt final, checklist sujet p. 28) · **B. Pour la soutenance**
> (présentation + démo) · **C. Supports internes** (on garde pour soi).
> Mise à jour : 2026-09-24. Les fichiers `*.md` sont les sources ; les `*.pdf`
> sont les fichiers à déposer/utiliser.

---

## A. À rendre — dépôt final (dossier + prototype + traces)

| # | Document | Fichier | Rôle |
|---|---|---|---|
| A1 | **Dossier écrit** | `05_Dossier_Ecrit.md/.pdf` | LE dossier : cas, approche, prompts (annexe), registre (10 risques), analyse critique, réponses à la checklist p. 28. **§ 9 complété** : modèle visé `gpt-4o-mini` (API OpenAI-compatible), OpenCode v2.0.15, Python 3.13.5, pytest 9.1.1, jsonschema 4.26.0, Markdown 3.10.3, xhtml2pdf 0.2.20 / weasyprint 70.0 / PyMuPDF 1.28.2 (`outils/md_to_pdf.py`), git 2.47.3. |
| A2 | Annexes du dossier | `01_Cadrage_CasB_Teleconsultation.md/.pdf` | Cadrage : frontières du cas B, limites, choix STRIDE + LINDDUN. |
| A3 | 〃 | `02_Architecture_MultiAgents.md/.pdf` | Conception : pipeline AG1→AG5, garde-fous G1→G10, schémas JSON. |
| A4 | 〃 | `03_Analyse_Manuelle_Reference.md/.pdf` | Analyse 100 % manuelle (vérité terrain, 10 risques attendus). |
| A5 | 〃 | `04_Tests_Comparaison_Agents.md/.pdf` | Jalon 4 : grille C1→C10 remplie, test d'injection, validation humaine. |
| A6 | **Prototype** | dossier `prototype/` | Code complet à déposer tel quel : `run.py`, `src/` (dont module de comparaison `src/core/comparaison.py`), `tests/` (82 tests, 8 fichiers, dont `test_comparaison.py`), `cases/`, `data/` (dont **`reference_manuelle.json`** — export structuré de 03, cible du `--comparer`), `knowledge/`, `requirements.txt`, `README.md`, `GUIDE_UTILISATION.md`, `FONCTIONNEMENT.md`. |
| A7 | **Traces de référence** | `prototype/runs/run-20260924-095723/` | Run **validation humaine mixte** signé `Dr Dupont` : R-01 corrigé (impact + source, niveau recalculé par la matrice), R-02→R-09 acceptés, R-10 différé (`valide_par` null). Octets mesurés : AG1 5 048 → AG5 11 289. |
| A8 | 〃 | `prototype/runs/run-20260924-095714/` | Run **cas B dry-run + `--comparer`** (`dummy-deterministic (test de chaîne — n'est PAS une analyse)`, `valide_par` null ; tautologie assumée et affichée). |
| A9 | 〃 | `prototype/runs/run-20260924-095718/` | Run **document piégé** (14 injections journalisées, registre identique au sain). |

> Les fichiers `.pdf` sont le rendu final ; garder les `.md` associés en sources
> (uniquement si le dépôt accepte les deux formats).

---

## B. Pour la soutenance (présentation + démo, 45 min)

| # | Document | Fichier | Rôle |
|---|---|---|---|
| B1 | **Slides de présentation** | `06_Slides_Soutenance.md/.pdf` | Support projeté au jury : 17 slides chronométrées (cadrage → démo → esprit critique). **⚠️ renseigner le nom des membres** sur S1 avant impression. |
| B2 | **Démo scriptée** | `08_Demo_Scriptee.md/.pdf` | Ta feuille de route de la démo (~8 min) : commandes exactes, sorties attendues, texte à dire, preuves au terminal B. *(Sur ton écran, pas projeté.)* |
| B3 | Preuves en direct | `prototype/runs/…` (registre + journal) | À afficher dans un **terminal B** pendant la démo : greps `valide_par`, `injection_detectee`, `validation_humaine`. |
| B4 | Guide de répétition | `07_Guide_Repetition_Soutenance.md/.pdf` | 20 questions probables + réponses argumentées. **S'entraîner avant** ; utile en attente au cas où, **ne pas le montrer au jury**. |

---

## C. Supports internes (on garde pour soi — non rendus)

| # | Document | Fichier | Rôle |
|---|---|---|---|
| C1 | Notes de cadrage | `PREPARATION.md` | Trame de préparation, décisions prises, journaux. Personnel. |
| C2 | Outil PDF | `outils/md_to_pdf.py` + `outils/README.md` | Conversion Markdown → PDF. Pas un livrable en soi, mais à joindre au dépôt si pratique (outil maison cité dans le § 9). |
| C3 | Sources du sujet | PDF `E21_*` (sujet) + cours CISSP | Documents de référence, à citer — pas à rendre. |
| C4 | Runs de travail | `prototype/runs/run-20260923-174404/174445/175756/175812/181321/181326/184554/` | Anciennes traces, **remplacées par les runs du 2026-09-24** ; l'ancienne trace a×10 `run-20260923-175812` est reléguée à *« démonstration mécanique du flux »*. Garder pour traçabilité, ne pas citer. |

---

## ⚠️ Rappels avant dépôt (checklist sujet p. 28)

- [x] **§ 9 du dossier complété** (outils d'IA : modèle réel, versions, dates)
- [x] **Tous les artefacts re-publics sur GitHub** : `github.com/PlayerFann14/tpmgmtsecu`
      (branche `main`) — docs 01→09 `.md/.pdf`, `PREPARATION.md`, `outils/`, `prototype/runs/`,
      `knowledge/`, `data/`
- [ ] **Noms des membres** sur les slides S1 et le cadre du dossier
- [ ] PDF du dossier **régénéré** après toute modification :
      `cd /root/tpmgmtsecu && /tmp/opencode/venv/bin/python outils/md_to_pdf.py 05_Dossier_Ecrit.md`
- [x] 82 tests verts (8 fichiers) : `cd prototype && PYTHONPATH=src python -m pytest tests/ -q`
- [ ] Démo répétée avec `08` + chrono (45 min)
- [ ] Aucune donnée réelle sensible envoyée à un LLM (cas 100 % fictif — G3)

---

*Références : sujet E21 (p. 27-28 « soutenance » et « ce que vous rendez ») ;
`05_Dossier_Ecrit.md` § 7 (réponses à la checklist) ; `07_Guide_Repetition_Soutenance.md`.*