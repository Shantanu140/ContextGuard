"""
tests/test_context.py -- automated tests for the contextguard package.

Run with: pytest tests/test_context.py -v
"""

import subprocess
from pathlib import Path

from contextguard.graph import parse_file, build_repo_graph
from contextguard.diff import find_changed_functions
from contextguard.context import build_full_context


def make_git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)


def write_file(folder, filename, content):
    path = Path(folder) / filename
    path.write_text(content)
    return path


def test_self_call_not_double_counted(tmp_path):
    """Regression test for the Day 18/19 bug."""
    code = "class E:\n    def helper(self):\n        return 1\n    def main(self):\n        return self.helper()\n"
    write_file(tmp_path, "e.py", code)
    functions, _ = parse_file(str(tmp_path / "e.py"))
    main = next(f for f in functions if f.name == "main")
    assert "helper" in main.self_calls
    assert "helper" not in main.calls


def test_cross_file_edge_resolves(tmp_path):
    write_file(tmp_path, "a.py", "def helper():\n    return 1\n")
    write_file(tmp_path, "b.py", "from a import helper\n\ndef main():\n    return helper()\n")
    graph, _ = build_repo_graph(str(tmp_path))
    assert graph.has_edge("b.main", "a.helper")


def test_find_changed_functions_identifies_correct_function(tmp_path):
    make_git_repo(tmp_path)
    code = "def helper():\n    return 1\n\ndef main():\n    return helper()\n"
    write_file(tmp_path, "e.py", code)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    write_file(tmp_path, "e.py", code.replace("return 1", "return 2"))
    _graph, lookup = build_repo_graph(str(tmp_path))
    changed = find_changed_functions(str(tmp_path), lookup)
    assert changed == ["e.helper"]


def test_build_full_context_graph_neighbors_are_per_function(tmp_path):
    """Regression test for the Day 25 bug: neighbors must differ per changed function."""
    make_git_repo(tmp_path)
    write_file(tmp_path, "a.py", "def x():\n    return 1\n\ndef y():\n    return x()\n")
    write_file(tmp_path, "b.py", "def z():\n    return 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    write_file(tmp_path, "a.py", "def x():\n    return 2\n\ndef y():\n    return x()\n")
    write_file(tmp_path, "b.py", "def z():\n    return 2\n")

    bundle = build_full_context(str(tmp_path))
    assert bundle["a.x"]["graph_neighbors"] != bundle["b.z"]["graph_neighbors"]
    assert "a.y" in bundle["a.x"]["graph_neighbors"]
    assert bundle["b.z"]["graph_neighbors"] == {}
