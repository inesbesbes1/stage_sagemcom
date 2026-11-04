# Schéma du Knowledge Graph

Le graphe est construit avec NetworkX et exporté au format GraphML. Les relations sont stockées comme attribut `relation` sur les arêtes. Le graphe actuel est non orienté ; les noms des relations indiquent leur sens métier.

## Types de nœuds

### `Ticket`

- Identifiant : clé Jira, par exemple `AVTV-7004`
- Attributs disponibles : `summary`, `description`, `severity`, `priority`, `status`, `resolution`

### `Program`

- Identifiant et nom du programme, par exemple `AVTV` ou `BBTV`

### `Module`

- Identifiant : `MODULE::<nom>`
- Attribut : `name`

### `Version`

- Identifiant : `VERSION::<nom>`
- Attribut : `name`

### `TestCase`

- Identifiant : valeur de `Test ID`
- Attributs : `title`, `module`, `programs`, `preconditions`, `steps`, `expected_result`

### `CoverageGap`

- Identifiant : `GAP::<programme>::<scénario>`
- Attributs : `scenario`, `program`, `n_bugs`, `n_tests`, `coverage_status`, `tests_per_bug`

## Types de relations

| Relation | Signification |
|---|---|
| `BELONGS_TO` | Le ticket appartient au programme. |
| `AFFECTS_MODULE` | Le ticket concerne le module. |
| `FIXED_IN` | Le ticket est associé à une version corrective. |
| `VALIDATED_FOR` | Le cas de test valide le programme. |
| `COVERS_MODULE` | Le cas de test couvre le module. |
| `TESTED_BY` | Le ticket est lié à un cas de test. |
| `HAS_COVERAGE_GAP` | Le programme possède une lacune de couverture pour le scénario. |
| `SIMILAR_TO` | Les tickets sont classés similaires par l’analyse cross-programme. |

## Limites actuelles

- Les nœuds et relations proviennent des fichiers `MOCK_*`.
- Les liens `TESTED_BY` dépendent du champ `Linked bugs` du fichier de tests.
- `CoverageGap` est classé avec une heuristique basée sur le nombre de tests associés.
- Les relations `SIMILAR_TO` ne sont ajoutées qu’après réception et classification des scores de Personne A.
