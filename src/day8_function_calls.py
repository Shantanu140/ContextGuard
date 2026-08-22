"""
Day 8 -- ContextGuard project
------------------------------
Goal: for every function found in a file, also figure out which OTHER
functions it calls. This is the direct seed of the dependency graph
we start building next week.
"""

import ast
from day3_function_class import Function


def get_call_names(function_node):
    """
    Given a single FunctionDef node, walk ONLY inside it and return a
    list of names of every function/method it calls.
    """
    call_names = []

    # ast.walk() can start from ANY node, not just the whole file.
    # Starting it here means we only see calls made INSIDE this one
    # function -- not calls made elsewhere in the file.
    for node in ast.walk(function_node):

        if isinstance(node, ast.Call):
            # node.func tells us WHAT was called, but its shape differs
            # depending on how the call was written.

            if isinstance(node.func, ast.Name):
                # A plain call like: format_receipt(items)
                call_names.append(node.func.id)

            elif isinstance(node.func, ast.Attribute):
                # A method call like: f.summary()
                # .attr holds just the method name ("summary"),
                # ignoring what it was called on (the "f" part).
                call_names.append(node.func.attr)

            # (Calls can be written in other, rarer shapes too -- we're
            # deliberately keeping this simple for now and only handling
            # the two most common cases.)

    return call_names


def find_functions_with_calls(file_path):
    """
    Same as Day 7's find_functions, but now each Function object also
    has its `calls` list filled in.
    """
    with open(file_path, "r") as f:
        source_code = f.read()

    tree = ast.parse(source_code, filename=file_path)

    functions_found = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            params = [arg.arg for arg in node.args.args]
            body_placeholder = f"(defined at line {node.lineno})"

            # NEW today: find what this specific function calls,
            # by walking starting from THIS node, not the whole file.
            calls = get_call_names(node)

            functions_found.append(Function(name, params, body_placeholder, calls))

    return functions_found


if __name__ == "__main__":
    target_file = "day2_count_words.py"

    functions = find_functions_with_calls(target_file)

    print(f"Found {len(functions)} function(s) in {target_file}:")
    for func in functions:
        print(f"  - {func}")
