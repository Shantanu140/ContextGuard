"""
ContextGuard -- graph_builder.py
----------------------------------
This module packages together everything built across Days 7-18:
  - AST-based function/method discovery, with proper class scoping (Day 7, 18)
  - Cross-file import resolution (Day 16)
  - A whole-repo dependency graph with collision-proof qualified names (Day 17)
  - self.method() resolution within the same class (Day 18)
  - Mapping a real git diff to the exact function(s) it changed (Day 9)
  - BFS traversal to gather nearby context (Day 13)

Everything else in the project should be able to get what it needs from
ONE function: build_context(repo_path). Nothing outside this file needs
to know HOW any of the above actually works.
"""

import ast
import os
import re
import subprocess
from collections import deque

import networkx as nx

from day3_function_class import Function


# ---------------------------------------------------------------------------
# Internal helpers (not meant to be used directly from outside this file --
# by convention, a leading underscore signals "internal detail, may change").
# ---------------------------------------------------------------------------

def _module_name_from_path(file_path):
    filename = os.path.basename(file_path)
    return os.path.splitext(filename)[0]


def _find_python_files(folder_path):
    python_files = []
    for current_folder, _subfolders, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith(".py"):
                python_files.append(os.path.join(current_folder, filename))
    return python_files


def _get_call_names(function_node):
    """Ordinary (non-self) calls made inside this function/method."""
    call_names = []
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Skip self.X() here -- those are handled separately below,
                # so they don't get double-counted as ordinary calls too.
                is_self_call = (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                )
                if not is_self_call:
                    call_names.append(node.func.attr)
    return call_names


def _get_self_call_names(function_node):
    """Calls made specifically as self.X() -- resolved only within the same class."""
    self_calls = []
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                self_calls.append(func.attr)
    return self_calls


def _parse_imports(tree):
    """Maps locally-used names to the module they were imported from."""
    import_map = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                local_name = alias.asname or alias.name
                import_map[local_name] = node.module
    return import_map


def _parse_file(file_path):
    """
    Returns (functions, import_map) for one file: every function/method
    found (with class scoping and self-calls correctly separated), plus
    that file's import map. Fails gracefully on unreadable/unparseable files.
    """
    try:
        with open(file_path, "r") as f:
            source_code = f.read()
        tree = ast.parse(source_code, filename=file_path)
    except (FileNotFoundError, UnicodeDecodeError, SyntaxError) as error:
        print(f"  [warning] skipping {file_path}: {error}")
        return [], {}

    functions_found = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions_found.append(_build_function(node, class_name=None))
        elif isinstance(node, ast.ClassDef):
            for class_child in node.body:
                if isinstance(class_child, ast.FunctionDef):
                    functions_found.append(_build_function(class_child, node.name))

    import_map = _parse_imports(tree)
    return functions_found, import_map


def _build_function(node, class_name):
    name = node.name
    params = [arg.arg for arg in node.args.args]
    body_placeholder = f"(defined at line {node.lineno})"
    return Function(
        name, params, body_placeholder,
        calls=_get_call_names(node),
        start_line=node.lineno,
        end_line=node.end_lineno,
        class_name=class_name,
        self_calls=_get_self_call_names(node),
    )


def _build_repo_graph(repo_path):
    """
    Builds the whole-repo graph. Every node is a fully-qualified name:
        "module.function"            for standalone functions
        "module.ClassName.method"    for methods
    which avoids collisions across BOTH different files (Day 17) and
    different classes within a file (Day 18).

    Also returns a lookup dict: qualified_name -> Function object, so
    callers can check line ranges (for diff mapping) without re-parsing.
    """
    python_files = _find_python_files(repo_path)

    file_data = {}  # module_name -> {"functions": [...], "import_map": {...}, "file_path": ...}
    for file_path in python_files:
        module_name = _module_name_from_path(file_path)
        functions, import_map = _parse_file(file_path)
        file_data[module_name] = {
            "functions": functions,
            "import_map": import_map,
            "file_path": file_path,
        }

    known_modules = set(file_data.keys())
    graph = nx.DiGraph()
    function_lookup = {}  # qualified_name -> Function

    for module_name, data in file_data.items():
        functions = data["functions"]
        import_map = data["import_map"]
        standalone_names = {f.name for f in functions if f.class_name is None}
        methods_by_class = {}
        for f in functions:
            if f.class_name:
                methods_by_class.setdefault(f.class_name, set()).add(f.name)

        for func in functions:
            qualified = f"{module_name}.{func.qualified_name()}"
            function_lookup[qualified] = (func, data["file_path"])
            graph.add_node(qualified)

            # Ordinary calls: same-file standalone function, or cross-file import.
            for call_name in func.calls:
                if call_name in standalone_names:
                    graph.add_edge(qualified, f"{module_name}.{call_name}")
                elif call_name in import_map and import_map[call_name] in known_modules:
                    graph.add_edge(qualified, f"{import_map[call_name]}.{call_name}")

            # self.X() calls: only within the same class, same file.
            if func.class_name:
                siblings = methods_by_class.get(func.class_name, set())
                for self_call_name in func.self_calls:
                    if self_call_name in siblings:
                        target = f"{module_name}.{func.class_name}.{self_call_name}"
                        graph.add_edge(qualified, target)

    return graph, function_lookup


