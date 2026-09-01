"""
Day 25 -- combine graph context (Phase 2) + retrieval context (Phase 3)
into one unified bundle per changed function.
"""

from graph_builder import build_context
from day22_chunk_codebase import chunk_repo
from day23_embed_chunks import embed_chunks
from day24_retrieve_similar import retrieve_similar


def build_full_context(repo_path: str, top_k: int = 5, max_hops: int = 2) -> dict:
    """
    For each changed function, returns:
      - graph_neighbors: {name: hop_distance} from Phase 2
      - similar_chunks: [(chunk, score), ...] from Phase 3
    """
    graph_result = build_context(repo_path, max_hops=max_hops)
    chunks = embed_chunks(chunk_repo(repo_path))
    chunk_by_name = {c["name"]: c for c in chunks}

    bundle = {}
    for changed_name in graph_result["changed_functions"]:
        query_chunk = chunk_by_name.get(changed_name)
        similar = retrieve_similar(query_chunk["text"], chunks, top_k) if query_chunk else []

        bundle[changed_name] = {
            "graph_neighbors": {
                name: dist for name, dist in graph_result["related_functions"].items()
            },
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
