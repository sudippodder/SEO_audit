"""fetcher.py — Full page fetch + signal extraction."""
import re, json, time, requests
from dataclasses import dataclass, field
from typing import Optional, List
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 12

@dataclass
class ParsedPage:
    url: str; html: str; soup: object
    fetch_time_ms: int = 0; page_size_kb: float = 0
    status_code: int = 0; error: Optional[str] = None
    is_https: bool = False; final_url: str = ""
    title: str = ""; meta_description: str = ""
    canonical: str = ""; robots_meta: str = ""; viewport_meta: str = ""
    h1_tags: List[str] = field(default_factory=list)
    h2_tags: List[str] = field(default_factory=list)
    h3_tags: List[str] = field(default_factory=list)
    all_headings: List[str] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    images: list = field(default_factory=list)
    images_with_alt: list = field(default_factory=list)
    internal_links: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    anchor_texts: List[str] = field(default_factory=list)
    schema_types: List[str] = field(default_factory=list)
    word_count: int = 0; full_text: str = ""; first_100_words: str = ""
    url_path: str = ""; url_slug: str = ""; domain: str = ""
    domain_length: int = 0; has_hyphens_in_slug: bool = False
    has_underscores_in_slug: bool = False; keyword_depth: int = 0
    has_favicon: bool = False; has_sitemap_html_link: bool = False
    has_robots_txt: bool = False; has_xml_sitemap: bool = False
    has_inline_css: bool = False; has_apple_icon: bool = False
    has_og_tags: bool = False; inline_style_count: int = 0
    script_count: int = 0; stylesheet_count: int = 0
    image_count: int = 0; http_requests_approx: int = 0
    image_filenames: List[str] = field(default_factory=list)
    bold_italic_text: str = ""
    # AI signals
    has_faq_schema: bool = False; has_faq_section: bool = False
    has_summary_section: bool = False; has_listicles: bool = False
    has_table: bool = False; has_numbered_steps: bool = False
    definition_count: int = 0; direct_answer_count: int = 0
    readability_score: float = 0.0
    # Extra signals
    has_keyword_synonyms: bool = False
    related_keywords_found: List[str] = field(default_factory=list)
    trusted_external_links: int = 0
    has_voice_search_qa: bool = False
    # ── NEW: AI Crawlability & Schema Depth ───────────────────────────────
    has_llms_txt: bool = False
    robots_ai_directives: dict = field(default_factory=dict)  # {"GPTBot": "allowed"|"blocked"}
    page_render_type: str = "unknown"           # static | ssr-likely | js-heavy
    schema_raw: list = field(default_factory=list)  # full JSON-LD objects
    organization_schema: dict = field(default_factory=dict)
    has_author_schema: bool = False
    has_breadcrumb_schema: bool = False
    has_service_schema: bool = False
    has_howto_article_schema: bool = False
    same_as_links: List[str] = field(default_factory=list)
    # ── NEW: Entity & Knowledge Graph ─────────────────────────────────────
    external_entity_links: dict = field(default_factory=dict)  # {"Wikipedia": url, ...}
    nap_phone: str = ""
    nap_address: str = ""
    schema_nap: dict = field(default_factory=dict)
    # ── NEW: Content Quality & LLM Readability ────────────────────────────
    date_modified: str = ""
    statistics_count: int = 0
    quotable_sentence_count: int = 0
    social_links: dict = field(default_factory=dict)     # {"linkedin": url, ...}
    review_platform_links: dict = field(default_factory=dict)  # {"G2": url, ...}
    press_mention_links: List[str] = field(default_factory=list)

