import os
import sys

import pandas as pd
import streamlit as st

# Ensure project root is on the path so `src.*` imports resolve.
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.backend.news_crawler import NewsCrawler
from src.backend.source_manager import SourceManager

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(_project_root, "news_sources.db")


@st.cache_resource
def get_source_manager() -> SourceManager:
    return SourceManager(db_path=DB_PATH)


@st.cache_resource
def get_news_crawler() -> NewsCrawler:
    return NewsCrawler(get_source_manager())


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="News Source Manager", page_icon="📰", layout="wide")
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
        --sidebar-bg-top: #0a1929;
        --sidebar-bg-bottom: #1a2f42;
        --shadow-sm: 0 1px 3px rgba(15, 20, 25, 0.08), 0 1px 2px rgba(15, 20, 25, 0.04);
        --shadow-md: 0 10px 30px rgba(15, 20, 25, 0.1), 0 4px 12px rgba(15, 20, 25, 0.06);
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
    .block-container {
        max-width: 1200px;
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg-top) 0%, var(--sidebar-bg-bottom) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    section[data-testid="stSidebar"] * {
        color: #e6ecf1 !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #9ec8bf !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        font-size: 0.72rem;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        text-transform: none;
        letter-spacing: 0;
        font-size: 0.9rem;
        font-weight: 500;
        color: #edf2f7 !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div {
        border-radius: 4px !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        background: rgba(255, 255, 255, 0.06) !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] {
        border-radius: 8px !important;
        border: 1px solid rgba(204, 251, 241, 0.6) !important;
        background: linear-gradient(160deg, #0d9488 0%, #0f766e 100%) !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25) !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        transform: translateY(-2px);
        filter: brightness(1.08);
        box-shadow: 0 8px 24px rgba(13, 148, 136, 0.35) !important;
    }

    .manager-header {
        border-bottom: 2px solid var(--line);
        margin-bottom: 1.2rem;
        padding-bottom: 1rem;
        position: relative;
    }
    .manager-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, var(--accent), #f59e0b);
    }
    .manager-kicker {
        margin: 0 0 0.5rem 0;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        background: linear-gradient(135deg, var(--accent), #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .manager-title {
        margin: 0;
        font-family: 'Sora', sans-serif;
        font-size: 2.2rem;
        line-height: 1.05;
        letter-spacing: -0.04em;
        font-weight: 800;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .manager-subtitle {
        margin: 0.45rem 0 0 0;
        color: var(--muted);
        max-width: 800px;
        line-height: 1.6;
    }

    .mini-stat {
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 16px 16px;
        margin-bottom: 1.2rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .mini-stat::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent), #f59e0b);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    .mini-stat:hover::before {
        transform: scaleX(1);
    }
    .mini-stat:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: var(--line-strong);
    }
    .mini-stat-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: var(--muted);
        margin-bottom: 6px;
    }
    .mini-stat-value {
        font-family: 'Sora', sans-serif;
        font-size: 1.6rem;
        line-height: 1.1;
        font-weight: 800;
        color: var(--ink);
    }

    h3 {
        font-family: 'Sora', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.01em;
    }
    .stForm {
        background: linear-gradient(135deg, var(--surface) 0%, #fefdfb 100%);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 1rem 1.2rem 0.9rem 1.2rem;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.3s ease;
    }
    .stForm:focus-within {
        box-shadow: var(--shadow-md);
        border-color: var(--line-strong);
    }
    div[data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    div[data-baseweb="select"] > div:hover,
    [data-baseweb="input"] > div:hover {
        border-color: var(--accent) !important;
    }
    button[kind="secondary"], button[kind="primary"] {
        border-radius: 8px !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3) !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    @media (max-width: 900px) {
        .manager-title {
            font-size: 1.65rem;
        }
    }

    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

source_manager = get_source_manager()
news_crawler = get_news_crawler()

all_sources_snapshot = source_manager.get_all_sources()
active_source_count = sum(1 for source in all_sources_snapshot if source.get("active") == 1)
rss_source_count = sum(1 for source in all_sources_snapshot if source.get("rss_feed"))

st.markdown(
    '<div class="manager-header">'
    '<p class="manager-kicker">Editorial Infrastructure</p>'
    '<p class="manager-title">News Source Management</p>'
    '<p class="manager-subtitle">'
    "Curate your source universe, control crawl state, and keep data collection reliable."
    "</p>"
    "</div>",
    unsafe_allow_html=True,
)

mc1, mc2, mc3 = st.columns(3)
for col, (label, value) in zip(
    [mc1, mc2, mc3],
    [
        ("Total Sources", len(all_sources_snapshot)),
        ("Active Sources", active_source_count),
        ("RSS Feeds", rss_source_count),
    ],
):
    col.markdown(
        f'<div class="mini-stat">'
        f'<div class="mini-stat-label">{label}</div>'
        f'<div class="mini-stat-value">{value}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    '<div style="padding-top:6px;padding-bottom:8px;">'
    '<span style="font-family:Sora,sans-serif;font-size:1rem;font-weight:600;">Source Manager</span><br>'
    '<span style="font-size:0.68rem;letter-spacing:0.08em;text-transform:uppercase;color:#9ec8bf;">Control Panel</span>'
    "</div>",
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation",
    ["Add Source", "View Sources", "Manage Sources", "Crawl News"],
)

# ---------------------------------------------------------------------------
# Add Source
# ---------------------------------------------------------------------------

if page == "Add Source":
    st.subheader("Add New News Source")

    with st.form("add_source_form"):
        name = st.text_input("News Source Name")
        url = st.text_input("Website URL")
        rss_feed = st.text_input("RSS Feed URL (optional)")

        bias_options = [
            "Unclassified",
            "Left-Leaning",
            "Center-Left",
            "Centrist",
            "Center-Right",
            "Right-Leaning",
        ]
        political_bias = st.selectbox("Political Bias", bias_options)

        submitted = st.form_submit_button("Add Source")

        if submitted:
            if not name or not url:
                st.error("Name and URL are required.")
            else:
                with st.spinner("Validating source..."):
                    result = source_manager.add_source(
                        name=name,
                        url=url,
                        rss_feed=rss_feed or None,
                        political_bias=political_bias,
                    )
                if result["success"]:
                    st.success(result["message"])
                else:
                    st.error(result["message"])

# ---------------------------------------------------------------------------
# View Sources
# ---------------------------------------------------------------------------

elif page == "View Sources":
    st.subheader("Active News Sources")

    sources = source_manager.get_active_sources()
    if sources:
        df = pd.DataFrame(sources)
        display_cols = ["id", "name", "url", "rss_feed", "political_bias", "last_scraped"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], use_container_width=True)
    else:
        st.info("No active sources found. Add one from the sidebar.")

# ---------------------------------------------------------------------------
# Manage Sources
# ---------------------------------------------------------------------------

elif page == "Manage Sources":
    st.subheader("Manage Sources")

    sources = source_manager.get_all_sources()
    if not sources:
        st.info("No sources available.")
    else:
        df = pd.DataFrame(sources)
        st.dataframe(df, use_container_width=True)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Toggle activation**")
            source_names = [s["name"] for s in sources]
            selected = st.selectbox("Select source", source_names, key="toggle_select")
            selected_source = next(s for s in sources if s["name"] == selected)
            is_active = selected_source["active"] == 1

            label = "Deactivate" if is_active else "Activate"
            if st.button(label):
                result = source_manager.update_source_status(
                    selected_source["id"], active=not is_active
                )
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

        with col2:
            st.markdown("**Remove source**")
            del_selected = st.selectbox("Select source", source_names, key="del_select")
            del_source = next(s for s in sources if s["name"] == del_selected)

            if st.button("Remove permanently"):
                result = source_manager.remove_source(del_source["id"])
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

# ---------------------------------------------------------------------------
# Crawl News
# ---------------------------------------------------------------------------

elif page == "Crawl News":
    st.subheader("Crawl News Articles")

    sources = source_manager.get_active_sources()
    if not sources:
        st.info("No active sources. Add and activate sources first.")
    else:
        crawl_mode = st.radio("Crawl mode", ["All active sources", "Single source"])

        if crawl_mode == "Single source":
            source_name = st.selectbox(
                "Pick a source", [s["name"] for s in sources]
            )

        if st.button("Start crawl"):
            with st.spinner("Crawling..."):
                if crawl_mode == "All active sources":
                    df = news_crawler.crawl_all_sources()
                else:
                    df = news_crawler.crawl_single_source(source_name)

            if df.empty:
                st.warning("No articles found.")
            else:
                st.success(f"Collected {len(df)} articles")
                st.dataframe(df, use_container_width=True)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name="crawled_articles.csv",
                    mime="text/csv",
                )
