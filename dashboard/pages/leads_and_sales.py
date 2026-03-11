"""Leads & Sales — MRR dashboard with KLIQ fees, hosting fees, and per-coach breakdown."""

import streamlit as st

st.set_page_config(page_title="Leads & Sales | KLIQ", layout="wide")

from datetime import datetime  # noqa: E402

import plotly.graph_objects as go  # noqa: E402
from data import (  # noqa: E402
    get_monthly_hosting_fees,
    get_monthly_kliq_fees,
    get_mrr_trend,
    get_revenue_by_coach,
)
from theme import PLOTLY_LAYOUT, apply_plotly_theme, inject_kliq_theme, sidebar_nav  # noqa: E402

inject_kliq_theme()
sidebar_nav()

st.title("Leads & Sales")
st.caption("Monthly Recurring Revenue — KLIQ platform fees + coach hosting subscriptions")

# ── Calendar month date slicer ───────────────────────────────────────────────

now = datetime.utcnow()
# Build month options (last 24 months)
month_options = []
for i in range(24):
    y = now.year
    m = now.month - i
    while m <= 0:
        m += 12
        y -= 1
    month_options.append((y, m, f"{datetime(y, m, 1):%B %Y}"))

slicer_col, _ = st.columns([1, 3])
with slicer_col:
    selected_label = st.selectbox(
        "Month",
        [opt[2] for opt in month_options],
        index=0,
    )

selected = next(opt for opt in month_options if opt[2] == selected_label)
sel_year, sel_month = selected[0], selected[1]

# ── MRR metric cards ─────────────────────────────────────────────────────────

kliq_data = get_monthly_kliq_fees(sel_year, sel_month)
hosting_data = get_monthly_hosting_fees(sel_year, sel_month)
mrr = kliq_data["kliq_fees"] + hosting_data["hosting_fees"]

card_cols = st.columns(4)
card_cols[0].metric("MRR", f"${mrr:,.2f}")
card_cols[1].metric("KLIQ Fees", f"${kliq_data['kliq_fees']:,.2f}")
card_cols[2].metric("Hosting Fees", f"${hosting_data['hosting_fees']:,.2f}")
card_cols[3].metric("GMV", f"${kliq_data['gmv']:,.2f}")

st.markdown("")

detail_cols = st.columns(2)
detail_cols[0].metric("Active Coaches (with revenue)", kliq_data["active_coaches"])
detail_cols[1].metric("Active Hosting Subscriptions", hosting_data["active_subscriptions"])

st.markdown("---")

# ── MRR trend chart ──────────────────────────────────────────────────────────

st.subheader("MRR Trend")

trend_df = get_mrr_trend(months=12)

if not trend_df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_df["month"],
        y=trend_df["mrr"],
        name="MRR",
        mode="lines+markers",
        line=dict(color="#1C3838", width=3),
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["month"],
        y=trend_df["kliq_fees"],
        name="KLIQ Fees",
        mode="lines",
        line=dict(color="#39938F", width=2, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["month"],
        y=trend_df["hosting_fees"],
        name="Hosting Fees",
        mode="lines",
        line=dict(color="#FF9F88", width=2, dash="dot"),
    ))
    fig.update_layout(
        yaxis_title="Revenue ($)",
        xaxis_title="Month",
        hovermode="x unified",
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No revenue data available yet.")

st.markdown("---")

# ── Per-coach revenue table ──────────────────────────────────────────────────

st.subheader(f"Revenue by Coach — {selected_label}")

coach_df = get_revenue_by_coach(sel_year, sel_month)

if not coach_df.empty:
    # Format currency columns
    display_df = coach_df.copy()
    display_df["kliq_fees"] = display_df["kliq_fees"].apply(lambda x: f"${x:,.2f}")
    display_df["gmv"] = display_df["gmv"].apply(lambda x: f"${x:,.2f}")
    display_df.columns = ["App ID", "Coach", "KLIQ Fees", "GMV", "Invoices"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "App ID": st.column_config.NumberColumn(width="small"),
            "Invoices": st.column_config.NumberColumn(width="small"),
        },
    )
    st.caption(f"{len(coach_df)} coaches with revenue in {selected_label}")
else:
    st.info(f"No coach revenue data for {selected_label}.")