def fetch(url: str) -> "ParsedPage":
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        elapsed = int((time.time() - start) * 1000)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return ParsedPage(url=url, html="", soup=None, error=f"Timed out after {TIMEOUT}s.", fetch_time_ms=TIMEOUT*1000)
    except requests.exceptions.ConnectionError:
        return ParsedPage(url=url, html="", soup=None, error="Connection failed. Check the URL is publicly accessible.")
    except requests.exceptions.HTTPError as e:
        return ParsedPage(url=url, html="", soup=None, error=f"HTTP {e.response.status_code}.", status_code=e.response.status_code)
    except Exception as e:
        return ParsedPage(url=url, html="", soup=None, error=str(e))
    html = resp.text
    soup = BeautifulSoup(html, "lxml")
    page = ParsedPage(url=url, html=html, soup=soup, fetch_time_ms=elapsed,
        page_size_kb=round(len(resp.content)/1024,1), status_code=resp.status_code,
        is_https=resp.url.startswith("https://"), final_url=resp.url)
    _populate(page, soup, resp.url)
    base = f"{urlparse(resp.url).scheme}://{urlparse(resp.url).netloc}"
    # robots.txt — AI directives + sitemap
    try:
        rr = requests.get(f"{base}/robots.txt", headers=HEADERS, timeout=5)
        if rr.status_code == 200:
            page.has_robots_txt = True
            rt = rr.text
            page.has_xml_sitemap = "sitemap" in rt.lower()
            page.robots_ai_directives = _parse_ai_directives(rt)
    except: pass
    # llms.txt
    try:
        lr = requests.get(f"{base}/llms.txt", headers=HEADERS, timeout=5)
        page.has_llms_txt = (lr.status_code == 200 and len(lr.text) > 10)
    except: pass
    return page

def _populate(page, soup, base_url):
    parsed = urlparse(base_url)
    base_domain = parsed.netloc
    page.domain = base_domain.replace("www.", "")
    page.domain_length = len(page.domain.split(".")[0])
    page.url_path = parsed.path
    slug = parsed.path.strip("/").split("/")[-1] if parsed.path.strip("/") else ""
    page.url_slug = slug
    page.has_hyphens_in_slug = "-" in slug
    page.has_underscores_in_slug = "_" in slug
    page.keyword_depth = len([p for p in parsed.path.strip("/").split("/") if p])

    t = soup.find("title")
    page.title = t.get_text(strip=True) if t else ""

    def _meta(name=None, prop=None):
        tag = soup.find("meta", attrs={"name": name} if name else {"property": prop})
        return tag.get("content","").strip() if tag else ""

    page.meta_description = _meta("description") or _meta(prop="og:description")
    page.viewport_meta = _meta("viewport")
    page.robots_meta = _meta("robots").lower()
    c = soup.find("link", rel="canonical")
    page.canonical = c.get("href","") if c else ""

    page.h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    page.h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    page.h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]
    page.all_headings = page.h1_tags + page.h2_tags + page.h3_tags + \
        [h.get_text(strip=True) for h in soup.find_all(["h4","h5","h6"])]

    page.paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    body = soup.find("body")
    page.full_text = body.get_text(separator=" ", strip=True) if body else ""
    words = page.full_text.split()
    page.word_count = len(words)
    page.first_100_words = " ".join(words[:100]).lower()

    page.images = soup.find_all("img")
    page.images_with_alt = [img for img in page.images if img.get("alt","").strip()]
    page.image_count = len(page.images)
    page.image_filenames = [img.get("src","").split("/")[-1].split("?")[0].lower() for img in page.images if img.get("src")]

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = a.get_text(strip=True)
        if text: page.anchor_texts.append(text)
        if urlparse(href).netloc.replace("www.", "") == page.domain:
            page.internal_links.append(href)
        elif href.startswith("http"):
            page.external_links.append(href)
    trusted_domains = ["gov","edu","wikipedia","bbc","reuters","nytimes","guardian","forbes","harvard"]
    page.trusted_external_links = sum(1 for l in page.external_links if any(d in l for d in trusted_domains))

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = [data] if isinstance(data, dict) else data
            for item in items:
                if isinstance(item, dict) and item.get("@type"):
                    t = item["@type"]
                    st = t if isinstance(t, str) else t[0]
                    page.schema_types.append(st)
                    if "faq" in st.lower(): page.has_faq_schema = True
        except: pass

    page.has_favicon = bool(soup.find("link", rel=lambda r: r and ("icon" in (" ".join(r) if isinstance(r,list) else r).lower())))
    page.has_apple_icon = bool(soup.find("link", rel=lambda r: r and "apple-touch-icon" in (" ".join(r) if isinstance(r,list) else str(r))))
    page.has_og_tags = bool(soup.find("meta", attrs={"property": re.compile("^og:")}))
    page.has_sitemap_html_link = bool(soup.find("a", href=re.compile(r"sitemap", re.I)))
    page.inline_style_count = len(soup.find_all(style=True))
    page.has_inline_css = page.inline_style_count > 5
    page.script_count = len(soup.find_all("script"))
    page.stylesheet_count = len(soup.find_all("link", rel=lambda r: r and ("stylesheet" in (r if isinstance(r,str) else " ".join(r)))))
    page.http_requests_approx = page.image_count + page.script_count + page.stylesheet_count

    # FAQ / summary sections
    faq_kws = ["faq","frequently asked","common questions","q&a","questions and answers"]
    summary_kws = ["summary","tl;dr","tldr","key takeaways","in short","in conclusion","bottom line","overview","recap"]
    full_lower = page.full_text.lower()
    page.has_faq_section = page.has_faq_schema or any(k in full_lower for k in faq_kws) or \
        any(k in h.lower() for h in page.all_headings for k in faq_kws)
    page.has_summary_section = any(k in full_lower[:800] or k in full_lower[-800:] for k in summary_kws) or \
        any(k in h.lower() for h in page.all_headings for k in summary_kws)
    page.has_listicles = bool(soup.find_all(["ul","ol"]))
    page.has_table = bool(soup.find("table"))
    page.has_numbered_steps = bool(soup.find("ol"))

    # Bold/italic text
    bold = " ".join(t.get_text() for t in soup.find_all(["strong","b"])).lower()
    italic = " ".join(t.get_text() for t in soup.find_all(["em","i"])).lower()
    page.bold_italic_text = bold + " " + italic

    # Definitions + direct answers
    import re as _re
    page.definition_count = len(_re.findall(r'\b\w[\w\s]{1,30}\s+(is|are|refers to|means|defined as)\b', page.full_text, _re.I))
    sents = _re.split(r'(?<=[.!?])\s+', page.full_text)
    page.direct_answer_count = sum(1 for s in sents if 5 < len(s.split()) < 25 and
        _re.match(r'^(yes|no|the |a |an |to |you can|it is|this is)', s.strip(), _re.I))

    # Voice search QA
    page.has_voice_search_qa = sum(1 for h in page.all_headings if "?" in h) >= 2

    # Readability
    try:
        import textstat
        page.readability_score = textstat.flesch_reading_ease(page.full_text) if len(page.full_text.split()) > 50 else 0
    except: page.readability_score = 0

    # ── Schema (deep) ──────────────────────────────────────────────────────
    _extract_schema_signals(page, soup)

    # ── Entity links ───────────────────────────────────────────────────────
    _extract_entity_links(page)

    # ── Content quality signals ────────────────────────────────────────────
    _extract_content_quality(page, soup)

    # ── JS render type ─────────────────────────────────────────────────────
    _detect_render_type(page)


