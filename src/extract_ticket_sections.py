
import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "MOCK_ALL.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "structured_tickets.csv"

# Sections to extract
PATTERNS = {
    "preconditions": r"Preconditions\s*:",
    "steps": r"Steps?\s+to\s+reproduce\s*:",
    "expected_result": r"Expected\s+result\s*:",
    "actual_result": r"Actual\s+result\s*:"
}


def extract_section(description, section_name):
    pattern = PATTERNS[section_name]

    # Find the beginning of the requested section
    match = re.search(pattern, description, re.IGNORECASE)

    if not match:
        return ""

    start = match.end()

    # Find the beginning of the next section
    next_positions = []

    for other_name, other_pattern in PATTERNS.items():
        if other_name == section_name:
            continue

        other_match = re.search(
            other_pattern,
            description[start:],
            re.IGNORECASE
        )

        if other_match:
            next_positions.append(
                start + other_match.start()
            )

    end = min(next_positions) if next_positions else len(description)

    return description[start:end].strip()


def extract_ticket_sections():

    print("\nTICKET SECTION EXTRACTION")
    print("=" * 55)

    df = pd.read_csv(INPUT_FILE)

    # Handle missing descriptions
    df["Description"] = df["Description"].fillna("").astype(str)

    # Identify program from ticket key
    df["Program"] = df["Key"].astype(str).str.split("-").str[0]

    # Extract the four sections
    for section in PATTERNS:
        df[section] = df["Description"].apply(
            lambda description: extract_section(
                description,
                section
            )
        )

    # Keep useful columns
    structured_df = df[
        [
            "Key",
            "Program",
            "Summary",
            "Component/s",
            "Severity",
            "Priority",
            "preconditions",
            "steps",
            "expected_result",
            "actual_result"
        ]
    ].copy()

    # Save structured tickets
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    structured_df.to_csv(OUTPUT_FILE, index=False)

    print("Total tickets:", len(structured_df))
    print("Output:", OUTPUT_FILE)

    print("\nSECTION EXTRACTION VALIDATION")
    print("-" * 40)

    for section in PATTERNS:
        extracted = (
            structured_df[section].fillna("").str.strip() != ""
        ).sum()

        print(f"{section}: {extracted}/{len(structured_df)}")

    print("\nSAMPLE EXTRACTED TICKET")
    print("-" * 40)

    sample = structured_df.iloc[0]

    for column in structured_df.columns:
        print(f"\n{column}: {sample[column]}")

    print("\nExtraction completed!")


if __name__ == "__main__":
    extract_ticket_sections()
