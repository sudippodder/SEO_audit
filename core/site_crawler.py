"""
site_crawler.py
Multi-page site crawler — discovers and fetches key pages for full-site GEO audit.
Classifies pages by type (homepage, about, contact, services, blog, case study, team, etc.).
Uses concurrent fetching for performance.
"""
import re
import sys
import time
import asyncio
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from .fetcher import fetch, ParsedPage, HEADERS, TIMEOUT


# ── Page type patterns ────────────────────────────────────────────────────────
PAGE_TYPE_PATTERNS: Dict[str, List[str]] = {
    "about": [
        r"/about\b", r"/about-us\b", r"/who-we-are\b", r"/our-story\b",
        r"/company\b", r"/our-company\b",
    ],
    "contact": [
        r"/contact\b", r"/contact-us\b", r"/get-in-touch\b", r"/reach-us\b",
    ],
    "services": [
        r"/services?\b", r"/solutions?\b", r"/what-we-do\b", r"/offerings?\b",
        r"/capabilities\b", r"/expertise\b",
    ],
    "team": [
        r"/teams?\b", r"/our-team\b", r"/people\b", r"/leadership\b",
        r"/management\b", r"/founders?\b",
    ],
    "case_study": [
        r"/case-stud", r"/portfolio\b", r"/work\b", r"/projects?\b",
        r"/success-stor", r"/client-stor",
    ],
    "blog": [
        r"/blog\b", r"/insights?\b", r"/resources?\b", r"/articles?\b",
        r"/news\b", r"/knowledge\b", r"/learn\b",
    ],
    "reviews": [
        r"/testimonials?\b", r"/reviews?\b", r"/clients?\b", r"/customers?\b",
        r"/feedback\b",
    ],
    "legal": [
        r"/privacy", r"/terms", r"/legal\b", r"/disclaimer\b",
        r"/cookie-policy\b", r"/gdpr\b",
    ],
    "pricing": [
        r"/pricing\b", r"/plans?\b", r"/packages?\b",
    ],
    "careers": [
        r"/careers?\b", r"/jobs?\b", r"/hiring\b", r"/join-us\b",
    ],
}

# Page types we want for GEO audit (in priority order)
GEO_PRIORITY_TYPES = [
    "about", "contact", "services", "team", "case_study", "blog", "reviews", "pricing",
]

# Anchor text hints for page type detection (fallback)
ANCHOR_HINTS: Dict[str, List[str]] = {
    "about": ["about us", "about", "who we are", "our story", "company"],
    "contact": ["contact", "contact us", "get in touch", "reach us"],
    "services": ["services", "solutions", "what we do", "offerings", "our services"],
    "team": ["team", "our team", "people", "leadership", "meet the team"],
    "case_study": ["case studies", "portfolio", "our work", "projects", "success stories"],
    "blog": ["blog", "insights", "resources", "articles", "news"],
    "reviews": ["testimonials", "reviews", "clients", "customer stories"],
}


@dataclass
class CrawledPage:
    """A fetched page with its classified type."""
    page: ParsedPage
    page_type: str      # homepage | about | contact | services | blog | case_study | team | reviews | other
    url: str
    confidence: float = 1.0  # 0–1 confidence in type classification


@dataclass
class SiteCrawlResult:
    """Result of crawling multiple pages of a site."""
    pages: List[CrawledPage] = field(default_factory=list)
    sitemap_found: bool = False
    pages_discovered: int = 0
    pages_crawled: int = 0
    crawl_time_ms: int = 0
    errors: List[str] = field(default_factory=list)
    bot_protection_detected: bool = False


def _classify_url(url: str, base_domain: str) -> Tuple[str, float]:
    """Classify a URL into a page type based on path patterns."""
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")

    # Skip non-page URLs
    if any(path.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".gif", ".svg", ".css", ".js", ".xml"]):
        return "skip", 0.0

    # Root path = homepage
    if path in ("", "/"):
        return "homepage", 1.0

    for page_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path, re.I):
                return page_type, 0.9
    return "other", 0.3


def _classify_by_anchor(anchor_text: str) -> Optional[str]:
    """Classify a link by its anchor text."""
    text_lower = anchor_text.lower().strip()
    for page_type, hints in ANCHOR_HINTS.items():
        for hint in hints:
            if hint == text_lower or text_lower.startswith(hint):
                return page_type
    return None


