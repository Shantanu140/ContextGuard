"""
Day 15 -- ContextGuard project
--------------------------------
Goal: run everything we've built so far (Days 7-14) across EVERY .py
file in a real repository, not just our own small scripts -- to catch
crashes, weird edge cases, or bad assumptions before we build further
on top of this foundation.
"""

import os

from day8_function_calls import find_functions_with_calls
from day11_adjacency_list import build_adjacency_list
from day12_networkx_graph import build_networkx_graph


def find_python_files(folder_path):
    """
    Returns a list of full paths to every .py file inside folder_path,
    including files inside nested subfolders.
    """
    python_files = []

    # os.walk visits folder_path, then every folder inside it, one at a
    # time. For each one, it gives us: the current folder's path, a list
    # of subfolder names inside it, and a list of filenames inside it.
    for current_folder, subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(current_folder, filename)
                python_files.append(full_path)

    return python_files


def test_pipeline_on_repo(folder_path):
    """
    Runs the function-finding + graph-building pipeline on every .py
    file in folder_path, and reports totals plus any files that caused
    warnings (handled gracefully thanks to Day 10's error handling).
    """
    python_files = find_python_files(folder_path)
    print(f"Found {len(python_files)} Python file(s) in {folder_path}\n")

    total_functions = 0
    total_edges = 0

    for file_path in python_files:
        functions = find_functions_with_calls(file_path)
        adjacency_list = build_adjacency_list(functions)
        graph = build_networkx_graph(adjacency_list)

        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()

        total_functions += node_count
        total_edges += edge_count

        print(f"  {file_path}")
        print(f"    functions: {node_count}, local call edges: {edge_count}")

    print(f"\nTotals across repo: {total_functions} functions, {total_edges} local call edges")


if __name__ == "__main__":
    # Point this at a real repo folder you've downloaded (see the
    # instructions for a few good small options to try).
    repo_path = r"E:\Sample Repos\agent-tutorial-master\agent-tutorial-master"
    test_pipeline_on_repo(repo_path)
