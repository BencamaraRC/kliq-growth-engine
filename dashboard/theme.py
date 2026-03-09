"""KLIQ Design System for Streamlit.

Provides CSS overrides, component helpers, and Plotly theming
that match the KLIQ design system (Gable Green palette, Inter font,
shadow cards, status badges, etc.).

Usage: call inject_kliq_theme() at the top of every page after set_page_config().
"""

from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
import yaml

# ─── KLIQ Design Tokens ──────────────────────────────────────────────────────

COLORS = {
    "gray_25": "#FCFCFD",
    "gray_50": "#F9FAFB",
    "gray_100": "#F3F4F6",
    "gray_200": "#E5E7EB",
    "gray_300": "#D2D6DB",
    "gray_400": "#9DA4AE",
    "gray_500": "#6C737F",
    "gray_600": "#4D5761",
    "gray_700": "#384250",
    "gray_800": "#1F2A37",
    "gray_900": "#111927",
    "gray_950": "#0D121C",
    # Gable Green (Primary teal)
    "teal_50": "#F3FAF8",
    "teal_100": "#D7F0ED",
    "teal_200": "#AEE1DA",
    "teal_300": "#7ECAC3",
    "teal_400": "#53AEA9",
    "teal_500": "#39938F",
    "teal_600": "#2C7574",
    "teal_700": "#265F5E",
    "teal_800": "#224D4D",
    "teal_900": "#1C3838",
    "teal_950": "#0E2325",
    # Accent
    "tangerine": "#FF9F88",
    "lime": "#DEFE9C",
    "alpine": "#9CF0FF",
    # Semantic
    "bg_primary": "#FFFDF9",
    "bg_card": "#FFFFFF",
    "text_primary": "#101828",
    "text_secondary": "#667085",
    "text_tertiary": "#9DA4AE",
    "border": "#EAECF0",
    "positive": "#039855",
    "negative": "#D92D20",
    "warning": "#F79009",
}

# Status badge color map: (text_color, bg_color) — keys are uppercase to match DB enums
STATUS_COLORS = {
    "DISCOVERED": ("#344054", "#F2F4F7"),
    "SCRAPED": ("#1C3838", "#E0F7FA"),
    "CONTENT_GENERATED": ("#B54708", "#FFFAEB"),
    "STORE_CREATED": ("#1C3838", "#F0FFF4"),
    "EMAIL_SENT": ("#B42318", "#FFF1ED"),
    "CLAIMED": ("#039855", "#ECFDF3"),
    "REJECTED": ("#D92D20", "#FEE4E2"),
}

PLATFORM_COLORS = {
    "YOUTUBE": ("#CC0000", "#FEE2E2"),
    "SKOOL": ("#1D4ED8", "#DBEAFE"),
    "PATREON": ("#FF424D", "#FFE4E6"),
    "WEBSITE": ("#4D5761", "#F3F4F6"),
    "TIKTOK": ("#000000", "#F3F4F6"),
    "INSTAGRAM": ("#C13584", "#FCE7F3"),
}

# Chart palette
CHART_COLORS = ["#1C3838", "#39938F", "#FF9F88", "#DEFE9C", "#9CF0FF", "#F79009", "#7ECAC3"]

# ─── Plotly Theme ─────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, sans-serif", color="#101828", size=13),
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFDF9",
    colorway=CHART_COLORS,
    xaxis=dict(gridcolor="#EAECF0", linecolor="#EAECF0"),
    yaxis=dict(gridcolor="#EAECF0", linecolor="#EAECF0"),
    margin=dict(l=20, r=20, t=48, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
)


