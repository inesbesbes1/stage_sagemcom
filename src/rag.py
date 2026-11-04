"""RAG prototype for synthetic AVS Jira tickets.

Features:
- Semantic retrieval with Sentence Transformers (TF-IDF fallback if unavailable).
- Near-duplicate grouping of retrieved candidates.
- Structured, source-grounded context and prompt generation for a future LLM.

This script DOES NOT call an LLM. It prepares the prompt only.
"""

import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure imports work when launched as: python src/rag.py ...
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from loader import detect_columns, load_table, prepare  # noqa: E402
from search import EmbeddingEngine, TfidfEngine  # noqa: E402


def extract_ticket_metadata(row, cols):
    """Extract metadata without confusing customer references with tags."""
    jira_key = str(row.get("_key", "Unknown"))
    project_match = re.match(r"^([A-Z][A-Z0-9]*)-", jira_key)
    jira_project = project_match.group(1) if project_match else "Unknown"

    summary_col = cols.get("summary")
    summary = str(row.get(summary_col, "")) if summary_col else ""
    tags = re.findall(r"\[([^\]]+)\]", summary)

    generation = next(
        (tag for tag in tags if re.fullmatch(r"Gen\d+", tag, flags=re.IGNORECASE)),
        "Not specified",
    )
    summary_tags = [
        tag for tag in tags
        if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", tag)
        and not re.fullmatch(r"Gen\d+", tag, flags=re.IGNORECASE)
    ]

    def value(field):
        column = cols.get(field)
        if not column:
            return "Not available"
        item = row.get(column, "")
        if pd.isna(item) or str(item).strip() == "":
            return "Not available"
        return str(item).strip()

    return {
        "jira_project": jira_project,
        "customer_reference": value("pr_ref"),
        "generation": generation,
        # Raw tags are not assumed to be a validated functional taxonomy.
        "summary_tags": ", ".join(summary_tags) if summary_tags else "Not specified",
        "status": value("status"),
        "priority": value("priority"),
        "severity": value("severity"),
        "component": value("component"),
        "version": value("version"),
        "product": value("product"),
        "description": value("description"),
    }


def make_engine(texts, force_tfidf=False):
    """Use embeddings when available; otherwise fall back to TF-IDF."""
    if not force_tfidf:
        try:
            engine = EmbeddingEngine(texts)
            print("Search engine: Sentence Transformers embeddings")
            return engine
        except Exception as exc:
            print(
                "[WARNING] Embeddings unavailable; falling back to TF-IDF "
                f"({type(exc).__name__}: {exc})"
            )
    engine = TfidfEngine(texts)
    print("Search engine: TF-IDF fallback")
    return engine


def get_document_vectors(engine):
    """Return normalized dense document vectors for cosine comparisons."""
    if hasattr(engine, "emb"):
        vectors = np.asarray(engine.emb, dtype=np.float32)
    elif hasattr(engine, "matrix"):
        from sklearn.preprocessing import normalize
        vectors = normalize(engine.matrix).toarray().astype(np.float32)
    else:
        raise TypeError("Unsupported search engine: no document vectors found")

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def normalize_title(title):
    """Normalize a summary for duplicate comparison (not semantic retrieval)."""
    text = str(title).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def retrieve_and_group(
    engine, df, query, k=5, candidate_pool=25, duplicate_threshold=0.92
):
    """Retrieve semantically, then group tickets with near-identical summaries.

    Retrieval uses the configured search engine. Deduplication compares the
    normalized Jira summaries, which avoids merging different defects merely
    because their long descriptions share a template. Similarity groups are
    still candidates for review, not proof of one identical incident.
    """
    scores = np.asarray(engine.scores(query), dtype=np.float32).reshape(-1)
    if len(scores) != len(df):
        raise ValueError(
            f"Search engine returned {len(scores)} scores for {len(df)} tickets"
        )

    candidate_indices = [
        int(i) for i in np.argsort(-scores)
        if np.isfinite(scores[i]) and scores[i] > 0
    ][:candidate_pool]

    groups = []
    for idx in candidate_indices:
        row = df.iloc[idx]
        title = str(row["_title"])
        normalized = normalize_title(title)
        ticket = {
            "key": str(row["_key"]),
            "score": float(scores[idx]),
            "title": title,
            "normalized_title": normalized,
            "row": row,
        }

        best_group = None
        best_similarity = -1.0
        for group in groups:
            similarity = SequenceMatcher(
                None, normalized, group["representative"]["normalized_title"]
            ).ratio()
            if similarity >= duplicate_threshold and similarity > best_similarity:
                best_group = group
                best_similarity = similarity

        if best_group is None:
            groups.append({"representative": ticket, "members": [ticket]})
        else:
            best_group["members"].append(ticket)

    groups.sort(key=lambda item: item["representative"]["score"], reverse=True)
    return groups[:k], len(candidate_indices)


