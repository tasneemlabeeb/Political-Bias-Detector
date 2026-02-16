import html
import os
import sys
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

# Ensure project root is on the path so `src.*` imports resolve.
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.backend.bias_classifier import PoliticalBiasClassifier
from src.backend.news_crawler import NewsCrawler
from src.backend.source_manager import SourceManager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(_project_root, "news_sources.db")

BIAS_ORDER = ["Left-Leaning", "Center-Left", "Centrist", "Center-Right", "Right-Leaning"]

BIAS_COLORS = {
    "Left-Leaning": "#1565C0",
    "Center-Left": "#42A5F5",
    "Centrist": "#78909C",
    "Center-Right": "#EF5350",
    "Right-Leaning": "#C62828",
}

BIAS_EMOJI = {
    "Left-Leaning": "&#9664;&#9664;",
    "Center-Left": "&#9664;",
    "Centrist": "&#9679;",
    "Center-Right": "&#9654;",
    "Right-Leaning": "&#9654;&#9654;",
}

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


@st.cache_resource
def get_source_manager() -> SourceManager:
    return SourceManager(db_path=DB_PATH)


@st.cache_resource
def get_news_crawler() -> NewsCrawler:
    return NewsCrawler(get_source_manager())


# ---------------------------------------------------------------------------
# Page config & global CSS
# ---------------------------------------------------------------------------

