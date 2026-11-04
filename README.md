# PFE SAGEMCOM : recherche de défauts similaires (prototype)

Format géré : exports Jira avec colonnes Key, Summary, Status, Severity, Fix Version/s... et titres
`[VTVAS-123] [Gen4][HDMI] texte`. Les crochets sont séparés automatiquement (référence client / étiquettes).

## Installation
    pip install -r requirements.txt        (pandas, openpyxl, scikit-learn)
Vérifier d'abord : python -c "import pandas, sklearn, openpyxl; print('ok')"

## Pack de données fictives pour travailler à deux (recommandé)
    python src/generate_mock_pack.py        # 400 tickets (2 programmes), 22 tests, lacunes connues, vérité terrain
    python src/explore.py data/MOCK_ALL.csv
    python src/search.py data/MOCK_ALL.csv --eval queries_mock.csv --compare
Voir TASKS.md pour le partage des tâches entre deux personnes.

## Test avec de FAUX tickets simples (même format que l'export réel)
    python src/generate_synthetic.py        # 300 tickets + requêtes de test + vérité terrain
    python src/explore.py data/SYNTHETIC_input_like.csv
    python src/search.py data/SYNTHETIC_input_like.csv --query "video does not come back after replugging HDMI"
    python src/search.py data/SYNTHETIC_input_like.csv --eval queries_synthetic.csv --compare
    python src/search.py data/SYNTHETIC_input_like.csv --export outputs/candidats.csv --k 15

## Rapprocher les faux tickets des vrais (profil statistique)
Sur le poste SAGEMCOM, sur le vrai fichier :
    python src/make_profile.py data/FICHIER.csv          # -> outputs/profile.json (fréquences seulement)
Le profil ne contient aucun titre, aucune description, aucun nom de personne : seulement gravité, priorité, statut,
résolution, composant, sprint, version, étiquettes les plus fréquentes, taux de cases vides, longueur des titres, dates.
Faire valider le fichier par le tuteur avant de l'emporter. Puis, chez vous :
    python src/generate_synthetic.py --profile outputs/profile.json
Les valeurs vues moins de 3 fois sont ignorées (--min-count 1 sur un petit fichier).
Limite : les titres restent inventés. Pour des titres réalistes, réécrire à la main une vingtaine de titres typiques
(sans copier les vrais) dans SCENARIOS de src/generate_synthetic.py. En mode profil, les étiquettes sont tirées
selon leur fréquence réelle, sans lien avec le scénario.

## Avec le vrai fichier (mettre le CSV dans data/)
    python src/explore.py data/input_sample.csv
    python src/search.py data/input_sample.csv --query "..."
    python src/search.py data/input_sample.csv --ticket AVTV-7397
    python src/search.py data/input_sample.csv --export outputs/candidats.csv

## Commandes
- explore.py : statistiques (colonnes, vides, doublons, étiquettes, dates) -> outputs/exploration_report.md
- search.py --query / --ticket : tickets les plus proches (clé + score)
- search.py --eval FICHIER [--compare] : Top-1, Top-5, MRR ; --compare met keywords / tfidf / embeddings côte à côte
- search.py --export : CSV au format Bug Matcher (Bug_Source, Summary_Source, Bug_Similaire, ...) + colonne Score ;
  par défaut seuls les tickets plus anciens sont candidats, score minimal 0.1 (--min-score)
- --engine embeddings : seulement si sentence-transformers et le modèle sont installables ; sinon repli sur TF-IDF.

## À lire avant de présenter les chiffres
- L'évaluation sur données SYNTHÉTIQUES prouve que le code marche, pas que la recherche est bonne sur les vrais tickets.
- Le moteur "keywords" est une approximation d'une recherche par mots-clés (comme Bug Matcher), pas son code.
- Une évaluation crédible demande des paires de tickets validées par l'équipe : remplir queries_template.csv
  (plusieurs clés attendues possibles, séparées par |).

## Règles
- Les vrais tickets restent sur le poste SAGEMCOM sans autorisation. Ne jamais partager .env ni jeton.
- Les données SYNTHETIC_* sont inventées.
