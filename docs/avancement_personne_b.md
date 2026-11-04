# Avancement de Personne B

## Périmètre actuel

Le travail ci-dessous a été réalisé avec les fichiers `MOCK_*`, qui contiennent des données simulées. Il valide la structure et le fonctionnement du prototype ; il ne mesure pas encore les performances sur les tickets Jira réels.

## Travail réalisé

| Tâche | État | Résultat |
|---|---|---|
| B1 — Exploration des données | Terminée sur MOCK | 400 tickets : 240 AVTV et 160 BBTV, ainsi que 22 cas de test. |
| B2 — Knowledge Graph | Terminé sur MOCK | Graphe NetworkX pour les tickets, programmes, modules, versions et tests ; schéma décrit dans `knowledge_graph_schema.md`. |
| B3 — Couverture | Prototype terminé | 25 combinaisons scénario/programme classées par nombre de tests : 13 `COVERED`, 4 `LOW_COVERAGE`, 8 `NO_COVERAGE`. Cette règle ne mesure pas la qualité des tests. |
| B4 — Préparation cross-programme | Préparée | Extraction de quatre sections de description et génération de 38 400 paires AVTV–BBTV. |
| B5 — Préparation de l’évaluation | Outils prêts, évaluation en attente | Création des étiquettes et du script de métriques. Sur MOCK, 2 720 paires sont positives et 35 680 négatives selon l’égalité du scénario. |
| B6 — Intégration des similarités | En attente de Personne A | Le script d’intégration existe, mais aucun score sémantique n’a encore été fourni. |

Les scripts d’évaluation ont été lancés : les 38 400 paires ont été préparées, mais 0 paire possède un score. Les métriques Precision, Recall, F1 et Accuracy ne peuvent donc pas encore être calculées.

## Fichiers principaux de Personne B

- `src/graph_builder.py`, `src/coverage_graph.py` : création du graphe et ajout des lacunes.
- `src/coverage_analyzer.py` : classification heuristique de couverture.
- `src/extract_ticket_sections.py`, `src/prepare_cross_program_pairs.py` : extraction et génération des paires.
- `src/prepare_cross_program_groundtruth.py` : création des étiquettes MOCK pour les paires.
- `src/evaluate_cross_program_metrics.py` : calcul des métriques lorsque les scores sont disponibles.
- `src/similarity_evaluator.py`, `src/integrate_cross_program_graph.py` : classification des similarités et intégration dans le graphe.
- `src/verify_graph.py`, `src/verify_coverage_graph.py`, `src/verify_cross_program_graph.py` : vérifications du graphe.
- `docs/knowledge_graph_schema.md`, `docs/cross_program_integration.md` : schéma et contrat d’échange avec Personne A.

## Prochaines étapes

1. **Personne A** fournit les scores en conservant les paires et les clés présentes dans `data/cross_program_pairs.csv`. Le fichier attendu est `data/cross_program_similarity_results.csv` avec `Key_avtv`, `Key_bbtv` et `semantic_similarity` compris entre 0 et 1. Les scores par section sont facultatifs.
2. **Personne B** exécute `python src/evaluate_cross_program_metrics.py`, examine les métriques et ajuste les seuils provisoires dans `src/similarity_evaluator.py` si nécessaire.
3. **Personne B** exécute l’intégration des relations `SIMILAR_TO` et vérifie les liens. Le vérificateur actuel attend zéro relation similaire ; il faudra adapter cette attente avant de valider un graphe contenant les scores de A.
4. Pour la validation réelle, obtenir un export Jira, les cas de test avec leurs liens aux tickets et des paires de similarité revues par des personnes expertes. Adapter alors les scripts qui lisent actuellement les fichiers `MOCK_*`.

## Limites et extensions

- La ground truth actuelle est simulée ; « même scénario » sert uniquement à produire les étiquettes du prototype.
- La forte proportion de paires négatives rend l’Accuracy seule trompeuse. Examiner aussi Precision, Recall et F1.
- Les seuils `0.60` et `0.80` sont provisoires et doivent être évalués avec des paires annotées.
- Les recommandations de nouveaux tests et la priorisation par risque sont des extensions possibles, à confirmer avec l’encadrant.
