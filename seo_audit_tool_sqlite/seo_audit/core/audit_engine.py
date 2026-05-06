"""
audit_engine.py
Orchestrates fetch + all scoring modules.
Returns a single AuditReport dataclass.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .fetcher import fetch, ParsedPage
from .seo_scorer import score as seo_score, ModuleResult
from .content_scorer import score as content_score
from .ai_scorer import score as ai_score
from .opportunity_scorer import score as opportunity_score


def _grade(score: int) -> tuple:
    """Return (label, colour_key) for a score."""
    if score <= 40:
        return "Poor", "red"
    elif score <= 70:
        return "Average", "amber"
    return "Strong", "green"


@dataclass
class AuditReport:
    url: str
    email: str
    fetch_time_ms: int
    error: Optional[str]
    overall_score: int
    overall_grade: str
    overall_color: str
    modules: List[ModuleResult] = field(default_factory=list)
    insights: List[Dict[str, Any]] = field(default_factory=list)
    page: Optional[Any] = None  # ParsedPage — excluded from storage


def run_audit(url: str, email: str) -> AuditReport:
    """Fetch a URL and run all four scoring modules."""

    page = fetch(url)

    if page.error:
        return AuditReport(
            url=url, email=email,
            fetch_time_ms=page.fetch_time_ms,
            error=page.error,
            overall_score=0, overall_grade="Error", overall_color="red",
        )

    seo = seo_score(page)
    content = content_score(page)
    ai = ai_score(page)
    opp = opportunity_score(seo, content, ai)

    overall = round((seo.score + content.score + ai.score + opp.score) / 4)
    grade, color = _grade(overall)

    insights = _generate_insights(seo, content, ai, opp)

    return AuditReport(
        url=url, email=email,
        fetch_time_ms=page.fetch_time_ms,
        error=None,
        overall_score=overall,
        overall_grade=grade,
        overall_color=color,
        modules=[seo, content, ai, opp],
        insights=insights,
        page=page,
    )


def _generate_insights(seo, content, ai, opp) -> List[Dict]:
    """Pick the 5 most impactful insights from failed/warned checks."""
    all_checks = seo.checks + content.checks + ai.checks

    bad = [c for c in all_checks if c.status in ("fail", "warn")]
    bad.sort(key=lambda c: (0 if c.status == "fail" else 1, -(c.max_score - c.score)))

    insights = []
    for c in bad[:5]:
        insights.append({
            "icon": "🔴" if c.status == "fail" else "🟡",
            "title": c.name,
            "finding": c.finding,
            "impact": c.impact,
            "status": c.status,
        })

    # Pad with positives if fewer than 3 issues
    if len(insights) < 3:
        good = [c for c in all_checks if c.status == "pass"]
        for c in good[:3 - len(insights)]:
            insights.append({
                "icon": "🟢",
                "title": c.name,
                "finding": c.finding,
                "impact": c.impact,
                "status": "pass",
            })

    return insights[:5]
