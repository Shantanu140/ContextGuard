"""
Day 14 -- ContextGuard project
--------------------------------
Goal: actually SEE the dependency graph, with the changed function and
its nearby neighbors color-coded by distance -- a real visual you could
put directly into hackathon slides.

Install first (only needs to be done once):
    pip install matplotlib
"""

import matplotlib.pyplot as plt
import networkx as nx

from day8_function_calls import find_functions_with_calls
from day11_adjacency_list import build_adjacency_list
from day12_networkx_graph import build_networkx_graph
from day13_bfs_context import find_within_hops


def get_node_colors(graph, start_node, max_hops=2):
    """
    Returns a list of colors, one per node in the graph, based on how
    far each node is from start_node:
      - the start node itself: red
      - 1 hop away: orange
      - 2 hops away: gold (yellow-ish)
      - anything farther, or unconnected: light gray
    """
    distances = find_within_hops(graph, start_node, max_hops=max_hops)

    color_by_distance = {
        0: "red",
        1: "orange",
        2: "gold",
    }

    colors = []
    for node in graph.nodes():
        if node == start_node:
            colors.append(color_by_distance[0])
        elif node in distances:
            colors.append(color_by_distance.get(distances[node], "lightgray"))
        else:
            colors.append("lightgray")

    return colors


def visualize_graph(graph, start_node, output_path="dependency_graph.png"):
    # spring_layout runs a physics-like simulation: connected nodes pull
    # toward each other, all nodes push apart -- this decides WHERE each
    # node is drawn so the picture is readable.
    # seed=42 makes the layout reproducible -- same input, same picture,
    # every time you run this (otherwise it would look slightly
    # different each run).
    positions = nx.spring_layout(graph, seed=42)

    colors = get_node_colors(graph, start_node)

    plt.figure(figsize=(8, 6))

    nx.draw(
        graph,
        positions,
        with_labels=True,        # show each function's name on its node
        node_color=colors,
        node_size=1800,
        font_size=9,
        arrows=True,              # show arrowheads, since this is a directed graph
        edge_color="gray",
    )

    plt.title(f"Dependency graph (highlighted from '{start_node}')")

    # Save to a file so you can drop it straight into slides...
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved graph image to {output_path}")

    # ...and also open it in a window right now, so you can see it immediately.
    plt.show()


if __name__ == "__main__":
    target_file = "day3_function_class.py"

    functions = find_functions_with_calls(target_file)
    adjacency_list = build_adjacency_list(functions)
    graph = build_networkx_graph(adjacency_list)

    visualize_graph(graph, start_node="param_count")
