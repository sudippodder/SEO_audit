"""
crawlability_checks.py
Section 1: Technical AI Crawlability
Section 2: Schema Markup Depth
"""
import re
from .geo_checks import CheckResult


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: TECHNICAL AI CRAWLABILITY
# ═══════════════════════════════════════════════════════════════════════════

def check_llms_txt(page, kw=None):
    """llms.txt — the emerging standard telling AI crawlers which pages to index."""
    if page.has_llms_txt:
        return CheckResult("llms.txt detected", 4, 4, "pass",
            "llms.txt file found at domain root — AI crawlers can discover and follow it.",
            "llms.txt tells ChatGPT, Perplexity, and Claude which pages are AI-indexable.",
            "No action needed. Keep it updated as content changes.", effort="quick")
    return CheckResult("llms.txt detected", 0, 4, "fail",
        "No llms.txt file found at domain root.",
        "Without llms.txt, AI systems lack guidance on which pages to index — a key emerging GEO gap.",
        "Create /llms.txt listing key pages: # Site Title\\n> Description\\n/page/: What this page covers",
        effort="quick")


def check_ai_bot_directives(page, kw=None):
    """robots.txt AI bot directives — GPTBot, ClaudeBot, PerplexityBot, etc."""
    directives = page.robots_ai_directives
    if not page.has_robots_txt:
        return CheckResult("AI bot directives (robots.txt)", 0, 4, "fail",
            "No robots.txt found — AI bots have no crawl guidance.",
            "Without robots.txt, AI crawlers may skip or inconsistently index your site.",
            "Create /robots.txt with explicit Allow: / for GPTBot, ClaudeBot, PerplexityBot, GoogleExtended.",
            effort="quick")
    blocked = [b for b, v in directives.items() if v == "blocked"]
    allowed = [b for b, v in directives.items() if v == "allowed"]
    if blocked:
        return CheckResult("AI bot directives (robots.txt)", 0, 4, "fail",
            f"AI bots are blocked in robots.txt: {', '.join(blocked)}.",
            "Blocking AI bots prevents indexing by ChatGPT, Gemini, Perplexity — critical GEO gap.",
            f"Remove Disallow rules for: {', '.join(blocked)}. Add explicit Allow: / instead.",
            effort="quick")
    if allowed:
        return CheckResult("AI bot directives (robots.txt)", 4, 4, "pass",
            f"AI bots explicitly allowed: {', '.join(allowed)}.",
            "Explicit AI bot permissions ensure consistent crawling by ChatGPT, Gemini, and Perplexity.",
            "No action needed. Monitor for new AI bots as they emerge.", effort="quick")
    return CheckResult("AI bot directives (robots.txt)", 2, 4, "warn",
        "robots.txt found but no AI-specific bot directives detected.",
        "Without explicit directives, AI bots rely on default behaviour — may crawl inconsistently.",
        "Add: User-agent: GPTBot\\nAllow: /\\nUser-agent: ClaudeBot\\nAllow: / to robots.txt",
        effort="quick")


def check_page_render_type(page, kw=None):
    """Page render type — static/SSR pages are far more AI-crawlable than JS-heavy pages."""
    rt = page.page_render_type
    if rt == "static":
        return CheckResult("Page render type (JS vs static/SSR)", 4, 4, "pass",
            f"Page is static or server-side rendered — high AI crawlability ({page.script_count} scripts, {page.word_count} words).",
            "Static/SSR pages are crawled correctly by all AI systems. JS-rendered content is often missed.",
            "No action needed.", effort="complex")
    if rt == "ssr-likely":
        return CheckResult("Page render type (JS vs static/SSR)", 3, 4, "warn",
            f"Page likely uses SSR but has significant JS ({page.script_count} scripts) — partial crawl risk.",
            "Heavy JS can cause AI crawlers to miss dynamically loaded content sections.",
            "Ensure all critical content is in the initial HTML payload. Test by viewing page source.",
            effort="complex")
    return CheckResult("Page render type (JS vs static/SSR)", 0, 4, "fail",
        f"Page appears JS-heavy ({page.script_count} scripts vs {page.word_count} visible words) — poor AI crawlability.",
        "JS-rendered pages are difficult for AI crawlers — many AI systems cannot execute JavaScript.",
        "Migrate to SSR (Next.js, Nuxt, SvelteKit) or add prerendering. Ensure content is in initial HTML.",
        effort="complex")


