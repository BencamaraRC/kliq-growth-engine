"""Campaign Manager — outreach performance and email analytics.

Shows:
- Per-step email performance (open/click/bounce rates)
- Email send timeline
- Conversion funnel (sent → opened → clicked → claimed)
- Recent claims
"""

import streamlit as st

st.set_page_config(page_title="Campaign Manager | KLIQ Growth Engine", layout="wide")

st.title("Campaign Manager")
st.markdown("Outreach campaign performance and email engagement analytics.")

try:
    from dashboard.data import (
        get_campaign_stats,
        get_email_timeline,
        get_kpi_summary,
        get_recent_claims,
    )

    kpis = get_kpi_summary()

    # --- Top metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Emails Sent", kpis["emails_sent"])
    col2.metric("Open Rate", f"{kpis['open_rate']}%")
    col3.metric("Claims", kpis["claimed"])
    col4.metric("Claim Rate", f"{kpis['claim_rate']}%")

    st.markdown("---")

    # --- Per-Step Performance ---
    st.subheader("Email Performance by Step")
    stats = get_campaign_stats()
    steps = stats.get("steps", [])

    if steps:
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go

        step_df = pd.DataFrame(steps)

        # Bar chart: sent/opened/clicked per step
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Sent", x=step_df["step"], y=step_df["sent"], marker_color="#1E81FF"))
        fig.add_trace(go.Bar(name="Opened", x=step_df["step"], y=step_df["opened"], marker_color="#28a745"))
        fig.add_trace(go.Bar(name="Clicked", x=step_df["step"], y=step_df["clicked"], marker_color="#ffc107"))
        fig.add_trace(go.Bar(name="Bounced", x=step_df["step"], y=step_df["bounced"], marker_color="#dc3545"))
        fig.update_layout(
            barmode="group",
            title="Engagement by Campaign Step",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stats table
        st.dataframe(
            step_df[["step", "sent", "opened", "clicked", "bounced", "unsubscribed", "open_rate", "click_rate"]],
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
        total_sent = sum(s["sent"] for s in steps if s["step_num"] == 1)
        total_opened = sum(s["opened"] for s in steps)
        total_clicked = sum(s["clicked"] for s in steps)
        total_claimed = kpis["claimed"]

        funnel_data = pd.DataFrame({
            "stage": ["Emails Sent", "Opened", "Clicked", "Claimed"],
            "count": [total_sent, total_opened, total_clicked, total_claimed],
        })

        fig = px.funnel(funnel_data, x="count", y="stage", title="Email → Claim Conversion")
        fig.update_layout(height=350)
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
            title=f"Emails Sent per Day (Last {days} Days)",
            barmode="stack",
        )
        fig.update_layout(height=350)
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
