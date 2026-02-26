"""KLIQ Growth Engine Dashboard — Main entry point.

Run with: streamlit run dashboard/app.py

Shows high-level KPIs and links to sub-pages for detailed views.
"""

import streamlit as st

st.set_page_config(
    page_title="KLIQ Growth Engine",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
st.sidebar.title("KLIQ Growth Engine")
st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon=":material/home:")
st.sidebar.page_link("pages/growth_engine.py", label="Pipeline Monitor", icon=":material/monitoring:")
st.sidebar.page_link("pages/competitor_intel.py", label="Competitor Intel", icon=":material/search:")
st.sidebar.page_link("pages/campaign_manager.py", label="Campaign Manager", icon=":material/mail:")
st.sidebar.page_link("pages/store_preview.py", label="Store Preview", icon=":material/storefront:")
st.sidebar.markdown("---")
st.sidebar.caption("v0.1.0 | Phase 6")

# --- Main Content ---
st.title("KLIQ Growth Engine")
st.markdown("Automated coach discovery, webstore generation, and outreach pipeline.")

try:
    from data import get_kpi_summary, get_daily_activity, get_funnel_data

    kpis = get_kpi_summary()

    # --- Top-line KPIs ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Prospects", kpis["total_prospects"])
    col2.metric("Stores Created", kpis["stores_created"])
    col3.metric("Emails Sent", kpis["emails_sent"])
    col4.metric("Claims", kpis["claimed"], help="Coaches who activated their store")
    col5.metric(
        "Claim Rate",
        f"{kpis['claim_rate']}%",
        help="Claims / Stores Created",
    )

    st.markdown("---")

    # --- Funnel ---
    st.subheader("Pipeline Funnel")
    funnel = get_funnel_data()
    if not funnel.empty:
        import plotly.express as px

        fig = px.funnel(
            funnel,
            x="count",
            y="status",
            title="Prospect Pipeline Stages",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No prospects yet. Trigger a discovery run to get started.")

    # --- Daily Activity ---
    st.subheader("Daily Activity (Last 30 Days)")
    daily = get_daily_activity(30)
    if not daily.empty:
        import plotly.express as px

        fig = px.line(
            daily,
            x="date",
            y=["discovered", "stores_created", "claimed"],
            title="Daily Pipeline Activity",
            labels={"value": "Count", "variable": "Metric"},
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity data yet.")

    # --- Status Breakdown ---
    st.subheader("Status Breakdown")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        | Stage | Count |
        |-------|-------|
        | Discovered | {kpis['discovered']} |
        | Scraped | {kpis['scraped']} |
        | Content Generated | {kpis['content_generated']} |
        | Store Created | {kpis['stores_created']} |
        | Email Sent | {kpis['emails_sent']} |
        | Claimed | {kpis['claimed']} |
        | Rejected | {kpis['rejected']} |
        """)

    with col_b:
        st.metric("Email Open Rate", f"{kpis['open_rate']}%")
        st.metric("Claim Conversion Rate", f"{kpis['claim_rate']}%")

except Exception as e:
    st.warning(f"Could not connect to database. Make sure PostgreSQL is running.\n\nError: {e}")
    st.info("To set up the database, run:\n```\ndocker compose up -d postgres redis\nalembic upgrade head\n```")
