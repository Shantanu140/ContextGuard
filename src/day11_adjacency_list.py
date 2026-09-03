"""
Day 11 -- ContextGuard project
--------------------------------
Goal: represent the "which function calls which" relationships as a real
directed graph, using an adjacency list -- and finally filter out calls
to built-ins/libraries that aren't part of our own codebase, which we
flagged as a known limitation back on Day 8/10.
"""

from day8_function_calls import find_functions_with_calls


def build_adjacency_list(functions):
    """
    Given a list of Function objects, returns a dictionary (the adjacency
    list) mapping each function's name to a list of the OTHER functions
    it calls -- but only counting calls to functions that are actually
    defined in this same set (i.e. real, local dependencies).
    """

    # First, collect the names of every function we actually found and
    # can reason about. Using a set here (remember Day 2!) because we
    # only care "is this name one of ours," not counting or ordering.
    known_function_names = {f.name for f in functions}

    graph = {}

    for func in functions:
        # Keep only the calls that point to a function we actually know
        # about -- this drops things like .split() or sorted(), which
        # aren't functions we defined ourselves.
        local_calls = [
            called_name
            for called_name in func.calls
            if called_name in known_function_names
        ]

        graph[func.name] = local_calls

    return graph


def print_graph(graph):
    """A small helper to print the adjacency list in a readable way."""
    for function_name, calls in graph.items():
        if calls:
            calls_joined = ", ".join(calls)
            print(f"  {function_name} -> {calls_joined}")
        else:
            print(f"  {function_name} -> (calls nothing local)")


if __name__ == "__main__":
    target_file = "day2_count_words.py"

    functions = find_functions_with_calls(target_file)
    graph = build_adjacency_list(functions)

    print(f"Dependency graph for {target_file}:")
    print_graph(graph)
