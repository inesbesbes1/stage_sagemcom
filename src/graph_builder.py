
import pandas as pd
import networkx as nx
from pathlib import Path


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

OUTPUT_DIR.mkdir(exist_ok=True)


def clean_value(value):
    """Convert missing values into None and clean text."""
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.lower() in ["", "nan", "none", "not specified"]:
        return None

    return value


def build_knowledge_graph():

    # Load datasets
    tickets_df = pd.read_csv(DATA_DIR / "MOCK_ALL.csv")
    tests_df = pd.read_csv(DATA_DIR / "MOCK_tests.csv")

    # Create an undirected graph
    graph = nx.Graph()

    # -----------------------------------
    # 1. CREATE TICKET NODES
    # -----------------------------------

    for _, row in tickets_df.iterrows():

        ticket_id = clean_value(row["Key"])

        if not ticket_id:
            continue

        graph.add_node(
            ticket_id,
            node_type="Ticket",
            summary=clean_value(row["Summary"]),
            description=clean_value(row["Description"]),
            severity=clean_value(row["Severity"]),
            priority=clean_value(row["Priority"]),
            status=clean_value(row["Status"]),
            resolution=clean_value(row["Resolution"]),
        )

        # -----------------------------------
        # 2. PROGRAM RELATIONSHIP
        # -----------------------------------

        if ticket_id.startswith("AVTV-"):
            program = "AVTV"
        elif ticket_id.startswith("BBTV-"):
            program = "BBTV"
        else:
            program = None

        if program:
            graph.add_node(
                program,
                node_type="Program"
            )

            graph.add_edge(
                ticket_id,
                program,
                relation="BELONGS_TO"
            )

        # -----------------------------------
        # 3. MODULE RELATIONSHIP
        # -----------------------------------

        module = clean_value(row["Component/s"])

        if module:
            module_id = f"MODULE::{module}"

            graph.add_node(
                module_id,
                node_type="Module",
                name=module
            )

            graph.add_edge(
                ticket_id,
                module_id,
                relation="AFFECTS_MODULE"
            )

        # -----------------------------------
        # 4. VERSION RELATIONSHIP
        # -----------------------------------

        version = clean_value(row["Fix Version/s"])

        if version:
            version_id = f"VERSION::{version}"

            graph.add_node(
                version_id,
                node_type="Version",
                name=version
            )

            graph.add_edge(
                ticket_id,
                version_id,
                relation="FIXED_IN"
            )

    # -----------------------------------
    # 5. CREATE TEST CASE NODES
    # -----------------------------------

    for _, row in tests_df.iterrows():

        test_id = clean_value(row["Test ID"])

        if not test_id:
            continue

        graph.add_node(
            test_id,
            node_type="TestCase",
            title=clean_value(row["Title"]),
            module=clean_value(row["Module"]),
            programs=clean_value(row["Programs"]),
            preconditions=clean_value(row["Preconditions"]),
            steps=clean_value(row["Steps"]),
            expected_result=clean_value(row["Expected result"])
        )

        # -----------------------------------
        # 6. TEST-PROGRAM RELATIONSHIPS
        # -----------------------------------

        programs = clean_value(row["Programs"])

        if programs:
            for program in programs.split("|"):

                program = program.strip()

                if program:
                    graph.add_node(
                        program,
                        node_type="Program"
                    )

                    graph.add_edge(
                        test_id,
                        program,
                        relation="VALIDATED_FOR"
                    )

        # -----------------------------------
        # 7. TEST-MODULE RELATIONSHIP
        # -----------------------------------

        module = clean_value(row["Module"])

        if module:
            module_id = f"MODULE::{module}"

            graph.add_node(
                module_id,
                node_type="Module",
                name=module
            )

            graph.add_edge(
                test_id,
                module_id,
                relation="COVERS_MODULE"
            )

        # -----------------------------------
        # 8. TEST-TICKET RELATIONSHIP
        # -----------------------------------

        linked_bugs = clean_value(row["Linked bugs"])

        if linked_bugs:
            for bug_id in linked_bugs.split("|"):

                bug_id = bug_id.strip()

                if bug_id in graph:
                    graph.add_edge(
                        bug_id,
                        test_id,
                        relation="TESTED_BY"
                    )

    return graph



if __name__ == "__main__":

    G = build_knowledge_graph()

    print("\nKNOWLEDGE GRAPH CREATED")
    print("=======================")

    print("Nodes:", G.number_of_nodes())
    print("Edges:", G.number_of_edges())

    from collections import Counter

    node_counts = Counter(
        data["node_type"]
        for _, data in G.nodes(data=True)
    )

    print("\nNode types:")

    for node_type, count in node_counts.items():
        print(f"{node_type}: {count}")

    # Clean None values before GraphML export
    for node, attributes in G.nodes(data=True):
        for key, value in list(attributes.items()):
            if value is None:
                del attributes[key]

    for source, target, attributes in G.edges(data=True):
        for key, value in list(attributes.items()):
            if value is None:
                del attributes[key]

    # Export graph
    nx.write_graphml(
        G,
        OUTPUT_DIR / "knowledge_graph.graphml"
    )

    print("\nGraph saved to outputs/knowledge_graph.graphml")

