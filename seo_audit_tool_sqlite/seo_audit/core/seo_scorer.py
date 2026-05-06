"""
seo_scorer.py
Scores the SEO Foundation module (max 100 pts).

Checks:
  Title tag            → 18 pts
  Meta description     → 16 pts
  H1 presence          → 14 pts
  H2 presence          → 12 pts
  Alt tag coverage     → 16 pts
  Indexability         → 14 pts
  Internal links       → 10 pts
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class CheckResult:
    name: str
    score: int
    max_score: int
    status: str          # "pass" | "warn" | "fail"
    finding: str
    impact: str


@dataclass
class ModuleResult:
    module: str
    score: int           # 0–100
    checks: List[CheckResult] = field(default_factory=list)


def score(page) -> ModuleResult:
    checks = []
    total = 0

    # ── Title tag (18 pts) ───────────────────────────────────────────────────
    t = page.title
    if not t:
        checks.append(CheckResult("Title tag", 0, 18, "fail",
            "No title tag found.",
            "Pages without a title tag are excluded from most AI-generated answer panels and lose significant click-through potential."))
    elif len(t) < 30:
        checks.append(CheckResult("Title tag", 10, 18, "warn",
            f"Title is too short ({len(t)} chars): \"{t[:60]}\"",
            "Short titles don't signal enough relevance to search engines. Aim for 50–60 characters."))
        total += 10
    elif len(t) > 70:
        checks.append(CheckResult("Title tag", 12, 18, "warn",
            f"Title is too long ({len(t)} chars) — will be truncated in SERPs.",
            "Truncated titles lose the tail keywords. Keep titles under 60 characters."))
        total += 12
    else:
        checks.append(CheckResult("Title tag", 18, 18, "pass",
            f"Title found ({len(t)} chars): \"{t[:60]}\"",
            "Well-optimised title length."))
        total += 18

    # ── Meta description (16 pts) ────────────────────────────────────────────
    m = page.meta_description
    if not m:
        checks.append(CheckResult("Meta description", 0, 16, "fail",
            "No meta description found.",
            "Missing meta descriptions reduce click-through rate and remove snippet control in search results."))
    elif len(m) < 80:
        checks.append(CheckResult("Meta description", 8, 16, "warn",
            f"Meta description is short ({len(m)} chars).",
            "Aim for 120–160 characters to fully utilise the SERP snippet space."))
        total += 8
    elif len(m) > 165:
        checks.append(CheckResult("Meta description", 10, 16, "warn",
            f"Meta description is too long ({len(m)} chars) — will be cut off.",
            "Keep under 160 characters to avoid truncation in search results."))
        total += 10
    else:
        checks.append(CheckResult("Meta description", 16, 16, "pass",
            f"Meta description found ({len(m)} chars).",
            "Good length — snippet will display fully."))
        total += 16

    # ── H1 presence (14 pts) ─────────────────────────────────────────────────
    h1s = page.h1_tags
    if not h1s:
        checks.append(CheckResult("H1 tag", 0, 14, "fail",
            "No H1 tag found on the page.",
            "The H1 is the single strongest on-page keyword signal. Its absence significantly weakens topical relevance."))
    elif len(h1s) > 1:
        checks.append(CheckResult("H1 tag", 8, 14, "warn",
            f"{len(h1s)} H1 tags found — should have exactly one.",
            "Multiple H1s dilute topical focus. Keep a single, keyword-rich H1."))
        total += 8
    else:
        checks.append(CheckResult("H1 tag", 14, 14, "pass",
            f"Single H1 found: \"{h1s[0][:60]}\"",
            "Correct H1 usage."))
        total += 14

    # ── H2 presence (12 pts) ─────────────────────────────────────────────────
    h2s = page.h2_tags
    if not h2s:
        checks.append(CheckResult("H2 tags", 0, 12, "fail",
            "No H2 headings found.",
            "H2s structure content for both users and crawlers. Their absence reduces scannability and topic depth signals."))
    elif len(h2s) < 2:
        checks.append(CheckResult("H2 tags", 7, 12, "warn",
            f"Only {len(h2s)} H2 heading found — more would improve content structure.",
            "Use H2s to break content into scannable sections."))
        total += 7
    else:
        checks.append(CheckResult("H2 tags", 12, 12, "pass",
            f"{len(h2s)} H2 headings found.",
            "Good heading hierarchy."))
        total += 12

    # ── Alt tag coverage (16 pts) ─────────────────────────────────────────────
    imgs = page.images
    imgs_alt = page.images_with_alt
    if not imgs:
        checks.append(CheckResult("Image alt tags", 16, 16, "pass",
            "No images found — not applicable.",
            "No images to evaluate."))
        total += 16
    else:
        pct = len(imgs_alt) / len(imgs) * 100
        if pct == 100:
            checks.append(CheckResult("Image alt tags", 16, 16, "pass",
                f"All {len(imgs)} images have alt text.",
                "Full alt coverage — good for accessibility and image search."))
            total += 16
        elif pct >= 70:
            pts = 10
            checks.append(CheckResult("Image alt tags", pts, 16, "warn",
                f"{len(imgs_alt)}/{len(imgs)} images have alt text ({pct:.0f}%).",
                "Missing alt tags reduce accessibility scores and image search visibility."))
            total += pts
        else:
            pts = 4
            checks.append(CheckResult("Image alt tags", pts, 16, "fail",
                f"Only {len(imgs_alt)}/{len(imgs)} images have alt text ({pct:.0f}%).",
                "Poor alt coverage is a significant accessibility and SEO issue."))
            total += pts

    # ── Indexability (14 pts) ────────────────────────────────────────────────
    robots = page.robots_meta
    if "noindex" in robots:
        checks.append(CheckResult("Indexability", 0, 14, "fail",
            "Page has a noindex directive — it will NOT be indexed by search engines.",
            "This page is invisible to all search engines. Remove noindex unless intentional."))
    else:
        checks.append(CheckResult("Indexability", 14, 14, "pass",
            "No noindex directive found — page is indexable.",
            "Page can be crawled and ranked."))
        total += 14

    # ── Internal links (10 pts) ──────────────────────────────────────────────
    n = len(set(page.internal_links))
    if n == 0:
        checks.append(CheckResult("Internal links", 0, 10, "fail",
            "No internal links detected.",
            "Internal links distribute PageRank and help crawlers discover content. Zero links isolates this page."))
    elif n < 5:
        pts = 5
        checks.append(CheckResult("Internal links", pts, 10, "warn",
            f"Only {n} internal link(s) found.",
            "Increase internal linking to improve crawl depth and topic authority signals."))
        total += pts
    else:
        checks.append(CheckResult("Internal links", 10, 10, "pass",
            f"{n} internal links found.",
            "Good internal linking structure."))
        total += 10

    # Normalise to 100
    max_possible = sum(c.max_score for c in checks)
    normalised = round((total / max_possible) * 100) if max_possible else 0

    return ModuleResult(module="SEO Foundation", score=normalised, checks=checks)
