"""Coach Profiles — browse and search all discovered coaches.

Main management view with search, filters, pagination, and CSV export.
"""

import streamlit as st

st.set_page_config(page_title="Profiles | KLIQ Growth Engine", layout="wide")

from theme import inject_kliq_theme, sidebar_nav, render_status_badge, render_platform_badge

inject_kliq_theme()
sidebar_nav()

st.title("Coach Profiles")
st.markdown("Browse and search all discovered coaches across platforms.")

PAGE_SIZE = 50

try:
    from data import (
        get_all_niches,
        get_all_platforms,
        get_prospects_count,
        get_prospects_table,
    )

    # --- Filters ---
    col_search, col_platform, col_status, col_niche = st.columns([3, 2, 2, 2])

    with col_search:
        search = st.text_input(
            "Search",
            placeholder="Search by name or email...",
            label_visibility="collapsed",
        )

    with col_platform:
        try:
            platform_options = ["All Platforms"] + get_all_platforms()
        except Exception:
            platform_options = ["All Platforms", "youtube", "skool", "patreon", "website"]
        platform_filter = st.selectbox("Platform", platform_options, label_visibility="collapsed")

    with col_status:
        status_filter = st.selectbox(
            "Status",
            ["All Statuses", "DISCOVERED", "SCRAPED", "CONTENT_GENERATED",
             "STORE_CREATED", "EMAIL_SENT", "CLAIMED", "REJECTED"],
            label_visibility="collapsed",
        )

    with col_niche:
        try:
            niche_options = ["All Niches"] + get_all_niches()
        except Exception:
            niche_options = ["All Niches"]
        niche_filter = st.selectbox("Niche", niche_options, label_visibility="collapsed")

    # Resolve filter values
    search_val = search.strip() if search and search.strip() else None
    platform_val = None if platform_filter == "All Platforms" else platform_filter
    status_val = None if status_filter == "All Statuses" else status_filter
    niche_val = None if niche_filter == "All Niches" else niche_filter

    # Reset pagination when filters change
    filter_key = f"{search_val}|{platform_val}|{status_val}|{niche_val}"
    if st.session_state.get("_profiles_filter_key") != filter_key:
        st.session_state["_profiles_filter_key"] = filter_key
        st.session_state["profiles_page"] = 0

    if "profiles_page" not in st.session_state:
        st.session_state["profiles_page"] = 0

    # --- Count + Pagination ---
    total_count = get_prospects_count(
        status=status_val, platform=platform_val, niche=niche_val, search=search_val
    )
    total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = min(st.session_state["profiles_page"], total_pages - 1)
    offset = current_page * PAGE_SIZE

    # --- Header row ---
    col_info, col_export = st.columns([4, 1])
    with col_info:
        start = offset + 1 if total_count > 0 else 0
        end = min(offset + PAGE_SIZE, total_count)
        st.markdown(
            f'<p style="color:#667085;font-size:14px;margin:8px 0;">'
            f'Showing {start}–{end} of {total_count:,} coaches</p>',
            unsafe_allow_html=True,
        )

    # --- Load data ---
    prospects = get_prospects_table(
        status=status_val,
        platform=platform_val,
        niche=niche_val,
        search=search_val,
        limit=PAGE_SIZE,
        offset=offset,
    )

    # CSV export (of current filtered view)
    with col_export:
        if not prospects.empty:
            csv_data = prospects.to_csv(index=False).encode("utf-8")
            st.download_button("Export CSV", csv_data, "kliq_coaches.csv", "text/csv")

    # --- Table ---
    if not prospects.empty:
        st.dataframe(
            prospects,
            use_container_width=True,
            hide_index=True,
            height=min(len(prospects) * 38 + 40, 600),
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "avatar": st.column_config.ImageColumn("Photo", width="small"),
                "name": st.column_config.TextColumn("Name", width="medium"),
                "email": st.column_config.TextColumn("Email", width="medium"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "platform": st.column_config.TextColumn("Platform", width="small"),
                "platform_url": st.column_config.LinkColumn("Platform", display_text="Open", width="small"),
                "website": st.column_config.LinkColumn("Website", display_text="Open", width="small"),
                "instagram": st.column_config.LinkColumn("Instagram", display_text="Open", width="small"),
                "youtube": st.column_config.LinkColumn("YouTube", display_text="Open", width="small"),
                "tiktok": st.column_config.LinkColumn("TikTok", display_text="Open", width="small"),
                "twitter": st.column_config.LinkColumn("Twitter/X", display_text="Open", width="small"),
                "followers": st.column_config.NumberColumn("Followers", format="%d"),
                "subscribers": st.column_config.NumberColumn("Subscribers", format="%d"),
                "niches": st.column_config.TextColumn("Niches", width="medium"),
                "app_id": st.column_config.NumberColumn("App ID", width="small"),
                "store_url": st.column_config.LinkColumn("Store", display_text="Open", width="small"),
                "store_preview": st.column_config.LinkColumn("Preview", display_text="Preview", width="small"),
                "discovered": st.column_config.DateColumn("Discovered", format="MMM D, YYYY"),
                "claimed": st.column_config.DateColumn("Claimed", format="MMM D, YYYY"),
            },
        )

        # --- Pagination controls ---
        col_prev, col_page_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("< Previous", disabled=current_page == 0):
                st.session_state["profiles_page"] = current_page - 1
                st.rerun()
        with col_page_info:
            st.markdown(
                f'<p style="text-align:center;color:#667085;font-size:14px;padding-top:8px;">'
                f'Page {current_page + 1} of {total_pages}</p>',
                unsafe_allow_html=True,
            )
        with col_next:
            if st.button("Next >", disabled=current_page >= total_pages - 1):
                st.session_state["profiles_page"] = current_page + 1
                st.rerun()

        # --- Navigate to detail or store preview ---
        st.markdown("---")
        nav_left, nav_right = st.columns(2)

        with nav_left:
            st.markdown(
                '<p style="color:#667085;font-size:14px;">View full profile:</p>',
                unsafe_allow_html=True,
            )
            detail_id = st.number_input(
                "Profile ID",
                min_value=1,
                step=1,
                value=None,
                placeholder="Enter coach ID",
                label_visibility="collapsed",
                key="nav_detail_id",
            )
            if detail_id:
                st.session_state["selected_prospect_id"] = int(detail_id)
                st.switch_page("pages/profile_detail.py")

        with nav_right:
            st.markdown(
                '<p style="color:#667085;font-size:14px;">Preview webstore:</p>',
                unsafe_allow_html=True,
            )
            preview_id = st.number_input(
                "Preview ID",
                min_value=1,
                step=1,
                value=None,
                placeholder="Enter coach ID",
                label_visibility="collapsed",
                key="nav_preview_id",
            )
            if preview_id:
                st.query_params["id"] = str(int(preview_id))
                st.switch_page("pages/store_preview.py")
    else:
        st.info("No coaches match the selected filters.")

except Exception as e:
    st.error(f"Database connection error: {e}")
