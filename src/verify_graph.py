
import pandas as pd
from pathlib import Path
from graph_builder import build_knowledge_graph

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Rebuild graph
G = build_knowledge_graph()

# Count nodes by type
tickets = [
    n for n, d in G.nodes(data=True)
    if d.get("node_type") == "Ticket"
]

tests = [
    n for n, d in G.nodes(data=True)
    if d.get("node_type") == "TestCase"
]

# Find direct Ticket-TestCase relationships
tested_tickets = set()
ticket_test_relations = []

for source, target, data in G.edges(data=True):
    if data.get("relation") == "TESTED_BY":
        tested_tickets.add(source)
        ticket_test_relations.append((source, target))

# Tickets without a directly linked test
untested_tickets = set(tickets) - tested_tickets

# Check references in the original test CSV
tests_df = pd.read_csv(DATA_DIR / "MOCK_tests.csv")

linked_bug_ids = set()

for value in tests_df["Linked bugs"].dropna():
    for bug_id in str(value).split("|"):
        bug_id = bug_id.strip()
        if bug_id:
            linked_bug_ids.add(bug_id)

missing_tickets = linked_bug_ids - set(tickets)

# Display results
print("\nKNOWLEDGE GRAPH VALIDATION")
print("=" * 40)

print("Total tickets:", len(tickets))
print("Total test cases:", len(tests))
print("Direct Ticket-Test relationships:", len(ticket_test_relations))

print("\nCOVERAGE OVERVIEW")
print("-" * 40)

print("Tickets with linked tests:", len(tested_tickets))
print("Tickets without linked tests:", len(untested_tickets))

coverage = (
    len(tested_tickets) / len(tickets) * 100
    if tickets else 0
)

print(f"Direct test-link coverage: {coverage:.2f}%")

print("\nDATA QUALITY")
print("-" * 40)

print("Unique bug references in tests:", len(linked_bug_ids))
print("References missing from graph:", len(missing_tickets))

print("\nSAMPLE TEST RELATIONSHIPS")
print("-" * 40)

for ticket_id, test_id in ticket_test_relations[:10]:
    print(f"{ticket_id} --TESTED_BY--> {test_id}")

print("\nSAMPLE TICKETS WITHOUT DIRECT TEST LINKS")
print("-" * 40)

for ticket_id in sorted(untested_tickets)[:10]:
    print(ticket_id)
