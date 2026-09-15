"""
Day 47 -- severity-based sorting of issues (high -> medium -> low).
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from groq import Groq

from contextguard.context import build_full_context
from contextguard.retrieval import chunk_repo

SAFETY_CHECKLIST = """Specifically check for these categories of issues:
1. Unchecked None/null access
2. Unbounded loops or recursion
3. Unhandled exceptions / missing error handling
4. Magic numbers with no explanation
5. Missing input validation
6. Resource leaks (files, sockets, connections not closed/released)
7. Mutable default arguments
8. Off-by-one errors in loops or ranges
9. Silently swallowed exceptions (bare except, or except: pass)
10. Return type / contract changes that could break existing callers"""

SYSTEM_PROMPT = f"""You are a code reviewer. You are given a changed function, plus related
functions from the same codebase (found via dependency graph and semantic similarity).

{SAFETY_CHECKLIST}

Rules:
- Only report issues you can genuinely justify from the given code -- do not invent problems.
- If an issue involves a RELATED function, explicitly name that function in the explanation.
- If RELATED FUNCTIONS and SEMANTICALLY SIMILAR FUNCTIONS are both "(none)", do NOT speculate
  about callers or dependencies you have no information about -- only assess the function in isolation.

Respond with ONLY a JSON array (no markdown, no extra text) of objects, each shaped exactly like:
{{"issue": "short title", "severity": "low|medium|high", "explanation": "why this matters", "suggested_fix": "what to do"}}

If there are no real issues, return an empty array: []"""


def build_prompt(changed_name, context, chunk_by_name):
    changed_code = chunk_by_name[changed_name]["text"]

    neighbors = "\n\n".join(
        f"# {name} ({dist} hop away)\n{chunk_by_name[name]['text']}"
        for name, dist in context["graph_neighbors"].items() if name in chunk_by_name
    ) or "(none)"

    similar = "\n\n".join(
        f"# {name} (similarity {score:.2f})\n{chunk_by_name[name]['text']}"
        for name, score in context["similar_chunks"]
        if name in chunk_by_name and name != changed_name
    ) or "(none)"

    return f"""CHANGED FUNCTION:
{changed_code}

RELATED FUNCTIONS (dependency graph):
{neighbors}

SEMANTICALLY SIMILAR FUNCTIONS:
{similar}"""


def get_structured_review(client, changed_name, context, chunk_by_name):
    prompt = build_prompt(changed_name, context, chunk_by_name)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"  [warning] model did not return valid JSON for {changed_name}, raw output:\n{raw_text}")
        return []


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def sort_by_severity(issues):
    return sorted(issues, key=lambda i: SEVERITY_ORDER.get(i.get("severity", "low"), 3))


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # change to your real path

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    context_bundle = build_full_context(repo_path)
    chunk_by_name = {c["name"]: c for c in chunk_repo(repo_path)}

    for changed_name, context in context_bundle.items():
        issues = get_structured_review(client, changed_name, context, chunk_by_name)
        issues = sort_by_severity(issues)

        print(f"\n=== {changed_name}: {len(issues)} issue(s) ===")
        for issue in issues:
            print(f"  [{issue.get('severity', '?')}] {issue.get('issue', '?')}")
            print(f"    {issue.get('explanation', '')}")
            print(f"    Fix: {issue.get('suggested_fix', '')}")
