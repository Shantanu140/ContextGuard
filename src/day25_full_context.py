"""
Day 25 -- combine graph context (Phase 2) + retrieval context (Phase 3)
into one unified bundle per changed function.
"""

from graph_builder import build_context
from day13_bfs_context import find_within_hops
from day22_chunk_codebase import chunk_repo
from day23_embed_chunks import embed_chunks
from day24_retrieve_similar import retrieve_similar


def build_full_context(repo_path: str, top_k: int = 5, max_hops: int = 2) -> dict:
    """
    For each changed function, returns:
      - graph_neighbors: {name: hop_distance} -- SPECIFIC to this function
      - similar_chunks: [(chunk, score), ...] from Phase 3
    """
    graph_result = build_context(repo_path, max_hops=max_hops)
    graph = graph_result["graph"]
    chunks = embed_chunks(chunk_repo(repo_path))
    chunk_by_name = {c["name"]: c for c in chunks}

    bundle = {}
    for changed_name in graph_result["changed_functions"]:
        # BUG FIX: previously reused graph_result["related_functions"],
        # which is already merged across ALL changed functions -- every
        # entry showed identical neighbors regardless of which function
        # actually changed. Re-running BFS per function fixes this.
        neighbors = find_within_hops(graph, changed_name, max_hops) if changed_name in graph else {}

        query_chunk = chunk_by_name.get(changed_name)
        similar = retrieve_similar(query_chunk["text"], chunks, top_k) if query_chunk else []

        bundle[changed_name] = {
            "graph_neighbors": neighbors,
            "similar_chunks": [(c["name"], score) for c, score in similar],
        }

    return bundle


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # change to your real path

    bundle = build_full_context(repo_path)

    for changed_name, context in bundle.items():
        print(f"\nChanged: {changed_name}")
        print("  Graph neighbors:", context["graph_neighbors"])
        print("  Similar chunks:")
        for name, score in context["similar_chunks"]:
            print(f"    {score:.3f}  {name}")
