"""LinkedIn Outreach — semi-automated LinkedIn connection + ICF email trigger."""

import os

import requests
import streamlit as st

st.set_page_config(page_title="LinkedIn Outreach | KLIQ", layout="wide")

from data import get_linkedin_queue, get_linkedin_stats  # noqa: E402
from theme import inject_kliq_theme, sidebar_nav  # noqa: E402

inject_kliq_theme()
sidebar_nav()

_app_base = os.getenv("APP_BASE_URL", "http://localhost:8000")
API_BASE = f"{_app_base}/api/linkedin"

st.title("LinkedIn Outreach")
st.caption("Semi-automated LinkedIn connection + ICF email trigger")

# ── Stats bar ──────────────────────────────────────────────────────────────────

stats = get_linkedin_stats()
cols = st.columns(7)
cols[0].metric("Queued", stats["queued"])
cols[1].metric("Copied", stats["copied"])
cols[2].metric("Sent", stats["sent"])
cols[3].metric("Accepted", stats["accepted"])
cols[4].metric("Declined", stats["declined"])
cols[5].metric("No Response", stats["no_response"])
cols[6].metric("Accept Rate", f"{stats['accept_rate']}%")

st.markdown("---")

# ── Filters ───────────────────────────────────────────────────────────────────

filter_col1, filter_col2, filter_col3 = st.columns([1, 2, 1])
with filter_col1:
    status_filter = st.selectbox(
        "Status",
        ["All", "QUEUED", "COPIED", "SENT", "ACCEPTED", "DECLINED", "NO_RESPONSE"],
        index=0,
    )
with filter_col2:
    search = st.text_input("Search by name or email", "")
with filter_col3:
    page_size = st.selectbox("Per page", [25, 50, 100], index=0)

status_val = None if status_filter == "All" else status_filter
search_val = search if search else None
df = get_linkedin_queue(status=status_val, search=search_val, limit=page_size)

# ── Connection note display (shown when a note is generated) ──────────────────

if "linkedin_note" not in st.session_state:
    st.session_state.linkedin_note = ""
if "linkedin_note_name" not in st.session_state:
    st.session_state.linkedin_note_name = ""
if "linkedin_note_url" not in st.session_state:
    st.session_state.linkedin_note_url = ""

if st.session_state.linkedin_note:
    st.success(f"Note generated for **{st.session_state.linkedin_note_name}**")
    st.code(st.session_state.linkedin_note, language=None)
    note_cols = st.columns(3)
    with note_cols[0]:
        li_url = st.session_state.linkedin_note_url
        if li_url:
            st.markdown(
                f'<a href="{li_url}" target="_blank" style="display:inline-block;'
                f"padding:6px 16px;background:#0A66C2;color:#fff;border-radius:8px;"
                f'font-weight:600;font-size:14px;text-decoration:none;">Open LinkedIn</a>',
                unsafe_allow_html=True,
            )
    with note_cols[1]:
        if st.button("Clear", key="clear_note"):
            st.session_state.linkedin_note = ""
            st.session_state.linkedin_note_name = ""
            st.session_state.linkedin_note_url = ""
            st.rerun()
    st.markdown("---")

# ── Prospect rows with inline actions ─────────────────────────────────────────

if df.empty:
    st.info("No prospects with LinkedIn URLs found.")
else:
    for idx, row in df.iterrows():
        pid = int(row["id"])
        name = row["name"] or ""
        email = row["email"] or ""
        linkedin_url = row["linkedin_url"] or ""
        status = row["outreach_status"] or "QUEUED"

        # Parse niches
        niches = row.get("niches")
        niche_str = ""
        if niches and isinstance(niches, list):
            niche_str = ", ".join(niches[:2])

        # Status badge
        status_colors = {
            "QUEUED": ("#344054", "#F2F4F7"),
            "COPIED": ("#B54708", "#FFFAEB"),
            "SENT": ("#175CD3", "#EFF8FF"),
            "ACCEPTED": ("#039855", "#ECFDF3"),
            "DECLINED": ("#D92D20", "#FEE4E2"),
            "NO_RESPONSE": ("#344054", "#F2F4F7"),
        }
        text_c, bg_c = status_colors.get(status, ("#344054", "#F2F4F7"))

        # Row layout
        row_cols = st.columns([2.5, 2.5, 1.5, 1, 1, 1, 1])

        # Name + LinkedIn link
        if linkedin_url:
            row_cols[0].markdown(
                f'**{name}** &nbsp; <a href="{linkedin_url}" target="_blank" '
                f'style="font-size:12px;color:#0A66C2;">LinkedIn</a>',
                unsafe_allow_html=True,
            )
        else:
            row_cols[0].markdown(f"**{name}**")

        row_cols[1].caption(email)
        row_cols[2].caption(niche_str)
        row_cols[3].markdown(
            f'<span style="padding:2px 8px;border-radius:9999px;font-size:11px;'
            f'font-weight:500;color:{text_c};background:{bg_c};">{status}</span>',
            unsafe_allow_html=True,
        )

        # Copy Note button
        with row_cols[4]:
            if st.button("Copy Note", key=f"copy_{pid}"):
                try:
                    resp = requests.post(f"{API_BASE}/{pid}/copy", timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.linkedin_note = data["connection_note"]
                        st.session_state.linkedin_note_name = data["prospect_name"]
                        st.session_state.linkedin_note_url = data["linkedin_url"]
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Error"))
                except requests.ConnectionError:
                    st.error("API offline")

        # Mark Sent button
        with row_cols[5]:
            if status in ("QUEUED", "COPIED"):
                if st.button("Sent", key=f"sent_{pid}"):
                    try:
                        resp = requests.patch(
                            f"{API_BASE}/{pid}/status",
                            json={"status": "SENT"},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.rerun()
                    except requests.ConnectionError:
                        st.error("API offline")

        # Accept button
        with row_cols[6]:
            if status == "SENT":
                if st.button("Accepted", key=f"acc_{pid}"):
                    try:
                        resp = requests.patch(
                            f"{API_BASE}/{pid}/status",
                            json={"status": "ACCEPTED"},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.rerun()
                    except requests.ConnectionError:
                        st.error("API offline")

    st.caption(f"Showing {len(df)} prospects")

st.markdown("---")

# ── Recent Acceptances ────────────────────────────────────────────────────────

st.subheader("Recent Acceptances")

accepted_df = get_linkedin_queue(status="ACCEPTED", limit=10)
if accepted_df.empty:
    st.caption("No accepted connections yet.")
else:
    for _, row in accepted_df.iterrows():
        acc_time = row["accepted_at"] or ""
        st.markdown(f"**{row['name']}** &nbsp; `ACCEPTED` &nbsp; {acc_time}")
