"""
contextguard/history.py -- logs each review run to a local SQLite file,
so past reviews stay visible even after the dashboard reruns or restarts.
"""

import json
import sqlite3
from datetime import datetime

DB_PATH = "contextguard_history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            repo_path TEXT,
            changed_function TEXT,
            issue_count INTEGER,
            issues_json TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_review(repo_path, changed_function, issues):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO reviews (timestamp, repo_path, changed_function, issue_count, issues_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), repo_path, changed_function, len(issues), json.dumps(issues)),
    )
    conn.commit()
    conn.close()


def get_history(limit=20):
    """Returns recent reviews as a list of dicts, most recent first."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, repo_path, changed_function, issue_count, issues_json "
        "FROM reviews ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "repo_path": r[1],
            "changed_function": r[2],
            "issue_count": r[3],
            "issues": json.loads(r[4]),
        }
        for r in rows
    ]
