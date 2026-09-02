"""
contextguard/graph.py -- AST parsing, the Function class, and the
whole-repo dependency graph. Consolidates Days 3, 7-9, 13, 16-19.
"""

import ast
import os
from collections import deque

import networkx as nx


class Function:
    """Represents one function/method found in the codebase."""

    def __init__(self, name, params, body, calls=None, start_line=None,
                 end_line=None, class_name=None, self_calls=None):
        self.name = name
        self.params = params
        self.body = body
        self.calls = calls if calls is not None else []
        self.start_line = start_line
        self.end_line = end_line
        self.class_name = class_name
        self.self_calls = self_calls if self_calls is not None else []

    def qualified_name(self):
        return f"{self.class_name}.{self.name}" if self.class_name else self.name

    def contains_line(self, line_number):
        if self.start_line is None or self.end_line is None:
            return False
        return self.start_line <= line_number <= self.end_line


def _module_name(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]


def find_python_files(folder_path):
    files = []
    for current, _dirs, filenames in os.walk(folder_path):
        files.extend(os.path.join(current, f) for f in filenames if f.endswith(".py"))
    return files


def _get_call_names(node):
    calls = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                calls.append(n.func.id)
            elif isinstance(n.func, ast.Attribute):
                is_self = isinstance(n.func.value, ast.Name) and n.func.value.id == "self"
                if not is_self:
                    calls.append(n.func.attr)
    return calls


def _get_self_call_names(node):
    calls = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if isinstance(n.func.value, ast.Name) and n.func.value.id == "self":
                calls.append(n.func.attr)
    return calls


def _parse_imports(tree):
    import_map = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                import_map[alias.asname or alias.name] = node.module
    return import_map


def _build_function(node, class_name):
    return Function(
        node.name,
        [a.arg for a in node.args.args],
        f"(defined at line {node.lineno})",
        calls=_get_call_names(node),
        start_line=node.lineno,
        end_line=node.end_lineno,
        class_name=class_name,
        self_calls=_get_self_call_names(node),
    )


def parse_file(file_path):
    """Returns (functions, import_map) for one file. Fails gracefully."""
    try:
        source = open(file_path, "r").read()
        tree = ast.parse(source, filename=file_path)
    except (FileNotFoundError, UnicodeDecodeError, SyntaxError) as error:
        print(f"  [warning] skipping {file_path}: {error}")
        return [], {}

    functions = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(_build_function(node, None))
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    functions.append(_build_function(child, node.name))

    return functions, _parse_imports(tree)


def build_repo_graph(repo_path):
    """
    Returns (graph, function_lookup). Nodes are fully-qualified names:
    "module.function" or "module.ClassName.method".
    function_lookup maps qualified_name -> (Function, file_path).
    """
    file_data = {}
    for file_path in find_python_files(repo_path):
        module_name = _module_name(file_path)
        functions, import_map = parse_file(file_path)
        file_data[module_name] = {"functions": functions, "import_map": import_map, "file_path": file_path}

    known_modules = set(file_data.keys())
    graph = nx.DiGraph()
    function_lookup = {}

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

            for call_name in func.calls:
                if call_name in standalone_names:
                    graph.add_edge(qualified, f"{module_name}.{call_name}")
                elif call_name in import_map and import_map[call_name] in known_modules:
                    graph.add_edge(qualified, f"{import_map[call_name]}.{call_name}")

            if func.class_name:
                siblings = methods_by_class.get(func.class_name, set())
                for self_call in func.self_calls:
                    if self_call in siblings:
                        graph.add_edge(qualified, f"{module_name}.{func.class_name}.{self_call}")

    return graph, function_lookup


def find_within_hops(graph, start_node, max_hops=2):
    """BFS in both directions."""
    visited = {start_node: 0}
    queue = deque([start_node])
    while queue:
        current = queue.popleft()
        distance = visited[current]
        if distance >= max_hops:
            continue
        for neighbor in list(graph.successors(current)) + list(graph.predecessors(current)):
            if neighbor not in visited:
                visited[neighbor] = distance + 1
                queue.append(neighbor)
    del visited[start_node]
    return visited