def _get_changed_line_ranges(repo_path):
    """Returns {relative_file_path: [changed line numbers]} from git diff -U0."""
    result = subprocess.run(
        ["git", "diff", "-U0", "--no-color"],
        cwd=repo_path, capture_output=True, text=True, check=True,
    )
    changed = {}
    current_file = None
    file_pattern = re.compile(r"^\+\+\+ b/(.*)$")
    hunk_pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for line in result.stdout.splitlines():
        file_match = file_pattern.match(line)
        if file_match:
            filename = file_match.group(1)
            current_file = None if filename == "/dev/null" else filename
            if current_file:
                changed.setdefault(current_file, [])
            continue
        hunk_match = hunk_pattern.match(line)
        if hunk_match and current_file:
            new_start = int(hunk_match.group(1))
            new_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
            if new_count > 0:
                changed[current_file].extend(range(new_start, new_start + new_count))
    return changed


def _find_within_hops(graph, start_node, max_hops=2):
    """BFS in both directions, same as Day 13."""
    visited = {start_node: 0}
    queue = deque([start_node])
    while queue:
        current = queue.popleft()
        distance = visited[current]
        if distance >= max_hops:
            continue
        neighbors = list(graph.successors(current)) + list(graph.predecessors(current))
        for neighbor in neighbors:
            if neighbor not in visited:
                visited[neighbor] = distance + 1
                queue.append(neighbor)
    del visited[start_node]
    return visited


# ---------------------------------------------------------------------------
# The ONE function everything else in ContextGuard should actually call.
# ---------------------------------------------------------------------------

def build_context(repo_path, max_hops=2):
    """
    Given a repo with uncommitted changes, returns a dictionary with:
      "changed_functions": list of qualified names directly touched by the diff
      "related_functions": dict of {qualified_name: hop_distance} for nearby context
      "graph": the full networkx DiGraph, in case a caller needs it directly

    This is the single entry point later phases (retrieval, LLM reasoning)
    should use -- they never need to know about AST parsing, imports, or BFS.
    """
    graph, function_lookup = _build_repo_graph(repo_path)
    changed_lines_by_file = _get_changed_line_ranges(repo_path)

    changed_functions = []
    for relative_path, line_numbers in changed_lines_by_file.items():
        module_name = _module_name_from_path(relative_path)
        for qualified_name, (func, _file_path) in function_lookup.items():
            if not qualified_name.startswith(module_name + "."):
                continue
            for line_number in line_numbers:
                if func.contains_line(line_number):
                    changed_functions.append(qualified_name)
                    break

    related_functions = {}
    for changed_name in changed_functions:
        if changed_name not in graph:
            continue
        nearby = _find_within_hops(graph, changed_name, max_hops=max_hops)
        for name, distance in nearby.items():
            if name not in related_functions or distance < related_functions[name]:
                related_functions[name] = distance

    return {
        "changed_functions": changed_functions,
        "related_functions": related_functions,
        "graph": graph,
    }


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard"  # update to your real path

    context = build_context(repo_path)

    print(f"Changed functions: {context['changed_functions']}")
    print("\nRelated functions (within 2 hops):")
    for name, distance in sorted(context["related_functions"].items(), key=lambda p: p[1]):
        print(f"  {name} -- {distance} hop(s) away")
