"""
dashboard.py -- minimal Streamlit UI for ContextGuard.
Run with: streamlit run dashboard.py  (from the repo root)
"""

import os

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st
from groq import Groq

from contextguard.context import build_full_context
from contextguard.graph import build_repo_graph
from contextguard.retrieval import chunk_repo
from contextguard.reasoning import get_structured_review, sort_by_severity


def show_graph(graph, changed_name, neighbors):
    nodes = [changed_name] + list(neighbors.keys())
    subgraph = graph.subgraph(nodes)
    colors = ["red" if n == changed_name else ("orange" if neighbors.get(n) == 1 else "gold") for n in subgraph.nodes()]

    fig, ax = plt.subplots(figsize=(5, 4))
    pos = nx.spring_layout(subgraph, seed=42)
    nx.draw(subgraph, pos, with_labels=True, node_color=colors, ax=ax, font_size=7, node_size=1000, arrows=True)
    st.pyplot(fig)


st.title("ContextGuard")

repo_path = st.text_input("Repo path", value=r"E:\Context Guard\ContextGuard\src")

if st.button("Run Review"):
    with st.spinner("Analyzing..."):
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        context_bundle = build_full_context(repo_path)

        if not context_bundle:
            st.info("No uncommitted changes found.")
        else:
            graph, _ = build_repo_graph(repo_path)
            chunk_by_name = {c["name"]: c for c in chunk_repo(repo_path)}

            for changed_name, context in context_bundle.items():
                issues = sort_by_severity(get_structured_review(client, changed_name, context, chunk_by_name))
                st.subheader(f"{changed_name} -- {len(issues)} issue(s)")

                for issue in issues:
                    severity = issue.get("severity", "?")
                    title = f"[{severity.upper()}] {issue.get('issue', '')}"
                    show = {"high": st.error, "medium": st.warning}.get(severity, st.success)
                    show(title)
                    st.write(issue.get("explanation", ""))
                    st.write(f"**Fix:** {issue.get('suggested_fix', '')}")

                with st.expander("Dependency graph"):
                    show_graph(graph, changed_name, context["graph_neighbors"])