def _parse_ai_directives(robots_txt: str) -> dict:
    """Parse robots.txt for known AI bot directives."""
    AI_BOTS = ["GPTBot", "ClaudeBot", "PerplexityBot", "GoogleExtended", "CCBot", "anthropic-ai", "cohere-ai"]
    directives = {}
    lines = robots_txt.splitlines()
    current_agents = []
    for line in lines:
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            current_agents = [agent]
        elif line.lower().startswith("disallow:") and current_agents:
            val = line.split(":", 1)[1].strip()
            for a in current_agents:
                for bot in AI_BOTS:
                    if bot.lower() == a.lower() or a == "*":
                        if val in ("/", ""):
                            directives[bot] = directives.get(bot, "blocked" if val == "/" else "allowed")
        elif line.lower().startswith("allow:") and current_agents:
            val = line.split(":", 1)[1].strip()
            if val == "/":
                for a in current_agents:
                    for bot in AI_BOTS:
                        if bot.lower() == a.lower():
                            directives[bot] = "allowed"
    return directives


def _extract_schema_signals(page, soup):
    """Deep schema extraction for Section 2 checks."""
    CONTENT_TYPES = {"HowTo", "Article", "BlogPosting", "NewsArticle", "WebPage"}
    raw = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    raw.append(item)
        except: pass
    page.schema_raw = raw
    for item in raw:
        stype = item.get("@type", "")
        if isinstance(stype, list): stype = " ".join(stype)
        if "Organization" in stype or "LocalBusiness" in stype:
            page.organization_schema = item
            page.same_as_links = item.get("sameAs", []) if isinstance(item.get("sameAs"), list) else ([item["sameAs"]] if item.get("sameAs") else [])
            addr = item.get("address", {})
            if isinstance(addr, dict):
                page.nap_address = addr.get("streetAddress", "") + " " + addr.get("addressLocality", "")
            page.schema_nap = {"name": item.get("name", ""), "phone": item.get("telephone", ""), "address": page.nap_address}
            page.nap_phone = item.get("telephone", "")
        if "Person" in stype or "author" in str(item).lower():
            page.has_author_schema = True
        if "BreadcrumbList" in stype:
            page.has_breadcrumb_schema = True
        if "Service" in stype:
            page.has_service_schema = True
        if any(ct in stype for ct in CONTENT_TYPES):
            page.has_howto_article_schema = True
            dm = item.get("dateModified") or item.get("datePublished", "")
            if dm: page.date_modified = dm


