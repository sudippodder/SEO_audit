"""
signal_aggregator.py
Aggregates signals from multiple crawled pages into a unified view.
Merges entity, trust, content, and authority signals from all page types.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from .site_crawler import SiteCrawlResult, CrawledPage
from .fetcher import ParsedPage


@dataclass
class AggregatedSignals:
    """Combined signals from all crawled pages for unified scoring."""

    # ── Entity signals (best from any page) ───────────────────────────────
    organization_schema: dict = field(default_factory=dict)
    same_as_links: List[str] = field(default_factory=list)
    nap_phone: str = ""
    nap_address: str = ""
    schema_nap: dict = field(default_factory=dict)
    has_author_schema: bool = False
    has_breadcrumb_schema: bool = False
    has_service_schema: bool = False
    has_howto_article_schema: bool = False

    # ── Trust signals (union across all pages) ────────────────────────────
    testimonials_found: bool = False
    case_studies_found: bool = False
    team_content_found: bool = False
    about_content_found: bool = False
    trust_badges_found: List[str] = field(default_factory=list)
    contact_info_found: bool = False

    # ── External links (union across all pages) ───────────────────────────
    all_social_links: dict = field(default_factory=dict)
    all_review_platform_links: dict = field(default_factory=dict)
    all_external_entity_links: dict = field(default_factory=dict)
    all_press_mention_links: List[str] = field(default_factory=list)

    # ── Content metrics (aggregated) ──────────────────────────────────────
    total_word_count: int = 0
    total_pages_with_schema: int = 0
    total_pages_with_faq: int = 0
    total_pages_with_blog: int = 0
    avg_readability: float = 0.0
    total_statistics_count: int = 0
    total_quotable_sentences: int = 0

    # ── Technical signals (from homepage primarily) ───────────────────────
    has_llms_txt: bool = False
    has_robots_txt: bool = False
    has_xml_sitemap: bool = False
    robots_ai_directives: dict = field(default_factory=dict)
    avg_fetch_time_ms: int = 0

    # ── Page type coverage ────────────────────────────────────────────────
    page_types_found: List[str] = field(default_factory=list)
    page_types_missing: List[str] = field(default_factory=list)
    pages_crawled: int = 0

    # ── All schema types across site ──────────────────────────────────────
    all_schema_types: List[str] = field(default_factory=list)

    # ── Date signals ──────────────────────────────────────────────────────
    most_recent_date_modified: str = ""

    # Source pages map (for traceability)
    signal_sources: Dict[str, List[str]] = field(default_factory=dict)
    # e.g. {"testimonials": ["homepage", "reviews"], "nap": ["contact"]}


def aggregate_signals(crawl_result: SiteCrawlResult) -> AggregatedSignals:
    """
    Merge signals from multiple crawled pages into a single AggregatedSignals.

    Strategy:
    - Entity/schema: take best (most complete) from any page
    - Trust/authority: union across all pages
    - Content metrics: sum or average as appropriate
    - Technical: from homepage primarily
    """
    agg = AggregatedSignals()
    agg.pages_crawled = crawl_result.pages_crawled

    # Track page types
    found_types: Set[str] = set()
    expected_types = {"homepage", "about", "contact", "services", "blog", "case_study", "team", "reviews"}
    readability_scores: List[float] = []
    fetch_times: List[int] = []
    all_schema: Set[str] = set()
    signal_sources: Dict[str, List[str]] = {}

    def _record_source(signal_name: str, page_type: str):
        signal_sources.setdefault(signal_name, []).append(page_type)

    for cp in crawl_result.pages:
        page: ParsedPage = cp.page
        ptype = cp.page_type
        found_types.add(ptype)
        fetch_times.append(page.fetch_time_ms)

        # ── Entity / Schema ───────────────────────────────────────────────
        if page.organization_schema and not agg.organization_schema:
            agg.organization_schema = page.organization_schema
            _record_source("organization_schema", ptype)

        if page.same_as_links:
            for link in page.same_as_links:
                if link not in agg.same_as_links:
                    agg.same_as_links.append(link)
            _record_source("same_as_links", ptype)

        if page.nap_phone and not agg.nap_phone:
            agg.nap_phone = page.nap_phone
            _record_source("nap_phone", ptype)

        if page.nap_address and not agg.nap_address:
            agg.nap_address = page.nap_address
            _record_source("nap_address", ptype)

        if page.schema_nap.get("name") and not agg.schema_nap.get("name"):
            agg.schema_nap = page.schema_nap
            _record_source("schema_nap", ptype)

        if page.has_author_schema:
            agg.has_author_schema = True
            _record_source("author_schema", ptype)

        if page.has_breadcrumb_schema:
            agg.has_breadcrumb_schema = True
            _record_source("breadcrumb_schema", ptype)

        if page.has_service_schema:
            agg.has_service_schema = True
            _record_source("service_schema", ptype)

        if page.has_howto_article_schema:
            agg.has_howto_article_schema = True
            _record_source("howto_article_schema", ptype)

        for st in page.schema_types:
            all_schema.add(st)

        if page.schema_types:
            agg.total_pages_with_schema += 1

        # ── Trust signals ─────────────────────────────────────────────────
        full_lower = page.full_text.lower()
        trust_kws = ["testimonial", "review", "says", "client says", "★", "⭐", "rated", "rating"]
        if any(kw in full_lower for kw in trust_kws) or (page.soup and page.soup.find("blockquote")):
            agg.testimonials_found = True
            _record_source("testimonials", ptype)

        case_kws = ["case study", "case studies", "success story", "results", "outcome", "achieved", "roi"]
        if any(kw in full_lower for kw in case_kws):
            agg.case_studies_found = True
            _record_source("case_studies", ptype)

        about_signals = ["about us", "our team", "meet the team", "our story", "founded", "our mission"]
        if any(s in full_lower for s in about_signals) or ptype == "about":
            agg.about_content_found = True
            _record_source("about_content", ptype)

        if ptype == "team" or any("team" in h.lower() for h in page.all_headings):
            agg.team_content_found = True
            _record_source("team_content", ptype)

        trust_badge_kws = ["certified", "certification", "award", "accredited", "partner",
                           "featured in", "as seen in", "member of", "verified", "iso"]
        page_badges = [s for s in trust_badge_kws if s in full_lower]
        for badge in page_badges:
            if badge not in agg.trust_badges_found:
                agg.trust_badges_found.append(badge)
                _record_source("trust_badges", ptype)

        contact_kws = ["contact", "phone", "email", "address", "location", "get in touch"]
        if any(kw in full_lower for kw in contact_kws) or ptype == "contact":
            agg.contact_info_found = True
            _record_source("contact_info", ptype)

        # ── External links ────────────────────────────────────────────────
        for key, val in page.social_links.items():
            if key not in agg.all_social_links:
                agg.all_social_links[key] = val
                _record_source(f"social_{key}", ptype)

        for key, val in page.review_platform_links.items():
            if key not in agg.all_review_platform_links:
                agg.all_review_platform_links[key] = val
                _record_source(f"review_{key}", ptype)

        for key, val in page.external_entity_links.items():
            if key not in agg.all_external_entity_links:
                agg.all_external_entity_links[key] = val
                _record_source(f"entity_{key}", ptype)

        for link in page.press_mention_links:
            if link not in agg.all_press_mention_links:
                agg.all_press_mention_links.append(link)
                _record_source("press_mentions", ptype)

        # ── Content metrics ───────────────────────────────────────────────
        agg.total_word_count += page.word_count

        if page.readability_score > 0:
            readability_scores.append(page.readability_score)

        if page.has_faq_section or page.has_faq_schema:
            agg.total_pages_with_faq += 1

        if ptype == "blog":
            agg.total_pages_with_blog += 1

        agg.total_statistics_count += page.statistics_count
        agg.total_quotable_sentences += page.quotable_sentence_count

        # ── Technical (from homepage or first available) ──────────────────
        if ptype == "homepage" or not agg.has_robots_txt:
            if page.has_llms_txt:
                agg.has_llms_txt = True
            if page.has_robots_txt:
                agg.has_robots_txt = True
            if page.has_xml_sitemap:
                agg.has_xml_sitemap = True
            if page.robots_ai_directives:
                agg.robots_ai_directives = page.robots_ai_directives

        # ── Date freshness ────────────────────────────────────────────────
        if page.date_modified:
            if not agg.most_recent_date_modified or page.date_modified > agg.most_recent_date_modified:
                agg.most_recent_date_modified = page.date_modified

    # ── Compute averages ──────────────────────────────────────────────────
    if readability_scores:
        agg.avg_readability = sum(readability_scores) / len(readability_scores)
    if fetch_times:
        agg.avg_fetch_time_ms = sum(fetch_times) // len(fetch_times)

    # ── Page type coverage ────────────────────────────────────────────────
    agg.page_types_found = sorted(found_types)
    agg.page_types_missing = sorted(expected_types - found_types)
    agg.all_schema_types = sorted(all_schema)
    agg.signal_sources = signal_sources

    return agg


def create_synthetic_page(agg: AggregatedSignals, homepage: ParsedPage) -> ParsedPage:
    """
    Create a synthetic ParsedPage that overlays aggregated signals onto the homepage.
    This allows existing scoring modules to run against the full-site data
    without major refactoring.
    """
    import copy
    synth = copy.copy(homepage)

    # Overlay aggregated entity signals
    if agg.organization_schema:
        synth.organization_schema = agg.organization_schema
    if agg.same_as_links:
        synth.same_as_links = agg.same_as_links
    if agg.nap_phone:
        synth.nap_phone = agg.nap_phone
    if agg.nap_address:
        synth.nap_address = agg.nap_address
    if agg.schema_nap.get("name"):
        synth.schema_nap = agg.schema_nap

    # Overlay schema signals
    synth.has_author_schema = agg.has_author_schema or synth.has_author_schema
    synth.has_breadcrumb_schema = agg.has_breadcrumb_schema or synth.has_breadcrumb_schema
    synth.has_service_schema = agg.has_service_schema or synth.has_service_schema
    synth.has_howto_article_schema = agg.has_howto_article_schema or synth.has_howto_article_schema
    synth.schema_types = list(set(synth.schema_types + agg.all_schema_types))

    # Overlay external links
    synth.social_links = {**synth.social_links, **agg.all_social_links}
    synth.review_platform_links = {**synth.review_platform_links, **agg.all_review_platform_links}
    synth.external_entity_links = {**synth.external_entity_links, **agg.all_external_entity_links}
    for link in agg.all_press_mention_links:
        if link not in synth.press_mention_links:
            synth.press_mention_links.append(link)

    # Overlay trust text signals (append to full_text for check functions)
    trust_additions = []
    if agg.testimonials_found and "testimonial" not in synth.full_text.lower():
        trust_additions.append("Our clients have left many testimonials and reviews about our work.")
    if agg.case_studies_found and "case study" not in synth.full_text.lower():
        trust_additions.append("We have documented case studies and success stories showing our results and outcomes.")
    if agg.about_content_found and "about us" not in synth.full_text.lower():
        trust_additions.append("About us: Our company has a detailed about page with our story and mission.")
    if agg.team_content_found and "our team" not in synth.full_text.lower():
        trust_additions.append("Meet the team: We have a dedicated team page with leadership bios.")
    if agg.contact_info_found and "contact" not in synth.full_text.lower():
        trust_additions.append("Contact us: Phone, email, and address available on our contact page.")
    for badge in agg.trust_badges_found:
        if badge not in synth.full_text.lower():
            trust_additions.append(f"We are {badge}.")

    if trust_additions:
        extra_text = " ".join(trust_additions)
        synth.full_text = synth.full_text + " " + extra_text
        synth.word_count = len(synth.full_text.split())

    # Overlay content metrics
    synth.statistics_count = max(synth.statistics_count, agg.total_statistics_count)
    synth.quotable_sentence_count = max(synth.quotable_sentence_count, agg.total_quotable_sentences)

    # Overlay technical signals
    synth.has_llms_txt = agg.has_llms_txt or synth.has_llms_txt
    synth.has_robots_txt = agg.has_robots_txt or synth.has_robots_txt
    synth.has_xml_sitemap = agg.has_xml_sitemap or synth.has_xml_sitemap
    if agg.robots_ai_directives:
        synth.robots_ai_directives = agg.robots_ai_directives

    # Overlay date
    if agg.most_recent_date_modified:
        synth.date_modified = agg.most_recent_date_modified

    return synth