def apply_plotly_theme(fig):
    """Apply KLIQ design tokens to a Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ─── CSS Injection ────────────────────────────────────────────────────────────

KLIQ_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* === Global === */
html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background-color: #FFFDF9 !important;
}

/* === Sidebar === */
section[data-testid="stSidebar"] {
    background-color: #1C3838 !important;
    padding-top: 1rem !important;
}
section[data-testid="stSidebar"] * {
    color: #FFFDFA !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}
section[data-testid="stSidebar"] .stPageLink {
    margin: 0 !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] .stPageLink a {
    color: #FFFDFA !important;
    border-radius: 8px;
    padding: 8px 12px !important;
    margin: 2px 0 !important;
    display: block !important;
    text-decoration: none !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: background-color 0.15s;
}
section[data-testid="stSidebar"] .stPageLink a:hover {
    background-color: rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] .stPageLink a span {
    font-size: 14px !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stCaption {
    padding-left: 0 !important;
    margin-left: 0 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.12) !important;
    margin: 12px 0 !important;
}

/* === Headings === */
h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #101828 !important;
    letter-spacing: -0.02em;
    font-size: 28px !important;
}
h2, h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #101828 !important;
    letter-spacing: -0.01em;
}

/* === Metric cards === */
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #EAECF0;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0px 1px 2px rgba(16, 24, 40, 0.05);
}
div[data-testid="stMetric"] label {
    color: #667085 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #101828 !important;
    font-weight: 700 !important;
    font-size: 30px !important;
}

/* === Buttons === */
.stButton > button {
    background-color: #1C3838 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
    font-size: 14px !important;
    transition: background-color 0.15s;
}
.stButton > button:hover {
    background-color: #0E2325 !important;
}

.stDownloadButton > button {
    background-color: transparent !important;
    color: #1C3838 !important;
    border: 1px solid #D2D6DB !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
.stDownloadButton > button:hover {
    background-color: #F3FAF8 !important;
    border-color: #1C3838 !important;
}

/* === DataFrames === */
.stDataFrame {
    border: 1px solid #EAECF0 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* === Tabs === */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    border-bottom: 1px solid #EAECF0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500;
    color: #667085;
    padding: 12px 20px;
}
.stTabs [aria-selected="true"] {
    font-weight: 600 !important;
    color: #1C3838 !important;
    border-bottom: 2px solid #1C3838 !important;
}

/* === Selectbox / Inputs === */
.stSelectbox > div > div, .stTextInput > div > div > input {
    border-radius: 8px !important;
    border-color: #D2D6DB !important;
    font-size: 14px !important;
}
.stSelectbox > div > div:focus-within, .stTextInput > div > div > input:focus {
    border-color: #39938F !important;
    box-shadow: 0 0 0 1px #39938F !important;
}

/* === Expanders === */
.streamlit-expanderHeader {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #101828 !important;
    font-size: 14px !important;
}

/* === Dividers === */
hr {
    border-color: #EAECF0 !important;
}

/* === Hide default Streamlit auto-nav and branding === */
[data-testid="stSidebarNav"] {display: none !important;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""


# ─── Page Setup ───────────────────────────────────────────────────────────────


def inject_kliq_theme():
    """Inject the KLIQ design system CSS. Call at the top of every page."""
    st.markdown(KLIQ_CSS, unsafe_allow_html=True)


def _get_authenticator():
    """Load or return the cached authenticator instance."""
    if "authenticator" not in st.session_state:
        _auth_config_path = Path(__file__).parent / "auth_config.yaml"
        with open(_auth_config_path) as f:
            _auth_cfg = yaml.safe_load(f)
        authenticator = stauth.Authenticate(
            _auth_cfg["credentials"],
            _auth_cfg["cookie"]["name"],
            _auth_cfg["cookie"]["key"],
            _auth_cfg["cookie"]["expiry_days"],
        )
        st.session_state["authenticator"] = authenticator
    return st.session_state["authenticator"]


def require_auth():
    """Check authentication and stop the page if the user is not logged in.

    Initializes the authenticator and reads the auth cookie on every page
    so sessions persist across Streamlit multi-page navigation.
    """
    authenticator = _get_authenticator()

    # Let the authenticator check the cookie to restore session
    if not st.session_state.get("authentication_status"):
        authenticator.login()
        if st.session_state.get("authentication_status") is None:
            st.info("Please log in to access the Growth Engine dashboard.")
            st.stop()
        elif st.session_state.get("authentication_status") is False:
            st.error("Invalid username or password.")
            st.stop()


def sidebar_nav():
    """Render the KLIQ-styled sidebar navigation."""
    require_auth()

    st.sidebar.markdown(
        '<div style="padding:4px 0 12px;font-family:Inter,sans-serif;font-weight:700;'
        'font-size:18px;color:#FFFDFA;letter-spacing:-0.01em;">'
        "KLIQ Growth Engine</div>",
        unsafe_allow_html=True,
    )

    # Show logged-in user and logout button
    username = st.session_state.get("name", "")
    if username:
        st.sidebar.markdown(
            f'<div style="font-size:12px;color:rgba(255,255,255,0.7);padding:0 0 4px;">'
            f'Logged in as <strong style="color:#fff;">{username}</strong></div>',
            unsafe_allow_html=True,
        )
    authenticator = st.session_state.get("authenticator")
    if authenticator:
        authenticator.logout("Logout", "sidebar")

    st.sidebar.markdown("---")
    st.sidebar.page_link("app.py", label="Dashboard", icon=":material/dashboard:")
    st.sidebar.page_link("pages/profiles.py", label="Profiles", icon=":material/people:")
    st.sidebar.page_link(
        "pages/profile_detail.py", label="Profile Detail", icon=":material/person:"
    )
    st.sidebar.page_link("pages/pipeline.py", label="Pipeline", icon=":material/monitoring:")
    st.sidebar.page_link("pages/campaigns.py", label="Campaigns", icon=":material/mail:")
    st.sidebar.page_link(
        "pages/store_preview.py", label="Store Preview", icon=":material/storefront:"
    )
    st.sidebar.page_link(
        "pages/cms_admin.py", label="CMS Admin", icon=":material/admin_panel_settings:"
    )
    st.sidebar.page_link("pages/operations.py", label="Operations", icon=":material/terminal:")
    st.sidebar.page_link(
        "pages/linkedin_outreach.py",
        label="LinkedIn Outreach",
        icon=":material/share:",
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("v0.2.0 | Growth Engine")


# ─── Component Helpers ────────────────────────────────────────────────────────


def render_status_badge(status: str) -> str:
    """Return HTML for a colored status pill badge."""
    key = status.upper() if status else ""
    text_color, bg_color = STATUS_COLORS.get(key, ("#344054", "#F2F4F7"))
    label = status.replace("_", " ").title()
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:9999px;'
        f"font-size:12px;font-weight:500;color:{text_color};background:{bg_color};"
        f'font-family:Inter,sans-serif;">{label}</span>'
    )


def render_platform_badge(platform: str) -> str:
    """Return HTML for a platform indicator pill."""
    key = platform.upper() if platform else ""
    text_color, bg_color = PLATFORM_COLORS.get(key, ("#4D5761", "#F3F4F6"))
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:9999px;'
        f"font-size:12px;font-weight:500;color:{text_color};background:{bg_color};"
        f'font-family:Inter,sans-serif;">{platform}</span>'
    )


def render_niche_tags(tags) -> str:
    """Return HTML for a row of niche tag pills."""
    if not tags or not isinstance(tags, list):
        return '<span style="color:#9DA4AE;font-size:13px;">No niches</span>'
    html_tags = []
    for tag in tags[:6]:
        html_tags.append(
            f'<span style="display:inline-block;padding:2px 10px;border-radius:9999px;'
            f"font-size:12px;font-weight:500;color:#1C3838;background:#F3FAF8;"
            f'border:1px solid #D7F0ED;margin:2px;font-family:Inter,sans-serif;">{tag}</span>'
        )
    extra = (
        f' <span style="color:#9DA4AE;font-size:12px;">+{len(tags) - 6} more</span>'
        if len(tags) > 6
        else ""
    )
    return " ".join(html_tags) + extra


def render_brand_colors(colors) -> str:
    """Return HTML for color swatch circles."""
    if not colors or not isinstance(colors, list):
        return '<span style="color:#9DA4AE;font-size:13px;">No colors</span>'
    swatches = []
    for c in colors[:6]:
        hex_c = c if c.startswith("#") else f"#{c}"
        swatches.append(
            f'<span style="display:inline-block;width:24px;height:24px;border-radius:6px;'
            f"background:{hex_c};border:1px solid #EAECF0;margin-right:4px;"
            f'vertical-align:middle;" title="{hex_c}"></span>'
        )
    return " ".join(swatches)


def render_kpi_row(metrics: list[tuple[str, str]]):
    """Render a row of KPI metrics. Each tuple is (label, value)."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
