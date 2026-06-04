import os, json, sqlite3, threading
from urllib.parse import urlparse

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "seo_audits.db")
DB_PATH = os.getenv("DB_PATH", _DEFAULT_DB)
_local = threading.local()

def _get_conn():
    if not hasattr(_local,"conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

def _init_db():
    conn = _get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS seo_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        url TEXT NOT NULL, email TEXT NOT NULL, keyword TEXT,
        domain TEXT, overall_score INTEGER, seo_score INTEGER, ai_score INTEGER,
        overall_grade TEXT, fetch_time_ms INTEGER, error TEXT, full_report TEXT)""")
    for col in ["keyword","ai_score","full_report"]:
        try: conn.execute(f"ALTER TABLE seo_audits ADD COLUMN {col} TEXT")
        except: pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON seo_audits(email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_domain ON seo_audits(domain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON seo_audits(created_at DESC)")

    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    conn.commit()

def seed_admin():
    try:
        from utils.auth import hash_password
        conn = _get_conn()
        row = conn.execute("SELECT id FROM users WHERE email='admin' OR email='admin@admin.com'").fetchone()
        if not row:
            pwd = hash_password("admin123")
            conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                         ("admin@admin.com", pwd, "admin"))
            conn.commit()
    except Exception as e:
        print(f"[storage] seed admin failed: {e}")

_init_db()
seed_admin()


def _serialize_geo_report(geo_report) -> dict:
    """Convert GeoReport dataclass into a plain dict for JSON storage."""
    if geo_report is None:
        return None

    def _check(c):
        return {
            "name": c.name, "score": c.score, "max_score": c.max_score,
            "status": c.status, "found": c.found, "impact": c.impact,
            "how_to_fix": c.how_to_fix, "category": getattr(c, "category", "GEO"),
        }

    def _mod(m):
        return {
            "module": m.module, "score": m.score, "icon": m.icon,
            "checks": [_check(c) for c in m.checks],
        }

    def _opp(o):
        return {
            "module": o.module, "score": o.score, "gap_score": o.gap_score,
            "checks": [_check(c) for c in o.checks],
        }

    return {
        "citation_readiness":  _mod(geo_report.citation_readiness),
        "entity_clarity":      _mod(geo_report.entity_clarity),
        "extractability":      _mod(geo_report.extractability),
        "trust_signals":       _mod(geo_report.trust_signals),
        "overview_readiness":  _mod(geo_report.overview_readiness),
        "information_gain":    _mod(geo_report.information_gain),
        "geo_opportunity":     _opp(geo_report.geo_opportunity),
        "geo_score":           geo_report.geo_score,
        "overall_ai_score":    geo_report.overall_ai_score,
    }


def _serialize_module_score(m) -> dict:
    """Serialize any ModuleScore-like dataclass with checks list."""
    if m is None: return None
    checks = []
    for c in (m.checks if hasattr(m, 'checks') else m.get('checks', [])):
        entry = {
            "name": c.name, "score": c.score, "max_score": c.max_score,
            "status": c.status, "found": c.found, "impact": c.impact,
            "how_to_fix": c.how_to_fix,
            "category": getattr(c, "category", "GEO"),
            "effort": getattr(c, "effort", "medium"),
        }
        checks.append(entry)
    return {
        "module": m.module if hasattr(m, 'module') else m.get('module'),
        "score":  m.score  if hasattr(m, 'score')  else m.get('score', 0),
        "icon":   m.icon   if hasattr(m, 'icon')   else m.get('icon', ''),
        "checks": checks,
    }


def _serialize_crawlability_report(r) -> dict:
    if r is None: return None
    return {
        "crawlability":       _serialize_module_score(r.crawlability),
        "schema_depth":       _serialize_module_score(r.schema_depth),
        "crawlability_score": r.crawlability_score,
        "schema_score":       r.schema_score,
    }


def _serialize_entity_report(r) -> dict:
    if r is None: return None
    return {
        "entity_kg":    _serialize_module_score(r.entity_kg),
        "entity_score": r.entity_score,
    }


def _serialize_content_quality_report(r) -> dict:
    if r is None: return None
    return {
        "content_quality":       _serialize_module_score(r.content_quality),
        "off_page":              _serialize_module_score(r.off_page),
        "content_quality_score": r.content_quality_score,
        "off_page_score":        r.off_page_score,
    }


def _serialize_external_authority_report(r) -> dict:
    if r is None: return None
    return {
        "external_authority":       _serialize_module_score(r.external_authority),
        "external_authority_score": r.external_authority_score,
    }


def _serialize_ai_visibility_report(r) -> dict:
    if r is None: return None
    d = {
        "ai_visibility":       _serialize_module_score(r.ai_visibility),
        "ai_visibility_score": r.ai_visibility_score,
    }
    # Include live AI test results if available
    ai_test = getattr(r, "ai_test_result", None)
    if ai_test and ai_test.tested:
        from core.ai_tester import serialize_ai_test_result
        d["ai_test_result"] = serialize_ai_test_result(ai_test)
    return d


def _serialize_external_validation(ext) -> dict:
    if ext is None: return None
    profiles = []
    for p in ext.profiles:
        profiles.append({
            "platform": p.platform,
            "exists": p.exists,
            "url": p.url,
            "rating": p.rating,
            "review_count": p.review_count,
            "verification_status": p.verification_status,
            "error_message": p.error_message,
            "extra_data": p.extra_data,
        })
    return {
        "profiles": profiles,
        "profiles_found": ext.profiles_found,
        "profiles_missing": ext.profiles_missing,
        "profiles_errored": ext.profiles_errored,
        "validation_time_ms": ext.validation_time_ms,
        "knowledge_panel_detected": ext.knowledge_panel_detected,
        "wikipedia_detected": ext.wikipedia_detected,
        "wikidata_detected": ext.wikidata_detected,
        "cached": getattr(ext, "cached", False),
    }


def _serialize_site_crawl(crawl) -> dict:
    if crawl is None: return None
    pages_info = []
    for cp in crawl.pages:
        pages_info.append({
            "url": cp.url,
            "page_type": cp.page_type,
            "confidence": cp.confidence,
            "word_count": cp.page.word_count if cp.page else 0,
            "has_error": bool(cp.page.error) if cp.page else True,
        })
    return {
        "pages": pages_info,
        "sitemap_found": crawl.sitemap_found,
        "pages_discovered": crawl.pages_discovered,
        "pages_crawled": crawl.pages_crawled,
        "crawl_time_ms": crawl.crawl_time_ms,
        "errors": crawl.errors,
    }


def _report_to_dict(report) -> dict:
    def _mod(m):
        if m is None: return None
        checks = [{"name":c.name,"score":c.score,"max_score":c.max_score,
                   "status":c.status,"found":c.found,"impact":c.impact,
                   "how_to_fix":c.how_to_fix,"category":getattr(c,"category","SEO"),
                   "effort":getattr(c,"effort","medium"),
                   "details":getattr(c,"details",None)}
                  for c in m.checks]
        return {"module": m.module, "score": m.score, "checks": checks}

    d = {
        "url": report.url, "email": report.email, "keyword": report.keyword,
        "fetch_time_ms": report.fetch_time_ms, "error": report.error,
        "overall_score": report.overall_score, "seo_score": report.seo_score,
        "ai_score": report.ai_score, "overall_grade": report.overall_grade,
        "overall_color": report.overall_color,
        "seo_module":              _mod(report.seo_module),
        "ai_module":               _mod(report.ai_module),
        "geo_report":              _serialize_geo_report(report.geo_report),
        "crawlability_report":     _serialize_crawlability_report(report.crawlability_report),
        "entity_report":           _serialize_entity_report(report.entity_report),
        "content_quality_report":  _serialize_content_quality_report(report.content_quality_report),
        "insights": report.insights,
    }
    # NEW fields — backward compatible (only added if they exist on report)
    if hasattr(report, "external_authority_report"):
        d["external_authority_report"] = _serialize_external_authority_report(
            report.external_authority_report)
    if hasattr(report, "ai_visibility_report"):
        d["ai_visibility_report"] = _serialize_ai_visibility_report(
            report.ai_visibility_report)
    if hasattr(report, "external_validation"):
        d["external_validation"] = _serialize_external_validation(
            report.external_validation)
    if hasattr(report, "site_crawl_result"):
        d["site_crawl_result"] = _serialize_site_crawl(report.site_crawl_result)
    if hasattr(report, "audit_mode"):
        d["audit_mode"] = report.audit_mode
    return d


def save_audit(report):
    try:
        domain = urlparse(report.url).netloc.replace("www.","")
        full_json = json.dumps(_report_to_dict(report), ensure_ascii=False)
        conn = _get_conn()
        cur = conn.execute("""INSERT INTO seo_audits
            (url,email,keyword,domain,overall_score,seo_score,ai_score,overall_grade,fetch_time_ms,error,full_report)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (report.url, report.email, report.keyword, domain,
             report.overall_score, report.seo_score, report.ai_score,
             report.overall_grade, report.fetch_time_ms, report.error, full_json))
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"[storage] insert failed: {e}"); return None

