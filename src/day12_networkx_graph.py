"""
Day 12 -- ContextGuard project
--------------------------------
Goal: convert our own hand-built adjacency list (Day 11) into a real
networkx DiGraph, and use it to answer a couple of basic graph questions
for free, instead of writing that logic ourselves.

Install first (only needs to be done once on your laptop):
    pip install networkx
"""

import networkx as nx

from day8_function_calls import find_functions_with_calls
from day11_adjacency_list import build_adjacency_list


def build_networkx_graph(adjacency_list):
    """
    Converts a plain adjacency-list dictionary (like the one from Day 11)
    into a real networkx DiGraph object.
    """
    graph = nx.DiGraph()

    for function_name, called_names in adjacency_list.items():
        # Even if a function calls nothing local, we still want it to
        # exist as a node in the graph (so it shows up when we ask
        # "what functions are there," even in isolation).
        graph.add_node(function_name)

        for called_name in called_names:
            # add_edge automatically adds both endpoints as nodes too,
            # if they aren't already there -- so this line alone would
            # actually be enough, but add_node above makes isolated
            # functions (that call nothing) explicit too.
            graph.add_edge(function_name, called_name)

    return graph


if __name__ == "__main__":
    target_file = "day3_function_class.py"

    functions = find_functions_with_calls(target_file)
    adjacency_list = build_adjacency_list(functions)
    graph = build_networkx_graph(adjacency_list)

    # A few basic questions networkx can now answer for us, with no
    # manual loop-writing on our part:

    print(f"Graph for {target_file}")
    print(f"  Total functions (nodes): {graph.number_of_nodes()}")
    print(f"  Total call relationships (edges): {graph.number_of_edges()}")

    print("\nAll functions in the graph:")
    for node in graph.nodes():
        print(f"  - {node}")

    print("\nWhat does 'summary' directly call?")
    if "summary" in graph:
        # successors() gives us every node this one has an outgoing edge to --
        # i.e. everything it directly calls.
        direct_calls = list(graph.successors("summary"))
        print(f"  {direct_calls}")

    print("\nWhat directly calls 'param_count'?")
    if "param_count" in graph:
        # predecessors() is the reverse: everything with an edge POINTING
        # INTO this node -- i.e. everything that calls it.
        callers = list(graph.predecessors("param_count"))
        print(f"  {callers}")
