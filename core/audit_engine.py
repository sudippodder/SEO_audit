"""audit_engine.py — Orchestrates fetch + scoring. Returns AuditReport."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .fetcher import fetch
from .seo_scorer import score as seo_score, ModuleResult
from .ai_scorer import score as ai_score
from .geo_scorer import score as geo_score, GeoReport

def _grade(s):
    if s <= 40: return "Poor", "red"
    if s <= 70: return "Average", "amber"
    return "Strong", "green"

@dataclass
class AuditReport:
    url: str; email: str; keyword: str
    fetch_time_ms: int; error: Optional[str]
    overall_score: int; seo_score: int; ai_score: int
    overall_grade: str; overall_color: str
    seo_module: Optional[ModuleResult] = None
    ai_module: Optional[ModuleResult] = None
    geo_report: Optional[GeoReport] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    page: Optional[Any] = None

def run_audit(url: str, email: str, keyword: str = "") -> AuditReport:
    page = fetch(url)
    if page.error:
        return AuditReport(url=url, email=email, keyword=keyword,
            fetch_time_ms=page.fetch_time_ms, error=page.error,
            overall_score=0, seo_score=0, ai_score=0,
            overall_grade="Error", overall_color="red")
    seo = seo_score(page, keyword)
    ai  = ai_score(page, keyword)
    geo = geo_score(page, legacy_ai_score=ai.score)

    # Overall blends SEO (35%) + GEO overall_ai_score (65%)
    overall = round(seo.score * 0.35 + geo.overall_ai_score * 0.65)
    grade, color = _grade(overall)
    insights = _insights(geo, seo)
    return AuditReport(url=url, email=email, keyword=keyword,
        fetch_time_ms=page.fetch_time_ms, error=None,
        overall_score=overall, seo_score=seo.score, ai_score=geo.overall_ai_score,
        overall_grade=grade, overall_color=color,
        seo_module=seo, ai_module=ai, geo_report=geo,
        insights=insights, page=page)

def _insights(geo: GeoReport, seo):
    """Pull top 5 insights prioritising GEO fails/warns, then SEO."""
    geo_checks = []
    for mod in [geo.citation_readiness, geo.entity_clarity, geo.extractability,
                geo.trust_signals, geo.overview_readiness, geo.information_gain]:
        geo_checks.extend(mod.checks)

    bad_geo = sorted(
        [c for c in geo_checks if c.status in ("fail", "warn")],
        key=lambda c: (0 if c.status == "fail" else 1, -(c.max_score - c.score))
    )
    bad_seo = sorted(
        [c for c in seo.checks if c.status in ("fail", "warn")],
        key=lambda c: (0 if c.status == "fail" else 1, -(c.max_score - c.score))
    )

    # GEO checks take first 4 slots, SEO fills the last 1 (for balance)
    combined = bad_geo[:4] + bad_seo[:1]
    out = []
    for c in combined[:5]:
        out.append({
            "icon": "🔴" if c.status == "fail" else "🟡",
            "title": c.name,
            "found": c.found,
            "impact": c.impact,
            "status": c.status,
        })
    return out