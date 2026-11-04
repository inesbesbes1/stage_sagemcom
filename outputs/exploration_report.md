# Rapport d'exploration : MOCK_ALL.csv

- Lignes : **400**  |  Colonnes : **17**
- Colonnes détectées : {'key': 'Key', 'summary': 'Summary', 'description': 'Description', 'status': 'Status', 'resolution': 'Resolution', 'severity': 'Severity', 'priority': 'Priority', 'component': 'Component/s', 'version': 'Fix Version/s', 'sprint': 'Sprint', 'pr_ref': 'PR reference in Customer Database', 'created': 'Created', 'updated': 'Updated'}
- Colonnes utilisées pour le texte : ['Summary', 'Description']

## Colonnes : type et taux de vide

| Colonne | Type | % vide | Valeurs distinctes |
|---|---|---|---|
| Key | object | 0.0 | 400 |
| PR reference in Customer Database | object | 0.0 | 400 |
| Severity | object | 0.0 | 3 |
| Priority | object | 0.0 | 3 |
| Summary | object | 0.0 | 400 |
| Status | object | 0.0 | 3 |
| Resolution | object | 19.8 | 3 |
| Component/s | object | 0.0 | 6 |
| Labels | float64 | 100.0 | 0 |
| Whiteboard | float64 | 100.0 | 0 |
| Assignee | object | 0.0 | 4 |
| Sprint | object | 51.0 | 3 |
| Fix Version/s | object | 52.5 | 3 |
| Created | object | 0.0 | 237 |
| Updated | object | 0.0 | 247 |
| Parent key | object | 93.5 | 21 |
| Description | object | 0.0 | 167 |

## Doublons

- Lignes strictement identiques : 0
- Clés de ticket dupliquées : 0
- Textes identiques (résumé+description) : 5

## Texte

- Mots par ticket : moyenne 57, médiane 57, max 71
- Tickets sans texte exploitable : 0
- Langues (estimation sur échantillon) : {'en': 300}

## Valeurs les plus fréquentes

**Component/s** : ToBeDefined (278), Player (28), Network (28), Settings (26), UI (26), Audio (14)
**Fix Version/s** : nan (210), [FW][STB37X] 5.2406.10 (71), [FW][M378] 4.2404.62 (60), [FW][AVSB] 2.2405.18 (59)
**Sprint** : nan (204), M378 Sprint 46 (83), STB37X Android 14 Sprint 45.2 (63), AVSB3930 Sprint 45 (50)
**Status** : CLOSED (321), OPEN (49), IN PROGRESS (30)
**Resolution** : FIXED (144), DUPLICATE (96), WONTFIX (81), nan (79)
**Severity** : Major (289), Minor (77), Critical (34)
**Priority** : Low (197), High (106), Medium (97)

## Étiquettes entre crochets dans les titres

- Titres contenant une référence client [XXX-123] : 400/400
- Titres avec au moins une étiquette : 372/400
- Étiquettes les plus fréquentes : Gen4 (164), Settings (87), Gen3 (83), DE-Prod (80), AVSB (80), Player (51), Power (34), UI (33), Boot (30), Crash (20)

## Dates

- Format détecté : %m/%d/%Y | création du 02/01/2025 au 09/10/2025

## À vérifier avec le tuteur

- Les champs ci-dessus correspondent-ils à ce que l'équipe utilise vraiment ?
- Où sont les tests fonctionnels liés (champ Jira, lien, autre outil) ?
- Données anonymisées ? Informations sensibles dans les descriptions ?