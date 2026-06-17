"""audit_engine.py — Orchestrates fetch + all scoring modules. Returns AuditReport.
Supports both single-page and full-site audit modes."""
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
from .external_authority_scorer import score as external_authority_score, ExternalAuthorityReport
from .ai_visibility_scorer import score as ai_visibility_score, AIVisibilityReport
from .site_crawler import crawl_site, SiteCrawlResult, get_page_type_coverage
from .signal_aggregator import aggregate_signals, create_synthetic_page, AggregatedSignals
from .external_validator import validate_external_profiles, ExternalValidationResult
from .ai_tester import run_ai_visibility_test, AITestResult

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
    # ── NEW: Full-site + External + AI Visibility ──────────────────────────
    external_authority_report: Optional[ExternalAuthorityReport] = None
    ai_visibility_report: Optional[AIVisibilityReport] = None
    site_crawl_result: Optional[SiteCrawlResult] = None
    external_validation: Optional[ExternalValidationResult] = None
    aggregated_signals: Optional[AggregatedSignals] = None
    audit_mode: str = "single"  # "single" | "full_site"
    # ──────────────────────────────────────────────────────────────────────
    insights: List[Dict[str, Any]] = field(default_factory=list)
    page: Optional[Any] = None


def run_audit(url: str, email: str, keyword: str = "",
              check_broken_links: bool = False,
              full_site: bool = False,
              openai_api_key: str = "",
              progress_callback=None) -> AuditReport:
    """
    Run the GEO audit.

    Args:
        url: Website URL to audit
        email: User's email
        keyword: Target keyword
        check_broken_links: Whether to check for broken links
        full_site: If True, crawl multiple pages and validate external profiles
        openai_api_key: If provided, run live AI visibility tests via OpenAI
        progress_callback: Function to call with (percentage, message)
    """
    def _prog(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)

    site_crawl = None
    agg_signals = None
    ext_validation = None
    ai_test_result = None

    if full_site:
        # ── FULL SITE MODE ────────────────────────────────────────────────
        _prog(5, "Discovering site pages…")
        site_crawl = crawl_site(url)
        if not site_crawl.pages:
            return AuditReport(url=url, email=email, keyword=keyword,
                fetch_time_ms=0, error="Could not crawl any pages on this site.",
                overall_score=0, seo_score=0, ai_score=0,
                overall_grade="Error", overall_color="red", audit_mode="full_site")

        # Get homepage
        homepage = site_crawl.pages[0].page
        if homepage.error:
            return AuditReport(url=url, email=email, keyword=keyword,
                fetch_time_ms=homepage.fetch_time_ms, error=homepage.error,
                overall_score=0, seo_score=0, ai_score=0,
                overall_grade="Error", overall_color="red", audit_mode="full_site")

        _prog(25, "Aggregating site signals…")
        # Aggregate signals across all pages
        agg_signals = aggregate_signals(site_crawl)

        # Create synthetic page with merged signals for scoring modules
        page = create_synthetic_page(agg_signals, homepage)

        _prog(40, "Validating external profiles (Trustpilot, G2, LinkedIn…)")
        # Run external profile validation
        ext_validation = validate_external_profiles(
            domain=page.domain,
            brand_name=page.domain.split(".")[0].capitalize(),
            social_links=agg_signals.all_social_links,
            review_platform_links=agg_signals.all_review_platform_links,
            external_entity_links=agg_signals.all_external_entity_links,
            same_as_links=agg_signals.same_as_links,
        )
        fetch_time = site_crawl.crawl_time_ms
    else:
        # ── SINGLE PAGE MODE (original) ───────────────────────────────────
        _prog(10, "Fetching page content…")
        page = fetch(url)
        if page.error:
            return AuditReport(url=url, email=email, keyword=keyword,
                fetch_time_ms=page.fetch_time_ms, error=page.error,
                overall_score=0, seo_score=0, ai_score=0,
                overall_grade="Error", overall_color="red")

        _prog(35, "Validating external profiles (Trustpilot, G2, LinkedIn…)")
        # Even in single-page mode, validate external profiles
        ext_validation = validate_external_profiles(
            domain=page.domain,
            brand_name=page.domain.split(".")[0].capitalize(),
            social_links=page.social_links,
            review_platform_links=page.review_platform_links,
            external_entity_links=page.external_entity_links,
            same_as_links=page.same_as_links,
        )
        fetch_time = page.fetch_time_ms

    _prog(55, "Analysing SEO and Schema signals…")
    # ── Run all scoring modules ───────────────────────────────────────────
    seo  = seo_score(page, keyword)
    ai   = ai_score(page, keyword)
    crawl = crawlability_score(page)
    entity = entity_score(page)
    cq   = content_quality_score(page, keyword)

    _prog(65, "Evaluating AI citation readiness (GEO modules)…")
    geo  = geo_score(page, legacy_ai_score=ai.score)

    _prog(75, "Scoring External Authority…")
    # NEW: External authority + AI visibility
    ext_auth = external_authority_score(ext_validation)

    # Run live AI visibility test if API key provided
    brand_name = page.domain.split(".")[0].capitalize()
    if openai_api_key:
        _prog(85, "🤖 Testing AI visibility with ChatGPT…")
        ai_test_result = run_ai_visibility_test(
            brand_name=brand_name,
            domain=page.domain,
            keyword=keyword,
            api_key=openai_api_key,
        )

    _prog(90, "Scoring AI Visibility…")
    ai_vis = ai_visibility_score(page, ext_validation, ai_test_result)

    # Optional: broken links check
    if check_broken_links:
        _prog(92, "Checking broken links…")
        _check_broken_links(page)

    _prog(95, "Calculating final scores…")

    # ── Weighted overall score ────────────────────────────────────────────
    if full_site:
        # Full site: includes external authority and AI visibility
        # Crawlability 15% | Schema 15% | Entity 15% | Extractability 10%
        # Trust 10% | Content Quality 10% | External Authority 15% | AI Visibility 10%
        overall = round(
            crawl.crawlability_score       * 0.15 +
            crawl.schema_score             * 0.15 +
            entity.entity_score            * 0.15 +
            geo.extractability.score       * 0.10 +
            geo.trust_signals.score        * 0.10 +
            cq.content_quality_score       * 0.10 +
            ext_auth.external_authority_score * 0.15 +
            ai_vis.ai_visibility_score     * 0.10
        )
    else:
        # Single page: original weights + reduced external authority
        # Crawlability 18% | Schema 18% | Entity 14% | Extractability 13%
        # Trust 13% | Content Quality 9% | Off-Page 5% | External Authority 5% | AI Visibility 5%
        overall = round(
            crawl.crawlability_score       * 0.18 +
            crawl.schema_score             * 0.18 +
            entity.entity_score            * 0.14 +
            geo.extractability.score       * 0.13 +
            geo.trust_signals.score        * 0.13 +
            cq.content_quality_score       * 0.09 +
            cq.off_page_score              * 0.05 +
            ext_auth.external_authority_score * 0.05 +
            ai_vis.ai_visibility_score     * 0.05
        )

    grade, color = _grade(overall)
    insights = _insights(geo, crawl, entity, cq, seo, ext_auth, ai_vis)

    return AuditReport(
        url=url, email=email, keyword=keyword,
        fetch_time_ms=fetch_time, error=None,
        overall_score=overall,
        seo_score=seo.score,
        ai_score=geo.overall_ai_score,
        overall_grade=grade, overall_color=color,
        seo_module=seo, ai_module=ai,
        geo_report=geo,
        crawlability_report=crawl,
        entity_report=entity,
        content_quality_report=cq,
        external_authority_report=ext_auth,
        ai_visibility_report=ai_vis,
        site_crawl_result=site_crawl,
        external_validation=ext_validation,
        aggregated_signals=agg_signals,
        audit_mode="full_site" if full_site else "single",
        insights=insights, page=page,
    )


def _insights(geo, crawl, entity, cq, seo, ext_auth=None, ai_vis=None):
    """Pull top 5 insights from all modules, GEO/Crawlability priority."""
    all_checks = []
    # Priority order: external authority > crawlability > entity > GEO modules > AI vis > content quality > SEO
    if ext_auth:
        all_checks.extend([(c, 0) for c in ext_auth.external_authority.checks])
    for mod in [crawl.crawlability, crawl.schema_depth]:
        all_checks.extend([(c, 1) for c in mod.checks])
    all_checks.extend([(c, 2) for c in entity.entity_kg.checks])
    for mod in [geo.citation_readiness, geo.entity_clarity, geo.extractability,
                geo.trust_signals, geo.overview_readiness, geo.information_gain]:
        all_checks.extend([(c, 3) for c in mod.checks])
    if ai_vis:
        all_checks.extend([(c, 4) for c in ai_vis.ai_visibility.checks])
    for mod in [cq.content_quality, cq.off_page]:
        all_checks.extend([(c, 5) for c in mod.checks])
    all_checks.extend([(c, 6) for c in seo.checks])

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