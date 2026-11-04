
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "structured_tickets.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "cross_program_pairs.csv"


def prepare_cross_program_pairs():

    print("\nCROSS-PROGRAM PAIR GENERATION")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    avtv = df[df["Program"] == "AVTV"].copy()
    bbtv = df[df["Program"] == "BBTV"].copy()

    print("AVTV tickets:", len(avtv))
    print("BBTV tickets:", len(bbtv))

    # Generate every AVTV-BBTV combination
    avtv["_key"] = 1
    bbtv["_key"] = 1

    pairs = avtv.merge(
        bbtv,
        on="_key",
        suffixes=("_avtv", "_bbtv")
    )

    pairs = pairs.drop(columns=["_key"])

    # Keep only useful comparison fields
    columns = [
        "Key_avtv",
        "Key_bbtv",
        "Summary_avtv",
        "Summary_bbtv",
        "Component/s_avtv",
        "Component/s_bbtv",
        "Severity_avtv",
        "Severity_bbtv",
        "preconditions_avtv",
        "preconditions_bbtv",
        "steps_avtv",
        "steps_bbtv",
        "expected_result_avtv",
        "expected_result_bbtv",
        "actual_result_avtv",
        "actual_result_bbtv"
    ]

    pairs = pairs[columns]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUTPUT_FILE, index=False)

    print("\nPAIR GENERATION RESULTS")
    print("-" * 40)
    print("Total candidate pairs:", len(pairs))
    print("Expected pairs:", len(avtv) * len(bbtv))

    print("\nSAMPLE PAIRS")
    print("-" * 40)

    print(
        pairs[
            ["Key_avtv", "Key_bbtv"]
        ].head(5).to_string(index=False)
    )

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    prepare_cross_program_pairs()
