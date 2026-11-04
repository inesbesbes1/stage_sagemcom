
import networkx as nx
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GRAPH_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "knowledge_graph_with_cross_program.graphml"
)


def verify_graph():

    print("\nCROSS-PROGRAM GRAPH VALIDATION")
    print("=" * 50)

    graph = nx.read_graphml(GRAPH_FILE)

    tickets = [
        node for node, data in graph.nodes(data=True)
        if data.get("node_type") == "Ticket"
    ]

    coverage_gaps = [
        node for node, data in graph.nodes(data=True)
        if data.get("node_type") == "CoverageGap"
    ]

    similar_edges = [
        (u, v, data)
        for u, v, data in graph.edges(data=True)
        if data.get("relation") == "SIMILAR_TO"
    ]

    print("Total nodes:", graph.number_of_nodes())
    print("Total edges:", graph.number_of_edges())
    print("Tickets:", len(tickets))
    print("Coverage gaps:", len(coverage_gaps))
    print("SIMILAR_TO relationships:", len(similar_edges))

    assert len(tickets) == 400, "Expected 400 tickets"
    assert len(coverage_gaps) == 25, "Expected 25 coverage gaps"
    assert len(similar_edges) == 0, "Unexpected similarity relationships"

    print("\nPASS: All original tickets preserved")
    print("PASS: Coverage gap nodes preserved")
    print("PASS: No false similarity relationships")
    print("\nGraph validation successful!")


if __name__ == "__main__":
    verify_graph()
