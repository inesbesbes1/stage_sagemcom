
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "cross_program_similarity_results.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "evaluated_cross_program_matches.csv"
)

# Provisional classification thresholds
HIGH_THRESHOLD = 0.80
MEDIUM_THRESHOLD = 0.60

# Weights for field-level similarity
WEIGHTS = {
    "preconditions_similarity": 0.15,
    "steps_similarity": 0.35,
    "expected_similarity": 0.20,
    "actual_similarity": 0.30
}


def validate_scores(df):

    score_columns = [
        "semantic_similarity",
        *WEIGHTS.keys()
    ]

    for column in score_columns:

        if column not in df.columns:
            continue

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        invalid = (
            df[column].notna()
            & ~df[column].between(0, 1)
        )

        if invalid.any():
            raise ValueError(
                f"Invalid scores found in {column}"
            )

    return df


def calculate_global_score(row):

    # Prefer the global score if available
    if pd.notna(row["semantic_similarity"]):
        return float(row["semantic_similarity"])

    # Otherwise calculate a weighted score
    available_scores = {
        column: weight
        for column, weight in WEIGHTS.items()
        if pd.notna(row[column])
    }

    if not available_scores:
        return None

    weighted_sum = sum(
        row[column] * weight
        for column, weight in available_scores.items()
    )

    total_weight = sum(available_scores.values())

    return weighted_sum / total_weight


def classify_similarity(score):

    if pd.isna(score):
        return "PENDING"

    if score >= HIGH_THRESHOLD:
        return "HIGH_SIMILARITY"

    if score >= MEDIUM_THRESHOLD:
        return "MEDIUM_SIMILARITY"

    return "LOW_SIMILARITY"


def evaluate_matches():

    print("\nCROSS-PROGRAM SIMILARITY EVALUATION")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    df = validate_scores(df)

    df["global_similarity"] = df.apply(
        calculate_global_score,
        axis=1
    )

    df["similarity_class"] = df["global_similarity"].apply(
        classify_similarity
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nCLASSIFICATION SUMMARY")
    print("-" * 40)

    print(
        df["similarity_class"]
        .value_counts()
        .to_string()
    )

    print("\nSCORE AVAILABILITY")
    print("-" * 40)

    print(
        "Pairs with scores:",
        df["global_similarity"].notna().sum()
    )

    print(
        "Pairs pending:",
        df["global_similarity"].isna().sum()
    )

    print("\nResults saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    evaluate_matches()
