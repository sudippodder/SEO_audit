"""
external_validator.py
Live validation of external profiles — Trustpilot, G2, Clutch, Crunchbase,
LinkedIn, YouTube, Wikipedia, Wikidata, Knowledge Panel heuristics.
Results are cached per domain for 24 hours in SQLite.
"""
import re
import time
import json
import sqlite3
import os
import requests
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from urllib.parse import urlparse, quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
TIMEOUT = 5
CACHE_TTL_SECONDS = 86400  # 24 hours


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class ExternalProfile:
    platform: str               # "Trustpilot", "G2", etc.
    exists: bool = False
    url: str = ""               # actual profile URL found
    rating: Optional[float] = None
    review_count: Optional[int] = None
    verification_status: str = "not_checked"  # checked | not_checked | error
    error_message: str = ""
    extra_data: Dict = field(default_factory=dict)


@dataclass
class ExternalValidationResult:
    profiles: List[ExternalProfile] = field(default_factory=list)
    profiles_found: int = 0
    profiles_missing: List[str] = field(default_factory=list)
    profiles_errored: List[str] = field(default_factory=list)
    validation_time_ms: int = 0
    knowledge_panel_detected: bool = False
    wikipedia_detected: bool = False
    wikidata_detected: bool = False
    cached: bool = False


# ── Cache Layer ───────────────────────────────────────────────────────────────

def _get_cache_db_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "seo_audits.db")


