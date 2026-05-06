"""
storage.py
Handles lead + audit result persistence using SQLite (zero config, no external service).

Database file: seo_audits.db  (auto-created next to this project on first run)
Full report JSON is stored in the `full_report` column so every audit can be
replayed and shown in-app at any time — no data is lost.
"""

import os
import json
import sqlite3
import threading
from urllib.parse import urlparse

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "seo_audits.db")
DB_PATH = os.getenv("DB_PATH", _DEFAULT_DB)

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def _init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seo_audits (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at        TEXT    DEFAULT (datetime('now','localtime')),
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
            error             TEXT,
            full_report       TEXT
        )
    """)
    try:
        conn.execute("ALTER TABLE seo_audits ADD COLUMN full_report TEXT")
    except Exception:
        pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email   ON seo_audits (email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_domain  ON seo_audits (domain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON seo_audits (created_at DESC)")
    conn.commit()


_init_db()


def _report_to_dict(report) -> dict:
    modules = []
    for m in report.modules:
        checks = []
        for c in m.checks:
            checks.append({
                "name":      c.name,
                "score":     c.score,
                "max_score": c.max_score,
                "status":    c.status,
                "finding":   c.finding,
                "impact":    c.impact,
            })
        mod = {"module": m.module, "score": m.score, "checks": checks}
        if hasattr(m, "top_recommendations"):
            mod["top_recommendations"] = m.top_recommendations
        if hasattr(m, "stats"):
            mod["stats"] = m.stats
        modules.append(mod)

    return {
        "url":           report.url,
        "email":         report.email,
        "fetch_time_ms": report.fetch_time_ms,
        "error":         report.error,
        "overall_score": report.overall_score,
        "overall_grade": report.overall_grade,
        "overall_color": report.overall_color,
        "modules":       modules,
        "insights":      report.insights,
    }


def save_audit(report):
    """Persist a full AuditReport. Returns new row ID on success, None on error."""
    try:
        domain = urlparse(report.url).netloc.replace("www.", "")
        scores = {m.module: m.score for m in report.modules}
        full_json = json.dumps(_report_to_dict(report), ensure_ascii=False)

        conn = _get_conn()
        cur = conn.execute("""
            INSERT INTO seo_audits
                (url, email, domain, overall_score, seo_score, content_score,
                 ai_score, opportunity_score, overall_grade, fetch_time_ms,
                 error, full_report)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.url, report.email, domain,
            report.overall_score,
            scores.get("SEO Foundation"),
            scores.get("Content Quality"),
            scores.get("AI Visibility"),
            scores.get("Opportunity Score"),
            report.overall_grade,
            report.fetch_time_ms,
            report.error,
            full_json,
        ))
        conn.commit()
        return cur.lastrowid

    except Exception as e:
        print(f"[storage] SQLite insert failed: {e}")
        return None


def get_recent_audits(limit: int = 100) -> list:
    """Return the most recent audit summary rows (no full_report blob)."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            """SELECT id, created_at, url, email, domain, overall_score,
                      seo_score, content_score, ai_score, opportunity_score,
                      overall_grade, fetch_time_ms, error
               FROM seo_audits ORDER BY created_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[storage] SQLite select failed: {e}")
        return []


def get_audit_by_id(audit_id: int):
    """Return the full saved report dict for a given row ID."""
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT full_report, created_at FROM seo_audits WHERE id = ?",
            (audit_id,)
        ).fetchone()
        if row and row["full_report"]:
            data = json.loads(row["full_report"])
            data["saved_at"] = row["created_at"]
            return data
        return None
    except Exception as e:
        print(f"[storage] get_audit_by_id failed: {e}")
        return None


def get_stats() -> dict:
    try:
        conn = _get_conn()
        row = conn.execute("""
            SELECT
                COUNT(*)                                        AS total_audits,
                COUNT(DISTINCT email)                           AS unique_leads,
                COUNT(DISTINCT domain)                          AS unique_domains,
                ROUND(AVG(overall_score), 1)                    AS avg_overall,
                ROUND(AVG(seo_score), 1)                        AS avg_seo,
                ROUND(AVG(ai_score), 1)                         AS avg_ai,
                SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) AS error_count
            FROM seo_audits
        """).fetchone()
        return dict(row) if row else {}
    except Exception:
        return {}


def export_csv() -> str:
    import csv, io
    rows = get_recent_audits(limit=10000)
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
