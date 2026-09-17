"""
contextguard/reasoning.py -- the LLM reasoning engine. Consolidates
Days 42-48: prompt building, structured JSON output, safety checklist,
retry logic, severity sorting.
"""

import json
import time

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

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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


def get_structured_review(client, changed_name, context, chunk_by_name, max_retries=3):
    prompt = build_prompt(changed_name, context, chunk_by_name)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as error:
            print(f"  [warning] API call failed (attempt {attempt}/{max_retries}): {error}")
            time.sleep(2 * attempt)
            continue

        raw_text = response.choices[0].message.content.strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"  [warning] invalid JSON (attempt {attempt}/{max_retries}), retrying...")
            time.sleep(1)

    print(f"  [error] giving up on {changed_name} after {max_retries} attempts")
    return []


def sort_by_severity(issues):
    return sorted(issues, key=lambda i: SEVERITY_ORDER.get(i.get("severity", "low"), 3))
