"""
Day 1 — ContextGuard project
-----------------------------
Goal: read a .py file and print every line, numbered.

This is deliberately simple — the point today is to get comfortable with:
  1. Defining a function (Python's version of a Java method)
  2. Opening and reading a file safely (the `with` keyword)
  3. Looping over lines (the `for` keyword)
  4. Basic string formatting to print nicely

Nothing here is throwaway — this exact "open a file, read its lines" pattern
is the very first step of every code-reading tool you build from here on.
"""
"""Hi, My name is Shantanu."""


def print_file_lines(file_path):
    """
    Reads the file at `file_path` and prints each line with its line number.

    In Java, this function's "signature" would look like:
        public static void printFileLines(String filePath)

    Notice Python doesn't need us to say the return type, or that it's
    "public static void" — Python is more relaxed about this.
    """

    # The `with` block below is Python's version of Java's try-with-resources.
    # It opens the file, gives it the name `f`, and guarantees the file
    # gets closed automatically once we leave this block — even if an
    # error happens inside it.
    with open(file_path, "r") as f:
        lines = f.readlines()  # reads the WHOLE file into a list of strings,
                                # one string per line (like an ArrayList<String> in Java)

    # enumerate() gives us both the index (0, 1, 2...) and the value (each line)
    # at the same time, instead of writing a manual counter like in Java:
    #   for (int i = 0; i < lines.length; i++) { ... }
    for line_number, line_text in enumerate(lines, start=0):
        # .rstrip() removes the trailing newline character so our printed
        # output doesn't have an extra blank line after every line of code
        clean_line = line_text.rstrip()
        print(f"{line_number:>3} |{clean_line} ")
        # f-strings (the f"..." above) are Python's version of Java's
        # String.format(). The {line_number:>3} part means "print this
        # number, right-aligned, padded to 3 characters wide" — just so
        # our output lines up neatly.


# This next bit is Python's loose equivalent of Java's `public static void main`.
# It means: "only run the code below if this file is being run directly
# (not if some other script is importing this file to reuse the function)."
if __name__ == "__main__":
    # For today, point this at any Python file you have on your laptop.
    # If you're not sure what to try it on, just point it at itself!
    target_file = "day1_read_file.py"
    print_file_lines(target_file)