def _extract_entity_links(page):
    """Detect external entity links and social profile links."""
    ENTITY_DOMAINS = {
        "Wikipedia": "wikipedia.org", "LinkedIn": "linkedin.com",
        "Crunchbase": "crunchbase.com", "G2": "g2.com", "Clutch": "clutch.co",
    }
    SOCIAL_DOMAINS = {
        "linkedin": "linkedin.com", "twitter": "twitter.com", "x": "x.com",
        "youtube": "youtube.com", "facebook": "facebook.com", "instagram": "instagram.com",
    }
    REVIEW_DOMAINS = {"G2": "g2.com", "Clutch": "clutch.co", "Trustpilot": "trustpilot.com", "GBR": "google.com/maps"}
    PRESS_DOMAINS = ["forbes", "techcrunch", "businesswire", "prnewswire", "reuters",
                     "bbc", "guardian", "nytimes", "entrepreneur", "inc.com"]
    all_links = page.external_links + page.same_as_links
    for link in all_links:
        ll = link.lower()
        for name, domain in ENTITY_DOMAINS.items():
            if domain in ll and name not in page.external_entity_links:
                page.external_entity_links[name] = link
        for key, domain in SOCIAL_DOMAINS.items():
            if domain in ll and key not in page.social_links:
                page.social_links[key] = link
        for name, domain in REVIEW_DOMAINS.items():
            if domain in ll and name not in page.review_platform_links:
                page.review_platform_links[name] = link
        for press in PRESS_DOMAINS:
            if press in ll:
                page.press_mention_links.append(link)
                break


def _extract_content_quality(page, soup):
    """Extract statistics density, quotable sentences, date signals."""
    # Statistics / data points
    page.statistics_count = len(re.findall(
        r'\b\d+(?:\.\d+)?\s*(?:%|percent|million|billion|thousand|\$|£|€|x\s+(?:faster|more|better))',
        page.full_text, re.I))
    # Quotable sentences: standalone factual "X is/does Y" with 8-25 words
    sents = re.split(r'(?<=[.!?])\s+', page.full_text)
    page.quotable_sentence_count = sum(
        1 for s in sents
        if 8 <= len(s.split()) <= 30
        and re.search(r'\b(is|are|was|were|provides|enables|helps|allows|means|refers to)\b', s, re.I)
        and not s.strip().startswith(("I ", "We ", "Our ", "You "))
    )
    # Date modified — check <time> tags and meta
    if not page.date_modified:
        for tag in soup.find_all("time"):
            dt = tag.get("datetime", "")
            if dt and len(dt) >= 8:
                page.date_modified = dt; break
        if not page.date_modified:
            for name in ["article:modified_time", "article:published_time", "og:updated_time"]:
                m = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
                if m and m.get("content"):
                    page.date_modified = m["content"]; break
    # NAP from visible text
    phone_match = re.search(r'\+?[\d][\d\s\-\(\)]{7,15}', page.full_text)
    if phone_match and not page.nap_phone:
        page.nap_phone = phone_match.group(0).strip()


def _detect_render_type(page):
    """Heuristic: is the page static, SSR-likely, or JS-heavy?"""
    if page.word_count == 0:
        page.page_render_type = "js-heavy"; return
    ratio = page.script_count / max(page.word_count / 100, 1)
    if ratio < 0.5 and page.word_count > 300:
        page.page_render_type = "static"
    elif ratio < 1.5:
        page.page_render_type = "ssr-likely"
    else:
        page.page_render_type = "js-heavy"