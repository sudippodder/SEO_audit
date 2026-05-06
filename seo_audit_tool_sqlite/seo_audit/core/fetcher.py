"""
fetcher.py
Fetches and parses HTML from a target URL.
Returns a ParsedPage dataclass consumed by all scorer modules.
"""

import time
import requests
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AISEOAuditBot/1.0; "
        "+https://yourdomain.com/seo-audit)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

TIMEOUT = 10  # seconds


@dataclass
class ParsedPage:
    url: str
    html: str
    soup: object                        # BeautifulSoup instance
    fetch_time_ms: int = 0
    error: Optional[str] = None
    status_code: int = 0

    # Convenience properties populated by parse()
    title: str = ""
    meta_description: str = ""
    h1_tags: list = field(default_factory=list)
    h2_tags: list = field(default_factory=list)
    h3_tags: list = field(default_factory=list)
    all_headings: list = field(default_factory=list)
    paragraphs: list = field(default_factory=list)
    images: list = field(default_factory=list)
    images_with_alt: list = field(default_factory=list)
    internal_links: list = field(default_factory=list)
    external_links: list = field(default_factory=list)
    canonical: str = ""
    robots_meta: str = ""
    schema_types: list = field(default_factory=list)
    word_count: int = 0
    full_text: str = ""


def fetch(url: str) -> ParsedPage:
    """Fetch URL and return a fully populated ParsedPage."""
    start = time.time()

    # Normalise URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        elapsed = int((time.time() - start) * 1000)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return ParsedPage(url=url, html="", soup=None, error="Request timed out (>10s).", fetch_time_ms=TIMEOUT * 1000)
    except requests.exceptions.ConnectionError:
        return ParsedPage(url=url, html="", soup=None, error="Could not connect to the URL. Check it is publicly accessible.")
    except requests.exceptions.HTTPError as e:
        return ParsedPage(url=url, html="", soup=None, error=f"HTTP error {e.response.status_code}.", status_code=e.response.status_code)
    except Exception as e:
        return ParsedPage(url=url, html="", soup=None, error=str(e))

    soup = BeautifulSoup(resp.text, "lxml")
    page = ParsedPage(
        url=url,
        html=resp.text,
        soup=soup,
        fetch_time_ms=elapsed,
        status_code=resp.status_code,
    )
    _populate(page, soup, url)
    return page


def _populate(page: ParsedPage, soup: BeautifulSoup, base_url: str):
    from urllib.parse import urlparse, urljoin

    base_domain = urlparse(base_url).netloc

    # Title
    title_tag = soup.find("title")
    page.title = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    meta = soup.find("meta", attrs={"name": "description"}) or \
           soup.find("meta", attrs={"property": "og:description"})
    page.meta_description = meta.get("content", "").strip() if meta else ""

    # Headings
    page.h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    page.h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    page.h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]
    page.all_headings = page.h1_tags + page.h2_tags + page.h3_tags + \
                        [h.get_text(strip=True) for h in soup.find_all(["h4","h5","h6"])]

    # Paragraphs
    page.paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

    # Images
    page.images = soup.find_all("img")
    page.images_with_alt = [img for img in page.images if img.get("alt", "").strip()]

    # Links
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if urlparse(href).netloc == base_domain:
            page.internal_links.append(href)
        elif href.startswith("http"):
            page.external_links.append(href)

    # Canonical + robots
    canon = soup.find("link", rel="canonical")
    page.canonical = canon.get("href", "") if canon else ""
    robots = soup.find("meta", attrs={"name": "robots"})
    page.robots_meta = robots.get("content", "").lower() if robots else ""

    # Schema.org types
    import json, re
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                t = data.get("@type", "")
                if t:
                    page.schema_types.append(t if isinstance(t, str) else t[0])
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type"):
                        page.schema_types.append(item["@type"])
        except Exception:
            pass

    # Full text + word count
    body = soup.find("body")
    if body:
        page.full_text = body.get_text(separator=" ", strip=True)
    page.word_count = len(page.full_text.split())
