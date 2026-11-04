# Partage des tâches à deux : mercredi 4 novembre

Personne A = Recherche et IA.  Personne B = Données, graphe, tests.
Départ commun (10 min) : dézipper, puis `python src/generate_mock_pack.py` et `python src/explore.py data/MOCK_ALL.csv`.
Toutes les données MOCK_* sont inventées (400 tickets, 2 programmes AVTV et BBTV, 22 tests, 8 lacunes connues).

## Sur site avec le tuteur (ce qui exige les vraies données)
- A : ouvrir le fichier Teams, lancer `explore.py` et `make_profile.py` dessus, noter taille et colonnes.
- B : demander au tuteur 10 à 20 paires de défauts similaires, l'export complet des bugs (`project = AVTV AND issuetype = Bug`),
  les tests fonctionnels existants, un jeton Jira en lecture seule, l'accord pour pip.
- Faire valider `outputs/profile.json` avant de l'emporter.

## Personne A : recherche et IA
| # | Tâche | Commande ou livrable |
|---|---|---|
| A1 | Mesurer l'état actuel | `python src/search.py data/MOCK_ALL.csv --eval queries_mock.csv --compare` -> tableau Top-1, Top-5, MRR |
| A2 | Analyser les échecs | Liste des requêtes ratées et de la cause (synonymes, mots absents) |
| A3 | Moteur sémantique sans téléchargement (TF-IDF + réduction de dimension) | Nouveau moteur dans search.py + nouveaux chiffres |
| A4 | Embeddings (chez soi, hors réseau SAGEMCOM) | `pip install sentence-transformers`, puis `--engine embeddings --compare` |
| A5 | Squelette RAG | Fonction qui renvoie les k tickets + un prompt qui cite les clés sources |

## Personne B : données, graphe, tests
| # | Tâche | Commande ou livrable |
|---|---|---|
| B1 | Schéma du graphe | Entités : Ticket, Programme, Module, Version, Sprint, Test, Catégorie. Relations : appartient à, corrigé dans, parent de, couvert par. Un schéma pour la diapo |
| B2 | Construire le graphe | Script qui lit MOCK_ALL.csv et MOCK_tests.csv et écrit un fichier de liens (source, relation, cible) |
| B3 | Détecter les lacunes de couverture | Bugs sans test par scénario et programme, comparés à MOCK_coverage_gaps.csv (8 attendues) : précision et rappel |
| B4 | Extraction et classification par règles | Module, action, erreur, catégorie depuis Description, comparés à MOCK_groundtruth.csv : taux de réussite |
| B5 | Gabarit de scénario de test | Préconditions, étapes, résultat attendu, rempli pour 3 défauts |

## Synchronisations
- Milieu de journée (15 min) : chacune montre ses premiers chiffres.
- Fin de journée (30 min) : revue croisée, chacune explique le travail de l'autre ; captures d'écran ;
  3 lignes pour la diapositive Avancement.

## Rappels
- Les résultats sur MOCK_* valident le code, pas la qualité sur les vrais tickets.
- Les vrais tickets restent sur le poste SAGEMCOM sans autorisation.
