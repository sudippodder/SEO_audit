"""
pdf_export.py
Generates a clean PDF report from the audit data dict.
Uses fpdf2 (pip install fpdf2).
"""
from typing import Optional


def generate_pdf(data: dict) -> Optional[bytes]:
    """Generate PDF bytes from audit data dict. Returns None if fpdf2 not installed."""
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    def _safe(text: str, maxlen: int = 0) -> str:
        """Strip/replace characters outside latin-1 (emojis, em-dash, smart quotes, etc.)."""
        if not isinstance(text, str):
            text = str(text)
        replacements = {
            "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u00b7": ".",
            "\u00a9": "(c)", "\u00ae": "(R)", "\u2122": "(TM)",
            "\u2026": "...", "\u00b0": "deg", "\u00d7": "x",
            "\u2264": "<=", "\u2265": ">=", "\u00e9": "e", "\u00e0": "a",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Remove all emojis and chars > 255 (latin-1 boundary)
        text = "".join(c if ord(c) < 256 else "?" for c in text)
        if maxlen and len(text) > maxlen:
            text = text[:maxlen]
        return text

    STATUS_COLOR = {
        "pass": (42, 138, 94),
        "warn": (200, 150, 47),
        "fail": (200, 75, 47),
    }
    EFFORT_LABEL = {"quick": "Quick Win", "medium": "Medium", "complex": "Complex"}

    class AuditPDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 11)
            self.set_fill_color(13, 13, 13)
            self.set_text_color(255, 255, 255)
            self.cell(0, 10, "  GEO Readiness Audit Report", fill=True, ln=True)
            self.set_text_color(0, 0, 0)
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            url_safe = _safe(data.get("url", ""), 60)
            self.cell(0, 10, f"Page {self.page_no()} | GEO Readiness Audit | {url_safe}", align="C")

    pdf = AuditPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title block
    from urllib.parse import urlparse
    domain = _safe(urlparse(data.get("url", "")).netloc.replace("www.", ""))
    kw = _safe(data.get("keyword", "") or "N/A", 40)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(13, 13, 13)
    pdf.cell(0, 10, f"GEO Audit: {domain}", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"URL: {_safe(data.get('url',''), 70)} | Keyword: {kw}", ln=True)
    pdf.ln(4)

    # Score banner
    scores = [
        ("Overall Score", data.get("overall_score", 0)),
        ("GEO Score",     (data.get("geo_report") or {}).get("geo_score", 0)),
        ("AI Score",      data.get("ai_score", 0)),
        ("SEO Score",     data.get("seo_score", 0)),
    ]
    col_w = 47
    for _, val in scores:
        color = (42, 138, 94) if val > 70 else ((200, 150, 47) if val > 40 else (200, 75, 47))
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(col_w, 12, str(val), fill=True, align="C")
    pdf.ln(12)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    for label, _ in scores:
        pdf.cell(col_w, 5, label, align="C")
    pdf.ln(10)

    # Key Insights
    insights = data.get("insights", [])
    if insights:
        _section_header(pdf, "Key AI/GEO Insights", _safe)
        for ins in insights[:5]:
            status = ins.get("status", "warn")
            r, g, b = STATUS_COLOR.get(status, (100, 100, 100))
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(18, 6, status.upper(), fill=True, align="C")
            pdf.set_fill_color(245, 245, 245)
            pdf.set_text_color(13, 13, 13)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(0, 6, f"  {_safe(ins.get('title',''), 70)}", fill=True, ln=True)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(80, 80, 80)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 4, "  " + _safe(ins.get("found", ""), 120))
            pdf.ln(1)
        pdf.ln(2)

    # New modules: crawlability, entity, content quality
    for rkey, label in [
        ("crawlability_report",    "Technical AI Crawlability & Schema"),
        ("entity_report",          "Entity & Knowledge Graph"),
        ("content_quality_report", "Content Quality & Off-Page Authority"),
    ]:
        rpt = data.get(rkey, {})
        if not rpt:
            continue
        _section_header(pdf, label, _safe)
        for mkey in ["crawlability", "schema_depth", "entity_kg", "content_quality", "off_page"]:
            mod = rpt.get(mkey)
            if not mod:
                continue
            _render_module(pdf, _safe(mod.get("module", mkey)), mod.get("score", 0), mod, _safe)

    # GEO Readiness modules
    geo = data.get("geo_report", {})
    if geo:
        _section_header(pdf, "GEO Readiness Modules", _safe)
        for gkey, glabel in [
            ("citation_readiness", "AI Citation Readiness"),
            ("entity_clarity",     "Brand / Entity Clarity"),
            ("extractability",     "AI Extractability"),
            ("trust_signals",      "AI Trust Signals"),
            ("overview_readiness", "AI Overview Readiness"),
            ("information_gain",   "Information Gain"),
        ]:
            mod = geo.get(gkey, {})
            if not mod:
                continue
            _render_module(pdf, glabel, mod.get("score", 0), mod, _safe)
        opp = geo.get("geo_opportunity", {})
        if opp:
            _section_header(pdf, f"GEO Opportunity Gap: {opp.get('gap_score', 0)}/100", _safe)
            _render_checks(pdf, opp.get("checks", []), _safe)

    # Traditional SEO
    seo_mod = data.get("seo_module", {})
    if seo_mod:
        _section_header(pdf, f"Traditional SEO Signals - Score: {seo_mod.get('score', 0)}/100", _safe)
        _render_checks(pdf, seo_mod.get("checks", []), _safe)

    return bytes(pdf.output())


