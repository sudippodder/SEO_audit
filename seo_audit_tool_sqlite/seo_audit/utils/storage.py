"""
storage.py
Handles lead + audit result persistence using SQLite (zero config, no external service).

Database file: seo_audits.db  (auto-created next to this project on first run)
You can open it with any SQLite viewer, or export to CSV via the admin panel in app.py.
"""

import os
import sqlite3
import threading
from urllib.parse import urlparse
from datetime import datetime, timezone

# Path to the SQLite file — sits in the project root by default.
# Override by setting DB_PATH in your .env file.
_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "seo_audits.db")
DB_PATH = os.getenv("DB_PATH", _DEFAULT_DB)

# Thread-local storage so each thread gets its own connection
# (Streamlit runs requests in threads)
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row   # rows behave like dicts
    return _local.conn


def _init_db():
    """Create the table if it doesn't exist yet."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seo_audits (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at        TEXT    DEFAULT (datetime('now')),
            url               TEXT    NOT NULL,
            email             TEXT    NOT NULL,
            domain            TEXT,
            overall_score     INTEGER,
            seo_score         INTEGER,
            content_score     INTEGER,
            ai_score          INTEGER,
            opportunity_score INTEGER,
            overall_grade     TEXT,
            fetch_time_ms     INTEGER,
            error             TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email    ON seo_audits (email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_domain   ON seo_audits (domain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created  ON seo_audits (created_at DESC)")
    conn.commit()


# Initialise on import
_init_db()


def save_audit(report) -> bool:
    """
    Persist an AuditReport to SQLite.
    Returns True on success, False on error.
    """
    try:
        domain = urlparse(report.url).netloc.replace("www.", "")
        scores = {m.module: m.score for m in report.modules}

        conn = _get_conn()
        conn.execute("""
            INSERT INTO seo_audits
                (url, email, domain, overall_score, seo_score, content_score,
                 ai_score, opportunity_score, overall_grade, fetch_time_ms, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.url,
            report.email,
            domain,
            report.overall_score,
            scores.get("SEO Foundation"),
            scores.get("Content Quality"),
            scores.get("AI Visibility"),
            scores.get("Opportunity Score"),
            report.overall_grade,
            report.fetch_time_ms,
            report.error,
        ))
        conn.commit()
        return True

    except Exception as e:
        print(f"[storage] SQLite insert failed: {e}")
        return False


def get_recent_audits(limit: int = 100) -> list[dict]:
    """Return the most recent audit rows as a list of dicts."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM seo_audits ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[storage] SQLite select failed: {e}")
        return []


def get_stats() -> dict:
    """Aggregate stats for the admin dashboard."""
    try:
        conn = _get_conn()
        row = conn.execute("""
            SELECT
                COUNT(*)                            AS total_audits,
                COUNT(DISTINCT email)               AS unique_leads,
                COUNT(DISTINCT domain)              AS unique_domains,
                ROUND(AVG(overall_score), 1)        AS avg_overall,
                ROUND(AVG(seo_score), 1)            AS avg_seo,
                ROUND(AVG(ai_score), 1)             AS avg_ai,
                SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) AS error_count
            FROM seo_audits
        """).fetchone()
        return dict(row) if row else {}
    except Exception:
        return {}


def export_csv() -> str:
    """Return all audit rows as a CSV string (for download button)."""
    import csv, io
    rows = get_recent_audits(limit=10000)
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
