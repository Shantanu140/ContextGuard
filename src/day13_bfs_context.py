"""
Day 13 -- ContextGuard project
--------------------------------
Goal: given one function (e.g. one that was just changed), find every
other function within N hops of it in the dependency graph -- counting
BOTH directions: what it calls, and what calls it.

This is a direct application of BFS, exactly as you've used it in DSA --
just applied to a real dependency graph instead of a textbook grid or tree.
"""

from collections import deque

from day8_function_calls import find_functions_with_calls
from day11_adjacency_list import build_adjacency_list
from day12_networkx_graph import build_networkx_graph


def find_within_hops(graph, start_node, max_hops=2):
    """
    Returns a dictionary mapping every function within `max_hops` steps
    of `start_node` to its exact distance (1, 2, ... up to max_hops).
    `start_node` itself is not included in the result.

    Counts BOTH successors (what a function calls) and predecessors
    (what calls it) as valid steps -- we care about both directions
    of influence for code review context.
    """

    # visited tracks every node we've reached so far, and how many hops
    # it took to get there. Starting node is distance 0 from itself.
    visited = {start_node: 0}

    # deque works like a list, but is efficient for adding to one end
    # and removing from the other -- exactly what a BFS queue needs.
    queue = deque([start_node])

    while queue:
        current_node = queue.popleft()  # take the next node to expand
        current_distance = visited[current_node]

        # Don't expand past our hop limit -- once we're already at
        # max_hops, there's no point looking at this node's neighbors,
        # since they'd be max_hops + 1 away.
        if current_distance >= max_hops:
            continue

        # Gather neighbors in BOTH directions: what this function calls,
        # and what calls this function.
        outgoing = list(graph.successors(current_node)) if current_node in graph else []
        incoming = list(graph.predecessors(current_node)) if current_node in graph else []
        neighbors = outgoing + incoming

        for neighbor in neighbors:
            if neighbor not in visited:
                visited[neighbor] = current_distance + 1
                queue.append(neighbor)

    # Remove the starting node itself from the result -- we only want
    # to report OTHER functions near it, not itself.
    del visited[start_node]

    return visited


if __name__ == "__main__":
    target_file = "day3_function_class.py"

    functions = find_functions_with_calls(target_file)
    adjacency_list = build_adjacency_list(functions)
    graph = build_networkx_graph(adjacency_list)

    start_function = "param_count"
    nearby = find_within_hops(graph, start_function, max_hops=2)

    print(f"Functions within 2 hops of '{start_function}':")
    if not nearby:
        print("  (none found)")
    else:
        # Sort by distance so closer functions are listed first.
        for name, distance in sorted(nearby.items(), key=lambda pair: pair[1]):
            print(f"  {name} -- {distance} hop(s) away")
