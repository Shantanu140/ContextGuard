"""
Day 20 -- ContextGuard project
--------------------------------
Goal: write real automated tests for graph_builder.py -- including a
regression test for the self-call double-counting bug found and fixed
yesterday, so it can never silently come back.

Install first (only needs to be done once):
    pip install pytest

Run with:
    pytest test_graph_builder.py -v
(the -v flag just means "verbose" -- show each test's name and result,
not only a final pass/fail count)
"""

import subprocess

from graph_builder import _parse_file, build_context


def make_git_repo(tmp_path):
    """
    A small helper (not a test itself) that sets up a real, empty git
    repository inside a temporary folder pytest gives us for this test
    only -- so tests never touch your real project files.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    return tmp_path


def write_file(folder, filename, content):
    """Small helper: writes `content` into `filename` inside `folder`."""
    path = folder / filename
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Test 1: the regression test for yesterday's bug.
# ---------------------------------------------------------------------------

def test_self_call_is_not_duplicated_in_ordinary_calls(tmp_path):
    """
    A self.method() call should appear in self_calls ONLY -- never also
    show up in the ordinary `calls` list. This is exactly the bug found
    and fixed on Day 18/19: without this check, it could silently
    reappear if the code is ever refactored carelessly.
    """
    code = """
class Example:
    def helper(self):
        return 1

    def main_method(self):
        return self.helper()
"""
    file_path = write_file(tmp_path, "example.py", code)

    functions, _import_map = _parse_file(str(file_path))
    main_method = next(f for f in functions if f.name == "main_method")

    assert "helper" in main_method.self_calls
    assert "helper" not in main_method.calls  # <- this line would have caught the bug


# ---------------------------------------------------------------------------
# Test 2: a standalone function calling another standalone function.
# ---------------------------------------------------------------------------

def test_standalone_call_resolves_correctly(tmp_path):
    code = """
def helper():
    return 1

def main():
    return helper()
"""
    file_path = write_file(tmp_path, "example.py", code)

    functions, _import_map = _parse_file(str(file_path))
    main_func = next(f for f in functions if f.name == "main")

    assert "helper" in main_func.calls


# ---------------------------------------------------------------------------
# Test 3: the full end-to-end pipeline, using a REAL git repo.
# ---------------------------------------------------------------------------

def test_build_context_finds_a_real_change(tmp_path):
    make_git_repo(tmp_path)

    code = """
def helper():
    return 1

def main():
    return helper()
"""
    write_file(tmp_path, "example.py", code)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)

    # Now make a REAL uncommitted change inside helper().
    changed_code = code.replace("return 1", "return 2  # changed")
    write_file(tmp_path, "example.py", changed_code)

    context = build_context(str(tmp_path))

    assert "example.helper" in context["changed_functions"]
    assert "example.main" in context["related_functions"]


def test_build_context_with_no_changes_returns_empty(tmp_path):
    make_git_repo(tmp_path)
    write_file(tmp_path, "example.py", "def helper():\n    return 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=tmp_path, check=True)

    context = build_context(str(tmp_path))

    assert context["changed_functions"] == []
