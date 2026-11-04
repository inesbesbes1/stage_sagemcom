
import pandas as pd

from similarity_evaluator import (
    calculate_global_score,
    classify_similarity
)


def run_tests():

    print("\nSIMILARITY EVALUATOR TESTS")
    print("=" * 50)

    # Test 1: High similarity
    assert classify_similarity(0.90) == "HIGH_SIMILARITY"
    print("PASS: High similarity classification")

    # Test 2: Medium similarity
    assert classify_similarity(0.70) == "MEDIUM_SIMILARITY"
    print("PASS: Medium similarity classification")

    # Test 3: Low similarity
    assert classify_similarity(0.30) == "LOW_SIMILARITY"
    print("PASS: Low similarity classification")

    # Test 4: Missing score
    assert classify_similarity(None) == "PENDING"
    print("PASS: Missing score classification")

    # Test 5: Weighted score
    row = pd.Series({
        "semantic_similarity": None,
        "preconditions_similarity": 0.80,
        "steps_similarity": 0.90,
        "expected_similarity": 0.70,
        "actual_similarity": 0.80
    })

    score = calculate_global_score(row)

    assert abs(score - 0.815) < 0.0001
    print("PASS: Weighted similarity calculation")

    print("\nAll tests passed!")


if __name__ == "__main__":
    run_tests()
