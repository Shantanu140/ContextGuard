"""
Day 42 -- feed build_full_context()'s output to the LLM for a real review.
"""

import os

from groq import Groq

from contextguard.context import build_full_context
from contextguard.retrieval import chunk_repo

SYSTEM_PROMPT = (
    "You are a code reviewer. You are given a changed function, plus related "
    "functions from the same codebase (found via dependency graph and semantic "
    "similarity). Point out any real risks the change might cause elsewhere in "
    "the related code. Be specific and concise."
)


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
{similar}

Review the changed function considering this context. What risks, if any, does this change pose to the related code?"""


if __name__ == "__main__":
    repo_path = r"E:\Context Guard\ContextGuard\src"  # change to your real path

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    context_bundle = build_full_context(repo_path)
    chunk_by_name = {c["name"]: c for c in chunk_repo(repo_path)}  # re-chunked here for the raw text; a bit redundant with build_full_context's internal chunking -- fine for now, worth cleaning up later

    for changed_name, context in context_bundle.items():
        prompt = build_prompt(changed_name, context, chunk_by_name)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        print(f"\n=== Review for {changed_name} ===")
        print(response.choices[0].message.content)
