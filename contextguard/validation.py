"""
contextguard/validation.py -- runs BOTH a context-aware review and a
diff-only baseline (same function, no graph/retrieval context) on the
same change, so you get a real before/after comparison instead of a claim.
"""

from contextguard.context import build_full_context
from contextguard.retrieval import chunk_repo
from contextguard.reasoning import get_structured_review

EMPTY_CONTEXT = {"graph_neighbors": {}, "similar_chunks": []}


def run_comparison(repo_path, client, top_k=5, max_hops=2):
    """
    Returns:
        {
          "qualified_function_name": {
              "context_aware": [issues...],
              "diff_only": [issues...],
          },
          ...
        }
    """
    context_bundle = build_full_context(repo_path, top_k=top_k, max_hops=max_hops)
    chunk_by_name = {c["name"]: c for c in chunk_repo(repo_path)}

    results = {}
    for changed_name, context in context_bundle.items():
        context_aware_issues = get_structured_review(client, changed_name, context, chunk_by_name)
        diff_only_issues = get_structured_review(client, changed_name, EMPTY_CONTEXT, chunk_by_name)

        results[changed_name] = {
            "context_aware": context_aware_issues,
            "diff_only": diff_only_issues,
        }

    return results


if __name__ == "__main__":
    import os
    from groq import Groq

    repo_path = r"E:\sqlparse_demo\sqlparse"  # point at your sqlparse test clone

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    comparison = run_comparison(repo_path, client)

    for changed_name, result in comparison.items():
        print(f"\n{'=' * 70}")
        print(f"CHANGED: {changed_name}")
        print(f"{'=' * 70}")

        print(f"\n--- CONTEXT-AWARE ({len(result['context_aware'])} issue(s)) ---")
        for issue in result["context_aware"]:
            print(f"  [{issue.get('severity', '?')}] {issue.get('issue', '?')}")
            print(f"    {issue.get('explanation', '')}")

        print(f"\n--- DIFF-ONLY BASELINE ({len(result['diff_only'])} issue(s)) ---")
        for issue in result["diff_only"]:
            print(f"  [{issue.get('severity', '?')}] {issue.get('issue', '?')}")
            print(f"    {issue.get('explanation', '')}")
