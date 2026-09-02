"""
contextguard/context.py -- THE single public entry point. Everything
outside this package should only ever need build_full_context().
"""

from contextguard.graph import build_repo_graph, find_within_hops
from contextguard.diff import find_changed_functions
from contextguard.retrieval import chunk_repo, embed_chunks, build_faiss_index, retrieve_top_k


def build_full_context(repo_path, top_k=5, max_hops=2):
    """
    Returns:
        {
          "qualified_function_name": {
              "graph_neighbors": {name: hop_distance},
              "similar_chunks": [(name, score), ...],
          },
          ...
        }
    One entry per function touched by the current uncommitted changes.
    """
    graph, function_lookup = build_repo_graph(repo_path)
    changed_functions = find_changed_functions(repo_path, function_lookup)

    chunks = embed_chunks(chunk_repo(repo_path))
    index = build_faiss_index(chunks)
    chunk_by_name = {c["name"]: c for c in chunks}

    bundle = {}
    for changed_name in changed_functions:
        neighbors = find_within_hops(graph, changed_name, max_hops) if changed_name in graph else {}

        query_chunk = chunk_by_name.get(changed_name)
        similar = retrieve_top_k(query_chunk["text"], index, chunks, top_k) if query_chunk else []

        bundle[changed_name] = {
            "graph_neighbors": neighbors,
            "similar_chunks": [(c["name"], score) for c, score in similar],
        }

    return bundle


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\contextguard"  # change to your real path
    bundle = build_full_context(repo_path)
    for name, ctx in bundle.items():
        print(f"\nChanged: {name}")
        print("  Graph neighbors:", ctx["graph_neighbors"])
        print("  Similar chunks:")
        for chunk_name, score in ctx["similar_chunks"]:
            print(f"    {score:.3f}  {chunk_name}")
