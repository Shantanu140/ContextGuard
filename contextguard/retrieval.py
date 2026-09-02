"""
contextguard/retrieval.py -- chunking the codebase, embedding chunks,
and FAISS-based similarity search. Consolidates Days 21-24, plus the
FAISS piece (Day 28) that was originally skipped.
"""

import ast

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from contextguard.graph import _module_name, find_python_files

_model = None


def get_model():
    """Loads the embedding model once, reused across calls."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def chunk_file(file_path):
    module_name = _module_name(file_path)
    try:
        source = open(file_path, "r").read()
        tree = ast.parse(source, filename=file_path)
    except (FileNotFoundError, UnicodeDecodeError, SyntaxError) as error:
        print(f"  [warning] skipping {file_path}: {error}")
        return []

    def make_chunk(node, class_name):
        name = f"{module_name}.{class_name}.{node.name}" if class_name else f"{module_name}.{node.name}"
        return {
            "name": name,
            "text": ast.get_source_segment(source, node),
            "docstring": ast.get_docstring(node),
        }

    chunks = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            chunks.append(make_chunk(node, None))
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    chunks.append(make_chunk(child, node.name))
    return chunks


def chunk_repo(repo_path):
    chunks = []
    for file_path in find_python_files(repo_path):
        chunks.extend(chunk_file(file_path))
    return chunks


def embed_chunks(chunks):
    """Adds an 'embedding' vector to each chunk."""
    texts = [c["text"] for c in chunks]
    vectors = get_model().encode(texts)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def build_faiss_index(chunks):
    """
    Builds a FAISS index over chunk embeddings, using inner product on
    L2-normalized vectors -- mathematically equivalent to cosine similarity,
    but FAISS's actual purpose (and why we use it over brute-force) is
    speed: it scales to large codebases without comparing every pair by hand.
    """
    vectors = np.array([c["embedding"] for c in chunks]).astype("float32")
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def retrieve_top_k(query_text, index, chunks, top_k=5):
    """Returns [(chunk, score), ...] for the top_k chunks most similar to query_text."""
    query_vector = get_model().encode([query_text]).astype("float32")
    faiss.normalize_L2(query_vector)
    scores, indices = index.search(query_vector, top_k)
    return [(chunks[i], float(scores[0][pos])) for pos, i in enumerate(indices[0])]
