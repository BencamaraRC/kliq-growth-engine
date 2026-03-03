"""Campaigns — outreach performance and email analytics.

Shows per-step email performance, conversion funnel, timeline, and recent claims.
"""

import streamlit as st

st.set_page_config(page_title="Campaigns | KLIQ Growth Engine", layout="wide")

from theme import apply_plotly_theme, inject_kliq_theme, sidebar_nav  # noqa: E402

inject_kliq_theme()
sidebar_nav()

st.title("Campaigns")
st.markdown("Outreach campaign performance and email engagement analytics.")

try:
    from data import (
        get_campaign_stats,
        get_email_timeline,
        get_kpi_summary,
        get_recent_claims,
    )

    kpis = get_kpi_summary()

    # --- Top metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emails Sent", f"{kpis['emails_sent']:,}")
    col2.metric("Open Rate", f"{kpis['open_rate']}%")
    col3.metric("Claims", f"{kpis['claimed']:,}")
    col4.metric("Claim Rate", f"{kpis['claim_rate']}%")

    st.markdown("---")

    # --- Per-Step Performance ---
    st.subheader("Email Performance by Step")
    stats = get_campaign_stats()
    steps = stats.get("steps", [])

    if steps:
        import pandas as pd
        import plotly.graph_objects as go

        step_df = pd.DataFrame(steps)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(name="Sent", x=step_df["step"], y=step_df["sent"], marker_color="#1C3838")
        )
        fig.add_trace(
            go.Bar(name="Opened", x=step_df["step"], y=step_df["opened"], marker_color="#039855")
        )
        fig.add_trace(
            go.Bar(name="Clicked", x=step_df["step"], y=step_df["clicked"], marker_color="#FF9F88")
        )
        fig.add_trace(
            go.Bar(name="Bounced", x=step_df["step"], y=step_df["bounced"], marker_color="#D92D20")
        )
        fig.update_layout(barmode="group", height=400)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            step_df[
                [
                    "step",
                    "sent",
                    "opened",
                    "clicked",
                    "bounced",
                    "unsubscribed",
                    "open_rate",
                    "click_rate",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "open_rate": st.column_config.NumberColumn("Open %", format="%.1f%%"),
                "click_rate": st.column_config.NumberColumn("Click %", format="%.1f%%"),
            },
        )
    else:
        st.info("No campaign data yet. Send outreach emails to see performance stats.")

    # --- Conversion Funnel ---
    st.subheader("Conversion Funnel")
    if steps:
        import pandas as pd
        import plotly.express as px

        total_sent = sum(s["sent"] for s in steps if s["step_num"] == 1)
        total_opened = sum(s["opened"] for s in steps)
        total_clicked = sum(s["clicked"] for s in steps)
        total_claimed = kpis["claimed"]

        funnel_data = pd.DataFrame(
            {
                "stage": ["Emails Sent", "Opened", "Clicked", "Claimed"],
                "count": [total_sent, total_opened, total_clicked, total_claimed],
            }
        )

        fig = px.funnel(
            funnel_data,
            x="count",
            y="stage",
            color_discrete_sequence=["#1C3838", "#39938F", "#FF9F88", "#039855"],
        )
        fig.update_layout(height=350)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    # --- Email Timeline ---
    st.subheader("Email Send Timeline")
    days = st.slider("Timeline days", 7, 90, 30, key="campaign_days")
    timeline = get_email_timeline(days)
    if not timeline.empty:
        import plotly.express as px

        step_names = {1: "Store Ready", 2: "Reminder 1", 3: "Reminder 2", 4: "Claimed Confirmation"}
        timeline["step_name"] = timeline["step"].map(step_names)

        fig = px.bar(
            timeline,
            x="date",
            y="count",
            color="step_name",
            barmode="stack",
            color_discrete_sequence=["#1C3838", "#39938F", "#FF9F88", "#9CF0FF"],
        )
        fig.update_layout(height=350)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No email data in the selected time range.")

    # --- Recent Claims ---
    st.markdown("---")
    st.subheader("Recent Claims")
    claims = get_recent_claims(20)
    if not claims.empty:
        st.dataframe(
            claims,
            use_container_width=True,
            hide_index=True,
            column_config={
                "store_url": st.column_config.LinkColumn("Store URL"),
            },
        )
    else:
        st.info("No store claims yet.")

except Exception as e:
    st.error(f"Database connection error: {e}")
