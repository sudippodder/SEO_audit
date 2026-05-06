"""
content_scorer.py
Scores the Content Quality module (max 100 pts).

Checks:
  Word count           → 30 pts
  Paragraph size       → 25 pts
  Heading usage ratio  → 25 pts
  Content depth        → 20 pts
"""

from dataclasses import dataclass, field
from typing import List
from .seo_scorer import CheckResult, ModuleResult


def score(page) -> ModuleResult:
    checks = []
    total = 0

    # ── Word count (30 pts) ──────────────────────────────────────────────────
    wc = page.word_count
    if wc < 150:
        checks.append(CheckResult("Word count", 0, 30, "fail",
            f"Very thin content — only {wc} words.",
            "Pages under 300 words rarely rank for competitive queries or appear in AI answer boxes. Significant content expansion needed."))
    elif wc < 300:
        checks.append(CheckResult("Word count", 8, 30, "warn",
            f"Low word count: {wc} words.",
            "Aim for at least 600–800 words for most informational pages to be considered substantive."))
        total += 8
    elif wc < 600:
        checks.append(CheckResult("Word count", 16, 30, "warn",
            f"Moderate content: {wc} words.",
            "Content is present but may be too thin for highly competitive topics."))
        total += 16
    elif wc < 1500:
        checks.append(CheckResult("Word count", 24, 30, "pass",
            f"Good content length: {wc} words.",
            "Solid content volume for most queries."))
        total += 24
    else:
        checks.append(CheckResult("Word count", 30, 30, "pass",
            f"Comprehensive content: {wc} words.",
            "Strong content depth — well positioned for competitive queries."))
        total += 30

    # ── Paragraph size (25 pts) ──────────────────────────────────────────────
    paras = [p for p in page.paragraphs if len(p.split()) > 10]
    if not paras:
        checks.append(CheckResult("Paragraph size", 10, 25, "warn",
            "No substantial paragraphs detected.",
            "Content may be too fragmented or missing body copy altogether."))
        total += 10
    else:
        avg_words = sum(len(p.split()) for p in paras) / len(paras)
        if avg_words > 150:
            checks.append(CheckResult("Paragraph size", 5, 25, "fail",
                f"Average paragraph is very long ({avg_words:.0f} words).",
                "AI extraction engines and modern readers prefer paragraphs under 80 words. Long blocks reduce scannability and AI snippet eligibility."))
            total += 5
        elif avg_words > 100:
            checks.append(CheckResult("Paragraph size", 14, 25, "warn",
                f"Paragraphs are slightly long ({avg_words:.0f} words avg).",
                "Consider breaking long paragraphs into shorter, focused units for better AI extractability."))
            total += 14
        elif avg_words < 20:
            checks.append(CheckResult("Paragraph size", 16, 25, "warn",
                f"Paragraphs are very short ({avg_words:.0f} words avg) — content may feel fragmented.",
                "While short paragraphs are fine, very short ones can indicate thin or bullet-only content."))
            total += 16
        else:
            checks.append(CheckResult("Paragraph size", 25, 25, "pass",
                f"Good paragraph length ({avg_words:.0f} words avg).",
                "Paragraph sizes are well-suited for AI extraction and readability."))
            total += 25

    # ── Heading usage ratio (25 pts) ─────────────────────────────────────────
    heading_count = len(page.all_headings)
    if page.word_count > 0:
        ratio = heading_count / (page.word_count / 200)  # headings per 200 words
    else:
        ratio = 0

    if heading_count == 0:
        checks.append(CheckResult("Heading usage", 0, 25, "fail",
            "No headings found in the content body.",
            "Content without headings is unstructured for both users and AI parsers. Add H2/H3 headings every 200–300 words."))
    elif ratio < 0.5:
        checks.append(CheckResult("Heading usage", 10, 25, "warn",
            f"Infrequent heading use — {heading_count} heading(s) across {page.word_count} words.",
            "Use headings more frequently to break up content and improve AI topic extraction."))
        total += 10
    elif ratio > 4:
        checks.append(CheckResult("Heading usage", 16, 25, "warn",
            f"Heading density is very high ({heading_count} headings) — content may be too fragmented.",
            "Overly frequent headings can make content feel shallow. Aim for substance under each heading."))
        total += 16
    else:
        checks.append(CheckResult("Heading usage", 25, 25, "pass",
            f"Good heading frequency — {heading_count} headings across {page.word_count} words.",
            "Heading structure supports scannability and AI topic parsing."))
        total += 25

    # ── Content depth signals (20 pts) ───────────────────────────────────────
    full_text_lower = page.full_text.lower()
    depth_signals = {
        "numbered lists or steps": any(tag in page.html for tag in ["<ol", "<li"]),
        "external references": len(page.external_links) > 0,
        "structured data": len(page.schema_types) > 0,
        "detailed headings (H3+)": len(page.h3_tags) > 0,
    }
    signal_count = sum(depth_signals.values())

    if signal_count == 0:
        checks.append(CheckResult("Content depth signals", 0, 20, "fail",
            "No depth signals detected (no lists, no schema, no H3s).",
            "Content lacks structural richness. Add lists, examples, and structured data to signal depth to search engines."))
    elif signal_count <= 2:
        pts = 10
        checks.append(CheckResult("Content depth signals", pts, 20, "warn",
            f"{signal_count}/4 depth signals present: {', '.join(k for k,v in depth_signals.items() if v)}.",
            "Add more structural elements (schema markup, numbered steps, sub-headings) to strengthen content depth signals."))
        total += pts
    else:
        checks.append(CheckResult("Content depth signals", 20, 20, "pass",
            f"{signal_count}/4 depth signals present: {', '.join(k for k,v in depth_signals.items() if v)}.",
            "Good content depth and structural richness."))
        total += 20

    max_possible = sum(c.max_score for c in checks)
    normalised = round((total / max_possible) * 100) if max_possible else 0

    return ModuleResult(module="Content Quality", score=normalised, checks=checks)
