# agents-risques — Prototype multi-agents d'analyse de risques (E21)

Prototype Python du **projet « Des agents IA pour analyser les risques »** (E21,
Management de la sécurité, M2 Cybersécurité). Cas d'étude **B · Téléconsultation
médicale** (*MediConsult*).

Le système reproduit la **démarche d'analyse de risques en 6 étapes** (cours ch. 05)
avec **5 agents spécialisés + 1 orchestrateur**, des **sorties JSON structurées**,
une **base de connaissances** (RAG), des **garde-fous de sécurité** et une
**validation humaine obligatoire** avant publication du registre.

## 📚 Documentation

- **`GUIDE_UTILISATION.md`** — ce que tu dois faire, pas à pas : installation,
  démos, mode réel, lecture des résultats, adaptation, dépannage, checklist soutenance.
- **`FONCTIONNEMENT.md`** — comment l'outil fonctionne en interne : architecture,
  flux, contrats JSON, garde-fous G1→G10 (avec les **10 motifs du sanitizer**),
  matrice, reprises, RAG, journalisation.

Documents de soutenance (racine du projet) :
- **`../04_Tests_Comparaison_Agents.md`** — grille C1→C10 remplie + test d'injection (jalon 4).
- **`../05_Dossier_Ecrit.md`** — dossier écrit (prompts, registre, analyse critique).
- **`../07_Guide_Repetition_Soutenance.md`** — questions probables + réponses (45 min).
- **`../08_Demo_Scriptee.md`** — démo scriptée pas à pas pour la soutenance.
- `../outils/md_to_pdf.py` — conversion Markdown → PDF des livrables.

## Démarrage rapide

```bash
cd prototype
python -m venv .venv && .venv/bin/pip install -r requirements.txt

# 1) Démo complète sans clé API (fournisseur simulé, déterministe) :
python run.py run --case cases/casB_mediconsult.md --no-human

# 2) Même chaîne avec validation humaine interactive :
printf 'a\n%.0s' $(seq 1 10) | python run.py run --case cases/casB_mediconsult.md

# 3) Test anti-injection (document piégé) :
python run.py test-injection --case cases/casB_injecte.md
```

### Mode réel (LLM)

```bash
export OPENAI_BASE_URL=https://api.openai.com/v1   # ou tout endpoint compatible
export OPENAI_API_KEY=...
export OPENAI_MODEL=<modèle à citer dans le dossier>
python run.py run --case cases/casB_mediconsult.md
```

> ⚠️ Le fournisseur réel **ne doit recevoir aucune donnée réelle et sensible**
> (garde-fou G3) : le cas B est entièrement fictif.

## Tests

```bash
python -m pytest tests/ -v          # 52 tests : matrice, sanitizer, garde-fous, orchestration
```

## Architecture

```
src/
├── agents/        orchestrator.py (pipeline + reprises + journal) · agents.py (les 5) · prompts.py (consignes)
├── cli/           main.py (argparse)
├── core/          config · models · schemas (JSON) · validation (garde-fous) ·
│                  sanitizer (anti-injection) · workspace (mémoire) · journal
├── llm/           interface · dummy (simulateur) · openai_compat (réel)
└── tools/         file_reader (read-only) · knowledge (RAG) · matrice · cve (snapshot)
knowledge/         STRIDE · LINDDUN · ISO 27002 · ANSSI · ATT&CK (sources citées)
cases/             casB_mediconsult.md (entrée) · casB_injecte.md (test)
data/              cve_snapshot.json (⚠ instantané de démo, à rafraîchir via le NVD)
runs/              workspace.json · registre_final.json · journal.jsonl (horodaté)
```

## Les 5 agents (une étape de la méthode chacun)

| Agent | Reçoit | Produit | Outils |
|---|---|---|---|
| AG1 Inventaire | description du système | actifs + valeur + propriétaire | lire_fichier, chercher_connaissance |
| AG2 Modèle | actifs + contexte | STRIDE (+ LINDDUN) + justification | chercher_connaissance |
| AG3 Menaces | actifs + modèle + frontières | menaces par actif et frontière | chercher_connaissance, rechercher_cve |
| AG4 Évaluation | menaces + échelles | P × I + justification | calculer_niveau (imposé) |
| AG5 Traitement | menaces notées | projet de registre (4 réponses) | chercher_connaissance, calculer_niveau |
| Orchestrateur | demande de l'analyste | historique + registre prêt pour l'humain | tous (code déterministe) |

## Garde-fous de sécurité (cf. `02_Architecture_MultiAgents.md`)

| # | Garde-fou | Où |
|---|---|---|
| G1 | Filtrage des entrées (prompt injection, LLM01 OWASP) | `core/sanitizer.py` |
| G2 | Outils en lecture seule + liste blanche par agent | `tools/registry.py` |
| G3 | Anonymisation (cas fictif, zéro donnée réelle) | prompts + README |
| G4 | `sources` non vide pour toute sortie | `core/validation.py` |
| G5 | Journalisation horodatée de chaque appel | `core/journal.py` |
| G6 | `valide_par` écrit uniquement par l'humain | `core/validation.py` + CLI |
| G7 | `niveau` = matrice déterministe (le LLM ne décide pas) | `tools/matrice.py` |
| G8 | Arrêt bavard après 3 tentatives (jamais de remplissage) | `agents/orchestrator.py` |
| G9 | Modèle remplaçable (interface) | `llm/interface.py` |
| G10 | Base de connaissances en lecture seule | `knowledge/` |

## Traces pour le dossier

Chaque exécution écrit dans `runs/<session>/` :
- `workspace.json` : mémoire partagée (produits des 5 agents) ;
- `registre_final.json` : le registre des risques, `valide_par` renseigné après validation ;
- `journal.jsonl` : trace horodatée des échanges (agent, tentative, statut, outils, erreurs)
  + événements d'injection détectés + décisions de validation humaine.

## Correspondance avec les livrables du sujet

- **Dossier écrit** : prompts dans `src/agents/prompts.py` (à recopier en annexe),
  architecture dans `../02_Architecture_MultiAgents.md`, analyse critique via le tableau
  de comparaison de `../03_Analyse_Manuelle_Reference.md`.
- **Prototype** : ce dépôt + traces d'exécution dans `runs/`.
- **Soutenance** : démo `run.py` (dry puis réel), journal, et tableau des garde-fous.