"""
Day 16 -- ContextGuard project
--------------------------------
Goal: parse a file's `import` statements, and use them to classify every
function call as:
  - "local"    -> defined in this same file (Day 11's original filter)
  - "imported" -> not defined here, but traceable to another module,
                  via a `from <module> import <name>` statement
  - "external" -> a built-in or library call we can't trace (e.g. .split())

Known limitation kept deliberately out of scope today: calls written as
`module.function()` (where the whole module is imported, e.g.
`import networkx as nx` then `nx.draw(...)`) aren't resolved to their
source module yet -- they'll currently fall into "external". That's a
reasonable simplification for now, not a silent wrong answer.
"""

import ast

from day8_function_calls import find_functions_with_calls


def parse_imports(file_path):
    """
    Returns a dictionary mapping each locally-used name to the module
    it was imported from, for `from <module> import <name>` statements.

    Example: `from day8_function_calls import find_functions_with_calls`
    produces: {"find_functions_with_calls": "day8_function_calls"}
    """
    with open(file_path, "r") as f:
        source_code = f.read()

    tree = ast.parse(source_code, filename=file_path)

    import_map = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module_name = node.module  # e.g. "day8_function_calls"

            # A single import statement can bring in several names at once,
            # e.g. `from x import a, b, c` -- node.names is a list covering all of them.
            for alias in node.names:
                original_name = alias.name           # the name as defined in the source module
                local_name = alias.asname or original_name  # what we call it here (handles "as" renaming)
                import_map[local_name] = module_name

    return import_map


def classify_call(call_name, known_local_functions, import_map):
    """
    Returns a tuple describing where a given call actually comes from:
      ("local", call_name)
      ("imported", module_name, call_name)
      ("external", call_name)
    """
    if call_name in known_local_functions:
        return ("local", call_name)
    elif call_name in import_map:
        return ("imported", import_map[call_name], call_name)
    else:
        return ("external", call_name)


def describe_file_calls(file_path):
    """
    Prints every function in file_path, and for each of its calls, which
    of the three buckets it falls into.
    """
    functions = find_functions_with_calls(file_path)
    known_local_functions = {f.name for f in functions}
    import_map = parse_imports(file_path)

    print(f"Imports found in {file_path}:")
    for local_name, module_name in import_map.items():
        print(f"  {local_name}  <-  {module_name}")

    print(f"\nCall breakdown for {file_path}:")
    for func in functions:
        print(f"\n  {func.name}:")
        if not func.calls:
            print("    (calls nothing)")
            continue

        for call_name in func.calls:
            classification = classify_call(call_name, known_local_functions, import_map)
            kind = classification[0]

            if kind == "local":
                print(f"    {call_name} -- local (defined in this file)")
            elif kind == "imported":
                _, module_name, _ = classification
                print(f"    {call_name} -- imported from '{module_name}'")
            else:
                print(f"    {call_name} -- external (built-in or library)")


if __name__ == "__main__":
    # This file genuinely imports from several other files in your own
    # project -- a real example of exactly what today is solving.
    target_file = "day14_visualize_graph.py"
    describe_file_calls(target_file)
