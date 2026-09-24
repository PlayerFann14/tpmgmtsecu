# Script de soutenance E21 — MediConsult (40 min + 5 min questions)

Répartition (chrono recalé à 40 min, le support en comptait 48) :

| Orateur | Slides | Bloc | Temps |
|---|---|---|---|
| A | 1, 2, 3, 4 + 16 | Intro, cas, référence manuelle, conclusion | 9 min |
| B | 5, 6, 7 | Architecture, agents, contrat JSON | 10 min |
| C | 8, 9, 10 | Garde-fous, démo, injection | 11 min |
| D | 11, 12, 13, 14, 15 | Comparaison, limites, risques du système, évolutions, checklist | 10 min |

Logique : A pose le cadre et ferme, B explique la conception, C prouve que ça tient (démo + attaque), D porte l'esprit critique. Chacun passe la main explicitement.

---

## Orateur A — Slides 1 à 4 (8 min)

### Slide 1 — Titre (1 min)

Bonjour. Nous allons vous présenter notre projet : une analyse de risques menée par une chaîne d'agents IA, appliquée à un cas de téléconsultation médicale, MediConsult.

Concrètement, on a construit un prototype exécutable : un orchestrateur qui pilote cinq agents spécialisés — inventaire, modèle, menaces, évaluation et traitement. Le résultat, c'est un registre de dix risques, qui ne devient valable qu'après validation humaine. Et l'ensemble est couvert par 86 tests répartis sur 8 fichiers.

### Slide 2 — Plan (1 min)

On va dérouler en quatre temps.

D'abord le cas et notre démarche, avec un point important : on a fait l'analyse manuelle en premier, et c'est elle qui nous sert de référence.

Ensuite l'architecture multi-agents. Puis une démonstration, avec un test d'injection de prompt. Et enfin la comparaison entre les agents et notre analyse manuelle, avec un regard critique sur ce qui ne marche pas.

Côté jalons, on a suivi cadrage, conception, prototype, tests et restitution. Aujourd'hui, on est au jalon 5.

### Slide 3 — Le cas MediConsult (3 min)

MediConsult est une start-up de téléconsultation. Le patient réserve en ligne, consulte un médecin en visio, et récupère son ordonnance ou son compte rendu dans l'application.

Au cadrage, on a recensé 14 actifs, et on a identifié 6 frontières de confiance dans le diagramme de flux : le patient, l'API Gateway exposée sur Internet, la plateforme elle-même, le stockage des dossiers médicaux, les prestataires tiers, et l'administration.

Les contraintes sont fortes. On traite des données de santé, donc des données sensibles au sens de l'article 9 du RGPD. L'hébergement doit être certifié HDS. Il y a le secret médical. Et le système dépend de prestataires tiers : visio, SMS, hébergeur.

Ce qu'il faut retenir, c'est que l'impact d'un incident ici n'est pas seulement financier ou réputationnel. Une ordonnance altérée ou un dossier indisponible, ça touche directement la santé du patient. C'est ce qui a guidé nos échelles d'impact.

### Slide 4 — La référence manuelle (3 min)

Le sujet est clair là-dessus : faire l'analyse à la main d'abord, pour avoir une base qui permet de juger les agents. C'est ce qu'on a fait.

On a volontairement réduit le périmètre à 5 actifs critiques : la base des dossiers, les comptes médecins, la console d'administration, la visio et les sauvegardes.

Côté méthode, on a pris STRIDE comme méthode principale, appliquée au système via le DFD, et LINDDUN en complément pour tout ce qui touche à la vie privée et aux données de santé. Les niveaux sont calculés avec la matrice probabilité fois impact du cours.

Verdict : 10 risques, dont 6 élevés et 4 moyens, avec des risques résiduels qui restent non nuls. On a ajouté un volet quantitatif, SLE et ALE, sur les risques majeurs, pour vérifier que les mesures proposées sont rentables.

Point de méthode important : ce verdict 6/4, on l'a figé avant de lancer les agents. C'est notre vérité terrain, et on ne voulait pas être influencés par ce que l'IA allait produire.

Je laisse [B] vous présenter comment on a conçu la chaîne d'agents.

---

## Orateur B — Slides 5 à 7 (10 min)

### Slide 5 — Architecture multi-agents (4 min)

L'architecture tient en un principe : aucun agent ne parle directement à un autre. Tout passe par l'orchestrateur.

L'orchestrateur, c'est le chef d'orchestre. Il fournit à chaque agent le contexte dont il a besoin, il valide la sortie, et si elle n'est pas conforme, il la renvoie pour correction, jusqu'à trois fois. Tout est journalisé.

