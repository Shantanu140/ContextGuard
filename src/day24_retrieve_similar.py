"""
Day 24 -- given a changed function, find its top-k most similar chunks.
"""

from sentence_transformers import util

from day22_chunk_codebase import chunk_repo
from day23_embed_chunks import embed_chunks, model


def retrieve_similar(query_text: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Returns the top_k chunks most similar in meaning to query_text."""
    query_vector = model.encode([query_text])[0]
    chunk_vectors = [c["embedding"] for c in chunks]

    scores = util.cos_sim(query_vector, chunk_vectors)[0]

    scored_chunks = list(zip(chunks, scores.tolist()))
    scored_chunks.sort(key=lambda pair: pair[1], reverse=True)

    return scored_chunks[:top_k]


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # <-- change this to your real path

    chunks = chunk_repo(repo_path)
    chunks = embed_chunks(chunks)

    # Pick any chunk's text as the "query" -- simulating "this changed function".
    query_chunk = chunks[0]
    results = retrieve_similar(query_chunk["text"], chunks, top_k=5)

    print(f"Query: {query_chunk['name']}\n")
    print("Top 5 similar chunks:")
    for chunk, score in results:
        print(f"  {score:.3f}  {chunk['name']}")
