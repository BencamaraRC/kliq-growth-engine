"""LinkedIn Outreach — semi-automated LinkedIn connection + ICF email trigger."""

import os

import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="LinkedIn Outreach | KLIQ", layout="wide")

from data import get_calendly_stats, get_linkedin_queue, get_linkedin_stats  # noqa: E402
from theme import inject_kliq_theme, sidebar_nav  # noqa: E402

inject_kliq_theme()
sidebar_nav()

_app_base = os.getenv("APP_BASE_URL", "http://localhost:8000")
API_BASE = f"{_app_base}/api/linkedin"

st.title("LinkedIn Outreach")
st.caption("Semi-automated LinkedIn connection + ICF email trigger")

# ── Stats bar ──────────────────────────────────────────────────────────────────

stats = get_linkedin_stats()
cal_stats = get_calendly_stats()
cols = st.columns(9)
cols[0].metric("Queued", stats["queued"])
cols[1].metric("Copied", stats["copied"])
cols[2].metric("Sent", stats["sent"])
cols[3].metric("Accepted", stats["accepted"])
cols[4].metric("Declined", stats["declined"])
cols[5].metric("No Response", stats["no_response"])
cols[6].metric("Accept Rate", f"{stats['accept_rate']}%")
cols[7].metric("Booked Demo", cal_stats["booked_demo"])
cols[8].metric("Conversion Rate", f"{cal_stats['conversion_rate']}%")

st.markdown("---")

# ── Filters ───────────────────────────────────────────────────────────────────

filter_col1, filter_col2, filter_col3 = st.columns([1, 2, 1])
with filter_col1:
    status_filter = st.selectbox(
        "Status",
        ["All", "QUEUED", "COPIED", "SENT", "ACCEPTED", "DECLINED", "NO_RESPONSE", "BOOKED_DEMO"],
        index=0,
    )
with filter_col2:
    search = st.text_input("Search by name or email", "")
with filter_col3:
    page_size = st.selectbox("Per page", [25, 50, 100], index=0)

status_val = None if status_filter == "All" else status_filter
search_val = search if search else None
df = get_linkedin_queue(status=status_val, search=search_val, limit=page_size)

# ── Session state init ───────────────────────────────────────────────────────

for key in ("linkedin_note", "linkedin_note_name", "linkedin_note_url", "linkedin_open_url"):
    if key not in st.session_state:
        st.session_state[key] = ""
if "linkedin_note_pid" not in st.session_state:
    st.session_state.linkedin_note_pid = None

# ── Auto-open LinkedIn in new tab via JS ──────────────────────────────────────

if st.session_state.linkedin_open_url:
    url_to_open = st.session_state.linkedin_open_url
    st.session_state.linkedin_open_url = ""
    components.html(
        f'<script>window.open("{url_to_open}", "_blank");</script>',
        height=0,
    )

# ── Active note panel ────────────────────────────────────────────────────────

