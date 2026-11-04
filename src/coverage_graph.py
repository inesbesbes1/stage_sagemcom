
import pandas as pd
import networkx as nx
from pathlib import Path

from graph_builder import build_knowledge_graph


PROJECT_ROOT = Path(__file__).resolve().parent.parent

COVERAGE_FILE = PROJECT_ROOT / "data" / "coverage_analysis.csv"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "knowledge_graph_with_coverage.graphml"


def add_coverage_gaps(G):

    df = pd.read_csv(COVERAGE_FILE)

    for _, row in df.iterrows():

        program = str(row["Program"])
        scenario = str(row["scenario"])

        gap_id = f"GAP::{program}::{scenario}"

        # Create CoverageGap node
        G.add_node(
            gap_id,
            node_type="CoverageGap",
            scenario=scenario,
            program=program,
            n_bugs=int(row["n_bugs"]),
            n_tests=int(row["n_tests"]),
            coverage_status=str(row["coverage_status"]),
            tests_per_bug=float(row["tests_per_bug"])
        )

        # Connect Program to CoverageGap
        if program in G:

            G.add_edge(
                program,
                gap_id,
                relation="HAS_COVERAGE_GAP"
            )

    return G


if __name__ == "__main__":

    G = build_knowledge_graph()

    print("\nADDING COVERAGE GAPS TO KNOWLEDGE GRAPH")
    print("=" * 50)

    G = add_coverage_gaps(G)

    gap_nodes = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get("node_type") == "CoverageGap"
    ]

    print("CoverageGap nodes:", len(gap_nodes))

    for node, data in gap_nodes:
        print(
            f'{data["program"]} | {data["scenario"]} | '
            f'{data["coverage_status"]} | '
            f'Bugs: {data["n_bugs"]} | Tests: {data["n_tests"]}'
        )

    # Clean None values before GraphML export
    for node, attributes in G.nodes(data=True):
        for key, value in list(attributes.items()):
            if value is None:
                del attributes[key]

    for source, target, attributes in G.edges(data=True):
        for key, value in list(attributes.items()):
            if value is None:
                del attributes[key]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    nx.write_graphml(G, OUTPUT_FILE)

    print("\nGraph saved to:", OUTPUT_FILE)
    print("Total nodes:", G.number_of_nodes())
    print("Total edges:", G.number_of_edges())