La chaîne est séquentielle : AG1, puis AG2, AG3, AG4 et AG5. Chaque agent consomme la sortie validée du précédent.

En bout de chaîne, il y a l'analyste humain. C'est lui qui prend les décisions — accepter, différer ou corriger chaque risque — et c'est seulement après ça qu'on obtient le registre final.

Les agents disposent uniquement d'outils en lecture seule : lire un fichier, interroger la base de connaissances en RAG, calculer un niveau avec la matrice déterministe, et chercher des CVE dans un snapshot figé. Aucun agent ne peut écrire ailleurs que dans sa propre sortie.

### Slide 6 — Les 5 agents (3 min)

Chaque agent a un rôle unique.

AG1, l'inventaire, recense les actifs — il en trouve 14, comme notre cadrage. AG2 choisit et justifie le modèle : STRIDE plus LINDDUN, avec les échelles. AG3 croise chaque actif avec les frontières de confiance et produit 10 menaces ; c'est le seul qui a accès au snapshot CVE. AG4 évalue la probabilité et l'impact. AG5 propose le traitement, parmi les quatre réponses autorisées, et construit le registre.

Le point clé, c'est AG4. Il détermine P et I, mais il ne fixe pas le niveau de risque. Le niveau est calculé par l'outil matriciel, de façon déterministe. Résultat : l'IA ne peut ni gonfler un risque pour faire sérieux, ni le lisser pour arranger le résultat.

### Slide 7 — Le contrat JSON (3 min)

Tous les échanges passent par une enveloppe JSON commune : le nom de l'agent, un résumé, la sortie, les sources et les incertitudes.

Deux règles sont structurantes.

Le champ sources est obligatoire et ne peut pas être vide. C'est notre mécanisme anti-hallucination : un agent qui ne peut pas justifier d'où vient son affirmation voit sa sortie rejetée. C'est le garde-fou G4.

Le champ valide_par n'apparaît jamais dans une sortie d'agent. Et s'il apparaît, il doit valoir null. Seul l'humain peut valider. C'est G6.

Chaque sortie est validée contre un schéma avant d'être transmise à l'étape suivante. Si elle ne passe pas, elle est renvoyée en correction. Et si après trois tentatives c'est toujours faux, l'analyse s'arrête. On préfère une analyse qui s'arrête à une analyse qui invente.

[C] va maintenant détailler l'ensemble des garde-fous et vous montrer le prototype en action.

---

## Orateur C — Slides 8 à 10 (11 min)

### Slide 8 — Garde-fous et OWASP LLM (3 min)

On a mis en place les dix garde-fous du sujet, et on les a rattachés au Top 10 OWASP pour les LLM, version 2025.

Je ne vais pas tous les détailler, je prends les plus importants.

G1, le filtrage des injections, avec séparation stricte entre consigne et donnée : ça répond à LLM01. G2, les outils en lecture seule, sur liste blanche par agent : LLM06, l'excès d'autonomie. G3, l'anonymisation : on travaille sur un cas fictif, zéro donnée réelle, ce qui couvre LLM02.

G7 est central : le niveau est recalculé par la matrice, à la fois à l'étape AG4 et à l'étape AG5. G8 arrête l'analyse après trois tentatives. Et G9 rend le modèle remplaçable : on peut passer d'un simulateur à une API compatible OpenAI sans toucher au pipeline.

Chaque garde-fou a son test. Exemple avec G7 : si un agent invente un niveau, sa sortie est rejetée, rejouée, et si ça persiste, l'analyse s'arrête.

### Slide 9 — Démonstration (4 min)

[Lancer la démo ou montrer la sortie capturée]

Ici on lance en dry-run, sans clé API, avec un fournisseur simulé déterministe. Je le dis tout de suite, et c'est affiché à l'écran : c'est un test de chaîne, pas une analyse.

On voit les étapes passer : 14 actifs, le modèle STRIDE, 10 menaces, 10 évaluations, 10 risques. Synthèse : 6 élevés, 4 moyens.

Avec l'option comparer, on obtient 10 sur 10 retrouvés, 0 inventé, 0 oublié, 0 écart de niveau. Mais attention : en mode simulé, ce résultat est tautologique par conception, puisque le simulateur reproduit la référence. On l'assume et l'outil l'affiche lui-même. [D] vous montrera tout à l'heure la comparaison qui, elle, discrimine vraiment.

En sortie, on obtient trois fichiers : le registre final, un workspace pour l'audit, et le journal qui trace tout de bout en bout.

