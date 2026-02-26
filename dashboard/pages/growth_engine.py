"""Pipeline Monitoring — detailed view of the Growth Engine pipeline.

Shows:
- Prospect funnel visualization
- Per-platform discovery stats
- Recent activity feed
- Pipeline task status (Celery)
"""

import streamlit as st

st.set_page_config(page_title="Pipeline Monitor | KLIQ Growth Engine", layout="wide")

st.title("Pipeline Monitor")
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
            title="Prospects by Pipeline Stage",
        )
        fig.update_layout(height=400, showlegend=False)
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
                title="Prospects per Platform",
            )
            fig.update_layout(height=350)
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
            title=f"Pipeline Throughput (Last {days} Days)",
            labels={"value": "Count", "variable": "Metric"},
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    # --- Recent Prospects ---
    st.subheader("Recent Prospects")
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "discovered", "scraped", "content_generated", "store_created", "email_sent", "claimed", "rejected"],
    )
    status_val = None if status_filter == "All" else status_filter
    prospects = get_prospects_table(status=status_val, limit=50)
    if not prospects.empty:
        st.dataframe(prospects, use_container_width=True, hide_index=True)
    else:
        st.info("No prospects match the filter.")

    # --- Pipeline Controls ---
    st.subheader("Pipeline Controls")
    st.markdown("Trigger pipeline actions via the API.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("Trigger Discovery", type="primary"):
            st.info("POST /api/pipeline/discover — use the API or curl to trigger discovery.")
    with col_b:
        if st.button("Process Outreach Queue"):
            st.info("POST /api/pipeline/outreach — processes pending outreach emails.")
    with col_c:
        if st.button("Flush BigQuery Events"):
            st.info("Events are flushed automatically every 30 seconds or 50 events.")

except Exception as e:
    st.error(f"Database connection error: {e}")
