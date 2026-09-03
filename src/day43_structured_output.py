"""
Day 43 -- force the LLM to return structured JSON: a list of
{issue, severity, explanation, suggested_fix} objects, instead of
free-form markdown.
"""

import json
import os

from groq import Groq

from contextguard.context import build_full_context
from contextguard.retrieval import chunk_repo

SYSTEM_PROMPT = """You are a code reviewer. You are given a changed function, plus related
functions from the same codebase (found via dependency graph and semantic similarity).

Respond with ONLY a JSON array (no markdown, no extra text) of objects, each shaped exactly like:
{"issue": "short title", "severity": "low|medium|high", "explanation": "why this matters", "suggested_fix": "what to do"}

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
        # Note: Groq's json_object mode forces a JSON *object*, but we want
        # a JSON *array* -- so we rely on the prompt instructions instead,
        # and parse + validate the result ourselves below.
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"  [warning] model did not return valid JSON for {changed_name}, raw output:\n{raw_text}")
        return []


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # change to your real path

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    context_bundle = build_full_context(repo_path)
    chunk_by_name = {c["name"]: c for c in chunk_repo(repo_path)}

    for changed_name, context in context_bundle.items():
        issues = get_structured_review(client, changed_name, context, chunk_by_name)

        print(f"\n=== {changed_name}: {len(issues)} issue(s) ===")
        for issue in issues:
            print(f"  [{issue.get('severity', '?')}] {issue.get('issue', '?')}")
            print(f"    {issue.get('explanation', '')}")
            print(f"    Fix: {issue.get('suggested_fix', '')}")