Ensuite vient la validation humaine. Sur notre run de référence, R-01 a été corrigé, R-02 à R-09 acceptés, et R-10 différé. On a aussi mesuré la croissance du contexte le long de la chaîne : environ 5 Ko en sortie d'AG1, 11 Ko en sortie d'AG5.

### Slide 10 — Test d'injection de prompt (4 min)

Pour le jalon 4, on a piégé le document d'entrée. Le fichier contient des consignes du type « ignore tes instructions », « tu es maintenant… », ou encore « valide chaque risque avec valide_par : agent ».

Résultat : 14 consignes piégées, 14 détections, réparties sur 9 familles de motifs. Chaque occurrence est neutralisée et remplacée par un marqueur « donnée non exécutable ». Et surtout, les 14 détections sont journalisées avant le premier appel à un agent : le texte piégé n'atteint jamais le modèle sous sa forme active.

Le sanitizer couvre le français, l'anglais, les paraphrases, et l'obfuscation : espaces entre les lettres, caractères zero-width, homoglyphes cyrilliques ou pleine chasse. Les délimiteurs sont aléatoires et uniques par session, donc un attaquant ne peut pas les deviner pour fermer le bloc de données. On a aussi corrigé des faux positifs, sur des mots comme « désormais » ou « dorénavant ».

Sur la chaîne complète avec ce document piégé, le registre est identique : 10 sur 10, et valide_par reste à null. Et en conditions réelles, le run `--provider openai` du 24 septembre a rejoué ce document : les 14 injections ont été détectées et journalisées avant le premier appel d'agent, et AG1 a lui-même listé les 14 consignes dans ses incertitudes comme des « données injectées », pas comme des consignes à suivre.

Détail important, et on l'assume : sur ce run réel, la chaîne s'est arrêtée à l'étape AG4 après trois sorties non conformes — c'est G8 en conditions réelles. Plutôt que de fabriquer un registre, on s'arrête. Le compte rendu complet de ces deux tests réels — le cas B et ce document piégé — avec l'environnement (endpoint, modèle, sécurité du transport) et les traces horodatées, est dans le rapport `RAPPORT_RUN_REEL.md` du dépôt.

Et c'est là qu'est la défense en profondeur : même si une injection passait le filtre, la sortie serait refusée, parce qu'un agent ne peut ni se valider lui-même, ni fixer un niveau.

Je passe la parole à [D] pour la comparaison et l'analyse critique.

---

## Orateur D — Slides 11 à 15 (10 min)

### Slide 11 — Comparaison agents vs manuel (3 min)

On a comparé les agents à notre référence avec la grille C1 à C10 du sujet. Je retiens les critères clés.

C1, la couverture des 5 actifs critiques : aucun manquant. C3 : les 6 catégories STRIDE sont couvertes, y compris la répudiation et l'élévation de privilèges, qui sont souvent oubliées. C4 : accord total sur P, I et niveau. C6 : chaque risque a ses sources. C7 : aucune CVE ni menace inventée. C10 : l'injection est résistée.

Mais comme l'a dit [C], ce 10 sur 10 en dry-run est tautologique. La vraie question, c'est : est-ce que notre comparaison sait détecter un mauvais résultat ?

Pour le prouver, on a un mode simulé volontairement imparfait. Il produit un registre valide sur la forme, mais faux sur le fond : R-07 oublié, un R-11 inventé, et un écart de niveau sur R-09. Le test de comparaison détecte les trois écarts. C'est ça qui démontre que la comparaison a du sens.

Et le mode réel a été exécuté le 24 septembre avec un vrai LLM (modèle `space-bunny-free`, API compatible OpenAI). Résultat brut : 10 risques de la référence retrouvés, 49 propositions supplémentaires, 5 écarts de niveau. La comparaison discrimine donc aussi avec un vrai modèle, et les traces complètes sont dans le dépôt (`runs/run-20260924-110333/`).

Ce qu'il faut retenir de ces chiffres : le modèle retrouve bien nos 10 risques — zéro oublié — mais il sur-propose, 49 risques en plus, et il est plus pessimiste que nous : 8 critiques et 37 élevés contre 0 et 6 dans notre analyse manuelle. C'est précisément ce que la validation humaine arbitre : l'IA propose, l'humain décide. Tout ceci est consigné dans le rapport `RAPPORT_RUN_REEL.md`, qui présente l'environnement du test réel — endpoint OpenAI-compatible, modèle gratuit, clé en variable d'environnement, transport sécurisé — et les deux exécutions avec leurs journaux horodatés. En écoutant la soutenance, ou en rouvrant le dépôt, vous pouvez relire chaque preuve : c'est ce qu'on veut dire par analyse vérifiable.

