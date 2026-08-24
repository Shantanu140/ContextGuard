"""
Day 17 -- ContextGuard project
--------------------------------
Goal: build the REAL, whole-repo dependency graph -- combining every
file's functions and calls into one graph, using qualified names
("module.function") so same-named functions in different files don't
collide, and resolving calls across file boundaries using Day 16's
import parsing.
"""

import os

import networkx as nx

from day8_function_calls import find_functions_with_calls
from day15_test_on_repo import find_python_files
from day16_cross_file_imports import parse_imports


def module_name_from_path(file_path):
    """Turns 'day8_function_calls.py' into 'day8_function_calls'."""
    filename = os.path.basename(file_path)
    return os.path.splitext(filename)[0]


def build_repo_graph(folder_path):
    """
    Builds one networkx DiGraph covering every function in every .py
    file under folder_path, with cross-file call edges resolved via
    imports where possible.
    """
    python_files = find_python_files(folder_path)

    # First pass: gather everything we need PER FILE before building
    # any edges -- we need to know about every module before we can
    # correctly resolve imports that point to each other.
    file_data = {}  # module_name -> {"functions": [...], "import_map": {...}}

    for file_path in python_files:
        module_name = module_name_from_path(file_path)
        functions = find_functions_with_calls(file_path)
        import_map = parse_imports(file_path)
        file_data[module_name] = {
            "functions": functions,
            "import_map": import_map,
        }

    known_modules = set(file_data.keys())

    graph = nx.DiGraph()

    # Second pass: now that we know every module and its functions,
    # actually build the graph and resolve calls.
    for module_name, data in file_data.items():
        functions = data["functions"]
        import_map = data["import_map"]
        local_function_names = {f.name for f in functions}

        for func in functions:
            source_node = f"{module_name}.{func.name}"
            graph.add_node(source_node)

            for call_name in func.calls:

                if call_name in local_function_names:
                    # Case 1: defined in the same file.
                    target_node = f"{module_name}.{call_name}"
                    graph.add_edge(source_node, target_node)

                elif call_name in import_map:
                    # Case 2: imported from somewhere -- but only add an
                    # edge if that source module is actually part of
                    # THIS repo (not an external library we don't have).
                    source_module = import_map[call_name]
                    if source_module in known_modules:
                        target_node = f"{source_module}.{call_name}"
                        graph.add_edge(source_node, target_node)
                    # else: imported from outside this repo (e.g. a real
                    # library) -- Case 3, external, skip it.

                # else: Case 3, external/unknown -- skip it.

    return graph


if __name__ == "__main__":
    # Try this on your OWN project first -- it now has real cross-file
    # imports (day9 imports from day8, day14 imports from day8/11/12/13, etc).
    repo_path = r"E:\Context Guard\ContextGuard\src"

    graph = build_repo_graph(repo_path)

    print(f"Repo-wide graph: {graph.number_of_nodes()} functions, {graph.number_of_edges()} edges\n")

    # Specifically highlight cross-file edges, since those are the
    # genuinely new thing today -- an edge whose two nodes have
    # DIFFERENT module prefixes.
    print("Cross-file edges found:")
    cross_file_count = 0
    for source_node, target_node in graph.edges():
        source_module = source_node.split(".")[0]
        target_module = target_node.split(".")[0]
        if source_module != target_module:
            print(f"  {source_node}  -->  {target_node}")
            cross_file_count += 1

    if cross_file_count == 0:
        print("  (none found)")
