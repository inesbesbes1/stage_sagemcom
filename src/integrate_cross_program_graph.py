
import pandas as pd
import networkx as nx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GRAPH_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "knowledge_graph_with_coverage.graphml"
)

RESULTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "evaluated_cross_program_matches.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "knowledge_graph_with_cross_program.graphml"
)


def integrate_cross_program_matches():

    print("\nCROSS-PROGRAM GRAPH INTEGRATION")
    print("=" * 55)

    # 1. Load existing Knowledge Graph
    if not GRAPH_FILE.exists():
        raise FileNotFoundError(f"Graph not found: {GRAPH_FILE}")

    graph = nx.read_graphml(GRAPH_FILE)

    print("Initial graph nodes:", graph.number_of_nodes())
    print("Initial graph edges:", graph.number_of_edges())

    # 2. Load evaluated similarity results
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(f"Results not found: {RESULTS_FILE}")

    df = pd.read_csv(RESULTS_FILE)

    required_columns = {
        "Key_avtv",
        "Key_bbtv",
        "global_similarity",
        "similarity_class"
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # 3. Keep only high-similarity pairs
    matches = df[
        df["similarity_class"] == "HIGH_SIMILARITY"
    ]

    print("\nMATCH SUMMARY")
    print("-" * 40)
    print("High similarity pairs:", len(matches))
    print(
        "Medium similarity pairs:",
        (df["similarity_class"] == "MEDIUM_SIMILARITY").sum()
    )
    print(
        "Low similarity pairs:",
        (df["similarity_class"] == "LOW_SIMILARITY").sum()
    )
    print(
        "Pending pairs:",
        (df["similarity_class"] == "PENDING").sum()
    )

    # 4. Add SIMILAR_TO relationships
    added = 0
    missing_tickets = 0

    for _, row in matches.iterrows():

        avtv_key = str(row["Key_avtv"])
        bbtv_key = str(row["Key_bbtv"])

        if not graph.has_node(avtv_key) or not graph.has_node(bbtv_key):
            missing_tickets += 1
            continue

        graph.add_edge(
            avtv_key,
            bbtv_key,
            relation="SIMILAR_TO",
            similarity=float(row["global_similarity"]),
            similarity_class="HIGH_SIMILARITY",
            analysis_type="CROSS_PROGRAM"
        )

        added += 1

    # 5. Save enriched graph
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    nx.write_graphml(graph, OUTPUT_FILE)

    print("\nINTEGRATION RESULTS")
    print("-" * 40)
    print("Relations added:", added)
    print("Pairs with missing tickets:", missing_tickets)
    print("Final graph nodes:", graph.number_of_nodes())
    print("Final graph edges:", graph.number_of_edges())

    print("\nGraph saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    integrate_cross_program_matches()