def check_ttfb(page, kw=None):
    """TTFB — AI crawlers have short fetch timeouts; slow TTFB means missed or incomplete pages."""
    ft = page.fetch_time_ms
    if ft < 500:
        return CheckResult("TTFB (Time to First Byte)", 3, 3, "pass",
            f"Excellent TTFB: {ft}ms — AI crawlers receive content almost instantly.",
            "Fast TTFB ensures AI crawlers don't timeout or deprioritise your pages.",
            "No action needed.", effort="medium")
    if ft < 1200:
        return CheckResult("TTFB (Time to First Byte)", 2, 3, "warn",
            f"Moderate TTFB: {ft}ms — acceptable but improvable.",
            "Slow TTFB increases crawler timeout risk, especially for AI systems with strict limits.",
            "Enable server caching, use CDN, optimise database queries. Target TTFB < 500ms.",
            effort="medium")
    return CheckResult("TTFB (Time to First Byte)", 0, 3, "fail",
        f"Slow TTFB: {ft}ms — AI crawlers may timeout or skip this page.",
        "TTFB over 1.2s significantly reduces crawl frequency and AI indexing probability.",
        "Critical: implement server caching (Redis/Varnish), use CDN, optimise server response.",
        effort="medium")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: SCHEMA MARKUP DEPTH
# ═══════════════════════════════════════════════════════════════════════════

def check_organization_schema(page, kw=None):
    """Organization schema completeness — the foundation of AI entity recognition."""
    org = page.organization_schema
    if not org:
        return CheckResult("Organization schema completeness", 0, 4, "fail",
            "No Organization or LocalBusiness schema found on this page.",
            "Without Organization schema, AI systems cannot reliably identify your business entity.",
            "Add Organization JSON-LD with: name, url, logo, sameAs (Wikipedia/LinkedIn), contactPoint, areaServed.",
            effort="quick")
    required = ["name", "url", "logo"]
    recommended = ["sameAs", "contactPoint", "foundingDate", "areaServed", "numberOfEmployees"]
    present_r = [f for f in required if org.get(f)]
    present_rec = [f for f in recommended if org.get(f)]
    missing_req = [f for f in required if not org.get(f)]
    missing_rec = [f for f in recommended if not org.get(f)]
    all_present = present_r + present_rec
    if not missing_req and len(missing_rec) <= 1:
        return CheckResult("Organization schema completeness", 4, 4, "pass",
            f"Complete Organization schema: {', '.join(all_present[:7])}.",
            "Complete Organization schema is the strongest AI entity identification signal.",
            "No action needed. Verify schema at search.google.com/test/rich-results", effort="quick")
    if not missing_req:
        return CheckResult("Organization schema completeness", 3, 4, "warn",
            f"Organization schema found but missing recommended: {', '.join(missing_rec[:3])}.",
            "Incomplete schema reduces AI entity profile richness and Knowledge Panel eligibility.",
            f"Add to Organization schema: {', '.join(missing_rec[:3])}.", effort="quick")
    return CheckResult("Organization schema completeness", 1, 4, "fail",
        f"Incomplete Organization schema. Missing required fields: {', '.join(missing_req)}.",
        "Missing required fields significantly reduce AI entity recognition confidence.",
        f"Add required fields: {', '.join(missing_req)}. Then add: {', '.join(missing_rec[:2])}.",
        effort="quick")


def check_service_schema(page, kw=None):
    """Service schema — allows AI to accurately describe your specific offerings."""
    if page.has_service_schema:
        return CheckResult("Service schema (per service page)", 3, 3, "pass",
            "Service schema detected — AI can accurately represent your service offerings.",
            "Service schema allows AI to describe your specific offerings accurately in generated answers.",
            "No action needed. Add offers and areaServed if not present.", effort="medium")
    has_any = len(page.schema_types) > 0
    if has_any:
        return CheckResult("Service schema (per service page)", 1, 3, "warn",
            f"Other schema found ({', '.join(page.schema_types[:3])}) but no Service schema.",
            "Without Service schema, AI cannot accurately represent your service offerings.",
            "Add Service JSON-LD: ServiceType, name, description, provider (your org), areaServed, offers.",
            effort="medium")
    return CheckResult("Service schema (per service page)", 0, 3, "fail",
        "No Service schema found. Service pages without structured data are poorly represented in AI.",
        "AI systems may misrepresent or omit your services in generated answers.",
        "Add Service schema to each service page. Include name, description, provider, areaServed.",
        effort="medium")


