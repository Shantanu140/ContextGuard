"""
Day 22 -- ContextGuard project
--------------------------------
Goal: extract the REAL source text of every function/method in a repo --
not the placeholder strings we've used since Day 7 -- so we have actual
content to embed starting tomorrow.
"""

import ast

from day15_test_on_repo import find_python_files


def make_chunk(node, source_code, class_name):
    """
    Builds one chunk dictionary for a single function/method node.
    """
    qualified_name = f"{class_name}.{node.name}" if class_name else node.name

    # This is today's key new tool: hand it the ORIGINAL file's full
    # text plus any node from that file's tree, and it gives back the
    # exact original text that node covers -- signature, body, comments
    # inside it, everything -- exactly as written.
    source_text = ast.get_source_segment(source_code, node)

    # ast.get_docstring() is a small built-in helper that specifically
    # pulls out a function's docstring (the """...""" right under its
    # signature), or returns None if there isn't one.
    docstring = ast.get_docstring(node)

    return {
        "name": qualified_name,
        "text": source_text,
        "docstring": docstring,
    }


def chunk_file(file_path):
    """
    Returns a list of chunk dictionaries for every function/method in
    one file.
    """
    with open(file_path, "r") as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as error:
        print(f"  [warning] skipping {file_path}: {error}")
        return []

    chunks = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            chunks.append(make_chunk(node, source_code, class_name=None))
        elif isinstance(node, ast.ClassDef):
            for class_child in node.body:
                if isinstance(class_child, ast.FunctionDef):
                    chunks.append(make_chunk(class_child, source_code, node.name))

    return chunks


def chunk_repo(repo_path):
    """
    Returns a list of chunk dictionaries for every function/method in
    every .py file in the given repo.
    """
    all_chunks = []
    for file_path in find_python_files(repo_path):
        all_chunks.extend(chunk_file(file_path))
    return all_chunks


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # update to your real path

    chunks = chunk_repo(repo_path)

    print(f"Found {len(chunks)} function/method chunks.\n")

    # Show the first 2 chunks in full, so you can see exactly what
    # real extracted source text looks like.
    for chunk in chunks[:2]:
        print(f"--- {chunk['name']} ---")
        print(f"Docstring: {chunk['docstring']!r}")
        print("Text:")
        print(chunk["text"])
        print()
