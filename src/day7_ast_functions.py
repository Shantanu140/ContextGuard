"""
Day 7 -- ContextGuard project
------------------------------
Goal: use Python's built-in `ast` module to actually understand a file's
structure, and automatically find every function defined in it -- along
with its parameters -- instead of manually typing them in like we did
on Day 3.

This is the moment Day 3's Function class stops being a toy and starts
being fed by real, automatically-discovered data.
"""

import ast
from day3_function_class import Function  # reusing the class you already built


def find_functions(file_path):
    """
    Reads a .py file, parses its structure, and returns a list of
    Function objects -- one for every function defined in the file.
    """

    with open(file_path, "r") as f:
        source_code = f.read()  # read the WHOLE file as one big string

    # Turn that raw text into a tree that understands Python's grammar.
    tree = ast.parse(source_code, filename=file_path)

    functions_found = []

    # Walk every node in the tree, at every level of nesting.
    for node in ast.walk(tree):

        # isinstance(node, ast.FunctionDef) asks: "is this specific node
        # a function definition?" Most nodes won't be -- they'll be things
        # like variable assignments, if-statements, etc. -- so this check
        # filters down to only the ones we care about.
        if isinstance(node, ast.FunctionDef):

            # node.name is simply the function's name as a string.
            name = node.name

            # node.args.args is a list of `ast.arg` objects, one per
            # parameter. Each one has a `.arg` attribute holding the
            # parameter's name as a string.
            # This line builds a plain list of parameter name strings,
            # e.g. ["price", "quantity"], using a LIST COMPREHENSION --
            # a compact way to write "make a new list by transforming
            # every item in another list," instead of a full for-loop
            # with .append() each time.
            params = [arg.arg for arg in node.args.args]

            # We're not extracting the real body text yet -- that's a
            # later day's problem. For now we just note the line number
            # so we know roughly where it lives in the file.
            body_placeholder = f"(defined at line {node.lineno})"

            functions_found.append(Function(name, params, body_placeholder))

    return functions_found


if __name__ == "__main__":
    # Try this on any .py file you've already built -- day2_count_words.py
    # is a good choice since it has more than one function-like piece to find.
    target_file = "day3_function_class.py"

    functions = find_functions(target_file)

    print(f"Found {len(functions)} function(s) in {target_file}:")
    for func in functions:
        # This works because Function already has a __str__ method
        # from Day 3 -- print() automatically uses it.
        print(f"  - {func}")
