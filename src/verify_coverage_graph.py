
import networkx as nx
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parent.parent

GRAPH_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "knowledge_graph_with_coverage.graphml"
)


def verify_coverage_graph():

    print("\nCOVERAGE GRAPH VALIDATION")
    print("=" * 50)

    # Load the exported graph
    G = nx.read_graphml(GRAPH_FILE)

    # Retrieve CoverageGap nodes
    gap_nodes = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get("node_type") == "CoverageGap"
    ]

    print("\n1. NODE VALIDATION")
    print("-" * 30)
    print("Total graph nodes:", G.number_of_nodes())
    print("CoverageGap nodes:", len(gap_nodes))

    # Count classifications
    status_counts = Counter(
        data["coverage_status"]
        for _, data in gap_nodes
    )

    print("\n2. COVERAGE CLASSIFICATION")
    print("-" * 30)

    for status, count in sorted(status_counts.items()):
        print(f"{status}: {count}")

    # Verify program relationships
    connected_gaps = 0
    orphan_gaps = []

    for node, data in gap_nodes:

        program = data["program"]

        if G.has_edge(program, node):
            edge_data = G.get_edge_data(program, node)

            if edge_data.get("relation") == "HAS_COVERAGE_GAP":
                connected_gaps += 1
            else:
                orphan_gaps.append(node)
        else:
            orphan_gaps.append(node)

    print("\n3. RELATIONSHIP VALIDATION")
    print("-" * 30)
    print("Valid HAS_COVERAGE_GAP relationships:", connected_gaps)
    print("Orphan CoverageGap nodes:", len(orphan_gaps))

    # Check data integrity
    invalid_nodes = []

    for node, data in gap_nodes:
        if (
            "scenario" not in data
            or "program" not in data
            or "n_bugs" not in data
            or "n_tests" not in data
            or "coverage_status" not in data
        ):
            invalid_nodes.append(node)

    print("\n4. DATA INTEGRITY")
    print("-" * 30)
    print("Nodes with missing attributes:", len(invalid_nodes))

    # Final validation
    success = (
        len(gap_nodes) == 25
        and connected_gaps == 25
        and len(orphan_gaps) == 0
        and len(invalid_nodes) == 0
        and status_counts == {
            "COVERED": 13,
            "NO_COVERAGE": 8,
            "LOW_COVERAGE": 4
        }
    )

    print("\n5. FINAL RESULT")
    print("=" * 50)

    if success:
        print("SUCCESS: Coverage Graph validation passed!")
    else:
        print("WARNING: Some validation checks failed.")

    return success


if __name__ == "__main__":
    verify_coverage_graph()