def _section_header(pdf, title: str, _safe):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(13, 13, 13)
    pdf.cell(0, 7, f"  {_safe(title)}", fill=True, ln=True)
    pdf.ln(1)


def _render_module(pdf, label: str, mod_score: int, mod: dict, _safe):
    checks = mod.get("checks", [])
    fails  = sum(1 for c in checks if isinstance(c, dict) and c.get("status") == "fail")
    warns  = sum(1 for c in checks if isinstance(c, dict) and c.get("status") == "warn")
    passes = len(checks) - fails - warns
    color = (42, 138, 94) if mod_score > 70 else ((200, 150, 47) if mod_score > 40 else (200, 75, 47))
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*color)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(20, 6, str(mod_score), fill=True, align="C")
    pdf.set_fill_color(248, 248, 248)
    pdf.set_text_color(13, 13, 13)
    pdf.cell(0, 6, f"  {_safe(label)}  |  FAIL: {fails}  WARN: {warns}  PASS: {passes}", fill=True, ln=True)
    bad = [c for c in checks if isinstance(c, dict) and c.get("status") in ("fail", "warn")]
    _render_checks(pdf, bad, _safe)
    pdf.ln(1)


def _render_checks(pdf, checks: list, _safe):
    STATUS_COLOR = {"pass": (42, 138, 94), "warn": (200, 150, 47), "fail": (200, 75, 47)}
    EFFORT_LABEL = {"quick": "Quick Win", "medium": "Medium", "complex": "Complex"}
    for c in checks:
        if not isinstance(c, dict):
            continue
        status = c.get("status", "warn")
        effort = EFFORT_LABEL.get(c.get("effort", "medium"), "Medium")
        r, g, b = STATUS_COLOR.get(status, (150, 150, 150))
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(16, 5, status.upper(), fill=True, align="C")
        pdf.set_fill_color(220, 220, 220)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(22, 5, effort, fill=True, align="C")
        pdf.set_text_color(13, 13, 13)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 5, f"  {_safe(c.get('name',''), 65)}", ln=True)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(60, 60, 60)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 3.5, "  " + _safe(c.get("found", ""), 150))
        if status in ("fail", "warn") and c.get("how_to_fix"):
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(30, 100, 60)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 3.5, "  Fix: " + _safe(c.get('how_to_fix', ''), 200))
        pdf.ln(1.5)