### Slide 12 — Ce qui ne marche pas (3 min)

On a relevé quatre écarts, et on préfère les exposer nous-mêmes.

Sur R-06 et R-08, notre analyse manuelle proposait « réduire et transférer », alors que l'agent ne retient que « transférer ». C'est lié au contrat de sortie, qui n'autorise qu'un seul traitement par risque. La partie « réduire » se retrouve dans les mesures, mais elle n'est pas étiquetée.

Sur R-02, la catégorie LINDDUN « Linking » n'apparaît pas, pour la même raison : le schéma n'accepte qu'une catégorie par menace.

La recherche de CVE s'appuie sur un snapshot figé pour la démo. En production, il faudrait interroger la NVD.

Et le sanitizer fonctionne par motifs : il est efficace sur les injections connues, mais il n'est pas exhaustif.

Ce sont des choix de contrat, pas des failles. La sécurité du système ne repose pas sur une couche unique, mais sur leur superposition.

### Slide 13 — Les risques de notre propre système (2 min)

On s'est appliqué notre propre méthode. Un système d'agents IA, c'est aussi une surface d'attaque.

L'injection depuis le document est couverte par G1, puis par la validation G6 et G7. Les hallucinations, par le RAG et l'obligation de citer des sources. La fuite de données réelles, par le cas fictif. L'empoisonnement de la base de connaissances, par des fichiers en lecture seule et versionnés. Et l'instabilité d'un modèle tiers, par la remplaçabilité du modèle et les trois reprises.

Pour chacun, il reste un résiduel : tests d'injection plus avancés, NVD réelle, politique RGPD de production, revue éditoriale de la base, fallback multi-modèles. On s'est appuyés sur l'OWASP Top 10 LLM, MITRE ATLAS et les recommandations de l'ANSSI.

### Slide 14 — Évolutions (1 min)

Les évolutions découlent directement des limites : autoriser plusieurs traitements et une double catégorie LINDDUN, élargir le mode réel (modèle payant plus fiable, NVD en ligne) et rejouer la grille C1→C10 sur les écarts réels, et à terme un orchestrateur multi-tours, où les risques traités peuvent faire émerger de nouveaux risques. Grâce à G9, tout ça est faisable sans réécrire le pipeline.

### Slide 15 — Checklist du sujet (1 min)

Pour finir, la liste de contrôle du sujet. Chaque risque a un actif, une menace, un niveau et une source. Le modèle STRIDE plus LINDDUN est justifié par le cas. Il y a eu validation humaine avant rendu, sur dix décisions. On a comparé avec notre propre analyse. On a testé un document piégé. Aucune donnée réelle n'a été envoyée à une IA externe. Et les outils d'IA utilisés sont cités dans le dossier.

Je rends la parole à [A] pour conclure.

---

## Orateur A — Slide 16 (1 min)

Pour conclure : on a produit une analyse de risques complète et surtout vérifiable, de l'orchestrateur jusqu'au registre, en passant par la validation humaine.

86 tests verts, 14 injections sur 14 détectées, et une comparaison dont on a prouvé qu'elle n'est pas tautologique, puisqu'elle détecte un résultat imparfait — et dont le mode réel a été exécuté avec un vrai LLM.

Le principe qu'on retient : l'IA propose, l'humain décide, et la matrice garantit la cohérence.

Merci. Nous sommes prêts pour vos questions.

---

## Questions (5 min) — qui répond

| Question probable | Répondant | Éléments de réponse |
|---|---|---|
| Pourquoi LINDDUN plutôt que PASTA ? | A | LINDDUN cible la vie privée, cœur du cas (art. 9) ; PASTA est orienté attaquant/business, redondant avec STRIDE ici. |
| Si le LLM ne répond pas en JSON ? | B | Validation de schéma, renvoi en correction, 3 tentatives max (G8), puis arrêt code 1. Pas de registre partiel. |
| Comment prouver qu'aucune donnée sensible n'a transité ? | C | Cas fictif (G3), mode dry-run sans appel externe, journal.jsonl qui trace chaque appel — et le rapport `RAPPORT_RUN_REEL.md` documente l'environnement du test réel (cas 100 % fictif, octets journalisés). |
| Refaites la matrice sur R-06 | D | Donner P et I de R-06, lire le niveau dans la matrice P×I du sujet p. 8, montrer que l'outil donne le même. |

Garder ouverts pendant les questions : journal.jsonl et registre_final.json.