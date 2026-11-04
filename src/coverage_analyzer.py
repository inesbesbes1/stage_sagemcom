
import pandas as pd
from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "MOCK_coverage_gaps.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "coverage_analysis.csv"


def classify_coverage(row):
    """Classify coverage based on the number of associated tests."""

    if row["n_tests"] == 0:
        return "NO_COVERAGE"

    elif row["n_tests"] == 1:
        return "LOW_COVERAGE"

    else:
        return "COVERED"


def analyze_coverage():

    print("\nCOVERAGE GAP ANALYSIS")
    print("=" * 50)

    # Load coverage data
    df = pd.read_csv(INPUT_FILE)

    # Check required columns
    required_columns = {
        "scenario", "Program", "n_bugs", "n_tests", "gap"
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Apply our classification
    df["coverage_status"] = df.apply(
        classify_coverage, axis=1
    )

    # Calculate test-to-bug ratio for descriptive purposes
    df["tests_per_bug"] = (
        df["n_tests"] / df["n_bugs"]
    ).round(3)

    # Display results
    print("\nCLASSIFICATION:")
    print(df[
        ["scenario", "Program", "n_bugs",
         "n_tests", "coverage_status"]
    ].to_string(index=False))

    # Count each category
    print("\nCOVERAGE SUMMARY:")
    print(df["coverage_status"].value_counts())

    # Export results
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nAnalysis saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    analyze_coverage()
