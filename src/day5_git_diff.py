"""
Day 5 -- ContextGuard project
------------------------------
Goal: use Python's subprocess module to run the real `git diff` command
and read back which files have uncommitted changes.

This is the very first real seed of ContextGuard's actual job: given some
change in a repository, figure out what it touched.
"""

import subprocess


def get_changed_files(repo_path):
    """
    Runs `git diff --name-only` inside the given repo folder, and returns
    a list of filenames that have uncommitted changes.
    """

    # subprocess.run() takes the command as a LIST of pieces, exactly as
    # you'd type them separately in PowerShell:
    #   git diff --name-only
    # becomes
    #   ["git", "diff", "--name-only"]
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_path,        # cwd = "current working directory" -- run the
                               # command AS IF we were sitting inside this folder
        capture_output=True,  # capture whatever the command prints, instead
                               # of letting it print straight to the screen
        text=True,             # give us the output as a normal string,
                               # not as raw bytes
        check=True,            # if the command fails, raise a Python error
                               # immediately instead of silently continuing
    )

    # result.stdout is one big string, with one filename per line
    # (or an empty string if nothing has changed).
    raw_output = result.stdout

    # .strip() removes any trailing blank line/whitespace.
    # .splitlines() breaks the string into a list, one item per line --
    # similar to what .split() did on Day 2, but specifically splitting on
    # line breaks rather than any whitespace.
    changed_files = raw_output.strip().splitlines()

    return changed_files


if __name__ == "__main__":
    # Point this at your actual ContextGuard folder's full path.
    # Example on Windows: r"E:\ContextGuard"
    # The r before the string means "raw string" -- it stops Python from
    # treating the backslashes as special characters.
    repo_path = r"E:\Context Guard\ContextGuard"

    changed = get_changed_files(repo_path)

    if not changed:
        print("No uncommitted changes found.")
        print("Try editing one of your files (without committing yet) and run this again.")
    else:
        print(f"Found {len(changed)} changed file(s):")
        for filename in changed:
            print(f"  - {filename}")
