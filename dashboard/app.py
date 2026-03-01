"""KLIQ Growth Engine Dashboard — Home.

Run with: streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="KLIQ Growth Engine",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from theme import inject_kliq_theme, sidebar_nav, apply_plotly_theme, CHART_COLORS

inject_kliq_theme()
sidebar_nav()

# --- Main Content ---
st.title("Dashboard")
st.markdown("Automated coach discovery, webstore generation, and outreach pipeline.")

try:
    from data import (
        get_daily_activity,
        get_funnel_data,
        get_kpi_summary,
        get_niche_distribution,
        get_platform_breakdown,
    )

    kpis = get_kpi_summary()

    # --- Top-line KPIs ---
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Prospects", f"{kpis['total_prospects']:,}")
    col2.metric("Stores Created", f"{kpis['stores_created']:,}")
    col3.metric("Emails Sent", f"{kpis['emails_sent']:,}")
    col4.metric("Claims", f"{kpis['claimed']:,}")
    col5.metric("Claim Rate", f"{kpis['claim_rate']}%")

    st.markdown("---")

    # --- Funnel + Platform Breakdown ---
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Pipeline Funnel")
        funnel = get_funnel_data()
        if not funnel.empty:
            import plotly.express as px

            fig = px.bar(
                funnel,
                x="status",
                y="count",
                color="status",
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(height=380, showlegend=False)
            apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No prospects yet. Trigger a discovery run to get started.")

    with col_right:
        st.subheader("By Platform")
        platforms = get_platform_breakdown()
        if not platforms.empty:
            import plotly.express as px

            fig = px.pie(
                platforms,
                values="count",
                names="platform",
                color_discrete_sequence=CHART_COLORS,
                hole=0.4,
            )
            fig.update_layout(height=380)
            apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No platform data yet.")

    # --- Daily Activity ---
    st.subheader("Daily Activity (Last 30 Days)")
    daily = get_daily_activity(30)
    if not daily.empty:
        import plotly.express as px

        fig = px.area(
            daily,
            x="date",
            y=["discovered", "stores_created", "claimed"],
            labels={"value": "Count", "variable": "Metric"},
            color_discrete_sequence=["#1C3838", "#39938F", "#FF9F88"],
        )
        fig.update_layout(height=320)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity data yet.")

    # --- Niche Distribution + Status Breakdown ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Top Niches")
        niches = get_niche_distribution()
        if not niches.empty:
            import plotly.express as px

            fig = px.bar(
                niches.head(12),
                x="count",
                y="niche",
                orientation="h",
                color_discrete_sequence=["#39938F"],
            )
            fig.update_layout(height=360, yaxis={"categoryorder": "total ascending"})
            apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Status Breakdown")
        st.markdown(f"""
| Stage | Count |
|-------|------:|
| Discovered | {kpis['discovered']:,} |
| Scraped | {kpis['scraped']:,} |
| Content Generated | {kpis['content_generated']:,} |
| Stores Created | {kpis['stores_created']:,} |
| Emails Sent | {kpis['emails_sent']:,} |
| Claimed | {kpis['claimed']:,} |
| Rejected | {kpis['rejected']:,} |
        """)
        st.markdown("")
        st.metric("Email Open Rate", f"{kpis['open_rate']}%")
        st.metric("Claim Conversion", f"{kpis['claim_rate']}%")

except Exception as e:
    st.warning(f"Could not connect to database. Make sure PostgreSQL is running.\n\nError: {e}")
    st.info("To set up the database, run:\n```\ndocker compose up -d postgres redis\nalembic upgrade head\n```")
