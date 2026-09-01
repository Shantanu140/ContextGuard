"""Semantic code retrieval for ContextGuard's Python prototype.

This module turns each discoverable function or immediate class method into a
small code chunk. It then uses embeddings and an in-memory FAISS index to find
code that is semantically related to a changed function. Retrieval supplies
evidence for later LLM reasoning; it does not decide whether code is buggy.
"""

import ast
import os

import numpy as np

from graph_builder import build_context


MODEL_NAME = "all-MiniLM-L6-v2"


def _module_name_from_path(file_path):
    """Return the filename without its directory or .py extension."""
    return os.path.splitext(os.path.basename(file_path))[0]


def _function_nodes(tree):
    """Yield module functions and immediate methods with their class name."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            yield node, None
        elif isinstance(node, ast.ClassDef):
            for class_child in node.body:
                if isinstance(class_child, ast.FunctionDef):
                    yield class_child, node.name


def chunk_python_file(file_path, repo_path=None):
    """Return one metadata-rich source chunk for each supported function."""
    try:
        with open(file_path, "r", encoding="utf-8") as source_file:
            source_lines = source_file.readlines()
        tree = ast.parse("".join(source_lines), filename=file_path)
    except (FileNotFoundError, UnicodeDecodeError, SyntaxError) as error:
        print(f"  [warning] skipping {file_path}: {error}")
        return []

    module_name = _module_name_from_path(file_path)
    stored_path = os.path.relpath(file_path, repo_path) if repo_path else file_path
    chunks = []

    for node, class_name in _function_nodes(tree):
        qualified_name = node.name
        if class_name is not None:
            qualified_name = f"{class_name}.{node.name}"

        source = "".join(source_lines[node.lineno - 1 : node.end_lineno])
        full_name = f"{module_name}.{qualified_name}"
        chunks.append(
            {
                "id": full_name,
                "file_path": stored_path,
                "qualified_name": full_name,
                "source": source,
            }
        )

    return chunks


def chunk_repository(repo_path):
    """Collect supported Python function chunks from every file in a repository."""
    chunks = []
    for current_folder, _subfolders, filenames in os.walk(repo_path):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                file_path = os.path.join(current_folder, filename)
                chunks.extend(chunk_python_file(file_path, repo_path))
    return chunks


def load_embedding_model(model_name=MODEL_NAME):
    """Load the model only when real embeddings are requested."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def build_faiss_index(chunks, model=None):
    """Embed chunks and place normalized vectors in an in-memory FAISS index."""
    if not chunks:
        return {"index": None, "chunks": [], "model": model}

    if model is None:
        model = load_embedding_model()

    embeddings = np.asarray(
        model.encode(
            [chunk["source"] for chunk in chunks],
            normalize_embeddings=True,
        ),
        dtype="float32",
    )

    import faiss

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return {"index": index, "chunks": chunks, "model": model}


def retrieve_related_chunks(query_source, search_data, top_k=5, exclude_ids=None):
    """Return the best semantic matches, excluding requested chunk IDs."""
    index = search_data["index"]
    chunks = search_data["chunks"]
    if index is None or not chunks:
        return []

    exclude_ids = set(exclude_ids or [])
    query_embedding = np.asarray(
        search_data["model"].encode([query_source], normalize_embeddings=True),
        dtype="float32",
    )
    scores, positions = index.search(query_embedding, len(chunks))

    matches = []
    for score, position in zip(scores[0], positions[0]):
        if position < 0:
            continue
        chunk = chunks[int(position)]
        if chunk["id"] in exclude_ids:
            continue
        match = dict(chunk)
        match["score"] = float(score)
        matches.append(match)
        if len(matches) == top_k:
            break
    return matches


def get_context(repo_path, max_hops=2, top_k=5, model=None):
    """Combine graph context with separately-ranked semantic code context."""
    graph_result = build_context(repo_path, max_hops=max_hops)
    chunks = chunk_repository(repo_path)
    chunk_by_id = {chunk["id"]: chunk for chunk in chunks}
    search_data = build_faiss_index(chunks, model=model)

    semantic_context = {}
    for changed_name in graph_result["changed_functions"]:
        changed_chunk = chunk_by_id.get(changed_name)
        if changed_chunk is None:
            semantic_context[changed_name] = []
            continue
        semantic_context[changed_name] = retrieve_related_chunks(
            changed_chunk["source"],
            search_data,
            top_k=top_k,
            exclude_ids={changed_name},
        )

    return {
        "changed_functions": graph_result["changed_functions"],
        "graph_context": graph_result["related_functions"],
        "semantic_context": semantic_context,
    }