st.set_page_config(page_title="News Reader", page_icon="📖", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Sora:wght@500;600;700&display=swap');

    :root {
        --bg-canvas: #f8f4ed;
        --surface: #fffdfb;
        --ink: #0f1419;
        --muted: #5a6570;
        --line: #ddd5c8;
        --line-strong: #c4b9a8;
        --accent: #0d9488;
        --accent-hover: #0f766e;
        --accent-soft: #ccfbf1;
        --accent-warm: #f59e0b;
        --sidebar-bg-top: #0a1929;
        --sidebar-bg-bottom: #1a2f42;
        --shadow-sm: 0 1px 3px rgba(15, 20, 25, 0.08), 0 1px 2px rgba(15, 20, 25, 0.04);
        --shadow-md: 0 10px 30px rgba(15, 20, 25, 0.1), 0 4px 12px rgba(15, 20, 25, 0.06);
        --shadow-lg: 0 20px 40px rgba(15, 20, 25, 0.12), 0 8px 16px rgba(15, 20, 25, 0.08);
    }

    html, body, .stApp {
        font-family: 'IBM Plex Sans', 'Helvetica Neue', sans-serif;
        color: var(--ink);
        background: var(--bg-canvas);
    }
    .stApp {
        background:
            radial-gradient(1100px 560px at -18% -14%, rgba(13, 148, 136, 0.16), transparent 60%),
            radial-gradient(900px 440px at 114% 12%, rgba(245, 158, 11, 0.16), transparent 58%),
            linear-gradient(180deg, #faf7f0 0%, #f8f4ed 66%, #f5f1e9 100%);
        background-attachment: fixed;
    }
    [data-testid="stAppViewContainer"] {
        overflow-x: hidden;
    }
    .block-container {
        max-width: 1400px;
        padding-top: 1.7rem;
        padding-bottom: 3rem;
    }

    /* ---------- Hide Sidebar ---------- */
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* ---------- Expander Styling ---------- */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        border-radius: 10px;
        font-weight: 600;
        color: var(--ink);
    }
    .streamlit-expanderHeader:hover {
        border-color: var(--line-strong);
        box-shadow: var(--shadow-sm);
    }
    div[data-testid="stExpander"] {
        background: transparent;
        border: none;
    }
    
    /* ---------- Button Enhancements ---------- */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(160deg, var(--accent) 0%, var(--accent-hover) 100%) !important;
        box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(13, 148, 136, 0.35) !important;
    }

    /* ---------- Header ---------- */
    .app-header {
        padding: 0.2rem 0 1.4rem 0;
        border-bottom: 2px solid var(--line);
        margin-bottom: 1.4rem;
        animation: fade-in 0.45s ease both;
        position: relative;
    }
    .app-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 120px;
        height: 2px;
        background: linear-gradient(90deg, var(--accent), var(--accent-warm));
    }
    .app-kicker {
        margin: 0 0 0.6rem 0;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        background: linear-gradient(135deg, var(--accent), var(--accent-warm));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .app-title {
        margin: 0;
        font-family: 'Sora', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: var(--ink);
        line-height: 1.05;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .app-subtitle {
        margin: 0.4rem 0 0 0;
        max-width: 840px;
        color: var(--muted);
        font-size: 0.96rem;
        line-height: 1.55;
    }

    /* ---------- Core cards ---------- */
    .metric-card,
    .spectrum-container,
    .chart-container,
    .article-card {
        background: var(--surface);
        border: 1px solid var(--line);
        box-shadow: var(--shadow-sm);
    }

    .metric-card {
        border-radius: 10px;
        padding: 20px 20px;
        text-align: center;
        animation: rise-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        box-shadow: var(--shadow-sm);
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent), var(--accent-warm));
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    .metric-card:hover::before {
        transform: scaleX(1);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: var(--line-strong);
        box-shadow: var(--shadow-lg);
    }
    .metric-value {
        font-family: 'Sora', sans-serif;
        font-size: 1.95rem;
        font-weight: 700;
        color: var(--ink);
        line-height: 1.08;
    }
    .metric-label {
        margin-top: 5px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
    }
    .metric-icon {
        font-size: 1.22rem;
        margin-bottom: 4px;
    }

    .section-header {
        margin: 1.85rem 0 0.85rem 0;
        padding-bottom: 7px;
        border-bottom: 1px solid var(--line);
        font-family: 'Sora', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        color: var(--ink);
    }

    .spectrum-container {
        border-radius: 10px;
        padding: 22px;
        animation: fade-in 0.4s ease both;
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.3s ease;
    }
    .spectrum-container:hover {
        box-shadow: var(--shadow-md);
    }
    .spectrum-bar {
        display: flex;
        width: 100%;
        height: 32px;
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid rgba(15, 20, 25, 0.12);
        background: #f5f1e9;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
    }
    .spectrum-segment {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 0;
        overflow: hidden;
        font-size: 0.7rem;
        font-weight: 700;
        color: #ffffff;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .spectrum-segment:hover {
        filter: saturate(1.2) brightness(1.05);
        transform: scaleY(1.05);
        z-index: 1;
    }
    .spectrum-legend {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 16px;
        margin-top: 12px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.76rem;
        color: var(--muted);
        font-weight: 500;
    }
    .legend-dot {
        width: 9px;
        height: 9px;
        border-radius: 2px;
    }

    .chart-container {
        border-radius: 10px;
        padding: 22px 22px 14px 22px;
        animation: fade-in 0.45s ease both;
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.3s ease;
    }
    .chart-container:hover {
        box-shadow: var(--shadow-md);
    }

    .article-card {
        border-radius: 8px;
        border-left: 4px solid var(--accent);
        padding: 16px 18px;
        margin-bottom: 14px;
        animation: rise-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
        word-wrap: break-word;
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        box-shadow: var(--shadow-sm);
        position: relative;
    }
    .article-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--accent), var(--accent-warm));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .article-card:hover::after {
        opacity: 1;
    }
    .article-card:hover {
        transform: translateY(-3px);
        border-color: var(--line-strong);
        box-shadow: var(--shadow-lg);
    }
    .article-title {
        display: block;
        font-family: 'Sora', sans-serif;
        font-size: 1.02rem;
        font-weight: 600;
        line-height: 1.4;
        color: var(--ink);
        text-decoration: none;
        transition: color 0.15s ease;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .article-title:hover {
        color: var(--accent);
    }
    .article-meta {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 9px;
    }
    .bias-badge,
    .source-badge,
    .ml-badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.67rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        border: 1px solid transparent;
    }
    .bias-badge {
        color: #f6f8fb;
    }
    .source-badge {
        color: #33414d;
        background: #ece6d9;
        border-color: #dfd6c8;
        font-weight: 500;
    }
    .ml-badge {
        color: #f6f8fb;
    }
    .badge-label {
        font-size: 0.62rem;
        color: var(--muted);
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .date-badge {
        color: #6f7c85;
        font-size: 0.72rem;
        letter-spacing: 0.03em;
    }
    .article-summary {
        margin-top: 9px;
        font-size: 0.88rem;
        color: #465462;
        line-height: 1.55;
        word-wrap: break-word;
        overflow-wrap: break-word;
        white-space: normal;
    }

    /* ---------- Empty/no-results ---------- */
    .empty-state {
        text-align: left;
        padding: 72px 8px 30px 8px;
    }
    .empty-icon {
        font-size: 2.6rem;
        margin-bottom: 8px;
    }
    .empty-title {
        font-family: 'Sora', sans-serif;
        font-size: 1.5rem;
        color: var(--ink);
        margin-bottom: 6px;
    }
    .empty-desc {
        max-width: 460px;
        color: var(--muted);
        font-size: 0.94rem;
        line-height: 1.55;
    }
    .no-results {
        text-align: left;
        border: 1px dashed var(--line-strong);
        border-radius: 4px;
        padding: 16px;
        color: var(--muted);
        background: rgba(255, 252, 245, 0.66);
    }

    /* ---------- AI diagnostics ---------- */
    .confidence-container {
        margin-top: 7px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .confidence-label {
        font-size: 0.66rem;
        font-weight: 600;
        color: var(--muted);
        white-space: nowrap;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .confidence-bar-bg {
        flex: 1;
        height: 5px;
        border-radius: 2px;
        background: #e6ded0;
        overflow: hidden;
    }
    .confidence-bar-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    .confidence-pct {
        min-width: 34px;
        text-align: right;
        font-size: 0.66rem;
        font-weight: 700;
    }
    .ai-details {
        margin-top: 8px;
        padding: 7px 9px;
        border: 1px solid #d8dfdf;
        border-radius: 4px;
        background: var(--accent-soft);
        color: #2f4d4a;
        font-size: 0.74rem;
        line-height: 1.45;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    /* ---------- Motion ---------- */
    @keyframes rise-in {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes fade-in {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }

    /* ---------- Responsive ---------- */
    @media (max-width: 980px) {
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.25rem;
        }
        .app-title {
            font-size: 1.85rem;
        }
        .app-subtitle {
            font-size: 0.9rem;
        }
        .metric-card {
            padding: 13px 12px;
        }
        .metric-value {
            font-size: 1.55rem;
        }
        .spectrum-container,
        .chart-container {
            padding: 14px;
        }
        .article-card {
            padding: 13px 13px;
        }
    }
    @media (max-width: 640px) {
        .app-title {
            font-size: 1.58rem;
        }
        .section-header {
            margin-top: 1.35rem;
        }
        .article-title {
            font-size: 0.95rem;
        }
        .article-summary {
            font-size: 0.84rem;
        }
    }

    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header & Controls
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="app-header">'
    '<p class="app-kicker">Cross-Source Intelligence</p>'
    '<p class="app-title">Political Bias News Reader</p>'
    '<p class="app-subtitle">'
    "Track narrative framing across outlets with ML ensemble predictions, lexical signals, "
    "and confidence diagnostics in one streamlined interface."
    "</p>"
    "</div>",
    unsafe_allow_html=True,
)

# Action buttons row
col1, col2, col3 = st.columns([2, 2, 4])
with col1:
    if st.button("📰 Fetch Latest News", type="primary", use_container_width=True):
        crawler = get_news_crawler()
        with st.spinner("Crawling sources..."):
            df = crawler.crawl_all_sources()
        st.session_state["articles"] = df
        st.session_state["fetch_done"] = True
        st.rerun()

articles: pd.DataFrame = st.session_state.get("articles", pd.DataFrame())

# ---------------------------------------------------------------------------
# AI Classification
# ---------------------------------------------------------------------------

if not articles.empty:
    with col2:
        if st.button("🤖 Classify with AI", type="primary", use_container_width=True):
            classifier = PoliticalBiasClassifier()
            progress_bar = st.progress(0, text="Loading models...")

            def _update_progress(frac: float) -> None:
                progress_bar.progress(min(frac, 1.0), text=f"Classifying... {frac:.0%}")

            result_df = classifier.classify_dataframe(articles, progress_callback=_update_progress)
            st.session_state["articles"] = result_df
            articles = result_df
            st.session_state["ml_done"] = True
            progress_bar.empty()
            st.rerun()

    ml_available = "ml_bias" in articles.columns and st.session_state.get("ml_done", False)

    # AI Settings in column 3
    with col3:
        if ml_available:
            sub1, sub2 = st.columns(2)
            with sub1:
                bias_source = st.selectbox(
                    "Bias Source",
                    options=["Source-assigned", "AI-detected"],
                    index=0,
                    label_visibility="collapsed",
                )
            with sub2:
                show_ai_reasoning = st.checkbox("Show AI reasoning", value=False, label_visibility="collapsed")
            active_bias_col = "ml_bias" if bias_source == "AI-detected" else "political_bias"
            min_ai_confidence_pct = 0
        else:
            active_bias_col = "political_bias"
            min_ai_confidence_pct = 0
            show_ai_reasoning = False
            st.caption("⬅️ Click 'Classify with AI' to enable ML features")
else:
    active_bias_col = "political_bias"
    ml_available = False
    min_ai_confidence_pct = 0
    show_ai_reasoning = False


st.markdown("")

if articles.empty:
    st.markdown(
        '<div class="empty-state">'
        '<div class="empty-icon">&#128225;</div>'
        '<div class="empty-title">No articles yet</div>'
        '<div class="empty-desc">'
        "Click <strong>Fetch Latest News</strong> above to crawl sources "
        "and start reading."
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.stop()

# Parse published dates once
if "published_dt" not in articles.columns:
    articles["published_dt"] = pd.to_datetime(articles["published"], errors="coerce")
    st.session_state["articles"] = articles
if "content" not in articles.columns:
    articles["content"] = ""
else:
    articles["content"] = articles["content"].fillna("")

# --- Filter controls ---
with st.expander("🔍 **Filters & Sorting**", expanded=False):
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    
    with fcol1:
        available_sources = sorted(articles["source_name"].unique())
        selected_sources = st.multiselect(
            "Source",
            options=available_sources,
            default=available_sources,
        )
    
    with fcol2:
        available_biases = [b for b in BIAS_ORDER if b in articles[active_bias_col].values]
        selected_biases = st.multiselect(
            "Political Bias",
            options=available_biases,
            default=available_biases,
        )
    
    with fcol3:
        default_start = date.today() - timedelta(days=7)
        date_start = st.date_input("From", value=default_start)
        
    with fcol4:
        default_end = date.today()
        date_end = st.date_input("To", value=default_end)
    
    scol1, scol2 = st.columns([3, 2])
    
    with scol1:
        keyword = st.text_input(
            "Keyword search",
            placeholder="Search title, summary, and full article text...",
        )
    
    with scol2:
        sort_options = [
            "Date (newest first)",
            "Date (oldest first)",
            "Source (A-Z)",
            "Bias (Left → Right)",
            "Bias (Right → Left)",
        ]
        if ml_available and "ml_confidence" in articles.columns:
            sort_options.append("AI confidence (high → low)")

        sort_option = st.selectbox("Sort by", sort_options)
    
    if ml_available and "ml_confidence" in articles.columns:
        min_ai_confidence_pct = st.slider(
            "Minimum AI confidence (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            help="Filter out lower-confidence AI classifications.",
        )
    else:
        min_ai_confidence_pct = 0

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

filtered = articles.copy()
filtered = filtered[filtered["source_name"].isin(selected_sources)]
filtered = filtered[filtered[active_bias_col].isin(selected_biases)]
has_date = filtered["published_dt"].notna()
in_range = (filtered["published_dt"].dt.date >= date_start) & (
    filtered["published_dt"].dt.date <= date_end
)
filtered = filtered[~has_date | in_range]
if keyword:
    kw_lower = keyword.lower()
    filtered = filtered[
        filtered["title"].str.lower().str.contains(kw_lower, na=False)
        | filtered["summary"].str.lower().str.contains(kw_lower, na=False)
        | filtered["content"].str.lower().str.contains(kw_lower, na=False)
    ]
if ml_available and min_ai_confidence_pct > 0 and "ml_confidence" in filtered.columns:
    filtered = filtered[filtered["ml_confidence"] * 100 >= min_ai_confidence_pct]

# Sort
bias_rank = {b: i for i, b in enumerate(BIAS_ORDER)}
if sort_option == "Date (newest first)":
    filtered = filtered.sort_values("published_dt", ascending=False, na_position="last")
elif sort_option == "Date (oldest first)":
    filtered = filtered.sort_values("published_dt", ascending=True, na_position="last")
elif sort_option == "Source (A-Z)":
    filtered = filtered.sort_values("source_name")
elif sort_option == "Bias (Left → Right)":
    filtered = filtered.assign(_br=filtered[active_bias_col].map(bias_rank))
    filtered = filtered.sort_values("_br").drop(columns=["_br"])
elif sort_option == "AI confidence (high → low)":
    filtered = filtered.sort_values("ml_confidence", ascending=False, na_position="last")
else:
    filtered = filtered.assign(_br=filtered[active_bias_col].map(bias_rank))
    filtered = filtered.sort_values("_br", ascending=False).drop(columns=["_br"])

st.markdown("")

# ---------------------------------------------------------------------------
# Metric cards
# ---------------------------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)
if ml_available and "ml_confidence" in articles.columns and not articles.empty:
    fourth_metric = ("&#129504;", "Avg AI Confidence", f"{articles['ml_confidence'].mean() * 100:.0f}%")
else:
    fourth_metric = ("&#9878;", "Bias Categories", articles[active_bias_col].nunique())

metrics = [
    ("&#128240;", "Total Articles", len(articles)),
    ("&#128269;", "Showing", len(filtered)),
    ("&#127760;", "Sources", articles["source_name"].nunique()),
    fourth_metric,
]
for idx, (col, (icon, label, value)) in enumerate(zip([c1, c2, c3, c4], metrics)):
    col.markdown(
        f'<div class="metric-card" style="animation-delay:{idx * 0.06:.2f}s;">'
        f'<div class="metric-icon">{icon}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------------
# AI diagnostics
# ---------------------------------------------------------------------------

if ml_available and not filtered.empty and {"ml_confidence", "bias_intensity", "ml_direction_score"}.issubset(filtered.columns):
    st.markdown('<div class="section-header">AI Diagnostics</div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    diag_metrics = [
        ("Confidence", f"{filtered['ml_confidence'].mean() * 100:.1f}%"),
        ("Bias Intensity", f"{filtered['bias_intensity'].mean() * 100:.1f}%"),
        ("Direction Score", f"{filtered['ml_direction_score'].mean():+.2f}"),
    ]
    for idx, (col, (label, value)) in enumerate(zip([d1, d2, d3], diag_metrics)):
        col.markdown(
            f'<div class="metric-card" style="animation-delay:{0.08 + idx * 0.06:.2f}s;">'
            f'<div class="metric-value" style="font-size:1.6rem;">{value}</div>'
            f'<div class="metric-label">{label}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown("")

# ---------------------------------------------------------------------------
# Bias spectrum bar
# ---------------------------------------------------------------------------

bias_counts = filtered[active_bias_col].value_counts()
total = bias_counts.sum() if bias_counts.sum() > 0 else 1

st.markdown('<div class="section-header">Bias Spectrum</div>', unsafe_allow_html=True)

segments_html = ""
for bias in BIAS_ORDER:
    count = bias_counts.get(bias, 0)
    pct = count / total * 100
    if pct > 0:
        color = BIAS_COLORS[bias]
        label = f"{count}" if pct > 8 else ""
        segments_html += (
            f'<div class="spectrum-segment" style="width:{pct:.1f}%;background:{color};"'
            f' title="{bias}: {count} ({pct:.0f}%)">{label}</div>'
        )

legend_html = ""
for b in BIAS_ORDER:
    legend_html += (
        f'<div class="legend-item">'
        f'<span class="legend-dot" style="background:{BIAS_COLORS[b]};"></span>'
        f"{b}</div>"
    )

st.markdown(
    f'<div class="spectrum-container">'
    f'<div class="spectrum-bar">{segments_html}</div>'
    f'<div class="spectrum-legend">{legend_html}</div>'
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown("")

# ---------------------------------------------------------------------------
# Bar chart — article count per bias category (Altair for themed colors)
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="section-header">Articles by Bias Category</div>',
    unsafe_allow_html=True,
)

chart_df = pd.DataFrame(
    {
        "Bias": BIAS_ORDER,
        "Articles": [bias_counts.get(b, 0) for b in BIAS_ORDER],
        "Color": [BIAS_COLORS[b] for b in BIAS_ORDER],
    }
)

chart = (
    alt.Chart(chart_df)
    .mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    .encode(
        x=alt.X("Bias:N", sort=BIAS_ORDER, axis=alt.Axis(labelAngle=0, title=None)),
        y=alt.Y("Articles:Q", axis=alt.Axis(title="Article Count", tickMinStep=1)),
        color=alt.Color(
            "Bias:N",
            scale=alt.Scale(domain=BIAS_ORDER, range=[BIAS_COLORS[b] for b in BIAS_ORDER]),
            legend=None,
        ),
        tooltip=["Bias", "Articles"],
    )
    .properties(height=280)
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False, domainColor="#e0e0e0")
)

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.altair_chart(chart, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ---------------------------------------------------------------------------
# Article cards
# ---------------------------------------------------------------------------

st.markdown(
    f'<div class="section-header">Articles ({len(filtered)})</div>',
    unsafe_allow_html=True,
)

if filtered.empty:
    st.markdown(
        '<div class="no-results">No articles match your current filters.</div>',
        unsafe_allow_html=True,
    )
else:
    for idx, (_, row) in enumerate(filtered.iterrows()):
        # Primary bias = whichever toggle is active
        bias = row[active_bias_col]
        color = BIAS_COLORS.get(bias, "#78909C")
        pub_date = (
            row["published_dt"].strftime("%b %d, %Y")
            if pd.notna(row["published_dt"])
            else "Unknown date"
        )
        raw_summary = str(row.get("summary", "")).strip()
        if not raw_summary:
            raw_summary = str(row.get("content", "")).strip()
        summary = (
            html.escape(raw_summary[:300]) + "..."
            if len(raw_summary) > 300
            else html.escape(raw_summary)
        )
        link = row["link"]
        title = html.escape(str(row["title"]))
        source = html.escape(str(row["source_name"]))
        emoji = BIAS_EMOJI.get(bias, "")

        # Secondary badge (the *other* bias source)
        secondary_html = ""
        if ml_available:
            if active_bias_col == "ml_bias":
                sec_bias = row["political_bias"]
                sec_label = "Source:"
            else:
                sec_bias = row["ml_bias"]
                sec_label = "AI:"
            sec_color = BIAS_COLORS.get(sec_bias, "#78909C")
            secondary_html = (
                f'<span class="badge-label">{sec_label}</span>'
                f'<span class="ml-badge" style="background:{sec_color};">{sec_bias}</span>'
            )

        # Confidence bar (only when ML data exists)
        confidence_html = ""
        if ml_available and "ml_confidence" in row.index:
            conf = row["ml_confidence"]
            pct = conf * 100
            if pct >= 70:
                bar_color = "#43a047"
            elif pct >= 50:
                bar_color = "#ffa726"
            else:
                bar_color = "#e53935"
            confidence_html = (
                f'<div class="confidence-container">'
                f'<span class="confidence-label">AI Confidence</span>'
                f'<div class="confidence-bar-bg">'
                f'<div class="confidence-bar-fill" style="width:{pct:.0f}%;background:{bar_color};"></div>'
                f'</div>'
                f'<span class="confidence-pct" style="color:{bar_color};">{pct:.0f}%</span>'
                f'</div>'
            )

        ai_details_html = ""
        if (
            ml_available
            and show_ai_reasoning
            and "ml_direction_score" in row.index
            and "bias_intensity" in row.index
        ):
            direction_score = float(row.get("ml_direction_score", 0.0))
            intensity_score = float(row.get("bias_intensity", 0.0))
            lex_left = int(row.get("ml_lexical_left_hits", 0))
            lex_right = int(row.get("ml_lexical_right_hits", 0))
            loaded_hits = int(row.get("ml_loaded_language_hits", 0))
            explanation = html.escape(str(row.get("ml_explanation", "")))
            ai_details_html = (
                '<div class="ai-details">'
                f'Direction score: {direction_score:+.2f} | '
                f'Bias intensity: {intensity_score:.2f} | '
                f'Lexical L/R hits: {lex_left}/{lex_right} | '
                f'Loaded terms: {loaded_hits}'
                f'<br>{explanation}'
                "</div>"
            )

        st.markdown(
            f'<div class="article-card" style="border-left-color:{color};animation-delay:{min(idx * 0.03, 0.45):.2f}s;">'
            f'<a class="article-title" href="{link}" target="_blank">{title}</a>'
            f'<div class="article-meta">'
            f'<span class="bias-badge" style="background:{color};">{emoji} {bias}</span>'
            f'{secondary_html}'
            f'<span class="source-badge">{source}</span>'
            f'<span class="date-badge">{pub_date}</span>'
            f"</div>"
            f'{confidence_html}'
            f'<div class="article-summary">{summary}</div>'
            f'{ai_details_html}'
            f"</div>",
            unsafe_allow_html=True,
        )