def _parse_sitemap(base_url: str) -> List[str]:
    """Parse sitemap.xml to discover URLs."""
    urls = []
    sitemap_urls_to_try = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/wp-sitemap.xml",
    ]
    for sitemap_url in sitemap_urls_to_try:
        try:
            resp = requests.get(sitemap_url, headers=HEADERS, timeout=8)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            # Check for sitemap index
            sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
            if sitemaps:
                # It's a sitemap index — fetch first 2 child sitemaps
                for sm in sitemaps[:2]:
                    try:
                        child_resp = requests.get(sm.text, headers=HEADERS, timeout=8)
                        if child_resp.status_code == 200:
                            child_root = ET.fromstring(child_resp.content)
                            for loc in child_root.findall(".//sm:url/sm:loc", ns):
                                if loc.text:
                                    urls.append(loc.text)
                    except Exception:
                        pass
            else:
                # Direct sitemap
                for loc in root.findall(".//sm:url/sm:loc", ns):
                    if loc.text:
                        urls.append(loc.text)
            if urls:
                break
        except Exception:
            continue
    return urls


def _discover_pages(homepage: ParsedPage, base_url: str) -> Dict[str, List[Tuple[str, float]]]:
    """
    Discover candidate pages for each page type.
    Returns: {page_type: [(url, confidence), ...]}
    """
    candidates: Dict[str, List[Tuple[str, float]]] = {pt: [] for pt in GEO_PRIORITY_TYPES}
    candidates["other"] = []
    seen_urls: Set[str] = set()
    base_domain = urlparse(base_url).netloc.replace("www.", "")

    # ── Source 1: sitemap.xml ─────────────────────────────────────────────
    sitemap_urls = _parse_sitemap(base_url)
    for url in sitemap_urls:
        parsed = urlparse(url)
        if base_domain not in parsed.netloc.replace("www.", ""):
            continue
        page_type, conf = _classify_url(url, base_domain)
        if page_type in candidates and url not in seen_urls:
            candidates[page_type].append((url, conf))
            seen_urls.add(url)

    # ── Source 2: internal links from homepage ────────────────────────────
    all_links = homepage.internal_links
    soup = homepage.soup
    if soup:
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"])
            parsed = urlparse(href)
            if base_domain not in parsed.netloc.replace("www.", ""):
                continue
            if href in seen_urls:
                continue

            anchor_text = a.get_text(strip=True)
            page_type, conf = _classify_url(href, base_domain)

            # Try anchor text classification as fallback/boost
            anchor_type = _classify_by_anchor(anchor_text) if anchor_text else None
            if anchor_type and anchor_type in candidates:
                if page_type == "other" or page_type == anchor_type:
                    page_type = anchor_type
                    conf = max(conf, 0.7)

            if page_type in candidates and href not in seen_urls:
                candidates[page_type].append((href, conf))
                seen_urls.add(href)

    return candidates