def get_recent_audits(limit=100, email=None):
    try:
        query = """SELECT id,created_at,url,email,keyword,domain,
            overall_score,seo_score,ai_score,overall_grade,fetch_time_ms,error
            FROM seo_audits """
        params = []
        if email:
            query += "WHERE email=? "
            params.append(email)
        query += "ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = _get_conn().execute(query, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as e: print(f"[storage] select failed: {e}"); return []

def get_audit_by_id(audit_id):
    try:
        row = _get_conn().execute(
            "SELECT full_report,created_at FROM seo_audits WHERE id=?", (audit_id,)).fetchone()
        if row and row["full_report"]:
            d = json.loads(row["full_report"]); d["saved_at"] = row["created_at"]; return d
        return None
    except Exception as e: print(f"[storage] get_by_id failed: {e}"); return None

def get_stats(email=None):
    try:
        query = """SELECT COUNT(*) AS total_audits,
            COUNT(DISTINCT email) AS unique_leads, COUNT(DISTINCT domain) AS unique_domains,
            ROUND(AVG(overall_score),1) AS avg_overall, ROUND(AVG(seo_score),1) AS avg_seo,
            ROUND(AVG(ai_score),1) AS avg_ai,
            SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) AS error_count
            FROM seo_audits"""
        params = []
        if email:
            query += " WHERE email=?"
            params.append(email)
        row = _get_conn().execute(query, params).fetchone()
        return dict(row) if row else {}
    except: return {}

def export_csv():
    import csv, io
    rows = get_recent_audits(10000)
    if not rows: return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
    return buf.getvalue()

# --- User Management ---

def create_user(email, password_hash, role='user'):
    try:
        conn = _get_conn()
        cur = conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                           (email, password_hash, role))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None  # Email exists

def get_user_by_email(email):
    try:
        row = _get_conn().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None
    except: return None

def update_user_password(email, new_password_hash):
    try:
        conn = _get_conn()
        conn.execute("UPDATE users SET password_hash=? WHERE email=?", (new_password_hash, email))
        conn.commit()
        return True
    except: return False

def get_all_users():
    try:
        rows = _get_conn().execute("SELECT id, email, role, created_at FROM users ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    except: return []

def update_user_role(email, new_role):
    try:
        conn = _get_conn()
        conn.execute("UPDATE users SET role=? WHERE email=?", (new_role, email))
        conn.commit()
        return True
    except: return False

def delete_user(email):
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM users WHERE email=?", (email,))
        conn.commit()
        return True
    except: return False