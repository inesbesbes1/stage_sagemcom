
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "cross_program_pairs.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "cross_program_similarity_results.csv"


def prepare_similarity_template():

    print("\nSIMILARITY INTEGRATION TEMPLATE")
    print("=" * 55)

    pairs = pd.read_csv(INPUT_FILE)

    # Keep the pair identifiers
    results = pairs[["Key_avtv", "Key_bbtv"]].copy()

    # Global semantic similarity
    results["semantic_similarity"] = pd.NA

    # Optional field-level similarity scores
    results["preconditions_similarity"] = pd.NA
    results["steps_similarity"] = pd.NA
    results["expected_similarity"] = pd.NA
    results["actual_similarity"] = pd.NA

    # Save the template without inventing scores
    results.to_csv(OUTPUT_FILE, index=False)

    print("Total pairs:", len(results))
    print("Columns:", results.columns.tolist())
    print("Scores initialized as empty values.")

    print("\nSAMPLE ROWS")
    print("-" * 40)
    print(results.head(5).to_string(index=False))

    print("\nTemplate saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    prepare_similarity_template()
