"""
Day 23 -- embed each function chunk into a vector for similarity search.
"""

from typing import Any

from sentence_transformers import SentenceTransformer

from day22_chunk_codebase import chunk_repo

model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Adds an 'embedding' vector to each chunk, based on its source text."""
    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # update to your real path

    chunks = chunk_repo(repo_path)
    chunks = embed_chunks(chunks)

    print(f"Embedded {len(chunks)} chunks.")
    print(f"Embedding size for '{chunks[0]['name']}': {len(chunks[0]['embedding'])}")
