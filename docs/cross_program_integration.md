# Contrat d’intégration cross-programme

Ce document définit le fichier de scores à échanger entre Personne A (moteur sémantique) et Personne B (évaluation et graphe).

## Fichier d’entrée de Personne A

Personne B génère les paires candidates dans `data/cross_program_pairs.csv` avec :

```powershell
python src/prepare_cross_program_pairs.py
```

Le fichier contient actuellement 38 400 paires. Personne A calcule les scores et complète `data/cross_program_similarity_results.csv`.

## Colonnes attendues

Colonnes obligatoires :

| Colonne | Description |
|---|---|
| `Key_avtv` | Clé du ticket AVTV de la paire. |
| `Key_bbtv` | Clé du ticket BBTV de la paire. |
| `semantic_similarity` | Score global de similarité compris entre 0 et 1. |

Les clés doivent rester identiques à celles de `cross_program_pairs.csv`. Il faut une seule ligne par paire et ne pas supprimer de paires. Les scores seuls suffisent pour l’échange ; les descriptions des tickets n’ont pas à être recopiées dans le fichier de résultats.

Scores facultatifs par champ :

- `preconditions_similarity`
- `steps_similarity`
- `expected_similarity`
- `actual_similarity`

Si `semantic_similarity` est vide, `src/similarity_evaluator.py` peut calculer le score global avec les scores de champs disponibles et les poids provisoires définis dans ce script. Toutes les valeurs numériques doivent être comprises entre 0 et 1.

## Traitement par Personne B

Après réception des scores :

1. Exécuter `python src/evaluate_cross_program_metrics.py` pour calculer Precision, Recall, F1 et Accuracy aux différents seuils. Le calcul ignore les paires qui n’ont pas de score.
2. Exécuter `python src/similarity_evaluator.py` pour produire `data/evaluated_cross_program_matches.csv` et les classes de similarité.
3. Exécuter `python src/integrate_cross_program_graph.py` pour ajouter les relations `SIMILAR_TO` classées `HIGH_SIMILARITY` au graphe.
4. Adapter `src/verify_cross_program_graph.py` pour vérifier le nombre attendu de relations à partir des résultats reçus : sa vérification actuelle exige zéro relation `SIMILAR_TO` et ne convient donc qu’au graphe sans scores.

## Interprétation

Les seuils `0.60` et `0.80` sont provisoires. Ils doivent être confrontés aux métriques et aux paires annotées. Les évaluations sur `MOCK_groundtruth.csv` valident le calcul sur des données simulées ; une validation de performance exige des paires réelles vérifiées par des experts.
