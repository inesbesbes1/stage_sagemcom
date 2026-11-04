# Retrieval Evaluation Results

Dataset: MOCK_ALL.csv
Number of tickets: 400
Number of queries: 28

| Engine | Dimensions | Top-1 | Top-5 | MRR |
|---|---:|---:|---:|---:|
| Keywords | - | 71% | 75% | 0.72 |
| TF-IDF | - | 68% | 68% | 0.68 |
| TF-IDF + SVD | 50 | 71% | 75% | 0.72 |
| TF-IDF + SVD | 100 | 68% | 68% | 0.68 |
| TF-IDF + SVD | 150 | 68% | 68% | 0.68 |
| Embeddings | - | 93% | 93% | 0.93 |
