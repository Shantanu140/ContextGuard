"""
Day 9 -- ContextGuard project
------------------------------
Goal: given the ACTUAL changed lines in a repo (not just changed file
names), figure out which specific function(s) those lines fall inside.

This combines Day 5 (running git commands from Python), Day 8 (finding
functions and their line ranges via ast), and today's new piece:
parsing a diff's line numbers.
"""

import os
import re
import subprocess

from day8_function_calls import find_functions_with_calls


def get_changed_line_ranges(repo_path):
    """
    Runs `git diff -U0` and returns a dictionary mapping each changed
    filename to a list of changed line numbers (in the NEW version of
    the file).

    Example return value:
        {"day1_read_file.py": [13, 14, 15]}
    """

    result = subprocess.run(
        ["git", "diff", "-U0", "--no-color"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )

    changed = {}       # the dictionary we'll return
    current_file = None  # tracks which file's section we're currently reading

    # This regular expression matches lines like "+++ b/day1_read_file.py"
    # and pulls out just the filename part.
    file_line_pattern = re.compile(r"^\+\+\+ b/(.*)$")

    # This one matches hunk headers like "@@ -12,0 +13,3 @@ ..." and
    # captures the two numbers after the "+": the starting line, and
    # (optionally) how many lines. If the ",count" part is missing,
    # it means a count of 1.
    hunk_pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    # git diff's output is one big block of text -- we read it line by line.
    for line in result.stdout.splitlines():

        file_match = file_line_pattern.match(line)
        if file_match:
            filename = file_match.group(1)
            if filename == "/dev/null":
                # This means the file was deleted -- nothing to map.
                current_file = None
            else:
                current_file = filename
                changed.setdefault(current_file, [])
            continue  # move to the next line; nothing more to do for this one

        hunk_match = hunk_pattern.match(line)
        if hunk_match and current_file:
            new_start = int(hunk_match.group(1))
            # group(2) is the optional count -- default to 1 if it wasn't there
            new_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1

            if new_count > 0:
                # range(a, b) in Python does NOT include b itself, so we
                # add new_count to cover exactly the right number of lines.
                changed[current_file].extend(range(new_start, new_start + new_count))
            # if new_count == 0, this hunk was a pure deletion --
            # no new lines were added, so there's nothing to map here.

    return changed


def find_changed_functions(repo_path):
    """
    The full pipeline: figure out which functions were actually touched
    by the current uncommitted changes in this repo.

    Returns a dictionary mapping filename -> list of changed function names.
    """
    changed_lines_by_file = get_changed_line_ranges(repo_path)

    changed_functions_by_file = {}

    for filename, line_numbers in changed_lines_by_file.items():
        full_path = os.path.join(repo_path, filename)

        functions = find_functions_with_calls(full_path)

        touched_function_names = []
        for func in functions:
            for line_number in line_numbers:
                if func.contains_line(line_number):
                    touched_function_names.append(func.name)
                    break  # no need to keep checking more lines for this function

        changed_functions_by_file[filename] = touched_function_names

    return changed_functions_by_file


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard"  # update this to your real path

    result = find_changed_functions(repo_path)

    if not result:
        print("No uncommitted changes found.")
        print("Edit a function in one of your files (without committing) and run this again.")
    else:
        for filename, function_names in result.items():
            print(f"{filename}:")
            if function_names:
                for name in function_names:
                    print(f"  - {name} was changed")
            else:
                print("  (changes found, but outside any function)")
