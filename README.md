# ContextGuard

**A code reviewer that sees what the diff can't.**

Most AI code review tools read the lines that changed. ContextGuard reads what those lines are *connected to* — mapping a change's real dependencies across the codebase and retrieving semantically related code — before an LLM ever reasons about risk.

Built for KPIT Sparkle 2027 — AI Systems track, *"AI-Driven Contextual Reasoning for Software Engineering."*

---

## The problem

A change that looks safe in isolation can silently break something elsewhere. A diff-only review has no way to know that. In large, safety-critical, or embedded codebases — exactly the kind KPIT builds — that blind spot is where real bugs slip through.

## What ContextGuard does differently

Given any uncommitted code change, ContextGuard:
1. Identifies exactly which function was touched (not just which file).
2. Builds a whole-repository dependency graph to find what that function calls, and what calls it — across files, and correctly scoped to classes.
3. Retrieves semantically related code elsewhere in the repo, even where it shares no dependency edge, using embeddings and similarity search.
4. Feeds all of that — not just the diff — to an LLM, and gets back a structured, severity-ranked list of real risks.

## Proof it works

On a real, externally authored 2,500-line codebase (`sqlparse`), a return-type change to one function was reviewed two ways: with full context, and with only the diff. The diff-only version missed the breakage entirely and flagged an unrelated issue instead. The context-aware version correctly identified that the change would break two real callers elsewhere in the codebase, by name.

Full results, including the honest caveats: [`results.md`](results.md).

---

## Architecture

| Stage | Module | What it does |
|---|---|---|
| Diff | `diff.py` | Parses `git diff` to find exactly which lines changed |
| Graph | `graph.py` | AST-based dependency graph across the whole repo — cross-file, class-aware |
| Retrieval | `retrieval.py` | Chunks code by function, embeds it, retrieves semantically related pieces via FAISS |
| Reasoning | `reasoning.py` | Builds context-rich prompts, gets structured severity-ranked output from an LLM, with retry logic |
| Interface | `cli.py`, `dashboard.py` | A command-line tool and a Streamlit dashboard with live graph visualization and session history |

`context.py` ties the pipeline together behind one function — everything downstream just calls it.

---

## Engineering rigor

- Automated `pytest` suite, including regression tests for two real bugs found and fixed during development.
- Verified against real, externally authored codebases the developer did not write (`agent-tutorial`, `sqlparse`) — not just its own source.
- Every claim in `results.md` was manually checked against the actual model output, not assumed.

---

## Known limitations

- `module.function()`-style calls (e.g. `nx.draw(...)`) aren't yet traced to their source module.
- Relative/package imports (`from . import x`) aren't yet resolved across package boundaries.
- Validation evidence currently covers one external repository — genuine, but a small sample.

Stated as open work, not hidden gaps.

---

## Tech stack

Python · `ast` · `networkx` · `sentence-transformers` · FAISS · Groq (`openai/gpt-oss-120b`) · `argparse` + `rich` · Streamlit · `sqlite3` · `pytest`

---

## Project layout

```
contextguard/     the package — graph, diff, retrieval, reasoning, context, history, cli
dashboard.py      Streamlit UI
tests/            pytest suite, mocked LLM calls
results.md        validation results
```
