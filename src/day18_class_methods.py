"""
Day 18 -- ContextGuard project
--------------------------------
Goal: properly detect class methods (qualified as "ClassName.method"),
and resolve self.method() calls specifically to other methods of the
SAME class -- instead of lumping them into "external" like Day 16/17 did.
"""

import ast

from day3_function_class import Function


def get_ordinary_call_names(function_node):
    """
    Returns ordinary (non-self) calls made inside this function/method.

    IMPORTANT FIX: earlier this reused day8_function_calls.get_call_names,
    which doesn't know about self.X() calls and includes them here too --
    that caused every self.X() call to be double-counted (once here,
    once in get_self_call_names below). This version explicitly excludes
    self.X() calls, so each call is classified exactly once.
    """
    call_names = []

    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            func = node.func

            if isinstance(func, ast.Name):
                call_names.append(func.id)

            elif isinstance(func, ast.Attribute):
                is_self_call = (
                    isinstance(func.value, ast.Name) and func.value.id == "self"
                )
                if not is_self_call:
                    call_names.append(func.attr)
                # if it IS a self-call, we deliberately skip it here --
                # get_self_call_names below is the only place that records it.

    return call_names


def get_self_call_names(function_node):
    """
    Returns a list of method names called specifically as self.X(...)
    inside this function -- a much more specific signal than a generic
    attribute call, since it always means "call another method of this
    same object."
    """
    self_calls = []

    for node in ast.walk(function_node):
        if isinstance(node, ast.Call):
            func = node.func
            # We want exactly: an Attribute call (like self.something())
            # where the thing being accessed is a Name node with id "self".
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                self_calls.append(func.attr)

    return self_calls


def find_functions_with_scope(file_path):
    """
    Like Day 8's function finder, but tracks whether each function is a
    standalone function (class_name=None) or a method belonging to a
    specific class (class_name="ClassName") -- and separately records
    self.X() calls.
    """
    with open(file_path, "r") as f:
        source_code = f.read()

    tree = ast.parse(source_code, filename=file_path)

    functions_found = []

    # We deliberately do NOT use ast.walk() at the top level here, because
    # ast.walk() flattens everything and loses the information of WHICH
    # class a method belongs to. Instead we look only at the file's
    # top-level statements (tree.body), and handle classes explicitly.
    for node in tree.body:

        if isinstance(node, ast.FunctionDef):
            # A standalone, module-level function.
            functions_found.append(_build_function(node, class_name=None))

        elif isinstance(node, ast.ClassDef):
            # A class -- look at ITS top-level statements for methods.
            class_name = node.name
            for class_child in node.body:
                if isinstance(class_child, ast.FunctionDef):
                    functions_found.append(_build_function(class_child, class_name))

    return functions_found


def _build_function(node, class_name):
    """Small helper: builds one Function object from a FunctionDef node."""
    name = node.name
    params = [arg.arg for arg in node.args.args]
    body_placeholder = f"(defined at line {node.lineno})"
    calls = get_ordinary_call_names(node)
    self_calls = get_self_call_names(node)

    return Function(
        name, params, body_placeholder, calls,
        start_line=node.lineno,
        end_line=node.end_lineno,
        class_name=class_name,
        self_calls=self_calls,
    )


def build_class_aware_edges(functions):
    """
    Builds a list of (source_qualified_name, target_qualified_name) edges,
    correctly handling both:
      - ordinary calls to standalone functions (resolved by plain name,
        same as Day 11)
      - self.X() calls, resolved ONLY to another method in the SAME class
    """
    # Standalone (non-method) functions, by plain name -- for ordinary call resolution.
    standalone_names = {f.name for f in functions if f.class_name is None}

    # Methods grouped by class, by plain method name -- for self.X() resolution.
    methods_by_class = {}
    for f in functions:
        if f.class_name:
            methods_by_class.setdefault(f.class_name, set()).add(f.name)

    edges = []

    for func in functions:
        source = func.qualified_name()

        # Ordinary calls: only resolve against standalone functions.
        for call_name in func.calls:
            if call_name in standalone_names:
                edges.append((source, call_name))

        # self.X() calls: only resolve against methods of the SAME class.
        if func.class_name:
            sibling_methods = methods_by_class.get(func.class_name, set())
            for self_call_name in func.self_calls:
                if self_call_name in sibling_methods:
                    target = f"{func.class_name}.{self_call_name}"
                    edges.append((source, target))

    return edges


if __name__ == "__main__":
    target_file = "agent.py"  # the real file from Day 15/17's external repo test

    functions = find_functions_with_scope(target_file)

    print(f"Functions/methods found in {target_file}:")
    for func in functions:
        print(f"  {func.qualified_name()}  (self_calls: {func.self_calls})")

    print()
    edges = build_class_aware_edges(functions)
    print("Resolved edges:")
    for source, target in edges:
        print(f"  {source} -> {target}")
