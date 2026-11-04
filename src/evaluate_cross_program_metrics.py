from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

LABELED_PAIRS_FILE = (
    PROJECT_ROOT / "data" / "cross_program_labeled_pairs.csv"
)
SCORES_FILE = (
    PROJECT_ROOT / "data" / "cross_program_similarity_results.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "cross_program_threshold_metrics.csv"
)

FIELD_WEIGHTS = {
    "preconditions_similarity": 0.15,
    "steps_similarity": 0.35,
    "expected_similarity": 0.20,
    "actual_similarity": 0.30,
}

PAIR_COLUMNS = ["Key_avtv", "Key_bbtv"]


def get_score(row):
    """Prend le score global, le score sémantique, ou calcule
    un score pondéré à partir des scores de champs disponibles."""

    if "global_similarity" in row.index and pd.notna(row["global_similarity"]):
        return float(row["global_similarity"])

    if "semantic_similarity" in row.index and pd.notna(row["semantic_similarity"]):
        return float(row["semantic_similarity"])

    available = {
        column: weight
        for column, weight in FIELD_WEIGHTS.items()
        if column in row.index and pd.notna(row[column])
    }

    if not available:
        return np.nan

    weighted_sum = sum(
        row[column] * weight
        for column, weight in available.items()
    )
    total_weight = sum(available.values())

    return weighted_sum / total_weight


def calculate_metrics(y_true, y_pred):
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    accuracy = (tp + tn) / len(y_true) if len(y_true) else 0.0

    return {
        "threshold": None,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
    }


def main():
    if not LABELED_PAIRS_FILE.exists():
        raise FileNotFoundError(
            f"Fichier absent : {LABELED_PAIRS_FILE}"
        )

    if not SCORES_FILE.exists():
        raise FileNotFoundError(
            f"Fichier absent : {SCORES_FILE}"
        )

    labels = pd.read_csv(LABELED_PAIRS_FILE)
    scores = pd.read_csv(SCORES_FILE)

    required_label_columns = set(PAIR_COLUMNS + ["is_match"])
    missing_labels = required_label_columns - set(labels.columns)
    if missing_labels:
        raise ValueError(
            f"Colonnes manquantes dans le fichier étiqueté : "
            f"{sorted(missing_labels)}"
        )

    missing_pair_columns = set(PAIR_COLUMNS) - set(scores.columns)
    if missing_pair_columns:
        raise ValueError(
            f"Colonnes manquantes dans le fichier de scores : "
            f"{sorted(missing_pair_columns)}"
        )

    # Normaliser les clés avant de joindre les deux fichiers.
    for column in PAIR_COLUMNS:
        labels[column] = labels[column].astype("string").str.strip()
        scores[column] = scores[column].astype("string").str.strip()

    if labels.duplicated(PAIR_COLUMNS).any():
        raise ValueError("Le fichier étiqueté contient des paires en double.")

    if scores.duplicated(PAIR_COLUMNS).any():
        raise ValueError("Le fichier de scores contient des paires en double.")

    score_columns = [
        column
        for column in [
            "global_similarity",
            "semantic_similarity",
            *FIELD_WEIGHTS.keys(),
        ]
        if column in scores.columns
    ]

    if not score_columns:
        raise ValueError(
            "Aucune colonne de score n'a été trouvée dans le fichier de scores."
        )

    for column in score_columns:
        scores[column] = pd.to_numeric(scores[column], errors="coerce")

        invalid = (
            scores[column].notna()
            & ~scores[column].between(0, 1)
        )
        if invalid.any():
            raise ValueError(
                f"Des scores hors de l'intervalle 0–1 sont présents "
                f"dans {column}."
            )

    data = labels.merge(
        scores[PAIR_COLUMNS + score_columns],
        on=PAIR_COLUMNS,
        how="left",
        validate="one_to_one",
    )

    data["score"] = data.apply(get_score, axis=1)
    scored = data[data["score"].notna()].copy()

    print(f"Paires étiquetées : {len(data)}")
    print(f"Paires avec un score : {len(scored)}")

    if scored.empty:
        print(
            "Aucun score disponible pour le moment. "
            "Le script est prêt ; relance-le après réception des scores de A."
        )
        return

    if len(scored) < len(data):
        print(
            "Attention : certaines paires n'ont pas de score. "
            "Les métriques portent uniquement sur les paires scorées."
        )

    y_true = scored["is_match"].astype(int)
    positive_rate = y_true.mean()

    print(f"Proportion de paires positives scorées : {positive_rate:.2%}")
    print(
        "Accuracy d'une prédiction toujours négative : "
        f"{1 - positive_rate:.2%}"
    )

    thresholds = np.round(np.arange(0.0, 1.001, 0.05), 2)
    results = []

    for threshold in thresholds:
        y_pred = (scored["score"] >= threshold).astype(int)
        metrics = calculate_metrics(y_true, y_pred)
        metrics["threshold"] = threshold
        results.append(metrics)

    metrics_df = pd.DataFrame(results)
    metrics_df.to_csv(OUTPUT_FILE, index=False)

    print("\nMétriques aux seuils actuels :")
    print(
        metrics_df[metrics_df["threshold"].isin([0.60, 0.80])][
            ["threshold", "precision", "recall", "f1", "accuracy"]
        ].to_string(index=False)
    )

    best = metrics_df.sort_values(
        ["f1", "precision"],
        ascending=False
    ).iloc[0]

    print(
        "\nMeilleur F1 sur ce jeu : "
        f"seuil={best['threshold']:.2f}, "
        f"precision={best['precision']:.3f}, "
        f"rappel={best['recall']:.3f}, "
        f"F1={best['f1']:.3f}"
    )
    print(f"\nTable complète enregistrée dans : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()