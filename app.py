"""app.py — AI GEO Audit Tool  |  streamlit run app.py"""
import os, time, json, validators
import streamlit as st
from dotenv import load_dotenv
from urllib.parse import urlparse
load_dotenv()

from core import run_audit
from utils.storage import save_audit, get_recent_audits, get_audit_by_id, get_stats, export_csv, _report_to_dict
from utils.storage import create_user, get_user_by_email, update_user_password, get_all_users, update_user_role, delete_user
from utils.auth import hash_password, verify_password, generate_temp_password, send_forgot_password_email
from utils.pdf_export import generate_pdf

st.set_page_config(page_title="GEO Readiness Audit", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.main .block-container{max-width:1080px;padding:1.5rem 2rem 4rem;}

/* Hero */
.hero-badge{display:inline-block;font-family:'Syne',sans-serif;font-size:10px;font-weight:700;
 letter-spacing:.2em;text-transform:uppercase;color:#c84b2f;border:1.5px solid #c84b2f;
 padding:4px 12px;border-radius:2px;margin-bottom:14px;}
.hero-title{font-family:'Syne',sans-serif;font-size:2.4rem;font-weight:800;line-height:1.08;
 letter-spacing:-.02em;color:#0d0d0d;margin-bottom:8px;}
.hero-title em{font-style:italic;color:#c84b2f;}
.hero-sub{font-size:.95rem;color:#6b6660;line-height:1.65;max-width:560px;}

/* Score banner */
.score-banner{background:#0d0d0d;color:#fff;border-radius:10px;padding:1.6rem 2rem;
 display:flex;align-items:center;gap:2rem;margin-bottom:1.5rem;flex-wrap:wrap;}
.score-big{font-family:'Syne',sans-serif;font-size:4rem;font-weight:800;line-height:1;}
.score-right{display:flex;flex-direction:column;gap:4px;}
.score-eye{font-size:10px;letter-spacing:.15em;text-transform:uppercase;opacity:.5;}
.sg-r{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:#e07060;}
.sg-a{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:#e0b860;}
.sg-g{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:#60c890;}
.score-sub{font-size:.82rem;opacity:.5;margin-top:2px;}
/* Two score pills */
.score-pair{display:flex;gap:12px;flex-wrap:wrap;}
.score-pill-box{background:rgba(255,255,255,.08);border-radius:8px;padding:.8rem 1.2rem;text-align:center;min-width:100px;}
.pill-num{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;line-height:1;}
.pill-label{font-size:10px;letter-spacing:.1em;text-transform:uppercase;opacity:.55;margin-top:2px;}

/* Section label */
.sec-label{font-family:'Syne',sans-serif;font-size:10px;font-weight:700;letter-spacing:.15em;
 text-transform:uppercase;color:#9a9285;border-bottom:1px solid rgba(13,13,13,.1);
 padding-bottom:8px;margin:1.6rem 0 .9rem;}

/* Insight card */
.ins-card{background:#fff;border:1.5px solid rgba(13,13,13,.1);border-radius:8px;
 padding:1rem 1.2rem;margin-bottom:9px;display:flex;gap:12px;align-items:flex-start;}
.ins-title{font-weight:500;font-size:.88rem;color:#0d0d0d;margin-bottom:3px;}
.ins-found{font-size:.82rem;color:#4a4540;line-height:1.55;margin-bottom:4px;}
.ins-impact{font-size:.78rem;color:#9a9285;line-height:1.5;font-style:italic;}

/* Check card */
.chk-card{background:#fff;border:1.5px solid rgba(13,13,13,.08);border-radius:8px;
 padding:1.1rem 1.3rem;margin-bottom:10px;border-left:4px solid var(--cc,#ccc);}
.chk-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;}
.chk-name{font-family:'Syne',sans-serif;font-size:.87rem;font-weight:700;color:#0d0d0d;}
.chk-badge{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;
 padding:2px 10px;border-radius:3px;background:var(--cc-bg,#f0f0f0);color:var(--cc,#555);}
.chip{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:2px 8px;border-radius:2px;}
.chip-f{background:#fde8e5;color:#c84b2f;}.chip-w{background:#fdf3e0;color:#b07010;}.chip-p{background:#e4f5ec;color:#1a7a45;}
.found-box{font-size:.83rem;color:#3a3530;line-height:1.6;padding:8px 10px;background:#f5f2ec;border-radius:4px;margin-bottom:8px;}
.impact-box{font-size:.8rem;color:#6b6660;line-height:1.55;margin-bottom:8px;}
.fix-box{border:1.5px solid rgba(42,138,94,.25);background:#f0faf5;border-radius:6px;padding:10px 12px;}
.fix-lbl{font-family:'Syne',sans-serif;font-size:9px;font-weight:700;letter-spacing:.15em;
 text-transform:uppercase;color:#2a8a5e;margin-bottom:5px;}
.fix-txt{font-size:.81rem;color:#1a4a35;line-height:1.6;}
/* Effort badges */
.effort-q{background:#e8f4ff;color:#1a5fa8;font-size:9px;font-weight:700;letter-spacing:.08em;
 padding:2px 7px;border-radius:2px;text-transform:uppercase;}
.effort-m{background:#fff3e0;color:#8a5a00;font-size:9px;font-weight:700;letter-spacing:.08em;
 padding:2px 7px;border-radius:2px;text-transform:uppercase;}
.effort-c{background:#fce8f3;color:#8a0060;font-size:9px;font-weight:700;letter-spacing:.08em;
 padding:2px 7px;border-radius:2px;text-transform:uppercase;}

/* Stats row */
.stat-box{background:#fff;border:1.5px solid rgba(13,13,13,.08);border-radius:6px;
 padding:9px 12px;margin-bottom:7px;display:flex;justify-content:space-between;align-items:center;}
.stat-val{font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;}

/* CTA */
.cta-block{background:#0d0d0d;border-radius:10px;padding:2.2rem 2rem;text-align:center;color:#fff;margin-top:2rem;}
.cta-eye{font-size:10px;letter-spacing:.18em;text-transform:uppercase;opacity:.45;margin-bottom:8px;font-family:'Syne',sans-serif;}
.cta-h{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;margin-bottom:7px;}
.cta-s{font-size:.88rem;opacity:.6;line-height:1.65;max-width:420px;margin:0 auto 1.6rem;}

/* Buttons */
div.stButton>button{font-family:'Syne',sans-serif!important;font-weight:700!important;
 letter-spacing:.06em!important;text-transform:uppercase!important;border-radius:4px!important;}
div.stButton>button[kind="primary"]{background:#0d0d0d!important;color:#fff!important;border:none!important;}
div.stButton>button[kind="primary"]:hover{background:#c84b2f!important;}
div.stButton>button[kind="secondary"]{background:transparent!important;color:#0d0d0d!important;border:1.5px solid rgba(13,13,13,.25)!important;}
.stProgress>div>div>div{background-color:#c84b2f!important;}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def gc(s):
    return "red" if s<=40 else ("amber" if s<=70 else "green")

def grade_label(s):
    return "Poor" if s<=40 else ("Average" if s<=70 else "Strong")

STATUS_C  = {"fail":"#c84b2f","warn":"#c8962f","pass":"#2a8a5e"}
STATUS_BG = {"fail":"#fde8e5","warn":"#fdf3e0","pass":"#e4f5ec"}
STATUS_IC = {"fail":"❌","warn":"⚠️","pass":"✅"}
CHIP_CLS  = {"fail":"chip-f","warn":"chip-w","pass":"chip-p"}

def validate(url, email):
    e = {}
    if not url.strip(): e["url"] = "Please enter a website URL."
    else:
        test = url if url.startswith("http") else "https://"+url
        if not validators.url(test): e["url"] = "Please enter a valid URL."
    if not email.strip(): e["email"] = "Email is required."
    elif not validators.email(email): e["email"] = "Please enter a valid email address."
    return e

def render_banner(data, domain):
    s = data["overall_score"]; sc = data.get("seo_score",0); ai = data.get("ai_score",0)
    geo = data.get("geo_report",{}); geo_score = geo.get("geo_score",0) if geo else 0
    ext_auth_score = (data.get("external_authority_report") or {}).get("external_authority_score", 0)
    ai_vis_score = (data.get("ai_visibility_report") or {}).get("ai_visibility_score", 0)
    grade = data["overall_grade"]; color = gc(s)
    saved = f" · Saved {data['saved_at']}" if data.get("saved_at") else ""
    kw_tag = f" · Keyword: <em>{data.get('keyword','')}</em>" if data.get("keyword") else ""
    st.markdown(f"""
    <div class="score-banner">
      <div>
        <div class="score-eye">Overall Score</div>
        <div class="score-big">{s}</div>
        <div class="score-eye">out of 100</div>
      </div>
      <div class="score-pair">
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if geo_score<=40 else 'a' if geo_score<=70 else 'g'}">{geo_score}</div>
          <div class="pill-label">GEO Score</div>
        </div>
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if ai<=40 else 'a' if ai<=70 else 'g'}">{ai}</div>
          <div class="pill-label">AI Score</div>
        </div>
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if ext_auth_score<=40 else 'a' if ext_auth_score<=70 else 'g'}">{ext_auth_score}</div>
          <div class="pill-label">Ext Authority</div>
        </div>
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if ai_vis_score<=40 else 'a' if ai_vis_score<=70 else 'g'}">{ai_vis_score}</div>
          <div class="pill-label">AI Visibility</div>
        </div>
        <div class="score-pill-box">
          <div class="pill-num sg-{'r' if sc<=40 else 'a' if sc<=70 else 'g'}">{sc}</div>
          <div class="pill-label">SEO Score</div>
        </div>
      </div>
      <div class="score-right">
        <span class="score-eye">Overall Grade</span>
        <span class="sg-{color[0]}">{grade}</span>
        <span class="score-sub">{domain}{saved}</span>
        <span class="score-sub" style="color:rgba(255,255,255,.4)">{kw_tag}</span>
      </div>
    </div>""", unsafe_allow_html=True)

EFFORT_CLS = {"quick": "effort-q", "medium": "effort-m", "complex": "effort-c"}
EFFORT_LBL = {"quick": "⚡ Quick Win", "medium": "🔧 Medium", "complex": "🏗️ Complex"}

def render_check_cards(checks):
    for c in checks:
        st_c = STATUS_C.get(c["status"],"#888")
        st_bg = STATUS_BG.get(c["status"],"#f5f5f5")
        chip = CHIP_CLS.get(c["status"],"")
        effort = c.get("effort", "medium")
        effort_html = f'<span class="{EFFORT_CLS.get(effort,"effort-m")}">{EFFORT_LBL.get(effort,"🔧 Medium")}</span>'
        fix_html = (f'<div class="fix-box"><div class="fix-lbl">🔧 How to fix</div>'
                    f'<div class="fix-txt">{c.get("how_to_fix","")}</div></div>'
                    if c["status"] in ("fail","warn") else "")
        details_html = ""
        if c.get("details"):
            d_items = "".join([f'<li style="margin-bottom:6px;">{d}</li>' for d in c["details"]])
            details_html = f'<div style="margin-top:10px;padding:10px;background:var(--cc-bg,#f9f9f9);border:1px solid rgba(13,13,13,0.05);border-radius:6px;font-size:0.82rem;max-height:220px;overflow-y:auto;color:#3a3530;"><strong style="font-family:\'Syne\',sans-serif;font-size:0.85rem;">Detailed Issues ({len(c["details"])}):</strong><ul style="margin-top:6px;padding-left:20px;">{d_items}</ul></div>'
        st.markdown(f"""
        <div class="chk-card" style="--cc:{st_c};--cc-bg:{st_bg};">
          <div class="chk-header">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="chip {chip}">{c['status'].upper()}</span>
              {effort_html}
              <span class="chk-name">{c['name']}</span>
            </div>
            <span class="chk-badge">{c['score']}/{c['max_score']} pts</span>
          </div>
          <div class="found-box">🔍 <strong>What we found:</strong> {c['found']}</div>
          <div class="impact-box">💥 <strong>Impact:</strong> {c['impact']}</div>
          {fix_html}
          {details_html}
        </div>""", unsafe_allow_html=True)

NEW_MODULES = [
    ("crawlability_report", "crawlability",   "🕷️ Technical AI Crawlability",      True),
    ("crawlability_report", "schema_depth",   "🗂️ Schema Markup Depth",            True),
    ("entity_report",       "entity_kg",      "🕸️ Entity & Knowledge Graph",        True),
    ("content_quality_report", "content_quality", "📖 Content Quality & LLM Readability", False),
    ("content_quality_report", "off_page",    "🔗 Off-Page & Citation Authority",   False),
    ("external_authority_report", "external_authority", "🌐 External Authority",     True),
    ("ai_visibility_report", "ai_visibility",  "🤖 AI Visibility",                  True),
]

def render_new_module(report_key, mod_key, label, is_critical, data):
    """Render a module from the new crawlability/entity/content_quality reports."""
    report = data.get(report_key, {})
    if not report:
        return
    mod = report.get(mod_key, {})
    if not mod:
        return
    checks = mod.get("checks", [])
    score  = mod.get("score", 0)
    fails  = sum(1 for c in checks if c["status"] == "fail")
    warns  = sum(1 for c in checks if c["status"] == "warn")
    passes = sum(1 for c in checks if c["status"] == "pass")
    crit_badge = '🚨 CRITICAL' if is_critical else ''
    sorted_c = sorted(checks, key=lambda c:(0 if c["status"]=="fail" else 1 if c["status"]=="warn" else 2))
    header = f"{label}{crit_badge}: {score}/100  ·  ❌ {fails}  ·  ⚠️ {warns}  ·  ✅ {passes}"
    with st.expander(header, expanded=(fails > 0)):
        t_all, t_fail, t_warn, t_pass = st.tabs(["All", "Failed", "Warnings", "Passed"])
        with t_all:  render_check_cards(sorted_c)
        with t_fail: render_check_cards([c for c in sorted_c if c["status"]=="fail"])
        with t_warn: render_check_cards([c for c in sorted_c if c["status"]=="warn"])
        with t_pass: render_check_cards([c for c in sorted_c if c["status"]=="pass"])


def render_fix_roadmap(data):
    """Fix Roadmap: all fail/warn checks sorted by effort then impact."""
    all_checks = []
    # Gather from all modules (including new external authority + AI visibility)
    for rkey, mkey, _, _ in NEW_MODULES:
        mod = (data.get(rkey) or {}).get(mkey, {})
        all_checks.extend(mod.get("checks", []))
    geo = data.get("geo_report", {})
    if geo:
        for gkey in ["citation_readiness","entity_clarity","extractability","trust_signals","overview_readiness","information_gain"]:
            mod = geo.get(gkey, {})
            if mod: all_checks.extend(mod.get("checks", []))
    seo = data.get("seo_module", {})
    if seo: all_checks.extend(seo.get("checks", []))

    bad = [c for c in all_checks if c.get("status") in ("fail", "warn")]
    effort_order = {"quick": 0, "medium": 1, "complex": 2}
    bad_sorted = sorted(bad, key=lambda c: (
        effort_order.get(c.get("effort", "medium"), 1),
        0 if c.get("status") == "fail" else 1,
        -(c.get("max_score", 0) - c.get("score", 0))
    ))
    quick = [c for c in bad_sorted if c.get("effort") == "quick"]
    medium = [c for c in bad_sorted if c.get("effort") == "medium"]
    complex_ = [c for c in bad_sorted if c.get("effort") == "complex"]
    st.markdown(f"""<div style="background:#f0f7ff;border:1.5px solid #b0d0f0;border-radius:8px;padding:12px 16px;margin-bottom:12px;">
      <strong>📋 Fix Roadmap</strong> — {len(quick)} Quick Wins · {len(medium)} Medium · {len(complex_)} Complex tasks
      <br><small style="color:#6b6660;">Sorted by effort level. Start with Quick Wins for fastest GEO score gains.</small>
    </div>""", unsafe_allow_html=True)
    if quick:
        st.markdown("**⚡ Quick Wins** *(< 1 day)*")
        render_check_cards(quick)
    if medium:
        st.markdown("**🔧 Medium Effort** *(1–3 days)*")
        render_check_cards(medium)
    if complex_:
        st.markdown("**🏗️ Complex** *(3+ days)*")
        render_check_cards(complex_)

GEO_MODULES = [
    ("citation_readiness",  "🤖 AI Citation Readiness"),
    ("entity_clarity",      "🏢 Brand / Entity Clarity"),
    ("extractability",      "⚡ AI Extractability"),
    ("trust_signals",       "🛡️ AI Trust Signals"),
    ("overview_readiness",  "📋 AI Overview Readiness"),
    ("information_gain",    "💡 Information Gain / Originality"),
]

def _all_geo_checks(geo):
    """Flatten all checks from all 6 GEO modules."""
    out = []
    for key, _ in GEO_MODULES:
        mod = geo.get(key, {})
        out.extend(mod.get("checks", []))
    return out

def render_geo_modules(geo):
    """Render each of the 6 GEO module expanders."""
    for key, label in GEO_MODULES:
        mod = geo.get(key, {})
        if not mod:
            continue
        checks = mod.get("checks", [])
        score  = mod.get("score", 0)
        fails  = sum(1 for c in checks if c["status"] == "fail")
        warns  = sum(1 for c in checks if c["status"] == "warn")
        passes = sum(1 for c in checks if c["status"] == "pass")
        sorted_c = sorted(checks, key=lambda c:(0 if c["status"]=="fail" else 1 if c["status"]=="warn" else 2))
        header = f"{label}: {score}/100  ·  ❌ {fails}  ·  ⚠️ {warns}  ·  ✅ {passes}"
        with st.expander(header, expanded=(fails > 0)):
            t_all, t_fail, t_warn, t_pass = st.tabs(["All", "Failed", "Warnings", "Passed"])
            with t_all:  render_check_cards(sorted_c)
            with t_fail: render_check_cards([c for c in sorted_c if c["status"]=="fail"])
            with t_warn: render_check_cards([c for c in sorted_c if c["status"]=="warn"])
            with t_pass: render_check_cards([c for c in sorted_c if c["status"]=="pass"])

def render_geo_opportunity(opp):
    """Render the GEO Opportunity Score section."""
    if not opp:
        return
    gap  = opp.get("gap_score", 0)
    score = opp.get("score", 0)
    checks = opp.get("checks", [])
    color = "#c84b2f" if gap >= 50 else ("#c8962f" if gap >= 25 else "#2a8a5e")
    st.markdown(f"""
    <div style="background:#0d0d0d;border-radius:10px;padding:1.4rem 1.8rem;margin-bottom:1rem;">
      <div style="font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,.45);margin-bottom:4px;">GEO Opportunity Gap</div>
      <div style="display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;">
        <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;color:{color};line-height:1;">{gap}<span style="font-size:1.4rem;opacity:.6;">/100</span></div>
        <div style="color:rgba(255,255,255,.7);font-size:.88rem;max-width:480px;line-height:1.6;">
          A gap score of <strong style="color:{color};">{gap}</strong> means your website is missing significant AI visibility opportunities.
          The lower your GEO score, the greater the opportunity for improvement.
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    sorted_opp = sorted(checks, key=lambda c:(0 if c["status"]=="fail" else 1 if c["status"]=="warn" else 2))
    render_check_cards(sorted_opp)

def _render_site_crawl_summary(data):
    """Render site crawl summary if full-site audit was performed."""
    crawl = data.get("site_crawl_result")
    if not crawl:
        return
    pages = crawl.get("pages", [])
    st.markdown('<div class="sec-label">🌐 Site Crawl Summary</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Pages Crawled", crawl.get("pages_crawled", 0))
    c2.metric("Pages Discovered", crawl.get("pages_discovered", 0))
    c3.metric("Crawl Time", f"{crawl.get('crawl_time_ms', 0)}ms")

    # Page type coverage
    type_icons = {"homepage": "🏠", "about": "ℹ️", "contact": "📞", "services": "⚙️",
                  "blog": "📝", "case_study": "📊", "team": "👥", "reviews": "⭐", "pricing": "💰"}
    expected = ["homepage", "about", "contact", "services", "blog", "case_study", "team", "reviews"]
    found_types = {p["page_type"] for p in pages}
    coverage_html = ""
    for pt in expected:
        icon = type_icons.get(pt, "📄")
        if pt in found_types:
            coverage_html += f'<span style="display:inline-block;background:#e4f5ec;color:#1a7a45;padding:3px 10px;border-radius:4px;margin:2px 4px;font-size:0.82rem;">{icon} {pt.replace("_"," ").title()} ✅</span>'
        else:
            coverage_html += f'<span style="display:inline-block;background:#fde8e5;color:#c84b2f;padding:3px 10px;border-radius:4px;margin:2px 4px;font-size:0.82rem;">{icon} {pt.replace("_"," ").title()} ❌</span>'
    st.markdown(f'<div style="margin:8px 0 16px;">{coverage_html}</div>', unsafe_allow_html=True)
    
    # ── Critical Crawl Warning (SPA / JS-Heavy detection) ──
    discovered = crawl.get("pages_discovered", 0)
    if discovered <= 1:
        st.markdown(f"""
        <div style="background:#fff3e0;border-left:4px solid #c8962f;border-radius:6px;padding:16px 20px;margin-bottom:20px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <span style="font-size:1.2rem;">⚠️</span>
                <strong style="font-family:'Syne',sans-serif;font-size:1rem;color:#8a5a00;">Critical AI Crawlability Issue Detected</strong>
            </div>
            <div style="font-size:0.88rem;color:#5c3c00;line-height:1.6;">
                <strong>Only {discovered} page was discovered.</strong> This typically happens when a website is built as a <em>Single Page Application (SPA)</em> using React, Vue, or Angular without <strong>Server-Side Rendering (SSR)</strong>, and lacks a valid <code>sitemap.xml</code>.<br><br>
                <strong>GEO Impact:</strong> Because your internal links (<code>&lt;a href="..."&gt;</code>) are only rendered via JavaScript after the page loads, simple AI bots (like ChatGPT, Claude, and Perplexity) will see a completely blank page with zero links. They cannot navigate your website to learn about your services. This renders your internal pages effectively invisible to Generative AI engines.
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_external_profiles(data):
    """Render external profile validation results."""
    ext = data.get("external_validation")
    if not ext:
        return
    profiles = ext.get("profiles", [])
    found = ext.get("profiles_found", 0)
    total = len(profiles)
    st.markdown(f'<div class="sec-label">🔍 External Profile Validation — {found}/{total} Detected</div>', unsafe_allow_html=True)

    platform_icons = {"Trustpilot": "⭐", "Clutch": "🏆", "G2": "📊", "Crunchbase": "🚀",
                      "LinkedIn": "💼", "YouTube": "📺", "Google Business": "📍",
                      "Wikipedia": "📚", "Wikidata": "🔗"}
    for p in profiles:
        icon = platform_icons.get(p["platform"], "🔹")
        if p.get("exists"):
            rating = f" · {p['rating']}/5" if p.get('rating') else ""
            reviews = f" · {p['review_count']} reviews" if p.get('review_count') else ""
            url_link = f" · <a href='{p['url']}' target='_blank' style='color:#2a8a5e;font-size:0.8rem;'>View →</a>" if p.get('url') else ""
            st.markdown(f'<div style="background:#e4f5ec;border:1px solid #c0e0d0;border-radius:6px;padding:8px 12px;margin-bottom:5px;font-size:0.85rem;">'
                        f'{icon} <strong>{p["platform"]}</strong> ✅ Verified{rating}{reviews}{url_link}</div>', unsafe_allow_html=True)
        elif p.get("verification_status") == "error":
            st.markdown(f'<div style="background:#fdf3e0;border:1px solid #e0d0a0;border-radius:6px;padding:8px 12px;margin-bottom:5px;font-size:0.85rem;">'
                        f'{icon} <strong>{p["platform"]}</strong> 🔍 Could not verify — {p.get("error_message", "connection issue")}</div>', unsafe_allow_html=True)
        elif p.get("verification_status") == "heuristic":
            st.markdown(f'<div style="background:#fdf3e0;border:1px solid #e0d0a0;border-radius:6px;padding:8px 12px;margin-bottom:5px;font-size:0.85rem;">'
                        f'{icon} <strong>{p["platform"]}</strong> ⚠️ Requires manual verification</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#fde8e5;border:1px solid #e0b0a0;border-radius:6px;padding:8px 12px;margin-bottom:5px;font-size:0.85rem;">'
                        f'{icon} <strong>{p["platform"]}</strong> ❌ Not detected</div>', unsafe_allow_html=True)
    cached = ext.get("cached", False)
    vtime = ext.get("validation_time_ms", 0)
    st.markdown(f'<div style="text-align:right;font-size:0.75rem;color:#9a9285;margin-top:4px;">'
                f'Validated in {vtime}ms{" (cached)" if cached else ""}</div>', unsafe_allow_html=True)

def _render_ai_test_results(data):
    """Render live AI (ChatGPT) test results if available."""
    ai_vis = data.get("ai_visibility_report", {})
    if not ai_vis:
        return
    ai_test = ai_vis.get("ai_test_result")
    if not ai_test or not ai_test.get("tested"):
        return

    st.markdown('<div class="sec-label">🤖 Live AI Visibility Test — ChatGPT Results</div>', unsafe_allow_html=True)

    vis_score = ai_test.get("visibility_score", 0)
    model = ai_test.get("model_used", "gpt-4o-mini")
    latency = ai_test.get("total_latency_ms", 0)
    brand_recognized = ai_test.get("brand_recognized", False)
    brand_recommended = ai_test.get("brand_recommended", False)
    sentiment = ai_test.get("overall_sentiment", "unknown")
    total_mentions = ai_test.get("total_mentions", 0)
    competitors = ai_test.get("competitors_found", [])

    # Error check
    if ai_test.get("api_error"):
        st.warning(f"⚠️ AI test error: {ai_test['api_error']}")
        return

    # Visibility score gauge
    score_color = "#2a8a5e" if vis_score > 70 else ("#c8962f" if vis_score > 40 else "#c84b2f")
    st.markdown(f"""<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:10px;padding:16px 20px;margin-bottom:12px;color:#fff;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:0.75rem;color:#aaa;text-transform:uppercase;letter-spacing:0.1em;">AI Visibility Score (ChatGPT)</div>
          <div style="font-size:2.5rem;font-weight:800;color:{score_color};">{vis_score}<span style="font-size:1rem;color:#888;">/100</span></div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.8rem;">Brand Recognised: <strong>{'✅ Yes' if brand_recognized else '❌ No'}</strong></div>
          <div style="font-size:0.8rem;">Brand Recommended: <strong>{'✅ Yes' if brand_recommended else '❌ No'}</strong></div>
          <div style="font-size:0.8rem;">Sentiment: <strong>{'🟢 ' + sentiment.title() if sentiment == 'positive' else '🟡 ' + sentiment.title() if sentiment == 'neutral' else '🔴 ' + sentiment.title() if sentiment == 'negative' else '⚪ ' + sentiment.title()}</strong></div>
          <div style="font-size:0.8rem;">Mentions: <strong>{total_mentions}</strong></div>
        </div>
      </div>
      <div style="font-size:0.7rem;color:#666;margin-top:8px;">Model: {model} · Tested in {latency}ms</div>
    </div>""", unsafe_allow_html=True)

    # Competitor landscape
    if competitors:
        comp_str = " · ".join(competitors[:8])
        st.markdown(f'<div style="background:#f8f6f2;border:1px solid #e0dcd5;border-radius:6px;padding:8px 12px;margin-bottom:10px;font-size:0.82rem;">'
                    f'<strong>🏆 AI-Identified Competitors:</strong> {comp_str}</div>', unsafe_allow_html=True)

    # Individual query results
    queries = ai_test.get("queries", [])
    query_labels = {
        "brand_knowledge": "🔍 Brand Knowledge Test",
        "keyword_recommendation": "🎯 Keyword Ranking Test",
        "competitor_comparison": "⚔️ Competitor Comparison Test",
    }
    for q in queries:
        qtype = q.get("query_type", "")
        label = query_labels.get(qtype, qtype)
        mentioned = q.get("brand_mentioned", False)
        position = q.get("position", "not_mentioned")
        q_sentiment = q.get("sentiment", "unknown")
        q_error = q.get("error", "")

        if q_error:
            status_badge = '— ERROR'
        elif mentioned:
            status_badge = '— ✅ DETECTED'
        else:
            status_badge = '— ❌ NOT FOUND'

        pos_str = ""
        if position and position != "not_mentioned":
            pos_str = f" · Position: <strong>{position}</strong>"
        sent_str = ""
        if q_sentiment and q_sentiment != "not_mentioned":
            sent_str = f" · Sentiment: <strong>{q_sentiment}</strong>"

        with st.expander(f"{label} {status_badge}", expanded=False):
            if q_error:
                st.error(f"Error: {q_error}")
            else:
                st.markdown(f'<div style="font-size:0.82rem;color:#4a4540;margin-bottom:6px;">'
                            f'Mentioned: <strong>{"Yes" if mentioned else "No"}</strong>'
                            f'{pos_str}{sent_str} · Mentions: <strong>{q.get("mention_count", 0)}</strong>'
                            f'</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:0.78rem;color:#6b6660;margin-bottom:4px;"><em>Prompt:</em> {q.get("prompt", "")}</div>', unsafe_allow_html=True)
                response = q.get("response", "")
                if response:
                    st.markdown("**ChatGPT Response:**")
                    st.markdown(f'<div style="background:#f8f6f2;border:1px solid #e0dcd5;border-radius:6px;padding:10px 14px;font-size:0.82rem;max-height:300px;overflow-y:auto;">{response}</div>', unsafe_allow_html=True)
                if q.get("competitor_mentions"):
                    st.markdown(f'<div style="font-size:0.78rem;color:#6b6660;margin-top:6px;">Competitors in response: {", ".join(q["competitor_mentions"][:6])}</div>', unsafe_allow_html=True)


def render_full_report(data):
    url = data.get("url",""); domain = urlparse(url).netloc.replace("www.","")
    seo_mod = data.get("seo_module",{})
    geo = data.get("geo_report",{})
    error = data.get("error")
    audit_mode = data.get("audit_mode", "single")
    if error:
        st.error(f"**Audit error:** {error}"); return

    # Audit mode badge
    if audit_mode == "full_site":
        st.markdown('<span style="background:#1a7a45;color:#fff;font-size:10px;font-weight:700;letter-spacing:.12em;padding:3px 10px;border-radius:3px;text-transform:uppercase;">Full Site Audit</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="background:#6b6660;color:#fff;font-size:10px;font-weight:700;letter-spacing:.12em;padding:3px 10px;border-radius:3px;text-transform:uppercase;">Single Page Audit</span>', unsafe_allow_html=True)

    render_banner(data, domain)

    # ── Site Crawl Summary (full-site only) ────────────────────────────────────
    if audit_mode == "full_site":
        _render_site_crawl_summary(data)

    # ── Fix Roadmap + Key Insights ────────────────────────────────────────────
    roadmap_tab, insights_tab, summary_tab = st.tabs(["📋 Fix Roadmap", "💡 Key Insights", "📊 Audit Summary"])
    with roadmap_tab:
        render_fix_roadmap(data)
    with insights_tab:
        for ins in data.get("insights",[]):
            effort = ins.get("effort", "medium")
            st.markdown(f"""
            <div class="ins-card">
              <span style="font-size:14px;margin-top:2px;">{ins['icon']}</span>
              <div>
                <div class="ins-title">{ins['title']} <span class="{EFFORT_CLS.get(effort,'effort-m')}">{EFFORT_LBL.get(effort,'')}</span></div>
                <div class="ins-found">{ins['found']}</div>
                <div class="ins-impact">{ins['impact']}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    with summary_tab:
        geo_checks_all = _all_geo_checks(geo) if geo else []
        seo_checks_all = seo_mod.get("checks",[]) if seo_mod else []
        new_checks_all = []
        for rkey, mkey, _, _ in NEW_MODULES:
            mod = (data.get(rkey) or {}).get(mkey, {})
            new_checks_all.extend(mod.get("checks", []) if mod else [])
        all_checks = new_checks_all + geo_checks_all + seo_checks_all
        total = len(all_checks)
        fails  = sum(1 for c in all_checks if c["status"]=="fail")
        warns  = sum(1 for c in all_checks if c["status"]=="warn")
        passes = sum(1 for c in all_checks if c["status"]=="pass")
        for label, val, col in [
            ("Total checks run", total, "#0d0d0d"),
            ("❌ Failed", fails, "#c84b2f"),
            ("⚠️ Warnings", warns, "#c8962f"),
            ("✅ Passed", passes, "#2a8a5e"),
        ]:
            st.markdown(f'<div class="stat-box"><span style="font-size:.83rem;color:#4a4540;">{label}</span><span class="stat-val" style="color:{col};">{val}</span></div>', unsafe_allow_html=True)
        # Show audit mode info
        ft = data.get("fetch_time_ms", 0)
        mode_label = "Full-site" if audit_mode == "full_site" else "Single-page"
        st.markdown(f'<div style="text-align:center;font-size:11px;color:#9a9285;margin-top:8px;">{mode_label} audit · Fetched in {ft}ms</div>', unsafe_allow_html=True)

    # ── Critical New Modules (Technical + Schema + Entity + Content + External Authority + AI Visibility) ──
    st.markdown('<div class="sec-label">Technical AI Crawlability &amp; Schema — Critical</div>', unsafe_allow_html=True)
    for rkey, mkey, label, is_crit in NEW_MODULES[:3]:  # crawlability, schema, entity
        render_new_module(rkey, mkey, label, is_crit, data)

    # ── External Authority & AI Visibility ─────────────────────────────────────
    ext_auth = data.get("external_authority_report")
    ai_vis = data.get("ai_visibility_report")
    if ext_auth or ai_vis:
        st.markdown('<div class="sec-label">External Authority &amp; AI Visibility</div>', unsafe_allow_html=True)
        if ext_auth:
            render_new_module("external_authority_report", "external_authority", "🌐 External Authority", True, data)
        if ai_vis:
            render_new_module("ai_visibility_report", "ai_visibility", "🤖 AI Visibility", True, data)

    # ── External Profile Validation Details ────────────────────────────────────
    _render_external_profiles(data)

    # ── Live AI Test Results (ChatGPT) ────────────────────────────────────────
    _render_ai_test_results(data)

    # ── Content Quality & Off-Page ────────────────────────────────────────────
    st.markdown('<div class="sec-label">Content Quality &amp; Off-Page Authority</div>', unsafe_allow_html=True)
    for rkey, mkey, label, is_crit in NEW_MODULES[3:5]:  # content quality, off-page
        render_new_module(rkey, mkey, label, is_crit, data)

    # ── GEO Readiness — 6 modules ─────────────────────────────────────────────
    st.markdown('<div class="sec-label">GEO Readiness — Detailed Report</div>', unsafe_allow_html=True)
    if geo:
        render_geo_modules(geo)

        # GEO Opportunity Score
        st.markdown('<div class="sec-label">GEO Opportunity Score</div>', unsafe_allow_html=True)
        render_geo_opportunity(geo.get("geo_opportunity",{}))
    else:
        st.info("GEO report not available for this audit. Re-run the audit to generate GEO scores.")

    # ── Traditional SEO Signals (collapsed by default) ────────────────────────
    st.markdown('<div class="sec-label">Traditional SEO Signals</div>', unsafe_allow_html=True)
    if seo_mod:
        seo_checks = seo_mod.get("checks", [])
        seo_fails  = sum(1 for c in seo_checks if c["status"]=="fail")
        seo_warns  = sum(1 for c in seo_checks if c["status"]=="warn")
        seo_passes = sum(1 for c in seo_checks if c["status"]=="pass")
        sorted_seo = sorted(seo_checks, key=lambda c:(0 if c["status"]=="fail" else 1 if c["status"]=="warn" else 2))
        with st.expander(f"📊 SEO Score: {seo_mod['score']}/100  ·  ❌ {seo_fails} failed  ·  ⚠️ {seo_warns} warnings  ·  ✅ {seo_passes} passed", expanded=False):
            tab_all, tab_fail, tab_warn, tab_pass = st.tabs(["All", "Failed", "Warnings", "Passed"])
            with tab_all:  render_check_cards(sorted_seo)
            with tab_fail: render_check_cards([c for c in sorted_seo if c["status"]=="fail"])
            with tab_warn: render_check_cards([c for c in sorted_seo if c["status"]=="warn"])
            with tab_pass: render_check_cards([c for c in sorted_seo if c["status"]=="pass"])

    # ── CTA + Downloads ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="cta-block">
      <div class="cta-eye">Want expert help?</div>
      <div class="cta-h">Get your complete GEO Readiness report</div>
      <div class="cta-s">This free audit highlights the gaps. Our full service includes AI content restructuring, entity clarity optimisation, trust signal building, and a GEO implementation plan tailored to your site.</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("📋  Get Full GEO Report", type="primary", use_container_width=True, key=f"cta1_{url[:15]}")
    with c2: st.button("📩  Request Detailed Audit", type="secondary", use_container_width=True, key=f"cta2_{url[:15]}")
    with c3:
        st.download_button("⬇️  Download JSON",
            data=json.dumps(data, indent=2, ensure_ascii=False),
            file_name=f"geo_audit_{domain}.json", mime="application/json",
            use_container_width=True, key=f"dl_{url[:15]}")
    with c4:
        pdf_bytes = generate_pdf(data)
        if pdf_bytes:
            st.download_button("📄  Download PDF",
                data=pdf_bytes, file_name=f"geo_audit_{domain}.pdf",
                mime="application/pdf", use_container_width=True, key=f"pdf_{url[:15]}")
        else:
            st.caption("Install fpdf2 for PDF export")

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("report",None),("show_results",False),("view_saved",None), ("user", None), ("view_admin", False)]:
    if k not in st.session_state: st.session_state[k] = v

# ── AUTHENTICATION ────────────────────────────────────────────────────────────
if not st.session_state.user:
    st.markdown('<div class="hero-badge">Welcome to AI SEO Audit</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Please <em>Login</em> or <em>Register</em></h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])
    
    with tab1:
        st.subheader("Login")
        l_email = st.text_input("Email", key="l_email")
        l_pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login", type="primary"):
            user = get_user_by_email(l_email)
            if user and verify_password(l_pwd, user["password_hash"]):
                st.session_state.user = user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid email or password.")
                
    with tab2:
        st.subheader("Register")
        r_email = st.text_input("Email", key="r_email")
        r_pwd = st.text_input("Password", type="password", key="r_pwd")
        r_pwd2 = st.text_input("Confirm Password", type="password", key="r_pwd2")
        if st.button("Register", type="primary"):
            if r_pwd != r_pwd2:
                st.error("Passwords do not match.")
            elif not validators.email(r_email):
                st.error("Invalid email address.")
            elif len(r_pwd) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                uid = create_user(r_email, hash_password(r_pwd))
                if uid:
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Email already exists.")
                    
    with tab3:
        st.subheader("Forgot Password")
        f_email = st.text_input("Email", key="f_email")
        if st.button("Reset Password"):
            user = get_user_by_email(f_email)
            if user:
                temp_pwd = generate_temp_password()
                update_user_password(f_email, hash_password(temp_pwd))
                if send_forgot_password_email(f_email, temp_pwd):
                    st.success("A temporary password has been sent to your email. (Check console if SMTP not configured)")
                else:
                    st.error("Failed to send email.")
            else:
                st.error("Email not found.")
    st.stop()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    u = st.session_state.user
    st.markdown(f"### 👤 {u['email']}")
    st.markdown(f"**Role:** {u['role'].capitalize()}")
    
    with st.expander("⚙️ Profile / Settings"):
        npwd = st.text_input("New Password", type="password", key="p_new")
        if st.button("Update Password"):
            if len(npwd) >= 6:
                update_user_password(u['email'], hash_password(npwd))
                st.success("Password updated!")
            else:
                st.error("Password too short.")
        st.divider()
        st.markdown("**🤖 AI Visibility Testing**")
        st.markdown('<span style="font-size:0.78rem;color:#6b6660;">Enter your OpenAI API key to enable live AI visibility testing. Tests if ChatGPT recognises your brand and recommends it for your keywords.</span>', unsafe_allow_html=True)
        openai_key = st.text_input("OpenAI API Key", type="password", key="openai_key",
                                    placeholder="sk-...")
        if openai_key:
            st.session_state.openai_api_key = openai_key
            st.success("✅ API key saved for this session")
        elif st.session_state.get('openai_api_key'):
            st.info("API key loaded from session")
        elif os.environ.get('OPENAI_API_KEY'):
            st.info("API key loaded from environment (.env)")
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.openai_api_key = None
            st.rerun()
            
    st.divider()
    
    if u['role'] == 'admin':
        if st.button("👑 Admin Dashboard", use_container_width=True):
            st.session_state.view_admin = True
            st.session_state.show_results = False
            st.session_state.view_saved = None
            st.session_state.report = None
            st.rerun()
        if st.session_state.get('view_admin'):
            if st.button("← Back to Audits", use_container_width=True):
                st.session_state.view_admin = False
                st.rerun()
        st.divider()

    filter_email = None if u['role'] == 'admin' else u['email']

    st.markdown("### 🗄️ Audit History")
    stats = get_stats(email=filter_email)
    if stats:
        c1,c2 = st.columns(2)
        c1.metric("Audits",  stats.get("total_audits",0))
        c2.metric("Leads",   stats.get("unique_leads",0))
        c1.metric("Domains", stats.get("unique_domains",0))
        c2.metric("Avg",     stats.get("avg_overall","—"))
    st.divider()
    rows = get_recent_audits(limit=60, email=filter_email)
    if rows:
        for r in rows:
            s = r.get("overall_score") or 0
            em = "🟢" if s>70 else ("🟡" if s>40 else "🔴")
            label = f"{em} {r['domain'] or r['url'][:28]}  ·  {s}"
            tip = f"{r['created_at'][:16]}  ·  {r['email']}  ·  kw: {r.get('keyword','—')}"
            if st.button(label, key=f"v_{r['id']}", help=tip, use_container_width=True):
                st.session_state.view_saved = r["id"]
                st.session_state.show_results = False
                st.session_state.report = None
                st.rerun()
        st.divider()
        csv_data = export_csv()
        if csv_data:
            st.download_button("⬇️ Export CSV", data=csv_data,
                file_name="seo_audit_leads.csv", mime="text/csv", use_container_width=True)
    else:
        st.info("No audits yet.")
    if st.session_state.view_saved or st.session_state.show_results:
        st.divider()
        if st.button("← New audit", use_container_width=True):
            st.session_state.show_results=False; st.session_state.report=None; st.session_state.view_saved=None; st.rerun()

# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────
if st.session_state.get('view_admin') and st.session_state.user['role'] == 'admin':
    st.markdown('<div class="hero-badge">Admin Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Manage <em>Users</em></h1>', unsafe_allow_html=True)
    
    users = get_all_users()
    if users:
        for user in users:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{user['email']}**")
            col2.write(f"Joined: {user['created_at'][:10]}")
            
            new_role = col3.selectbox("Role", ["user", "admin"], index=0 if user['role']=='user' else 1, key=f"role_{user['email']}")
            if new_role != user['role']:
                update_user_role(user['email'], new_role)
                st.rerun()
                
            if user['email'] != st.session_state.user['email']:
                if col4.button("Delete", key=f"del_{user['email']}"):
                    delete_user(user['email'])
                    st.rerun()
            st.markdown("---")
    st.stop()

# ── SAVED AUDIT VIEW ──────────────────────────────────────────────────────────
if st.session_state.view_saved:
    data = get_audit_by_id(st.session_state.view_saved)
    if data:
        d = urlparse(data.get("url","")).netloc.replace("www.","")
        st.markdown(f'<div class="hero-badge">Saved Audit — {d}</div>', unsafe_allow_html=True)
        render_full_report(data)
    else:
        st.error("Could not load this audit.")
    st.stop()

# ── HERO + FORM ───────────────────────────────────────────────────────────────
if not st.session_state.show_results and not st.session_state.get('view_admin'):
    st.markdown('<div class="hero-badge">Free GEO Readiness Audit</div>', unsafe_allow_html=True)
    st.markdown("""
    <h1 class="hero-title">Is your website <em>AI citation ready?</em></h1>
    <p class="hero-sub">Enter your URL for a full GEO audit — AI Citation Readiness, Brand Entity Clarity, Extractability, Trust Signals, AI Overview Readiness, and Information Gain scores with actionable fix instructions.</p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    col_u, col_e = st.columns(2)
    with col_u: url_input = st.text_input("Website URL", placeholder="https://yourwebsite.com")
    with col_e: email_input = st.text_input("Your Email *(required)*", value=st.session_state.user['email'], placeholder="you@company.com")
    kw_input = st.text_input("Target Keyword *(recommended — e.g. 'best python seo tools')*",
                              placeholder="Enter your primary target keyword for deeper analysis")
    opt_c1, opt_c2 = st.columns(2)
    with opt_c1:
        full_site = st.checkbox("🌐 Full Site Audit *(crawls key pages + validates external profiles)*", value=True)
    with opt_c2:
        check_broken = st.checkbox("🔗 Check for broken links *(adds ~10s)*", value=False)

    # AI testing option
    has_api_key = bool(st.session_state.get('openai_api_key') or os.environ.get('OPENAI_API_KEY'))
    ai_test_enabled = st.checkbox(
        "🤖 Live AI Visibility Test *(queries ChatGPT to check brand recognition)*",
        value=has_api_key,
        disabled=not has_api_key,
        help="Requires OpenAI API key. Add it in Settings (sidebar)." if not has_api_key else "Will query ChatGPT 3 times (~$0.01 cost)"
    )
    if not has_api_key and ai_test_enabled:
        ai_test_enabled = False
    if not has_api_key:
        st.markdown('<span style="font-size:0.78rem;color:#c8962f;">💡 Add your OpenAI API key in ⚙️ Settings (sidebar) to enable live AI visibility testing</span>', unsafe_allow_html=True)

    if full_site:
        st.markdown('<div style="background:#f0f7ff;border:1px solid #b0d0f0;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:0.82rem;color:#3a5a80;">'
                    '🌐 <strong>Full Site Audit</strong> will crawl ~10 key pages (About, Contact, Services, Blog, Case Studies…), '
                    'validate external profiles (Trustpilot, G2, LinkedIn, Wikipedia…), and generate a combined score across the entire site. '
                    'Takes ~20-40 seconds.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3,1])
    with c1: run_btn = st.button("🔍  Run GEO Audit", type="primary", use_container_width=True)
    with c2: st.markdown('<p style="font-size:11px;color:#9a9285;padding-top:10px;">No spam ever.</p>', unsafe_allow_html=True)

    if run_btn:
        errs = validate(url_input, email_input)
        if errs:
            for _,m in errs.items(): st.error(m)
        else:
            norm_url = url_input if url_input.startswith("http") else "https://"+url_input
            prog = st.progress(0); txt = st.empty()
            
            def update_progress(pct, msg):
                txt.markdown(f"**{msg}**")
                prog.progress(pct)
                
            api_key = (st.session_state.get('openai_api_key') or os.environ.get('OPENAI_API_KEY', '')) if ai_test_enabled else ''
            
            report = run_audit(
                norm_url, email_input, kw_input.strip(),
                check_broken_links=check_broken, full_site=full_site,
                openai_api_key=api_key,
                progress_callback=update_progress
            )
            save_audit(report)
            prog.progress(100); txt.markdown("**Done! Loading your report…**")
            time.sleep(0.3); prog.empty(); txt.empty()
            st.session_state.report = report
            st.session_state.show_results = True
            st.rerun()

# ── LIVE RESULTS ──────────────────────────────────────────────────────────────
if st.session_state.show_results and st.session_state.report:
    report = st.session_state.report
    domain = urlparse(report.url).netloc.replace("www.","")
    if report.error:
        st.error(f"**Could not audit:** {report.error}")
        if st.button("← Try again"): st.session_state.show_results=False; st.session_state.report=None; st.rerun()
        st.stop()
    st.markdown(f'<div class="hero-badge">GEO Audit Complete — {domain}</div>', unsafe_allow_html=True)
    render_full_report(_report_to_dict(report))
    st.markdown(f'<div style="text-align:center;margin-top:1.5rem;font-size:11px;color:#9a9285;">Audited <strong>{domain}</strong> · GEO scoring is heuristic-based · Results for guidance only</div>', unsafe_allow_html=True)