# ContextGuard

ContextGuard is an AI-powered code-review assistant that reasons about a code
change using its surrounding context, not just the visible diff. It is being
built for KPIT Sparkle 2027's AI-Driven Contextual Reasoning for Software
Engineering track, with safety-critical software-review workflows as the
long-term use case.

## Current prototype

The current Python prototype can:

- read an uncommitted Git diff and identify the functions touched by changed
  lines;
- build a repository-wide dependency graph for local calls, supported
  `from module import function` calls, and `self.method()` calls;
- gather nearby functions with breadth-first traversal; and
- start semantic code retrieval with embeddings and FAISS.

## How change detection works

1. `graph_builder.py` runs `git diff -U0` and reads the changed line numbers.
2. It parses Python files with the built-in AST module to find function and
   method boundaries.
3. It maps each changed line to its enclosing function and gathers connected
   functions from the dependency graph.

## Current limitations

- This is a Python-only static-analysis prototype.
- Dynamic calls, external libraries, and module-style calls such as
  `module.function()` are not fully resolved yet.
- Semantic retrieval is context selection, not a bug detector; the LLM
  reasoning phase will be added later.