def crawl_site(url: str, max_pages: int = 50, max_workers: int = 6) -> SiteCrawlResult:
    """
    Crawl key pages of a website for full-site GEO audit.

    1. Fetch the homepage
    2. Discover candidate pages via sitemap + internal links
    3. Select best candidate for each page type
    4. Fetch selected pages concurrently
    5. Return classified results
    """
    start = time.time()
    result = SiteCrawlResult()

    # ── Step 1: Normalize base URL ────────────────────────────────────────
    url = url.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # ── Step 2: Fetch homepage ────────────────────────────────────────────
    homepage = fetch(url)
    if homepage.error:
        result.errors.append(f"Homepage fetch failed: {homepage.error}")
        result.crawl_time_ms = int((time.time() - start) * 1000)
        return result
        
    if homepage.is_bot_blocked:
        result.bot_protection_detected = True

    # ── CHECK FOR SPA ─────────────────────────────────────────────────────
    is_spa = homepage.page_render_type == "js-heavy" or (len(homepage.internal_links) < 2 and homepage.script_count > 0)
    
    if is_spa:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1920, "height": 1080}
            )
            pw_page = context.new_page()
            
            try:
                pw_page.goto(url, timeout=30000, wait_until="networkidle")
            except Exception:
                pass
            
            html = pw_page.content()
            homepage = fetch(url, provided_html=html)
            if homepage.is_bot_blocked:
                result.bot_protection_detected = True
            
            result.pages.append(CrawledPage(page=homepage, page_type="homepage", url=url, confidence=1.0))
            candidates = _discover_pages(homepage, base_url)
            
            sitemap_urls = _parse_sitemap(base_url)
            result.sitemap_found = len(sitemap_urls) > 0
            result.pages_discovered = sum(len(v) for v in candidates.values()) + 1
            
            urls_to_fetch: List[Tuple[str, str]] = []
            for page_type in GEO_PRIORITY_TYPES:
                type_candidates = candidates.get(page_type, [])
                if type_candidates:
                    type_candidates.sort(key=lambda x: x[1], reverse=True)
                    best_url, best_conf = type_candidates.pop(0)
                    urls_to_fetch.append((best_url, page_type))
                    if len(urls_to_fetch) >= max_pages - 1:
                        break
                        
            if len(urls_to_fetch) < max_pages - 1:
                remaining = []
                for pt, type_candidates in candidates.items():
                    for c_url, conf in type_candidates:
                        remaining.append((c_url, pt, conf))
                remaining.sort(key=lambda x: x[2], reverse=True)
                for r_url, pt, conf in remaining:
                    if len(urls_to_fetch) >= max_pages - 1:
                        break
                    urls_to_fetch.append((r_url, pt))
            
            # Fetch candidate pages sequentially using Playwright
            for fetch_url, ptype in urls_to_fetch:
                try:
                    pw_page.goto(fetch_url, timeout=20000, wait_until="networkidle")
                except Exception:
                    pass
                sub_html = pw_page.content()
                sub_page = fetch(fetch_url, provided_html=sub_html)
                if not sub_page.error:
                    result.pages.append(CrawledPage(page=sub_page, page_type=ptype, url=fetch_url))
            
            browser.close()
            result.pages_crawled = len(result.pages)
            result.crawl_time_ms = int((time.time() - start) * 1000)
            return result

    result.pages.append(CrawledPage(page=homepage, page_type="homepage", url=url, confidence=1.0))

    # ── Step 3: Discover candidate pages ──────────────────────────────────
    candidates = _discover_pages(homepage, base_url)

    # Check if sitemap was found
    sitemap_urls = _parse_sitemap(base_url)
    result.sitemap_found = len(sitemap_urls) > 0
    result.pages_discovered = sum(len(v) for v in candidates.values()) + 1  # +1 for homepage

    # ── Step 4: Select best candidate per type ────────────────────────────
    urls_to_fetch: List[Tuple[str, str]] = []  # (url, page_type)
    
    # First priority: one of each GEO priority type
    for page_type in GEO_PRIORITY_TYPES:
        type_candidates = candidates.get(page_type, [])
        if not type_candidates:
            continue
        # Sort by confidence (highest first), take best
        type_candidates.sort(key=lambda x: x[1], reverse=True)
        best_url, best_conf = type_candidates.pop(0)
        urls_to_fetch.append((best_url, page_type))
        if len(urls_to_fetch) >= max_pages - 1:  # -1 for homepage already fetched
            break

    # If we still have room, add more pages (sorted by confidence)
    if len(urls_to_fetch) < max_pages - 1:
        remaining = []
        for pt, type_candidates in candidates.items():
            for c_url, conf in type_candidates:
                remaining.append((c_url, pt, conf))
        # Sort remaining primarily by confidence
        remaining.sort(key=lambda x: x[2], reverse=True)
        
        for r_url, pt, conf in remaining:
            if len(urls_to_fetch) >= max_pages - 1:
                break
            urls_to_fetch.append((r_url, pt))

    # ── Step 5: Fetch pages concurrently ──────────────────────────────────
    def _fetch_page(url_type: Tuple[str, str]) -> Optional[CrawledPage]:
        fetch_url, ptype = url_type
        try:
            page = fetch(fetch_url)
            if page.error:
                return None
            return CrawledPage(page=page, page_type=ptype, url=fetch_url)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_page, ut): ut for ut in urls_to_fetch}
        for future in as_completed(futures):
            crawled = future.result()
            if crawled:
                result.pages.append(crawled)

    result.pages_crawled = len(result.pages)
    result.crawl_time_ms = int((time.time() - start) * 1000)
    return result


def get_page_type_coverage(crawl_result: SiteCrawlResult) -> Dict[str, str]:
    """
    Returns a dict of {page_type: status} for UI display.
    Status: "found" | "missing"
    """
    found_types = {p.page_type for p in crawl_result.pages}
    coverage = {}
    for pt in ["homepage"] + GEO_PRIORITY_TYPES:
        coverage[pt] = "found" if pt in found_types else "missing"
    return coverage