def _init_cache_table():
    """Create cache table if not exists."""
    try:
        conn = sqlite3.connect(_get_cache_db_path())
        conn.execute("""
            CREATE TABLE IF NOT EXISTS external_validation_cache (
                domain TEXT PRIMARY KEY,
                result_json TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()
    except Exception:
        pass


def _get_cached(domain: str) -> Optional[ExternalValidationResult]:
    """Check cache for recent validation result."""
    try:
        conn = sqlite3.connect(_get_cache_db_path())
        row = conn.execute(
            "SELECT result_json, created_at FROM external_validation_cache WHERE domain = ?",
            (domain,)
        ).fetchone()
        conn.close()
        if row:
            result_json, created_at = row
            if time.time() - created_at < CACHE_TTL_SECONDS:
                data = json.loads(result_json)
                result = ExternalValidationResult()
                result.profiles = [ExternalProfile(**p) for p in data.get("profiles", [])]
                result.profiles_found = data.get("profiles_found", 0)
                result.profiles_missing = data.get("profiles_missing", [])
                result.profiles_errored = data.get("profiles_errored", [])
                result.validation_time_ms = data.get("validation_time_ms", 0)
                result.knowledge_panel_detected = data.get("knowledge_panel_detected", False)
                result.wikipedia_detected = data.get("wikipedia_detected", False)
                result.wikidata_detected = data.get("wikidata_detected", False)
                result.cached = True
                return result
    except Exception:
        pass
    return None


def _save_cache(domain: str, result: ExternalValidationResult):
    """Save validation result to cache."""
    try:
        data = {
            "profiles": [asdict(p) for p in result.profiles],
            "profiles_found": result.profiles_found,
            "profiles_missing": result.profiles_missing,
            "profiles_errored": result.profiles_errored,
            "validation_time_ms": result.validation_time_ms,
            "knowledge_panel_detected": result.knowledge_panel_detected,
            "wikipedia_detected": result.wikipedia_detected,
            "wikidata_detected": result.wikidata_detected,
        }
        conn = sqlite3.connect(_get_cache_db_path())
        conn.execute(
            "INSERT OR REPLACE INTO external_validation_cache (domain, result_json, created_at) VALUES (?, ?, ?)",
            (domain, json.dumps(data), time.time())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Platform Validators ──────────────────────────────────────────────────────

def _check_url_exists(url: str, timeout: int = TIMEOUT) -> tuple:
    """HEAD/GET a URL, return (exists, status_code, response_text_or_None)."""
    try:
        resp = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return True, resp.status_code, None
        # Some platforms block HEAD — try GET
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return True, resp.status_code, resp.text[:5000]
        return False, resp.status_code, None
    except requests.exceptions.Timeout:
        return None, 0, None  # None = could not verify
    except Exception:
        return None, 0, None


def _run_playwright_validator(platform: str, target: str) -> ExternalProfile:
    import subprocess
    import os
    import sys
    import json
    
    profile = ExternalProfile(platform=platform.capitalize())
    script_path = os.path.join(os.path.dirname(__file__), "playwright_validator.py")
    
    try:
        res = subprocess.run(
            [sys.executable, script_path, platform, target],
            capture_output=True,
            text=True,
            timeout=45
        )
        
        if res.returncode == 0 and res.stdout.strip():
            try:
                data = json.loads(res.stdout.strip())
                profile.exists = data.get("exists", False)
                profile.url = data.get("url", "")
                profile.verification_status = data.get("verification_status", "error")
                profile.rating = data.get("rating")
                profile.review_count = data.get("review_count")
                profile.error_message = data.get("error_message", "")
            except json.JSONDecodeError:
                profile.verification_status = "error"
                profile.error_message = "Failed to parse Playwright script output."
        else:
            profile.verification_status = "error"
            profile.error_message = res.stderr.strip()[:150] or f"{platform.capitalize()} script failed."
            
    except subprocess.TimeoutExpired:
        profile.verification_status = "error"
        profile.error_message = f"{platform.capitalize()} script timed out."
    except Exception as e:
        profile.verification_status = "error"
        profile.error_message = f"{type(e).__name__}: {str(e)}"[:150]
        
    return profile

def _validate_trustpilot(domain: str) -> ExternalProfile:
    """Check Trustpilot for business review page."""
    clean_domain = domain.replace("www.", "")
    return _run_playwright_validator("trustpilot", clean_domain)

def _validate_clutch(domain: str, brand_name: str) -> ExternalProfile:
    """Check Clutch for company profile."""
    # Clutch profile URL format can be based on brand_name slug or domain name
    slug = brand_name.lower().replace(" ", "-").replace(".", "-")
    # To keep it simple, we just pass the slug. The Playwright script can try it.
    # Note: If it fails, maybe the slug was different. But this is the best heuristic.
    return _run_playwright_validator("clutch", slug)

def _validate_g2(brand_name: str) -> ExternalProfile:
    """Check G2 for product/company page."""
    slug = brand_name.lower().replace(" ", "-")
    return _run_playwright_validator("g2", slug)


def _validate_crunchbase(brand_name: str) -> ExternalProfile:
    """Check Crunchbase for organization profile."""
    profile = ExternalProfile(platform="Crunchbase")
    slug = brand_name.lower().replace(" ", "-")
    url = f"https://www.crunchbase.com/organization/{slug}"
    exists, status, _ = _check_url_exists(url)
    if exists:
        profile.exists = True
        profile.url = url
        profile.verification_status = "checked"
    elif exists is None:
        profile.verification_status = "error"
        profile.error_message = "Could not verify Crunchbase profile"
    else:
        profile.exists = False
        profile.verification_status = "checked"
    return profile


def _validate_linkedin(brand_name: str) -> ExternalProfile:
    """Check LinkedIn for company page."""
    profile = ExternalProfile(platform="LinkedIn")
    slug = brand_name.lower().replace(" ", "-")
    url = f"https://www.linkedin.com/company/{slug}"
    exists, status, _ = _check_url_exists(url)
    if exists:
        profile.exists = True
        profile.url = url
        profile.verification_status = "checked"
    elif exists is None:
        profile.verification_status = "error"
        profile.error_message = "Could not verify LinkedIn profile (may require login)"
    else:
        profile.exists = False
        profile.verification_status = "checked"
    return profile


def _validate_youtube(brand_name: str) -> ExternalProfile:
    """Check YouTube for channel."""
    profile = ExternalProfile(platform="YouTube")
    slug = brand_name.lower().replace(" ", "")
    urls_to_try = [
        f"https://www.youtube.com/@{slug}",
        f"https://www.youtube.com/c/{slug}",
        f"https://www.youtube.com/{slug}",
    ]
    for url in urls_to_try:
        exists, status, _ = _check_url_exists(url)
        if exists:
            profile.exists = True
            profile.url = url
            profile.verification_status = "checked"
            return profile
    profile.exists = False
    profile.verification_status = "checked"
    return profile


def _validate_google_business(brand_name: str, onsite_link: str = None) -> ExternalProfile:
    """Heuristic check for Google Business Profile presence."""
    from urllib.parse import quote
    profile = ExternalProfile(platform="Google Business")
    
    if onsite_link:
        profile.exists = True
        profile.url = onsite_link
        profile.verification_status = "checked"
        profile.extra_data["note"] = "Verified via on-site link"
        return profile
    # If no on-site link is found, try to find it using the headless browser search
    pw_result = _run_playwright_validator("google_business", brand_name)
    if pw_result:
        pw_result.platform = "Google Business"
        return pw_result
    else:
        profile.verification_status = "error"
        profile.error_message = "Playwright validator returned empty result."
        return profile


def _validate_wikipedia(brand_name: str) -> ExternalProfile:
    """Check Wikipedia for article about the brand."""
    profile = ExternalProfile(platform="Wikipedia")
    title = brand_name.replace(" ", "_")
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
    try:
        resp = requests.get(api_url, headers={
            "User-Agent": "GEOAuditTool/1.0 (contact@example.com)",
        }, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("type") == "standard":
                profile.exists = True
                profile.url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                profile.verification_status = "checked"
                profile.extra_data["extract"] = data.get("extract", "")[:200]
                profile.extra_data["description"] = data.get("description", "")
                return profile
        profile.exists = False
        profile.verification_status = "checked"
    except Exception as e:
        profile.verification_status = "error"
        profile.error_message = str(e)[:100]
    return profile


def _validate_wikidata(brand_name: str) -> ExternalProfile:
    """Search Wikidata for entity matching the brand."""
    profile = ExternalProfile(platform="Wikidata")
    api_url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": brand_name,
        "language": "en",
        "limit": 3,
        "format": "json",
    }
    try:
        resp = requests.get(api_url, params=params, headers={
            "User-Agent": "GEOAuditTool/1.0 (contact@example.com)",
        }, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("search", [])
            for r in results:
                label = r.get("label", "").lower()
                desc = r.get("description", "").lower()
                if brand_name.lower() in label or label in brand_name.lower():
                    # Check if it's a company/organization
                    if any(kw in desc for kw in [
                        "company", "organization", "software", "enterprise", "firm",
                        "agency", "platform", "service", "startup", "business",
                        "corporation", "technology", "inc", "ltd",
                    ]):
                        profile.exists = True
                        profile.url = f"https://www.wikidata.org/wiki/{r['id']}"
                        profile.verification_status = "checked"
                        profile.extra_data["qid"] = r["id"]
                        profile.extra_data["description"] = r.get("description", "")
                        return profile
            profile.exists = False
            profile.verification_status = "checked"
    except Exception as e:
        profile.verification_status = "error"
        profile.error_message = str(e)[:100]
    return profile


# ── Also check profiles already discovered on the site ────────────────────────

def _check_onsite_links(
    social_links: Dict[str, str],
    review_platform_links: Dict[str, str],
    external_entity_links: Dict[str, str],
    same_as_links: List[str],
) -> Dict[str, str]:
    """
    Extract known platform URLs from on-site signals.
    Returns {platform_name: url} for platforms found on the site.
    """
    found = {}
    all_links = list(social_links.values()) + list(review_platform_links.values()) + \
                list(external_entity_links.values()) + same_as_links

    platform_domains = {
        "Trustpilot": ["trustpilot.com"],
        "Clutch": ["clutch.co"],
        "G2": ["g2.com"],
        "Crunchbase": ["crunchbase.com"],
        "LinkedIn": ["linkedin.com"],
        "YouTube": ["youtube.com"],
        "Wikipedia": ["wikipedia.org"],
        "Facebook": ["facebook.com"],
        "Twitter": ["twitter.com"],
        "Instagram": ["instagram.com"],
        "Google Business": ["google.com/maps", "g.page"],
    }
    for link in all_links:
        ll = link.lower()
        for name, domains in platform_domains.items():
            for domain in domains:
                if domain in ll and name not in found:
                    found[name] = link
    return found


# ── Main Validation Entry Point ──────────────────────────────────────────────

def validate_external_profiles(
    domain: str,
    brand_name: str = "",
    social_links: Dict[str, str] = None,
    review_platform_links: Dict[str, str] = None,
    external_entity_links: Dict[str, str] = None,
    same_as_links: List[str] = None,
    use_cache: bool = True,
) -> ExternalValidationResult:
    """
    Validate external profiles for a domain/brand.

    Args:
        domain: e.g. "valuecoders.com"
        brand_name: e.g. "ValueCoders" (derived from domain if empty)
        social_links: from page.social_links
        review_platform_links: from page.review_platform_links
        external_entity_links: from page.external_entity_links
        same_as_links: from page.same_as_links
        use_cache: check/store in SQLite cache

    Returns:
        ExternalValidationResult with validated profiles
    """
    _init_cache_table()

    clean_domain = domain.replace("www.", "")
    if not brand_name:
        brand_name = clean_domain.split(".")[0].capitalize()

    # Check cache
    if use_cache:
        cached = _get_cached(clean_domain)
        if cached:
            return cached

    start = time.time()
    result = ExternalValidationResult()

    # Gather on-site hints for link-based platforms
    onsite_links = _check_onsite_links(
        social_links or {},
        review_platform_links or {},
        external_entity_links or {},
        same_as_links or [],
    )

    # ── Run all validators ────────────────────────────────────────────────
    validators = [
        ("Trustpilot",       lambda: _validate_trustpilot(clean_domain)),
        ("Clutch",           lambda: _validate_clutch(clean_domain, brand_name)),
        ("G2",               lambda: _validate_g2(brand_name)),
        ("Crunchbase",       lambda: _validate_crunchbase(brand_name)),
        ("LinkedIn",         lambda: _validate_linkedin(brand_name)),
        ("YouTube",          lambda: _validate_youtube(brand_name)),
        ("Google Business",  lambda: _validate_google_business(brand_name, onsite_links.get("Google Business"))),
        ("Wikipedia",        lambda: _validate_wikipedia(brand_name)),
        ("Wikidata",         lambda: _validate_wikidata(brand_name)),
    ]

    for platform_name, validator_fn in validators:
        try:
            profile = validator_fn()
            # Enrich with on-site link if we found one
            if platform_name in onsite_links and not profile.exists:
                profile.extra_data["onsite_link"] = onsite_links[platform_name]
                profile.extra_data["onsite_detected"] = True
            elif platform_name in onsite_links and profile.exists:
                profile.extra_data["onsite_link"] = onsite_links[platform_name]
            result.profiles.append(profile)
        except Exception as e:
            result.profiles.append(ExternalProfile(
                platform=platform_name,
                verification_status="error",
                error_message=str(e)[:100],
            ))

    # ── Summarise ─────────────────────────────────────────────────────────
    result.profiles_found = sum(1 for p in result.profiles if p.exists)
    result.profiles_missing = [p.platform for p in result.profiles
                                if not p.exists and p.verification_status == "checked"]
    result.profiles_errored = [p.platform for p in result.profiles
                                if p.verification_status == "error"]
    result.knowledge_panel_detected = False  # True KP check needs Google API
    result.wikipedia_detected = any(p.platform == "Wikipedia" and p.exists for p in result.profiles)
    result.wikidata_detected = any(p.platform == "Wikidata" and p.exists for p in result.profiles)

    result.validation_time_ms = int((time.time() - start) * 1000)

    # Save to cache
    if use_cache:
        _save_cache(clean_domain, result)

    return result


def get_profile_by_platform(result: ExternalValidationResult, platform: str) -> Optional[ExternalProfile]:
    """Helper to get a specific platform's profile from validation results."""
    for p in result.profiles:
        if p.platform.lower() == platform.lower():
            return p
    return None
