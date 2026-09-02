"""
contextguard/diff.py -- reading git diffs and mapping changed lines to
the functions they fall inside. Consolidates Days 5, 9.
"""

import os
import re
import subprocess

from contextguard.graph import _module_name


def get_changed_line_ranges(repo_path):
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


def find_changed_functions(repo_path, function_lookup):
    """
    Returns qualified names of every function touched by current
    uncommitted changes, using an already-built function_lookup
    (from graph.build_repo_graph) rather than re-parsing files.
    """
    changed_lines_by_file = get_changed_line_ranges(repo_path)
    changed_names = []

    for relative_path, line_numbers in changed_lines_by_file.items():
        module_name = _module_name(os.path.join(repo_path, relative_path))
        for qualified_name, (func, _file_path) in function_lookup.items():
            if not qualified_name.startswith(module_name + "."):
                continue
            if any(func.contains_line(n) for n in line_numbers):
                changed_names.append(qualified_name)

    return changed_names