if st.session_state.linkedin_note:
    li_url = st.session_state.linkedin_note_url
    is_search_url = "linkedin.com/in/" not in (li_url or "")
    pid = st.session_state.linkedin_note_pid

    if is_search_url:
        st.warning(
            f"**{st.session_state.linkedin_note_name}** — No direct profile URL. "
            "Google search opened — click their LinkedIn profile, then paste the URL below to save it."
        )
    else:
        st.success(
            f"Note generated for **{st.session_state.linkedin_note_name}** — "
            "LinkedIn profile opened in new tab"
        )

    st.caption("Copy the note below and paste it into the LinkedIn connection request:")
    st.code(st.session_state.linkedin_note, language=None)

    # If search URL, show field to paste the real profile URL
    if is_search_url and pid:
        url_col1, url_col2 = st.columns([3, 1])
        with url_col1:
            new_url = st.text_input(
                "Paste real LinkedIn profile URL (linkedin.com/in/...)",
                key="new_linkedin_url",
                placeholder="https://www.linkedin.com/in/their-profile",
            )
        with url_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Save URL", key="save_url"):
                if new_url and "linkedin.com/in/" in new_url:
                    try:
                        resp = requests.patch(
                            f"{API_BASE}/{pid}/url",
                            json={"linkedin_url": new_url},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.session_state.linkedin_note_url = new_url
                            st.session_state.linkedin_open_url = new_url
                            st.rerun()
                    except requests.ConnectionError:
                        st.error("API offline")
                else:
                    st.error("Please paste a valid linkedin.com/in/ URL")

    action_cols = st.columns(4)
    with action_cols[0]:
        if li_url:
            st.markdown(
                f'<a href="{li_url}" target="_blank" style="display:inline-block;'
                f"padding:6px 16px;background:#0A66C2;color:#fff;border-radius:8px;"
                f'font-weight:600;font-size:14px;text-decoration:none;">Open LinkedIn</a>',
                unsafe_allow_html=True,
            )
    with action_cols[1]:
        if st.button("Mark as Sent", key="mark_sent_top"):
            try:
                if pid:
                    requests.patch(f"{API_BASE}/{pid}/status", json={"status": "SENT"}, timeout=10)
                st.session_state.linkedin_note = ""
                st.session_state.linkedin_note_name = ""
                st.session_state.linkedin_note_url = ""
                st.rerun()
            except requests.ConnectionError:
                st.error("API offline")
    with action_cols[2]:
        if st.button("Clear", key="clear_note"):
            st.session_state.linkedin_note = ""
            st.session_state.linkedin_note_name = ""
            st.session_state.linkedin_note_url = ""
            st.rerun()
    st.markdown("---")

# ── Prospect rows ─────────────────────────────────────────────────────────────

if df.empty:
    st.info("No prospects with LinkedIn URLs found.")
else:
    for idx, row in df.iterrows():
        pid = int(row["id"])
        name = row["name"] or ""
        email = row["email"] or ""
        linkedin_url = row["linkedin_url"] or ""
        status = row["outreach_status"] or "QUEUED"
        is_direct = "linkedin.com/in/" in linkedin_url

        niches = row.get("niches")
        niche_str = ""
        if niches and isinstance(niches, list):
            niche_str = ", ".join(niches[:2])

        status_colors = {
            "QUEUED": ("#344054", "#F2F4F7"),
            "COPIED": ("#B54708", "#FFFAEB"),
            "SENT": ("#175CD3", "#EFF8FF"),
            "ACCEPTED": ("#039855", "#ECFDF3"),
            "DECLINED": ("#D92D20", "#FEE4E2"),
            "NO_RESPONSE": ("#344054", "#F2F4F7"),
            "BOOKED_DEMO": ("#7C3AED", "#F3E8FF"),
        }
        text_c, bg_c = status_colors.get(status, ("#344054", "#F2F4F7"))

        row_cols = st.columns([2.5, 2.5, 1.5, 1, 1, 1, 1])

        # Name + LinkedIn indicator
        link_icon = "Profile" if is_direct else "Find"
        link_color = "#039855" if is_direct else "#B54708"
        if linkedin_url:
            row_cols[0].markdown(
                f'**{name}** &nbsp; <a href="{linkedin_url}" target="_blank" '
                f'style="font-size:11px;color:{link_color};">{link_icon}</a>',
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

        with row_cols[4]:
            if st.button("Copy Note", key=f"copy_{pid}"):
                try:
                    resp = requests.post(f"{API_BASE}/{pid}/copy", timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.linkedin_note = data["connection_note"]
                        st.session_state.linkedin_note_name = data["prospect_name"]
                        st.session_state.linkedin_note_url = data["linkedin_url"]
                        st.session_state.linkedin_note_pid = pid
                        st.session_state.linkedin_open_url = data["linkedin_url"]
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Error"))
                except requests.ConnectionError:
                    st.error("API offline")

        with row_cols[5]:
            if status in ("QUEUED", "COPIED"):
                if st.button("Sent", key=f"sent_{pid}"):
                    try:
                        requests.patch(f"{API_BASE}/{pid}/status", json={"status": "SENT"}, timeout=10)
                        st.rerun()
                    except requests.ConnectionError:
                        st.error("API offline")

        with row_cols[6]:
            if status == "SENT":
                if st.button("Accepted", key=f"acc_{pid}"):
                    try:
                        requests.patch(f"{API_BASE}/{pid}/status", json={"status": "ACCEPTED"}, timeout=10)
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
