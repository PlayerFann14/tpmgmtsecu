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
  flux, contrats JSON, garde-fous G1→G10 (avec les **11 motifs du sanitizer**),
  matrice, reprises, RAG, comparaison `--comparer`, journalisation.

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
python run.py run --case cases/casB_mediconsult.md --provider openai
```

Le fournisseur réel (`src/llm/openai_compat.py`) lit uniquement les variables
d'environnement `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL` (aucun secret
en dur) et appelle `POST {base_url}/chat/completions` avec `temperature=0.2`.

> ⚠️ Le fournisseur réel **ne doit recevoir aucune donnée réelle et sensible**
> (garde-fou G3) : le cas B est entièrement fictif.

## Tests

```bash
cd prototype && PYTHONPATH=src python -m pytest tests/ -q   # 82 tests verts (8 fichiers)
```

Répartition : `test_sanitizer.py` (32) · `test_orchestrateur.py` · `test_comparaison.py` ·
`test_audit_fixes.py` · `test_validation.py` · `test_matrice.py` · `test_file_reader.py` ·
`test_workspace.py`.

## Comparaison avec la référence (jalon 4)

`python run.py run --case cases/casB_mediconsult.md --no-human --comparer` compare le
registre généré à la **référence manuelle structurée** `data/reference_manuelle.json`
(`src/core/comparaison.py` : `retrouves` / `inventes` / `oublies` / `ecarts_par_risque` /
`nb_ecarts_niveau` / `taux_reconciliation`).

> ⚠️ **Honnêteté** : en dry-run (`dummy`), le simulateur reproduit la référence pour
> tester la chaîne — la comparaison y est **tautologique par conception** et le CLI le
> rappelle explicitement. Elle ne prend un sens qu'en mode réel : `--provider openai`
> (variable d'env impératives : `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` ;
> `temperature=0.2`). Le mode `fidele=False` du simulateur (tests) prouve que la
> comparaison n'est pas une tautologie : registre valide mais divergent (R-07 oublié,
> R-11 inventé, R-09 écart de niveau), détecté par `comparer_registres`.

## Architecture

```
src/
├── agents/        orchestrator.py (pipeline + reprises + journal) · agents.py (les 5) · prompts.py (consignes)
├── cli/           main.py (argparse)
├── core/          config · models · schemas (JSON) · validation (garde-fous) ·
│                  sanitizer (anti-injection) · comparaison (vs référence) ·
│                  workspace (mémoire) · journal
├── llm/           interface · dummy (simulateur) · openai_compat (réel)
└── tools/         file_reader (read-only) · knowledge (RAG) · matrice · cve (snapshot)
knowledge/         STRIDE · LINDDUN · ISO 27002 · ANSSI · ATT&CK (sources citées)
cases/             casB_mediconsult.md (entrée) · casB_injecte.md (test, 14 instructions)
data/              cve_snapshot.json (⚠ instantané de démo, à rafraîchir via le NVD) ·
                   reference_manuelle.json (vérité terrain humaine, jalon 4)
runs/              workspace.json · registre_final.json · journal.jsonl (horodaté)
```

## Les 5 agents (une étape de la méthode chacun)

| Agent | Reçoit | Produit | Outils |
|---|---|---|---|
| AG1 Inventaire | description du système | actifs + valeur + propriétaire | lire_fichier |
| AG2 Modèle | actifs + contexte | STRIDE (+ LINDDUN) + justification | chercher_connaissance |
| AG3 Menaces | actifs + modèle + frontières | menaces par actif et frontière | chercher_connaissance, rechercher_cve (mots-clés du document) |
| AG4 Évaluation | menaces + échelles | P × I + justification | calculer_niveau (imposé) |
| AG5 Traitement | menaces notées | projet de registre (4 réponses) | chercher_connaissance, calculer_niveau |
| Orchestrateur | demande de l'analyste | historique + registre prêt pour l'humain | prouve le code déterministe, outils délégués selon l'agent |

> ⚠️ Les outils ne sont **jamais appelés par les agents eux-mêmes** : c'est
> l'orchestrateur qui les invoque au nom de chaque agent selon une liste blanche
> (`_OUTILS_PAR_AGENT`, cf. `src/agents/orchestrator.py`).

## Garde-fous de sécurité (cf. `02_Architecture_MultiAgents.md`)

| # | Garde-fou | Où |
|---|---|---|
| G1 | Filtrage des entrées (prompt injection, LLM01 OWASP) | `core/sanitizer.py` |
| G2 | Outils en lecture seule + liste blanche par agent (délégués par l'orchestrateur) | `tools/registry.py`, `agents/orchestrator.py` |
| G3 | Anonymisation (cas fictif, zéro donnée réelle) | prompts + README |
| G4 | `sources` non vide **et format valide** pour toute sortie | `core/validation.py` |
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
- `journal.jsonl` : trace horodatée des échanges (agent, tentative, statut, outils,
  **`octets_entree`/`octets_sortie` réels**) + événements d'injection détectés
  (par occurrence) + décisions de validation humaine (`accepte`/`differe`/`corrige`)
  et corrections (`correction_humaine`).

Dernières traces utiles au dossier (2026-09-24) : `run-20260924-095714` (dry-run cas B
+ `--comparer`), `run-20260924-095718` (document piégé : **14 injections** dans le journal),
`run-20260924-095723` (validation humaine `Dr Dupont` : R-01 corrigé, R-02→R-09 acceptés,
R-10 différé).

## Correspondance avec les livrables du sujet

- **Dossier écrit** : prompts dans `src/agents/prompts.py` (à recopier en annexe),
  architecture dans `../02_Architecture_MultiAgents.md`, analyse critique via le tableau
  de comparaison de `../03_Analyse_Manuelle_Reference.md`.
- **Prototype** : ce dépôt + traces d'exécution dans `runs/`.
- **Soutenance** : démo `run.py` (dry puis réel), journal, et tableau des garde-fous.