"""
app.py — AI SEO Audit Tool
Run with:  streamlit run app.py
"""

import os
import time
import validators
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core import run_audit
from utils import save_audit
from utils.storage import get_recent_audits, get_stats, export_csv

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI SEO Audit",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.main .block-container { max-width: 780px; padding: 2rem 1.5rem 4rem; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero-badge {
    display: inline-block;
    font-family: 'Syne', sans-serif;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: #c84b2f; border: 1.5px solid #c84b2f;
    padding: 4px 12px; border-radius: 2px;
    margin-bottom: 16px;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem; font-weight: 800;
    line-height: 1.08; letter-spacing: -0.02em;
    color: #0d0d0d; margin-bottom: 12px;
}
.hero-title em { font-style: italic; color: #c84b2f; }
.hero-sub {
    font-size: 1rem; color: #6b6660; line-height: 1.65;
    max-width: 500px; margin-bottom: 0;
}

/* ── Form card ── */
.form-card {
    background: #ffffff;
    border: 1.5px solid rgba(13,13,13,0.1);
    border-radius: 10px;
    padding: 2rem 2rem 1.5rem;
    margin: 1.5rem 0;
}

/* ── Metric score card ── */
.overall-score-card {
    background: #0d0d0d; color: #fff;
    border-radius: 10px; padding: 1.8rem 2rem;
    display: flex; align-items: center; gap: 1.5rem;
    margin-bottom: 1.5rem;
}
.big-score {
    font-family: 'Syne', sans-serif;
    font-size: 4.5rem; font-weight: 800; line-height: 1;
}
.score-meta { display: flex; flex-direction: column; gap: 4px; }
.score-eyebrow { font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; opacity: 0.5; }
.score-grade-red   { font-family:'Syne',sans-serif; font-size:1.3rem; font-weight:700; color:#e07060; }
.score-grade-amber { font-family:'Syne',sans-serif; font-size:1.3rem; font-weight:700; color:#e0b860; }
.score-grade-green { font-family:'Syne',sans-serif; font-size:1.3rem; font-weight:700; color:#60c890; }
.score-domain { font-size:0.85rem; opacity:0.55; margin-top:4px; }

/* ── Module score blocks ── */
.module-card {
    background: #fff;
    border: 1.5px solid rgba(13,13,13,0.1);
    border-radius: 8px; padding: 1.2rem 1.4rem;
    margin-bottom: 0;
    position: relative; overflow: hidden;
}
.module-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent);
}
.module-label {
    font-family: 'Syne', sans-serif;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #9a9285; margin-bottom: 6px;
}
.module-score {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem; font-weight: 800; line-height: 1; color: #0d0d0d;
}
.module-tag {
    font-size: 11px; font-weight: 500;
    padding: 2px 8px; border-radius: 3px;
    display: inline-block; margin-top: 6px;
}
.tag-red    { background: #fde8e5; color: #c84b2f; }
.tag-amber  { background: #fdf3e0; color: #b07010; }
.tag-green  { background: #e4f5ec; color: #1a7a45; }

/* ── Section header ── */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: #9a9285;
    border-bottom: 1px solid rgba(13,13,13,0.1);
    padding-bottom: 8px; margin: 1.8rem 0 1rem;
}

/* ── Insight cards ── */
.insight-card {
    background: #fff;
    border: 1.5px solid rgba(13,13,13,0.1);
    border-radius: 8px; padding: 1rem 1.2rem;
    display: flex; gap: 12px; align-items: flex-start;
    margin-bottom: 10px;
}
.insight-icon { font-size: 14px; margin-top: 2px; flex-shrink: 0; }
.insight-body {}
.insight-title { font-weight: 500; font-size: 0.9rem; color: #0d0d0d; margin-bottom: 2px; }
.insight-text  { font-size: 0.85rem; color: #5a5550; line-height: 1.55; }

/* ── Check detail rows ── */
.check-row {
    padding: 10px 0; border-bottom: 1px solid rgba(13,13,13,0.07);
    display: flex; align-items: flex-start; gap: 12px;
}
.check-icon { width: 20px; text-align: center; flex-shrink: 0; }
.check-body { flex: 1; }
.check-name  { font-size: 0.85rem; font-weight: 500; color: #0d0d0d; }
.check-find  { font-size: 0.8rem; color: #6b6660; line-height: 1.5; margin-top: 2px; }
.check-score { font-family:'Syne',sans-serif; font-size:0.8rem; font-weight:700; color:#9a9285; flex-shrink:0; }

/* ── CTA ── */
.cta-block {
    background: #0d0d0d; border-radius: 10px;
    padding: 2.5rem 2rem; text-align: center;
    margin-top: 2rem; color: #fff;
}
.cta-eyebrow { font-size:10px; letter-spacing:0.18em; text-transform:uppercase; opacity:0.45; margin-bottom:10px; font-family:'Syne',sans-serif; }
.cta-title { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; margin-bottom:8px; }
.cta-sub { font-size:0.9rem; opacity:0.6; line-height:1.65; max-width:420px; margin:0 auto 1.8rem; }

/* ── Buttons ── */
div.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
}
div.stButton > button[kind="primary"] {
    background: #0d0d0d !important;
    color: #fff !important;
    border: none !important;
    padding: 0.7rem 1.5rem !important;
}
div.stButton > button[kind="primary"]:hover { background: #c84b2f !important; }

div.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #0d0d0d !important;
    border: 1.5px solid rgba(13,13,13,0.3) !important;
}

/* Progress bar colour */
.stProgress > div > div > div { background-color: #c84b2f !important; }

/* Input fields */
.stTextInput > div > div > input {
    border-radius: 4px !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def grade_color(score: int) -> str:
    if score <= 40: return "red"
    if score <= 70: return "amber"
    return "green"

def tag_html(score: int) -> str:
    label = "Poor" if score <= 40 else ("Average" if score <= 70 else "Strong")
    cls   = "tag-red" if score <= 40 else ("tag-amber" if score <= 70 else "tag-green")
    return f'<span class="module-tag {cls}">{label}</span>'

MODULE_COLORS = {
    "SEO Foundation":   "#2f6bc8",
    "Content Quality":  "#2a8a5e",
    "AI Visibility":    "#c84b2f",
    "Opportunity Score":"#c8962f",
}

CHECK_ICONS = {"pass": "✅", "warn": "⚠️", "fail": "❌"}


def validate_inputs(url: str, email: str):
    errors = {}
    if not url.strip():
        errors["url"] = "Please enter a website URL."
    else:
        test = url if url.startswith("http") else "https://" + url
        if not validators.url(test):
            errors["url"] = "Please enter a valid URL, e.g. https://yoursite.com"
    if not email.strip():
        errors["email"] = "Email is required — we'll send your full report here."
    elif not validators.email(email):
        errors["email"] = "Please enter a valid email address."
    return errors


# ── Session state ─────────────────────────────────────────────────────────────
if "report" not in st.session_state:
    st.session_state.report = None
if "show_results" not in st.session_state:
    st.session_state.show_results = False


# ── ADMIN SIDEBAR ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ Leads & Audit Data")
    st.caption("Internal view — not visible to users")
    st.divider()

    stats = get_stats()
    if stats:
        c1, c2 = st.columns(2)
        c1.metric("Total Audits",   stats.get("total_audits", 0))
        c2.metric("Unique Leads",   stats.get("unique_leads", 0))
        c1.metric("Unique Domains", stats.get("unique_domains", 0))
        c2.metric("Avg Score",      stats.get("avg_overall", "—"))
        st.divider()

    show_leads = st.toggle("Show recent leads", value=False)
    if show_leads:
        rows = get_recent_audits(limit=50)
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)
            display_cols = ["created_at", "email", "domain", "overall_score",
                            "seo_score", "content_score", "ai_score", "overall_grade"]
            df = df[[c for c in display_cols if c in df.columns]]
            df.columns = [c.replace("_", " ").title() for c in df.columns]
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv_data = export_csv()
            if csv_data:
                st.download_button(
                    label="⬇️ Export CSV",
                    data=csv_data,
                    file_name="seo_audit_leads.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.info("No audits recorded yet.")

    st.divider()
    st.caption(f"DB: `seo_audits.db`")


# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-badge">Free AI SEO Audit</div>', unsafe_allow_html=True)
st.markdown("""
<h1 class="hero-title">How visible are you<br>to <em>AI search?</em></h1>
<p class="hero-sub">Enter your URL and get an instant breakdown of your SEO health and AI visibility score — no login needed.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ── FORM ──────────────────────────────────────────────────────────────────────
if not st.session_state.show_results:
    with st.container():
        url_input   = st.text_input("Website URL", placeholder="https://yourwebsite.com", key="url_field")
        email_input = st.text_input("Your Email *(required — we'll send your full report)*",
                                    placeholder="you@company.com", key="email_field")

        col1, col2 = st.columns([3, 1])
        with col1:
            run_btn = st.button("🔍  Run AI SEO Audit", type="primary", use_container_width=True)
        with col2:
            st.markdown('<p style="font-size:11px;color:#9a9285;margin-top:10px;">No spam. Unsubscribe anytime.</p>',
                        unsafe_allow_html=True)

    if run_btn:
        errors = validate_inputs(url_input, email_input)
        if errors:
            for field, msg in errors.items():
                st.error(msg)
        else:
            # ── Loading state ────────────────────────────────────────────────
            norm_url = url_input if url_input.startswith("http") else "https://" + url_input
            progress_bar = st.progress(0)
            status_text  = st.empty()

            steps = [
                (15,  "Fetching page content…"),
                (35,  "Analysing SEO foundation…"),
                (55,  "Checking content quality…"),
                (75,  "Evaluating AI visibility signals…"),
                (90,  "Calculating opportunity gaps…"),
                (100, "Generating insights…"),
            ]

            for pct, msg in steps[:-1]:
                status_text.markdown(f"**{msg}**")
                progress_bar.progress(pct)
                time.sleep(0.4)

            report = run_audit(norm_url, email_input)
            save_audit(report)

            progress_bar.progress(100)
            status_text.markdown("**Done! Loading your results…**")
            time.sleep(0.4)
            progress_bar.empty()
            status_text.empty()

            st.session_state.report = report
            st.session_state.show_results = True
            st.rerun()


# ── RESULTS ───────────────────────────────────────────────────────────────────
if st.session_state.show_results and st.session_state.report:
    report = st.session_state.report
    from urllib.parse import urlparse
    domain = urlparse(report.url).netloc.replace("www.", "")

    if report.error:
        st.error(f"**Could not audit this URL:** {report.error}")
        st.markdown("Please check the URL is publicly accessible and try again.")
        if st.button("← Try again"):
            st.session_state.show_results = False
            st.session_state.report = None
            st.rerun()
        st.stop()

    # ── Overall score ────────────────────────────────────────────────────────
    color = grade_color(report.overall_score)
    grade_cls = f"score-grade-{color}"
    st.markdown(f"""
    <div class="overall-score-card">
        <div class="big-score">{report.overall_score}</div>
        <div class="score-meta">
            <span class="score-eyebrow">Overall SEO + AI Score</span>
            <span class="{grade_cls}">{report.overall_grade}</span>
            <span class="score-domain">{domain}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 4 module score blocks ────────────────────────────────────────────────
    st.markdown('<div class="section-header">Score Breakdown</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, module in enumerate(report.modules):
        c = MODULE_COLORS.get(module.module, "#888")
        with cols[i]:
            st.markdown(f"""
            <div class="module-card" style="--accent:{c}">
                <div class="module-label">{module.module}</div>
                <div class="module-score">{module.score}</div>
                <div style="height:3px;background:#e8e3d9;border-radius:2px;margin:8px 0;">
                    <div style="height:3px;background:{c};width:{module.score}%;border-radius:2px;"></div>
                </div>
                {tag_html(module.score)}
            </div>
            """, unsafe_allow_html=True)

    # ── Key insights ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Key Insights</div>', unsafe_allow_html=True)
    for ins in report.insights:
        st.markdown(f"""
        <div class="insight-card">
            <span class="insight-icon">{ins['icon']}</span>
            <div class="insight-body">
                <div class="insight-title">{ins['title']}</div>
                <div class="insight-text">{ins['finding']}<br><em>{ins['impact']}</em></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Detailed check breakdown (expandable) ─────────────────────────────────
    st.markdown('<div class="section-header">Detailed Checks</div>', unsafe_allow_html=True)

    module_colors = {
        "SEO Foundation":   "#2f6bc8",
        "Content Quality":  "#2a8a5e",
        "AI Visibility":    "#c84b2f",
        "Opportunity Score":"#c8962f",
    }

    for module in report.modules:
        c = module_colors.get(module.module, "#888")
        with st.expander(f"{module.module}  —  {module.score}/100", expanded=False):
            for chk in module.checks:
                icon = CHECK_ICONS.get(chk.status, "•")
                st.markdown(f"""
                <div class="check-row">
                    <span class="check-icon">{icon}</span>
                    <div class="check-body">
                        <div class="check-name">{chk.name}</div>
                        <div class="check-find">{chk.finding}</div>
                        <div class="check-find" style="color:#9a9285;margin-top:3px;">{chk.impact}</div>
                    </div>
                    <span class="check-score">{chk.score}/{chk.max_score}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Top recommendations (from Opportunity module) ─────────────────────────
    opp_module = next((m for m in report.modules if m.module == "Opportunity Score"), None)
    if opp_module and hasattr(opp_module, "top_recommendations") and opp_module.top_recommendations:
        st.markdown('<div class="section-header">Priority Fixes</div>', unsafe_allow_html=True)
        for i, rec in enumerate(opp_module.top_recommendations, 1):
            icon = CHECK_ICONS.get(rec["status"], "•")
            st.markdown(f"""
            <div class="insight-card">
                <span class="insight-icon">{icon}</span>
                <div class="insight-body">
                    <div class="insight-title">{i}. {rec['name']}</div>
                    <div class="insight-text">{rec['finding']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── CTA ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="cta-block">
        <div class="cta-eyebrow">Want the full picture?</div>
        <div class="cta-title">Get your complete AI SEO report</div>
        <div class="cta-sub">
            Your score shows the surface. The full audit covers 40+ checks, keyword gaps,
            competitor comparison, and a step-by-step fix plan tailored to your site.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        st.button("📋  Get Full AI SEO Report", type="primary", use_container_width=True)
    with col_b:
        st.button("📩  Request Detailed Audit", type="secondary", use_container_width=True)
    with col_c:
        if st.button("← Audit another URL", type="secondary", use_container_width=True):
            st.session_state.show_results = False
            st.session_state.report = None
            st.rerun()

    # ── Footer meta ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;margin-top:2rem;font-size:11px;color:#9a9285;">
        Audited <strong>{domain}</strong> in {report.fetch_time_ms}ms
        · Scoring is heuristic-based · Results are for guidance only
    </div>
    """, unsafe_allow_html=True)
