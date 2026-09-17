"""
contextguard/cli.py -- the CLI: `python -m contextguard.cli review <repo-path>`
"""

import argparse
import os

from groq import Groq
from rich.console import Console
from rich.table import Table

from contextguard.context import build_full_context
from contextguard.retrieval import chunk_repo
from contextguard.reasoning import get_structured_review, sort_by_severity

SEVERITY_COLOR = {"high": "red", "medium": "yellow", "low": "green"}

console = Console()


def run_review(repo_path):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    context_bundle = build_full_context(repo_path)

    if not context_bundle:
        console.print("[bold]No uncommitted changes found.[/bold]")
        return

    chunk_by_name = {c["name"]: c for c in chunk_repo(repo_path)}

    for changed_name, context in context_bundle.items():
        issues = sort_by_severity(get_structured_review(client, changed_name, context, chunk_by_name))

        console.print(f"\n[bold underline]{changed_name}[/bold underline] -- {len(issues)} issue(s)")

        if not issues:
            continue

        table = Table(show_lines=True)
        table.add_column("Severity", width=8)
        table.add_column("Issue")
        table.add_column("Explanation")
        table.add_column("Suggested fix")

        for issue in issues:
            severity = issue.get("severity", "?")
            color = SEVERITY_COLOR.get(severity, "white")
            table.add_row(
                f"[{color}]{severity}[/{color}]",
                issue.get("issue", ""),
                issue.get("explanation", ""),
                issue.get("suggested_fix", ""),
            )

        console.print(table)


def main():
    parser = argparse.ArgumentParser(prog="contextguard")
    subparsers = parser.add_subparsers(dest="command")

    review_parser = subparsers.add_parser("review", help="Review uncommitted changes in a repo")
    review_parser.add_argument("repo_path")

    args = parser.parse_args()

    if args.command == "review":
        run_review(args.repo_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
