"""
Day 22 -- ContextGuard project
--------------------------------
Goal: extract the REAL source text of every function/method in a repo --
not the placeholder strings we've used since Day 7 -- so we have actual
content to embed starting tomorrow.
"""

import ast
import os

from day15_test_on_repo import find_python_files


def make_chunk(node, source_code, class_name, module_name):
    """
    Builds one chunk dictionary for a single function/method node.
    Name format matches graph_builder.py: "module.function" or
    "module.ClassName.method" -- required so chunk names and graph
    node names can be matched directly, with no collisions across files.
    """
    if class_name:
        qualified_name = f"{module_name}.{class_name}.{node.name}"
    else:
        qualified_name = f"{module_name}.{node.name}"

    source_text = ast.get_source_segment(source_code, node)
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
    module_name = os.path.splitext(os.path.basename(file_path))[0]

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
            chunks.append(make_chunk(node, source_code, None, module_name))
        elif isinstance(node, ast.ClassDef):
            for class_child in node.body:
                if isinstance(class_child, ast.FunctionDef):
                    chunks.append(make_chunk(class_child, source_code, node.name, module_name))

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
    repo_path = r"E:\ContextGuard\src"  # update to your real path

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
