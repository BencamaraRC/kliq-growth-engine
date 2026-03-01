"""Pipeline Monitor — detailed view of the Growth Engine pipeline.

Shows funnel visualization, platform stats, daily throughput, and recent prospects.
"""

import streamlit as st

st.set_page_config(page_title="Pipeline | KLIQ Growth Engine", layout="wide")

from theme import inject_kliq_theme, sidebar_nav, apply_plotly_theme, CHART_COLORS

inject_kliq_theme()
sidebar_nav()

st.title("Pipeline")
st.markdown("Real-time view of the Growth Engine scraping, generation, and outreach pipeline.")

try:
    from data import (
        get_daily_activity,
        get_funnel_data,
        get_platform_breakdown,
        get_prospects_table,
    )

    # --- Funnel ---
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
        fig.update_layout(height=400, showlegend=False)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No prospects in the pipeline yet.")

    # --- Platform Breakdown ---
    st.subheader("Discovery by Platform")
    col1, col2 = st.columns(2)

    platforms = get_platform_breakdown()
    if not platforms.empty:
        import plotly.express as px

        with col1:
            fig = px.pie(
                platforms,
                values="count",
                names="platform",
                color_discrete_sequence=CHART_COLORS,
                hole=0.4,
            )
            fig.update_layout(height=350)
            apply_plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(platforms, use_container_width=True, hide_index=True)
    else:
        st.info("No platform data yet.")

    # --- Daily Throughput ---
    st.subheader("Daily Throughput")
    days = st.slider("Days to show", 7, 90, 30)
    daily = get_daily_activity(days)
    if not daily.empty:
        import plotly.express as px

        fig = px.area(
            daily,
            x="date",
            y=["discovered", "stores_created", "claimed"],
            labels={"value": "Count", "variable": "Metric"},
            color_discrete_sequence=["#1C3838", "#39938F", "#FF9F88"],
        )
        fig.update_layout(height=350)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    # --- Recent Prospects ---
    st.subheader("Recent Prospects")
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "DISCOVERED", "SCRAPED", "CONTENT_GENERATED", "STORE_CREATED", "EMAIL_SENT", "CLAIMED", "REJECTED"],
    )
    status_val = None if status_filter == "All" else status_filter
    prospects = get_prospects_table(status=status_val, limit=50)
    if not prospects.empty:
        st.dataframe(prospects, use_container_width=True, hide_index=True)
    else:
        st.info("No prospects match the filter.")

except Exception as e:
    st.error(f"Database connection error: {e}")