def build_context(groups, cols):
    """Build evidence context, retaining all keys and metadata per group."""
    sections = []

    for number, group in enumerate(groups, start=1):
        representative = group["representative"]
        meta = extract_ticket_metadata(representative["row"], cols)

        member_lines = []
        for member in group["members"]:
            m = extract_ticket_metadata(member["row"], cols)
            member_lines.append(
                f"- {member['key']} | query_score={member['score']:.3f} | "
                f"Jira project={m['jira_project']} | generation={m['generation']} | "
                f"version={m['version']} | status={m['status']} | "
                f"priority={m['priority']} | severity={m['severity']} | "
                f"summary_tags={m['summary_tags']}"
            )

        sections.append(f"""[SIMILARITY GROUP {number}]
Number of grouped tickets: {len(group['members'])}
Representative Jira Key: {representative['key']}
Representative query similarity: {representative['score']:.3f}
Summary: {representative['title']}
Jira Project: {meta['jira_project']}
Customer Reference: {meta['customer_reference']}
Generation: {meta['generation']}
Summary Tags (raw): {meta['summary_tags']}
Product/Program field: {meta['product']}
Status: {meta['status']}
Priority: {meta['priority']}
Severity: {meta['severity']}
Component: {meta['component']}
Version: {meta['version']}
Description: {meta['description']}
Grouped Jira tickets:
{chr(10).join(member_lines)}""")

    return "\n\n".join(sections) if sections else "No relevant tickets were retrieved."


def build_prompt(query, context):
    return f"""You are an assistant supporting software validation and QA engineers
working on Audio Video Solutions (AVS) products.

USER QUESTION:
{query}

RETRIEVED AND GROUPED JIRA CONTEXT:
{context}

INSTRUCTIONS:
1. Use only information present in the retrieved Jira context.
2. Treat each similarity group as potentially related tickets, not proof of one identical incident.
3. Cite the Jira key whenever using ticket information.
4. Distinguish observed facts from hypotheses.
5. Do not invent root causes, fixes, or test results.
6. Compare Jira projects, generations, versions, statuses, priorities and severities when available.
7. Identify repeated symptoms and differences between tickets in the same group.
8. Suggest functional validation scenarios based on the evidence.
9. If information is missing, explicitly state that it is unavailable.
10. Do not interpret Jira project prefixes as customer-program names.

STRUCTURE YOUR ANSWER:
- Problem understanding
- Related ticket groups (representative ticket and all Jira keys)
- Common symptoms and differences
- Cross-project / cross-generation observations
- Possible functional coverage gaps
- Suggested validation scenarios
- Limitations and missing information"""


def main():
    parser = argparse.ArgumentParser(
        description="Semantic retrieval and near-duplicate grouping for AVS tickets"
    )
    parser.add_argument("file", help="Path to the ticket CSV/XLSX")
    parser.add_argument("--query", required=True, help="Question to investigate")
    parser.add_argument("--k", type=int, default=5, help="Maximum number of groups")
    parser.add_argument(
        "--pool", type=int, default=25,
        help="Number of top semantic candidates examined before grouping (default: 25)",
    )
    parser.add_argument(
        "--duplicate-threshold", type=float, default=0.92,
        help="Normalized-summary similarity threshold for grouping (default: 0.92)",
    )
    parser.add_argument(
        "--tfidf", action="store_true",
        help="Force TF-IDF instead of Sentence Transformers (useful for offline tests)",
    )
    parser.add_argument("--output", help="Optional path to save the generated prompt")
    args = parser.parse_args()

    if args.k < 1:
        parser.error("--k must be at least 1")
    if args.pool < 1:
        parser.error("--pool must be at least 1")
    if not 0.0 <= args.duplicate_threshold <= 1.0:
        parser.error("--duplicate-threshold must be between 0 and 1")

    raw = load_table(args.file)
    df, cols, text_cols = prepare(raw, detect_columns(raw))
    df = df[df["text"].fillna("").astype(str).str.len() > 0].reset_index(drop=True)

    if df.empty:
        parser.error("No non-empty ticket text was found in the input file")

    print(f"\n{len(df)} tickets loaded")
    print(f"Text fields used: {text_cols}")
    print(f"Query: {args.query}")

    engine = make_engine(df["text"].astype(str).tolist(), force_tfidf=args.tfidf)
    groups, candidate_count = retrieve_and_group(
        engine,
        df,
        args.query,
        k=args.k,
        candidate_pool=args.pool,
        duplicate_threshold=args.duplicate_threshold,
    )

    grouped_count = sum(len(group["members"]) for group in groups)
    print(
        f"\n{candidate_count} candidate tickets examined; "
        f"{grouped_count} tickets represented in {len(groups)} groups"
    )
    print(f"Summary duplicate threshold: {args.duplicate_threshold:.2f}")
    if candidate_count < args.pool:
        print("Note: fewer than --pool candidates had a positive similarity score.")

    for number, group in enumerate(groups, start=1):
        rep = group["representative"]
        print(
            f"\nGROUP {number} | {len(group['members'])} ticket(s) | "
            f"representative={rep['key']} | query_score={rep['score']:.3f}"
        )
        for member in group["members"]:
            print(
                f"  {member['key']:<15} score={member['score']:.3f}  "
                f"{member['title'][:90]}"
            )

    context = build_context(groups, cols)
    prompt = build_prompt(args.query, context)

    print("\n" + "=" * 65)
    print("GENERATED LLM PROMPT (not sent to an LLM)")
    print("=" * 65)
    print(prompt)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(prompt, encoding="utf-8")
        print(f"\nPrompt saved to: {output_path}")


if __name__ == "__main__":
    main()
