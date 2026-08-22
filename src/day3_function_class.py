"""
Day 3 -- ContextGuard project
------------------------------
Goal: define a `Function` class that bundles a function's name, parameters,
and body together as one object -- instead of three separate loose variables.

This is a *manual* stand-in for today. Starting Day 7, we'll build code that
automatically reads a real .py file and creates these Function objects for
us, by understanding the code's structure. Today, we just build the
container itself and get comfortable with it.
"""


class Function:
    """Represents one function found in some code."""

    def __init__(self, name, params, body, calls=None, start_line=None, end_line=None):
        # self.X = X means: "store this value on THIS object, permanently,
        # under the label X" -- so we can read it back later as f.name, f.params, etc.
        self.name = name      # a string, e.g. "calculate_total"
        self.params = params  # a list of strings, e.g. ["price", "quantity"]
        self.body = body      # a string containing the function's code

        # `calls` (added Day 8): a list of names of other functions this
        # function calls. Defaults to an empty list rather than None.
        self.calls = calls if calls is not None else []

        # `start_line` / `end_line` (NEW today): which lines of the file
        # this function occupies. Used to answer "did a changed line fall
        # inside this function?"
        self.start_line = start_line
        self.end_line = end_line

    def contains_line(self, line_number):
        """
        Returns True if the given line number falls within this function's
        boundaries. Returns False if we don't know this function's line
        range at all (start_line/end_line were never set).
        """
        if self.start_line is None or self.end_line is None:
            return False
        return self.start_line <= line_number <= self.end_line

    def param_count(self):
        """
        A METHOD -- a function that belongs to this class, and can use
        the object's own data (via self) without needing it passed in again.
        """
        return len(self.params)

    def summary(self):
        """Returns a short, readable one-line description of this function."""
        params_joined = ", ".join(self.params)  # ["a", "b"] -> "a, b"
        base = f"{self.name}({params_joined})  [{self.param_count()} params]"
        if self.calls:
            calls_joined = ", ".join(self.calls)
            base += f"  -> calls: {calls_joined}"
        return base

    def __str__(self):
        """
        A special (dunder) method: when you `print(some_function_object)`,
        Python calls this automatically to decide what text to show.
        Without this, print() would show something unhelpful like
        <__main__.Function object at 0x7f...>.
        """
        return self.summary()


if __name__ == "__main__":
    # Manually creating a few Function objects, as if we'd already found
    # them in some real code (this manual step is what AST parsing will
    # automate for us starting Day 7).
    functions_found = [
        Function("calculate_total", ["price", "quantity"], "return price * quantity"),
        Function("apply_discount", ["total", "percent"], "return total * (1 - percent / 100)"),
        Function("format_receipt", ["items"], "return '\\n'.join(items)"),
    ]

    print("Functions found in this file:")
    for func in functions_found:
        # Because we defined __str__ above, this print() call automatically
        # shows func.summary() instead of a meaningless memory address.
        print(f"  - {func}")

    # A quick, real use of this data: which function takes the most parameters?
    # max() with a key= works the same way sorted()'s key= did on Day 2.
    most_params = max(functions_found, key=lambda f: f.param_count())
    print(f"\nFunction with the most parameters: {most_params.name}")
