"""CMS Admin — mockup of what admin.joinkliq.io would show for a claimed store.

Proves that Growth Engine data (prospects + AI-generated content) maps correctly
into every CMS table. Reads from Growth Engine PostgreSQL only — does NOT connect
to CMS MySQL. Applies the same mapping logic as store_builder.py to simulate output.
"""

import json
import uuid

import streamlit as st

st.set_page_config(page_title="CMS Admin | KLIQ Growth Engine", layout="wide")

from theme import inject_kliq_theme, sidebar_nav  # noqa: E402

inject_kliq_theme()
sidebar_nav()

st.markdown("#### CMS Admin Preview")
st.caption(
    "Simulates what admin.joinkliq.io would show when a store is created. "
    "Data is read from the Growth Engine DB and mapped using the same logic as the CMS store builder."
)

try:
    from data import engine
    from sqlalchemy import text

    # --- Select a prospect with generated content ---
    with engine.connect() as conn:
        prospects = conn.execute(
            text("""
                SELECT p.id, p.name, p.email, p.primary_platform, p.status,
                       p.profile_image_url, p.first_name, p.last_name,
                       p.niche_tags, p.brand_colors, p.bio, p.website_url
                FROM prospects p
                ORDER BY p.name
            """)
        ).fetchall()

    if not prospects:
        st.info("No prospects yet. Run discovery first.")
        st.stop()

    options = {f"{p[1]} ({p[3]}) — {p[4]}": p[0] for p in prospects}
    selected = st.selectbox("Select a coach", list(options.keys()))
    prospect_id = options[selected]

    # Find the prospect row
    prospect = None
    for p in prospects:
        if p[0] == prospect_id:
            prospect = p
            break

    p_id, p_name, p_email, p_platform, p_status = prospect[0], prospect[1], prospect[2], prospect[3], prospect[4]
    p_image, p_first, p_last = prospect[5], prospect[6], prospect[7]
    p_niche = prospect[8]
    p_brand_colors = prospect[9]
    p_bio = prospect[10]
    p_website = prospect[11]

    first_name = p_first or (p_name.split()[0] if p_name else "Coach")
    last_name = p_last or (p_name.split()[1] if p_name and len(p_name.split()) > 1 else "")
    coach_name = p_name or f"{first_name} {last_name}"
    email = p_email or f"unclaimed-{p_id}@joinkliq.io"
    store_slug = p_name.lower().replace(" ", "-").replace(".", "")[:30] if p_name else f"coach-{p_id}"

    # Load generated content
    with engine.connect() as conn:
        generated = conn.execute(
            text("SELECT * FROM generated_content WHERE prospect_id = :id"),
            {"id": prospect_id},
        ).fetchall()

    gen_by_type = {}
    for g in generated:
        mapping = g._mapping
        ct = mapping.get("content_type", "")
        if ct not in gen_by_type:
            gen_by_type[ct] = []
        gen_by_type[ct].append(mapping)

    # Parse generated content
    bio_data = {}
    if "bio" in gen_by_type:
        try:
            bio_data = json.loads(gen_by_type["bio"][0].get("body", "{}"))
        except (json.JSONDecodeError, IndexError):
            pass

    seo_data = {}
    if "seo" in gen_by_type:
        try:
            seo_data = json.loads(gen_by_type["seo"][0].get("body", "{}"))
        except (json.JSONDecodeError, IndexError):
            pass

    colors_data = {}
    if "colors" in gen_by_type:
        try:
            colors_data = json.loads(gen_by_type["colors"][0].get("body", "{}"))
        except (json.JSONDecodeError, IndexError):
            pass

    product_records = gen_by_type.get("product", [])
    blog_records = gen_by_type.get("blog", [])

    # --- Build simulated CMS data ---
    app_id = 1000 + p_id  # Simulated application ID
    guid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"kliq-{p_id}"))

    # Color mapping (replicates store_builder._build_colors)
    primary = colors_data.get("primary", "#1E81FF").lstrip("#")
    secondary = colors_data.get("secondary", "#1A74E5").lstrip("#")
    accent = colors_data.get("accent", "#1E81FF").lstrip("#")
    bg = colors_data.get("background", "#FFFFFF").lstrip("#")
    text_color = colors_data.get("text", "#1A1A1A").lstrip("#")

    def is_dark(hex_color):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return False
        r, g_, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (0.299 * r + 0.587 * g_ + 0.114 * b) < 128

    on_primary = "FFFFFF" if is_dark(primary) else "1A1A1A"
    on_secondary = "FFFFFF" if is_dark(secondary) else "1A1A1A"

    # ═══════════════════════════════════════════════════════════════════════════
    # TABS
    # ═══════════════════════════════════════════════════════════════════════════

    tabs = st.tabs([
        "Application",
        "Settings",
        "Brand Colors",
        "Coach User",
        "Products",
        "Pages",
        "Features",
    ])

    # ── Tab: Application ──────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("##### `applications` table")
        st.caption("The core store record. Created with status=1 (Draft), activated to status=2 on claim.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Field**")
            for field in ["id", "guid", "name", "email", "status_id", "currency_id", "created_by"]:
                st.code(field, language=None)
        with col2:
            st.markdown("**Value**")
            values = [
                str(app_id),
                guid,
                p_name or "—",
                email,
                "1 (Draft) → 2 (Active on claim)",
                "2 (USD)",
                "1 (Super Admin)",
            ]
            for v in values:
                st.code(v, language=None)

    # ── Tab: Settings ─────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("##### `application_settings` table")

        st.markdown("**Naming & Branding**")
        settings_naming = {
            "app_name": p_name or "—",
            "coach_name": coach_name,
            "web_url": f"https://{seo_data.get('store_slug', store_slug)}.joinkliq.io",
            "support_email": email,
            "profile_placeholder": p_image or "—",
        }
        for k, v in settings_naming.items():
            c1, c2 = st.columns([1, 3])
            c1.code(k, language=None)
            c2.markdown(f"`{v}`")

        st.markdown("**SEO**")
        seo_fields = {
            "meta_title": seo_data.get("seo_title", "—"),
            "meta_description": seo_data.get("seo_description", "—"),
            "meta_keywords": ", ".join(seo_data.get("seo_keywords", [])) or "—",
        }
        for k, v in seo_fields.items():
            c1, c2 = st.columns([1, 3])
            c1.code(k, language=None)
            c2.markdown(f"{v[:120]}{'...' if len(str(v)) > 120 else ''}")

        st.markdown("**Tab Labels**")
        tab_labels = {
            "tab_home_text": "Home",
            "tab_library_text": "Library",
            "tab_community_text": "Community",
            "tab_shop_text": "Shop",
            "tab_account_text": "Account",
            "tab_wellness_text": "Wellness",
        }
        cols = st.columns(6)
        for i, (k, v) in enumerate(tab_labels.items()):
            with cols[i]:
                st.caption(k.replace("tab_", "").replace("_text", ""))
                st.markdown(f"**{v}**")

    # ── Tab: Brand Colors ─────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("##### `application_colors` table")
        st.caption("30+ color fields applied across the entire branded app.")

        color_groups = {
            "Core": {
                "primary": primary,
                "on_primary": on_primary,
                "secondary": secondary,
                "on_secondary": on_secondary,
                "button_primary": primary,
                "button_secondary": secondary,
                "on_button": on_primary,
                "progress": primary,
            },
            "Theme": {
                "theme": primary,
                "on_theme": on_primary,
                "tab_dark_active": primary,
                "tab_light_active": primary,
            },
            "Sections": {
                "session_primary": primary,
                "session_secondary": secondary,
                "library_primary": secondary,
                "library_secondary": accent,
                "nutrition_primary": accent,
                "nutrition_secondary": primary,
                "wellness_primary": primary,
                "wellness_secondary": accent,
            },
            "Text on Sections": {
                "on_session": on_primary,
                "on_library": on_secondary,
                "on_nutrition": on_primary,
                "on_wellness": on_primary,
            },
            "App Chrome": {
                "appbar": primary,
                "on_appbar": on_primary,
                "background": bg,
                "dark_background": "121212",
                "on_background": text_color,
                "on_dark_background": "FFFFFF",
                "bottom_tab_bg": bg,
                "on_bottom_tab": text_color,
            },
            "Tags & Overlays": {
                "tags": accent,
                "on_tags": on_primary,
                "session_overlay": primary,
                "library_overlay": secondary,
                "nutrition_overlay": accent,
                "wellness_overlay": primary,
            },
            "Program": {
                "program_primary": primary,
                "program_secondary": secondary,
                "on_program": on_primary,
                "program_overlay": primary,
            },
        }

        for group_name, colors in color_groups.items():
            st.markdown(f"**{group_name}**")
            cols = st.columns(min(len(colors), 4))
            for i, (name, hex_val) in enumerate(colors.items()):
                with cols[i % 4]:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
                        f'<div style="width:24px;height:24px;border-radius:50%;background:#{hex_val};'
                        f'border:1px solid #ddd;flex-shrink:0;"></div>'
                        f'<span style="font-size:12px;font-family:monospace;">{name}<br/>#{hex_val}</span>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            st.markdown("")

    # ── Tab: Coach User ───────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("##### `users` table")
        st.caption("Coach admin account. Created as Draft, activated on claim when password is set.")

        if p_image:
            st.image(p_image, width=80)

        user_fields = {
            "first_name": first_name,
            "last_name": last_name or "—",
            "email": email,
            "password": "bcrypt($temp_password) → bcrypt($coach_password) on claim",
            "user_type": "3 (Coach Admin)",
            "status_id": "1 (Draft) → 2 (Active on claim)",
            "photo_url": p_image or "—",
            "is_email_verified": "False → True on claim",
            "auto_login_token": "Generated on claim (30-min expiry)",
        }
        for k, v in user_fields.items():
            c1, c2 = st.columns([1, 3])
            c1.code(k, language=None)
            c2.markdown(f"`{v}`")

        st.markdown("---")
        st.markdown("**Related tables created:**")
        st.markdown(
            "- `user_details` — profile metadata (address, gender, weight, height)\n"
            "- `user_roles` — links user to Coach Admin role\n"
            "- `user_applications` — links user to this application\n"
            "- `roles` — Coach Admin role (user_type=3, status=Active)\n"
            "- `application_roles` — links role to application\n"
            "- `permission_groups` — all Coach Admin permissions from `permission_references`"
        )

    # ── Tab: Products ─────────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown("##### `products` table")
        st.caption("Subscription tiers and one-time purchases from AI pricing analysis.")

        if not product_records:
            st.info("No products generated yet. Run the AI pipeline for this prospect.")
        else:
            for i, pr in enumerate(product_records):
                try:
                    p_data = json.loads(pr.get("body", "{}"))
                except json.JSONDecodeError:
                    continue

                name = pr.get("title") or p_data.get("name", f"Product {i+1}")
                desc = p_data.get("description", "")
                price_cents = p_data.get("price_cents", 0)
                currency = p_data.get("currency", "USD")
                interval = p_data.get("interval", "month")
                features = p_data.get("features", [])
                recommended = p_data.get("recommended", False)

                price_display = f"${price_cents / 100:.2f}" if currency == "USD" else f"{price_cents / 100:.2f} {currency}"

                with st.expander(
                    f"{'⭐ ' if recommended else ''}{name} — {price_display}/{interval}",
                    expanded=i == 0,
                ):
                    prod_fields = {
                        "name": name,
                        "description": desc[:100] + ("..." if len(desc) > 100 else ""),
                        "unit_amount": f"{price_cents} cents ({price_display})",
                        "currency_id": f"2 ({currency})" if currency == "USD" else currency,
                        "interval": interval,
                        "interval_count": "1",
                        "status_id": "1 (Draft) → 2 (Active on claim)",
                        "stripe_product_id": "— (set after Stripe connect)",
                    }
                    for k, v in prod_fields.items():
                        c1, c2 = st.columns([1, 3])
                        c1.code(k, language=None)
                        c2.markdown(f"`{v}`")

                    if features:
                        st.markdown("**Features:**")
                        for f in features:
                            st.markdown(f"- {f}")

    # ── Tab: Pages ────────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown("##### `pages` table")
        st.caption("About page + blog posts from AI content generation.")

        # About page
        long_bio = bio_data.get("long_bio", "")
        if long_bio:
            with st.expander("About Page (page_type_id=1)", expanded=True):
                page_fields = {
                    "title": "About",
                    "page_type_id": "1 (About)",
                    "status_id": "1 (Draft) → 2 (Active on claim)",
                    "media_url": p_image or "—",
                }
                for k, v in page_fields.items():
                    c1, c2 = st.columns([1, 3])
                    c1.code(k, language=None)
                    c2.markdown(f"`{v}`")
                st.markdown("**Content preview:**")
                st.markdown(long_bio[:500] + ("..." if len(long_bio) > 500 else ""))
        else:
            st.info("No About page content generated yet.")

        # Blog posts
        if blog_records:
            st.markdown("---")
            st.markdown(f"**Blog Posts ({len(blog_records)} articles)**")
            for i, br in enumerate(blog_records):
                try:
                    b_data = json.loads(br.get("body", "{}"))
                except json.JSONDecodeError:
                    continue

                title = br.get("title") or b_data.get("blog_title", f"Blog Post {i+1}")
                excerpt = b_data.get("excerpt", "")

                with st.expander(f"Blog: {title}", expanded=i == 0):
                    blog_fields = {
                        "title": title,
                        "page_type_id": "2 (Blog)",
                        "status_id": "1 (Draft) → 2 (Active on claim)",
                        "meta_title": b_data.get("seo_title", "—"),
                        "meta_description": b_data.get("seo_description", "—"),
                    }
                    for k, v in blog_fields.items():
                        c1, c2 = st.columns([1, 3])
                        c1.code(k, language=None)
                        c2.markdown(f"`{v}`")
                    if excerpt:
                        st.markdown(f"**Excerpt:** {excerpt}")
        elif not long_bio:
            st.info("No pages generated yet. Run the AI pipeline for this prospect.")

    # ── Tab: Features ─────────────────────────────────────────────────────────
    with tabs[6]:
        st.markdown("##### `application_feature_setups` table")
        st.caption("Feature flags for the branded app. All defaults shown.")

        feature_groups = {
            "Authentication": {
                "enable_google_signin": False,
                "enable_apple_login": False,
                "enable_fb_login": False,
            },
            "App Features": {
                "enable_switch_theme": False,
                "enable_referral": False,
                "enable_in_app_purchase": False,
                "enable_engagement_email": True,
                "has_one_to_one": False,
                "has_program": False,
                "has_light_bg": False,
                "hide_signup": False,
                "show_nutrition_filter": False,
            },
        }

        for group_name, features in feature_groups.items():
            st.markdown(f"**{group_name}**")
            cols = st.columns(3)
            for i, (name, default) in enumerate(features.items()):
                with cols[i % 3]:
                    icon = "✅" if default else "⬜"
                    st.markdown(
                        f'<div style="font-size:13px;font-family:monospace;padding:4px 0;">'
                        f"{icon} {name}</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        st.markdown("**Section Order (subscribed / unsubscribed)**")
        order_fields = [
            "nutrition", "wellness", "community", "home", "library", "shop"
        ]
        cols = st.columns(6)
        for i, section in enumerate(order_fields):
            with cols[i]:
                st.caption(section.title())
                st.markdown(f"sub: `{i+1}`  \nunsub: `{i+1}`")

    # ── Summary bar ───────────────────────────────────────────────────────────
    st.markdown("---")
    total_tables = 14 + len(product_records) + len(blog_records) + (1 if long_bio else 0)
    st.markdown(
        f"**CMS records that would be created:** ~{total_tables} rows across "
        f"`applications`, `application_settings`, `application_colors`, "
        f"`application_feature_setups`, `audio_settings`, `roles`, `users`, "
        f"`user_details`, `user_roles`, `user_applications`, `application_roles`, "
        f"`permission_groups`, `email_templates`, `referral_points`, "
        f"`products` ({len(product_records)}), `pages` ({len(blog_records) + (1 if long_bio else 0)})"
    )

except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Ensure DATABASE_URL is set and the database is accessible.")