def check_author_schema(page, kw=None):
    """Person/Author schema — critical for E-E-A-T and AI citation confidence."""
    if page.has_author_schema:
        return CheckResult("Person / Author schema", 3, 3, "pass",
            "Person or Author schema detected — entity markup with credentials found.",
            "Author entity markup boosts E-E-A-T signals and AI citation confidence.",
            "No action needed. Add sameAs (LinkedIn) to strengthen the entity signal.", effort="quick")
    is_content = page.word_count > 500 and len(page.h2_tags) > 1
    if is_content:
        return CheckResult("Person / Author schema", 0, 3, "fail",
            "Content page detected but no Person/Author schema found.",
            "Content without author entity markup is treated as anonymous — lower E-E-A-T and AI trust.",
            "Add Person JSON-LD: name, jobTitle, sameAs (LinkedIn URL), knowsAbout (topics).",
            effort="quick")
    return CheckResult("Person / Author schema", 2, 3, "warn",
        "No Author schema found. Less critical for non-article pages.",
        "Author schema primarily benefits blog posts, guides, and expert opinion content.",
        "Add Person schema on article/blog pages with: name, credentials, and LinkedIn URL.",
        effort="quick")


def check_breadcrumb_schema(page, kw=None):
    """BreadcrumbList schema — helps AI map site hierarchy and content relationships."""
    if page.has_breadcrumb_schema:
        return CheckResult("BreadcrumbList schema", 3, 3, "pass",
            "BreadcrumbList schema detected — AI can understand site hierarchy.",
            "Breadcrumb schema helps AI map content relationships and improves snippet extraction.",
            "No action needed.", effort="quick")
    return CheckResult("BreadcrumbList schema", 0, 3, "fail",
        "No BreadcrumbList schema found.",
        "Without breadcrumb schema, AI cannot understand content hierarchy — reducing context accuracy.",
        "Add BreadcrumbList JSON-LD: Home > Category > Current Page. Validates at Rich Results Test.",
        effort="quick")


def check_howto_article_schema(page, kw=None):
    """HowTo / Article / WebPage schema — eligibility for AI Overview cards."""
    content_types = {"HowTo", "Article", "BlogPosting", "WebPage", "NewsArticle", "FAQPage"}
    found = [t for t in page.schema_types if any(ct.lower() in t.lower() for ct in content_types)]
    if found:
        return CheckResult("HowTo / Article / WebPage schema", 3, 3, "pass",
            f"Content schema found: {', '.join(found)}.",
            "Content-type schema makes pages eligible for AI Overview cards and featured snippets.",
            "No action needed. Ensure datePublished and dateModified are included.", effort="medium")
    if page.word_count > 400:
        return CheckResult("HowTo / Article / WebPage schema", 0, 3, "fail",
            "Content page detected but no HowTo, Article, or WebPage schema found.",
            "Content without schema type is less likely to appear in AI Overview selection.",
            "Add Article or WebPage JSON-LD with: headline, datePublished, dateModified, author, publisher.",
            effort="medium")
    return CheckResult("HowTo / Article / WebPage schema", 2, 3, "warn",
        "No content-type schema found. May be acceptable for non-article pages.",
        "Content-type schema is most critical for articles, guides, and how-to content.",
        "Add appropriate schema if this is a content page: Article, HowTo, or WebPage.",
        effort="medium")


def check_schema_validation(page, kw=None):
    """Schema validation — detect missing required fields and structural errors."""
    if not page.schema_raw:
        return CheckResult("Schema validation (errors/warnings)", 0, 3, "fail",
            "No JSON-LD schema found — nothing to validate.",
            "Pages without schema miss eligibility for rich results and AI structured citations.",
            "Add JSON-LD schema and validate at search.google.com/test/rich-results", effort="quick")
    issues = []
    for s in page.schema_raw:
        stype = str(s.get("@type", "Unknown"))
        if not s.get("@context"):
            issues.append(f"{stype}: missing @context")
        if "Organization" in stype and not s.get("name"):
            issues.append("Organization: missing required 'name'")
        if "FAQPage" in stype and not s.get("mainEntity"):
            issues.append("FAQPage: mainEntity (Q&A) missing or empty")
        if "Article" in stype or "BlogPosting" in stype:
            if not s.get("datePublished"):
                issues.append(f"{stype}: missing datePublished")
            if not s.get("author"):
                issues.append(f"{stype}: missing author")
    if not issues:
        return CheckResult("Schema validation (errors/warnings)", 3, 3, "pass",
            f"{len(page.schema_raw)} schema block(s) validated — no critical errors detected.",
            "Clean schema increases probability of rich result eligibility.",
            "Run Google Rich Results Test for full validation.", effort="quick")
    return CheckResult("Schema validation (errors/warnings)", 1, 3, "warn",
        f"Schema issues found: {'; '.join(issues[:3])}.",
        "Schema errors prevent rich result eligibility and reduce AI structured data accuracy.",
        f"Fix: {'; '.join(issues[:3])}. Validate at search.google.com/test/rich-results",
        effort="quick")
