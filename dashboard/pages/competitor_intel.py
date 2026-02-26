"""Competitor Intelligence — browse and analyze discovered coaches.

Shows:
- Searchable/filterable prospect table
- Niche tag distribution
- Platform comparison
- Detailed prospect view with cross-platform data
"""

import streamlit as st

st.set_page_config(page_title="Competitor Intel | KLIQ Growth Engine", layout="wide")

st.title("Competitor Intelligence")
st.markdown("Browse coaches discovered across YouTube, Skool, Patreon, and websites.")

try:
    from data import (
        get_niche_distribution,
        get_platform_breakdown,
        get_prospect_detail,
        get_prospects_table,
    )

    # --- Filters ---
    col1, col2, col3 = st.columns(3)
    with col1:
        platform_filter = st.selectbox(
            "Platform",
            ["All", "youtube", "skool", "patreon", "website"],
        )
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "discovered", "scraped", "content_generated", "store_created", "email_sent", "claimed"],
        )
    with col3:
        niche_search = st.text_input("Search niche tag", placeholder="e.g. fitness, yoga")

    platform_val = None if platform_filter == "All" else platform_filter
    status_val = None if status_filter == "All" else status_filter
    niche_val = niche_search.strip() if niche_search.strip() else None

    # --- Prospects Table ---
    st.subheader("Discovered Coaches")
    prospects = get_prospects_table(
        status=status_val,
        platform=platform_val,
        niche=niche_val,
        limit=100,
    )

    if not prospects.empty:
        st.dataframe(
            prospects,
            use_container_width=True,
            hide_index=True,
            column_config={
                "store_url": st.column_config.LinkColumn("Store URL"),
                "followers": st.column_config.NumberColumn("Followers", format="%d"),
                "subscribers": st.column_config.NumberColumn("Subscribers", format="%d"),
            },
        )

        # --- Prospect Detail ---
        st.subheader("Prospect Detail")
        prospect_id = st.number_input(
            "Enter Prospect ID to view details",
            min_value=1,
            step=1,
            value=None,
            placeholder="Select a prospect ID from the table above",
        )

        if prospect_id:
            detail = get_prospect_detail(int(prospect_id))
            if detail:
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown(f"### {detail['name']}")
                    st.markdown(f"**Email:** {detail.get('email', 'N/A')}")
                    st.markdown(f"**Platform:** {detail['primary_platform']}")
                    st.markdown(f"**Status:** {detail['status']}")
                    st.markdown(f"**Bio:** {detail.get('bio', 'N/A')[:300]}")
                    if detail.get("niche_tags"):
                        tags = detail["niche_tags"]
                        if isinstance(tags, list):
                            st.markdown(f"**Niches:** {', '.join(tags)}")
                    if detail.get("social_links"):
                        st.markdown("**Social Links:**")
                        links = detail["social_links"]
                        if isinstance(links, dict):
                            for platform_name, url in links.items():
                                st.markdown(f"  - {platform_name}: {url}")

                with col_b:
                    st.markdown("**Metrics:**")
                    st.metric("Followers", detail.get("follower_count", 0))
                    st.metric("Subscribers", detail.get("subscriber_count", 0))
                    st.metric("Content Pieces", detail.get("content_count", 0))

                    if detail.get("kliq_store_url"):
                        st.markdown(f"**KLIQ Store:** [{detail['kliq_store_url']}]({detail['kliq_store_url']})")
                    if detail.get("brand_colors"):
                        st.markdown("**Brand Colors:**")
                        colors = detail["brand_colors"]
                        if isinstance(colors, list):
                            color_html = " ".join(
                                f'<span style="background:#{c};width:30px;height:30px;display:inline-block;border-radius:4px;margin:2px"></span>'
                                for c in colors[:5]
                            )
                            st.markdown(color_html, unsafe_allow_html=True)

                # Cross-platform profiles
                if detail.get("platform_profiles"):
                    st.subheader("Cross-Platform Profiles")
                    for pp in detail["platform_profiles"]:
                        st.markdown(f"- **{pp['platform']}** ({pp['platform_id']})")

                # Scraped content
                if detail.get("scraped_content"):
                    st.subheader("Scraped Content")
                    for content in detail["scraped_content"][:10]:
                        with st.expander(f"{content.get('content_type', 'content')}: {content.get('title', 'Untitled')}"):
                            st.markdown(f"**Views:** {content.get('view_count', 0)}")
                            if content.get("url"):
                                st.markdown(f"**URL:** {content['url']}")
                            if content.get("body"):
                                st.text(content["body"][:500])

                # Campaign events
                if detail.get("campaign_events"):
                    st.subheader("Email History")
                    step_names = {1: "Store Ready", 2: "Reminder 1", 3: "Reminder 2", 4: "Claimed"}
                    for event in detail["campaign_events"]:
                        step = step_names.get(event.get("step"), f"Step {event.get('step')}")
                        status = event.get("email_status", "unknown")
                        sent = event.get("sent_at", "N/A")
                        st.markdown(f"- **{step}** — {status} (sent: {sent})")
            else:
                st.warning(f"Prospect #{prospect_id} not found.")
    else:
        st.info("No prospects match the selected filters.")

    # --- Analytics ---
    st.markdown("---")
    col_x, col_y = st.columns(2)

    with col_x:
        st.subheader("Niche Distribution")
        niches = get_niche_distribution()
        if not niches.empty:
            import plotly.express as px

            fig = px.bar(
                niches.head(15),
                x="count",
                y="niche",
                orientation="h",
                title="Top 15 Niche Tags",
            )
            fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    with col_y:
        st.subheader("Platform Distribution")
        platforms = get_platform_breakdown()
        if not platforms.empty:
            import plotly.express as px

            fig = px.pie(
                platforms,
                values="count",
                names="platform",
                title="Coaches by Platform",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Database connection error: {e}")
