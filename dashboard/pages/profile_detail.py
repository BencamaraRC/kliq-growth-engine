"""Profile Detail — full coach profile with scraped content, AI content, pricing, email history.

Accessed from the Profiles page by entering a prospect ID.
"""

import json

import streamlit as st

st.set_page_config(page_title="Profile Detail | KLIQ Growth Engine", layout="wide")

from theme import (  # noqa: E402
    inject_kliq_theme,
    render_brand_colors,
    render_niche_tags,
    render_platform_badge,
    render_status_badge,
    sidebar_nav,
)

inject_kliq_theme()
sidebar_nav()

# --- Get prospect ID ---
prospect_id = st.session_state.get("selected_prospect_id")
query_id = st.query_params.get("id")
if query_id:
    prospect_id = int(query_id)

if not prospect_id:
    st.title("Profile Detail")
    st.info("No coach selected. Go to **Profiles** and enter an ID to view details.")
    if st.button("Go to Profiles"):
        st.switch_page("pages/profiles.py")
    st.stop()

try:
    from data import get_prospect_detail

    detail = get_prospect_detail(int(prospect_id))

    if not detail:
        st.title("Profile Detail")
        st.warning(f"Prospect #{prospect_id} not found.")
        if st.button("Back to Profiles"):
            st.switch_page("pages/profiles.py")
        st.stop()

    # --- Top bar: Back + Delete ---
    top_left, top_right = st.columns([4, 1])
    with top_left:
        if st.button("< Back to Profiles"):
            st.switch_page("pages/profiles.py")
    with top_right:
        if detail.get("status", "").upper() != "REJECTED":
            if st.button("Delete", icon=":material/close:", type="secondary", key="delete_prospect"):
                st.session_state["confirm_delete_prospect"] = True

    # Confirmation dialog
    if st.session_state.get("confirm_delete_prospect"):
        st.warning(
            f'Are you sure you want to remove **{detail.get("name")}**? '
            "This will set their status to REJECTED, stop all email sequences, "
            "and exclude them from future scraping."
        )
        confirm_col1, confirm_col2, _ = st.columns([1, 1, 4])
        with confirm_col1:
            if st.button("Yes, remove", key="confirm_delete_yes"):
                from data import engine
                from sqlalchemy import text as sql_text
                with engine.connect() as conn:
                    conn.execute(
                        sql_text("UPDATE prospects SET status = 'REJECTED', updated_at = NOW() WHERE id = :id"),
                        {"id": int(prospect_id)},
                    )
                    conn.commit()
                st.session_state["confirm_delete_prospect"] = False
                st.success(f"{detail.get('name')} has been removed.")
                st.rerun()
        with confirm_col2:
            if st.button("Cancel", key="confirm_delete_no"):
                st.session_state["confirm_delete_prospect"] = False
                st.rerun()

    # --- Header ---
    st.markdown(
        f'<h1 style="margin-bottom:4px;">{detail.get("name", "Unknown Coach")}</h1>',
        unsafe_allow_html=True,
    )

    # Status + platform badges
    badges = render_status_badge(detail.get("status", "discovered"))
    badges += " " + render_platform_badge(detail.get("primary_platform", ""))
    st.markdown(badges, unsafe_allow_html=True)
    st.markdown("")

    # --- Two-column layout ---
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Email
        email = detail.get("email")
        if email:
            st.markdown(f"**Email:** {email}")

        # Platform URL
        url = detail.get("primary_platform_url") or detail.get("website_url")
        if url:
            st.markdown(f"**URL:** [{url}]({url})")

        # Bio
        bio = detail.get("bio")
        if bio:
            st.markdown("**Bio:**")
            st.markdown(
                f'<p style="color:#4D5761;font-size:14px;line-height:1.6;">{bio[:500]}{"..." if len(bio) > 500 else ""}</p>',
                unsafe_allow_html=True,
            )

        # Niche tags
        tags = detail.get("niche_tags")
        if tags:
            st.markdown("**Niches:**")
            st.markdown(render_niche_tags(tags), unsafe_allow_html=True)

        # Brand colors
        colors = detail.get("brand_colors")
        if colors:
            st.markdown("**Brand Colors:**")
            st.markdown(render_brand_colors(colors), unsafe_allow_html=True)

        # Social links
        social = detail.get("social_links")
        if social and isinstance(social, dict):
            st.markdown("**Social Links:**")
            links = []
            for platform_name, link_url in social.items():
                links.append(f"[{platform_name}]({link_url})")
            st.markdown(" | ".join(links))

    with col_right:
        # Metrics
        st.markdown("**Metrics**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Followers", f"{detail.get('follower_count', 0):,}")
        m2.metric("Subscribers", f"{detail.get('subscriber_count', 0):,}")
        m3.metric("Content", f"{detail.get('content_count', 0):,}")

        # KLIQ Store
        store_url = detail.get("kliq_store_url")
        app_id = detail.get("kliq_application_id")
        if store_url or app_id:
            st.markdown("**KLIQ Store**")
            if store_url:
                st.markdown(f"[{store_url}]({store_url})")
            if app_id:
                st.markdown(f"App ID: `{app_id}`")

        # Timestamps
        st.markdown("**Timeline**")
        ts_data = {
            "Discovered": detail.get("discovered_at"),
            "Store Created": detail.get("store_created_at"),
            "Claimed": detail.get("claimed_at"),
        }
        for label, ts in ts_data.items():
            if ts:
                st.markdown(f"- {label}: {str(ts)[:10]}")

    st.markdown("---")

    # --- Tabbed content sections ---
    tabs = st.tabs(
        ["Scraped Content", "AI-Generated Content", "Pricing", "Cross-Platform", "Email History"]
    )

    # Tab 1: Scraped Content
    with tabs[0]:
        content_items = detail.get("scraped_content", [])
        if content_items:
            st.markdown(
                f"**{len(content_items)} content pieces** scraped from {detail.get('primary_platform', 'platform')}"
            )
            for item in content_items[:20]:
                title = item.get("title") or "Untitled"
                content_type = item.get("content_type", "content")
                views = item.get("view_count", 0)
                item_url = item.get("url", "")

                with st.expander(f"{content_type.title()}: {title} ({views:,} views)"):
                    if item_url:
                        st.markdown(f"**URL:** [{item_url}]({item_url})")
                    st.markdown(
                        f"**Views:** {views:,} | **Engagement:** {item.get('engagement_count', 0):,}"
                    )
                    if item.get("published_at"):
                        st.markdown(f"**Published:** {str(item['published_at'])[:10]}")
                    if item.get("tags"):
                        st.markdown(
                            f"**Tags:** {', '.join(item['tags']) if isinstance(item['tags'], list) else item['tags']}"
                        )
                    body = item.get("body")
                    if body:
                        st.text(str(body)[:800])

            if len(content_items) > 20:
                st.caption(f"Showing 20 of {len(content_items)} items.")
        else:
            st.info("No scraped content for this coach.")

    # Tab 2: AI-Generated Content
    with tabs[1]:
        generated = detail.get("generated_content", [])
        if generated:
            # Group by content_type
            by_type = {}
            for g in generated:
                ct = g.get("content_type", "other")
                by_type.setdefault(ct, []).append(g)

            for content_type, items in by_type.items():
                st.subheader(content_type.replace("_", " ").title())
                for item in items:
                    title = item.get("title") or content_type.title()
                    body = item.get("body")

                    with st.expander(title):
                        if body:
                            # Try to parse as JSON for structured content
                            try:
                                parsed = json.loads(body) if isinstance(body, str) else body
                                if isinstance(parsed, dict):
                                    for k, v in parsed.items():
                                        if isinstance(v, list):
                                            st.markdown(
                                                f"**{k.replace('_', ' ').title()}:** {', '.join(str(x) for x in v)}"
                                            )
                                        elif isinstance(v, str) and len(v) > 200:
                                            st.markdown(f"**{k.replace('_', ' ').title()}:**")
                                            st.markdown(v[:500])
                                        else:
                                            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                                else:
                                    st.text(str(parsed)[:800])
                            except (json.JSONDecodeError, TypeError):
                                st.text(str(body)[:800])
        else:
            st.info("No AI-generated content for this coach.")

    # Tab 3: Pricing
    with tabs[2]:
        pricing = detail.get("scraped_pricing", [])
        if pricing:
            st.markdown(f"**{len(pricing)} pricing tiers** discovered")
            for tier in pricing:
                name = tier.get("tier_name") or tier.get("name", "Unnamed Tier")
                price = tier.get("price_amount", 0)
                interval = tier.get("interval", "")
                platform = tier.get("platform", "")

                with st.expander(f"{name} — ${price / 100:.2f}/{interval}" if price else name):
                    st.markdown(f"**Platform:** {platform}")
                    st.markdown(f"**Price:** ${price / 100:.2f}" if price else "**Price:** Free")
                    if interval:
                        st.markdown(f"**Interval:** {interval}")
                    desc = tier.get("description")
                    if desc:
                        st.markdown(f"**Description:** {desc}")
                    benefits = tier.get("benefits")
                    if benefits and isinstance(benefits, list):
                        st.markdown("**Benefits:**")
                        for b in benefits:
                            st.markdown(f"- {b}")
                    members = tier.get("member_count")
                    if members:
                        st.markdown(f"**Members:** {members:,}")
        else:
            st.info("No pricing data scraped for this coach.")

    # Tab 4: Cross-Platform Profiles
    with tabs[3]:
        profiles = detail.get("platform_profiles", [])
        if profiles:
            st.markdown(f"**{len(profiles)} platform profiles** linked")
            for pp in profiles:
                platform = pp.get("platform", "unknown")
                pid = pp.get("platform_id", "")
                purl = pp.get("platform_url", "")
                badge = render_platform_badge(platform)
                link = f" — [{purl}]({purl})" if purl else ""
                st.markdown(f"{badge} `{pid}`{link}", unsafe_allow_html=True)
        else:
            st.info("No cross-platform profiles linked.")

    # Tab 5: Email History
    with tabs[4]:
        events = detail.get("campaign_events", [])
        if events:
            step_names = {
                1: "Store Ready",
                2: "Reminder 1",
                3: "Reminder 2",
                4: "Claimed Confirmation",
            }
            st.markdown(f"**{len(events)} email events**")
            for event in events:
                step = step_names.get(event.get("step"), f"Step {event.get('step')}")
                email_status = event.get("email_status", "unknown")
                sent_at = event.get("sent_at")
                opened_at = event.get("opened_at")
                clicked_at = event.get("clicked_at")

                badge = (
                    render_status_badge(email_status)
                    if email_status in ("claimed", "rejected")
                    else (
                        f'<span style="display:inline-block;padding:2px 10px;border-radius:9999px;'
                        f'font-size:12px;font-weight:500;color:#344054;background:#F2F4F7;">{email_status}</span>'
                    )
                )

                timeline = f"Sent: {str(sent_at)[:16]}" if sent_at else ""
                if opened_at:
                    timeline += f" | Opened: {str(opened_at)[:16]}"
                if clicked_at:
                    timeline += f" | Clicked: {str(clicked_at)[:16]}"

                st.markdown(
                    f"**{step}** {badge}<br>"
                    f'<span style="color:#667085;font-size:13px;">{timeline}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown("")
        else:
            st.info("No email outreach sent to this coach yet.")

except Exception as e:
    st.error(f"Database connection error: {e}")
