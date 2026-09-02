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
import sys
from types import SimpleNamespace

import numpy as np

from graph_builder import _build_repo_graph, _parse_file, build_context
from retrieval import build_faiss_index, chunk_python_file, retrieve_related_chunks


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
    assert context["related_functions"] == {}


def test_cross_file_import_creates_a_repo_graph_edge(tmp_path):
    write_file(tmp_path, "helper.py", "def helper():\n    return 1\n")
    write_file(
        tmp_path,
        "consumer.py",
        "from helper import helper\n\ndef caller():\n    return helper()\n",
    )

    graph, _lookup = _build_repo_graph(str(tmp_path))

    assert ("consumer.caller", "helper.helper") in graph.edges()


def test_self_method_creates_exactly_one_repo_graph_edge(tmp_path):
    write_file(
        tmp_path,
        "example.py",
        """
class Example:
    def helper(self):
        return 1

    def main_method(self):
        return self.helper()
""",
    )

    graph, _lookup = _build_repo_graph(str(tmp_path))

    assert list(graph.edges()).count(
        ("example.Example.main_method", "example.Example.helper")
    ) == 1


def test_invalid_python_file_is_skipped_without_losing_valid_files(tmp_path):
    write_file(tmp_path, "valid.py", "def usable():\n    return 1\n")
    write_file(tmp_path, "legacy.py", 'print "Python 2 syntax"\n')

    graph, _lookup = _build_repo_graph(str(tmp_path))

    assert "valid.usable" in graph
    assert not any(node.startswith("legacy.") for node in graph.nodes())


class FakeEmbeddingModel:
    """A deterministic stand-in so tests never download a real ML model."""

    def __init__(self, vectors):
        self.vectors = vectors

    def encode(self, texts, normalize_embeddings=True):
        return np.array([self.vectors[text] for text in texts], dtype="float32")


class FakeIndexFlatIP:
    """Tiny FAISS-like index used only to test retrieval logic offline."""

    def __init__(self, dimension):
        self.dimension = dimension
        self.vectors = None

    def add(self, vectors):
        self.vectors = vectors

    def search(self, queries, count):
        scores = queries @ self.vectors.T
        positions = np.argsort(-scores, axis=1)[:, :count]
        return np.take_along_axis(scores, positions, axis=1), positions


def test_function_chunk_keeps_identity_path_and_source(tmp_path):
    source = """
def helper(value):
    return value + 1

class Worker:
    def run(self):
        return helper(1)
"""
    file_path = write_file(tmp_path, "sample.py", source)

    chunks = chunk_python_file(str(file_path), str(tmp_path))

    assert [chunk["id"] for chunk in chunks] == ["sample.helper", "sample.Worker.run"]
    assert chunks[0]["file_path"] == "sample.py"
    assert "def helper" in chunks[0]["source"]
    assert "def run" in chunks[1]["source"]


def test_retrieval_ranks_matches_and_excludes_the_changed_chunk(monkeypatch):
    chunks = [
        {"id": "a.changed", "file_path": "a.py", "qualified_name": "a.changed", "source": "changed"},
        {"id": "b.related", "file_path": "b.py", "qualified_name": "b.related", "source": "related"},
        {"id": "c.other", "file_path": "c.py", "qualified_name": "c.other", "source": "other"},
    ]
    model = FakeEmbeddingModel(
        {
            "changed": [1.0, 0.0],
            "related": [0.9, 0.1],
            "other": [0.0, 1.0],
        }
    )
    monkeypatch.setitem(sys.modules, "faiss", SimpleNamespace(IndexFlatIP=FakeIndexFlatIP))

    search_data = build_faiss_index(chunks, model=model)
    matches = retrieve_related_chunks(
        "changed", search_data, top_k=2, exclude_ids={"a.changed"}
    )

    assert [match["id"] for match in matches] == ["b.related", "c.other"]
    assert matches[0]["score"] > matches[1]["score"]
