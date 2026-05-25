"""audit_engine.py — Orchestrates fetch + all scoring modules. Returns AuditReport."""
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .fetcher import fetch
from .seo_scorer import score as seo_score, ModuleResult
from .ai_scorer import score as ai_score
from .geo_scorer import score as geo_score, GeoReport
from .crawlability_scorer import score as crawlability_score, CrawlabilityReport
from .entity_scorer import score as entity_score, EntityReport
from .content_quality_scorer import score as content_quality_score, ContentQualityReport

HEADERS = {"User-Agent": "Mozilla/5.0"}

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
    crawlability_report: Optional[CrawlabilityReport] = None
    entity_report: Optional[EntityReport] = None
    content_quality_report: Optional[ContentQualityReport] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    page: Optional[Any] = None


def run_audit(url: str, email: str, keyword: str = "",
              check_broken_links: bool = False) -> AuditReport:
    page = fetch(url)
    if page.error:
        return AuditReport(url=url, email=email, keyword=keyword,
            fetch_time_ms=page.fetch_time_ms, error=page.error,
            overall_score=0, seo_score=0, ai_score=0,
            overall_grade="Error", overall_color="red")

    # Run all scoring modules
    seo  = seo_score(page, keyword)
    ai   = ai_score(page, keyword)
    geo  = geo_score(page, legacy_ai_score=ai.score)
    crawl = crawlability_score(page)
    entity = entity_score(page)
    cq   = content_quality_score(page, keyword)

    # Optional: broken links check
    if check_broken_links:
        _check_broken_links(page)

    # ── Weighted overall score (PDF model) ───────────────────────────────────
    # Crawlability 20% | Schema 20% | Entity 15% | Content Extractability 15%
    # Evidence/Trust 15% | Content Quality 10% | Off-Page 5%
    overall = round(
        crawl.crawlability_score  * 0.20 +
        crawl.schema_score        * 0.20 +
        entity.entity_score       * 0.15 +
        geo.extractability.score  * 0.15 +
        geo.trust_signals.score   * 0.15 +
        cq.content_quality_score  * 0.10 +
        cq.off_page_score         * 0.05
    )
    grade, color = _grade(overall)
    insights = _insights(geo, crawl, entity, cq, seo)

    return AuditReport(
        url=url, email=email, keyword=keyword,
        fetch_time_ms=page.fetch_time_ms, error=None,
        overall_score=overall,
        seo_score=seo.score,
        ai_score=geo.overall_ai_score,
        overall_grade=grade, overall_color=color,
        seo_module=seo, ai_module=ai,
        geo_report=geo,
        crawlability_report=crawl,
        entity_report=entity,
        content_quality_report=cq,
        insights=insights, page=page,
    )


def _insights(geo, crawl, entity, cq, seo):
    """Pull top 5 insights from all modules, GEO/Crawlability priority."""
    all_checks = []
    # Priority order: crawlability > entity > GEO modules > content quality > SEO
    for mod in [crawl.crawlability, crawl.schema_depth]:
        all_checks.extend([(c, 0) for c in mod.checks])
    all_checks.extend([(c, 1) for c in entity.entity_kg.checks])
    for mod in [geo.citation_readiness, geo.entity_clarity, geo.extractability,
                geo.trust_signals, geo.overview_readiness, geo.information_gain]:
        all_checks.extend([(c, 2) for c in mod.checks])
    for mod in [cq.content_quality, cq.off_page]:
        all_checks.extend([(c, 3) for c in mod.checks])
    all_checks.extend([(c, 4) for c in seo.checks])

    bad = sorted(
        [(c, p) for c, p in all_checks if c.status in ("fail", "warn")],
        key=lambda x: (x[1], 0 if x[0].status == "fail" else 1, -(x[0].max_score - x[0].score))
    )
    out = []
    for c, _ in bad[:5]:
        out.append({
            "icon": "🔴" if c.status == "fail" else "🟡",
            "title": c.name,
            "found": c.found,
            "impact": c.impact,
            "status": c.status,
            "effort": getattr(c, "effort", "medium"),
        })
    return out


def _check_broken_links(page, sample=15):
    """Optional: HEAD-check a sample of internal links for broken ones."""
    checked = 0
    broken = []
    links = list(set(page.internal_links))[:sample]
    for link in links:
        try:
            r = requests.head(link, headers=HEADERS, timeout=5, allow_redirects=True)
            if r.status_code >= 400:
                broken.append((link, r.status_code))
        except Exception:
            broken.append((link, "timeout"))
        checked += 1
    # Store results on page for use in a check card
    page._broken_links = broken
    page._links_checked = checked