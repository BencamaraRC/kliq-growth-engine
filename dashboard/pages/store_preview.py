"""Store Preview — visual mockup of what a generated KLIQ webstore looks like.

Renders a full-page preview matching the actual KLIQ public webstore design
as seen on live stores like Lift Your Vibe. Uses st.components.v1.html() for
reliable HTML rendering.
"""

import base64
import json
import urllib.request

import streamlit as st
import streamlit.components.v1 as components


_img_cache: dict[str, str] = {}


def _fetch_image_b64(url: str) -> str:
    """Fetch an image URL and return a base64 data URI."""
    if url in _img_cache:
        return _img_cache[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            mime = resp.headers.get("Content-Type", "image/jpeg")
            result = f"data:{mime};base64,{base64.b64encode(data).decode()}"
            _img_cache[url] = result
            return result
    except Exception:
        _img_cache[url] = ""
        return ""

st.set_page_config(page_title="Store Preview | KLIQ Growth Engine", layout="wide")

from theme import inject_kliq_theme, sidebar_nav

inject_kliq_theme()
sidebar_nav()

st.markdown("#### Store Preview")

try:
    from data import engine
    from sqlalchemy import text

    # --- Select a prospect ---
    with engine.connect() as conn:
        prospects = conn.execute(
            text("""
                SELECT p.id, p.name, p.primary_platform, p.status
                FROM prospects p
                WHERE EXISTS (SELECT 1 FROM generated_content gc WHERE gc.prospect_id = p.id)
                ORDER BY p.name
            """)
        ).fetchall()

    if not prospects:
        st.info("No prospects with generated content yet. Run the AI pipeline first.")
        st.stop()

    options = {f"{p[1]} ({p[2]}) — {p[3]}": p[0] for p in prospects}
    option_keys = list(options.keys())
    # Default to KLIQ prospect if available
    default_idx = 0
    for i, key in enumerate(option_keys):
        if "KLIQ" in key:
            default_idx = i
            break
    selected = st.selectbox("Select a coach to preview their store", option_keys, index=default_idx)
    prospect_id = options[selected]

    # --- Load all data ---
    with engine.connect() as conn:
        prospect = dict(
            conn.execute(
                text("SELECT * FROM prospects WHERE id = :id"), {"id": prospect_id}
            ).fetchone()._mapping
        )

        generated = conn.execute(
            text("SELECT * FROM generated_content WHERE prospect_id = :id"),
            {"id": prospect_id},
        ).fetchall()

    # Parse generated content
    bio_data = {}
    seo_data = {}
    color_data = {}
    products = []
    blogs = []

    for row in generated:
        r = dict(row._mapping)
        body = r.get("body", "{}")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}

        if r["content_type"] == "bio":
            bio_data = parsed
        elif r["content_type"] == "seo":
            seo_data = parsed
        elif r["content_type"] == "colors":
            color_data = parsed
        elif r["content_type"] == "product":
            parsed["title"] = r.get("title", "")
            products.append(parsed)
        elif r["content_type"] == "blog":
            parsed["title"] = r.get("title", "")
            blogs.append(parsed)

    # --- KLIQ Design Tokens (from Figma design system) ---
    tangerine = "#FF9F88"
    kliq_green = "#1C3838"
    kliq_dark = "#021111"
    page_bg = "#FFFDF9"
    card_bg = "#FFFFFF"
    text_primary = "#101828"
    text_secondary = "#1D2939"
    text_tertiary = "#667085"
    border_color = "#EAECF0"
    surface_primary = "#F9FAFB"   # Gray/50
    surface_secondary = "#F2F4F7" # Gray/100
    hero_bg = color_data.get("hero_bg", kliq_green)
    creator_primary = color_data.get("primary", kliq_green)

    # Shadow tokens from design system
    shadow_xs = "0 1px 2px rgba(16,24,40,0.05)"
    shadow_sm = "0 1px 3px rgba(16,24,40,0.1), 0 1px 2px rgba(16,24,40,0.06)"
    shadow_md = "0 4px 8px -2px rgba(16,24,40,0.1), 0 2px 4px -2px rgba(16,24,40,0.06)"

    coach_name = prospect["name"]
    store_name = bio_data.get("store_name", coach_name)
    short_bio = bio_data.get("short_bio", prospect.get("bio", ""))
    profile_img = prospect.get("profile_image_url", "")

    # Niche tags
    raw_niche_tags = prospect.get("niche_tags", [])
    if isinstance(raw_niche_tags, str):
        try:
            niche_tags = json.loads(raw_niche_tags)
        except (json.JSONDecodeError, TypeError):
            niche_tags = []
    else:
        niche_tags = raw_niche_tags or []
    niche_subtitle = niche_tags[0].title() if niche_tags else bio_data.get("niche", "")

    # Nav tabs (mobile: bottom bar style shown as top tabs)
    nav_tabs = ["Home", "Program", "Library", "Communities"]

    tabs_html = ""
    for i, tab in enumerate(nav_tabs):
        active = i == 0
        bg = surface_primary if active else "transparent"
        weight = "600" if active else "400"
        color = text_primary if active else text_tertiary
        tabs_html += f'<span style="color:{color};padding:6px 12px;font-size:12px;font-weight:{weight};cursor:pointer;background:{bg};border-radius:8px;">{tab}</span>'

    # Avatar HTML
    profile_b64 = _fetch_image_b64(profile_img) if profile_img else ""
    initial = coach_name[0] if coach_name else "K"
    if profile_b64:
        nav_avatar = f'<img src="{profile_b64}" style="width:28px;height:28px;border-radius:50%;object-fit:cover;display:block;flex-shrink:0;" />'
        avatar_html = f'<img src="{profile_b64}" style="width:64px;height:64px;border-radius:50%;border:2px solid #fff;box-shadow:{shadow_sm};object-fit:cover;display:block;" />'
        small_avatar = f'<img src="{profile_b64}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />'
    else:
        nav_avatar = f'<div style="width:28px;height:28px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="color:#fff;font-weight:600;font-size:11px;line-height:1;">{initial}</span></div>'
        avatar_html = f'<div style="width:64px;height:64px;border-radius:50%;border:2px solid #fff;box-shadow:{shadow_sm};background:{kliq_green};display:flex;align-items:center;justify-content:center;"><span style="font-size:24px;font-weight:600;color:#fff;line-height:1;">{initial}</span></div>'
        small_avatar = f'<div style="width:32px;height:32px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-weight:600;font-size:12px;">{initial}</span></div>'

    # Niche pills
    niche_pills_html = ""
    for tag in niche_tags[:3]:
        niche_pills_html += f'<span style="display:inline-block;background:#FFECE7;color:{text_primary};padding:3px 10px;border-radius:20px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.3px;margin-right:4px;">{tag}</span>'

    # --- Reusable card style (from Figma: 320px, 12px padding, column, 16px gap) ---
    card_320 = "display:flex;width:320px;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex-shrink:0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;box-sizing:border-box;"

    # --- Build product cards (320px horizontal scroll) ---
    product_cards_html = ""
    for product in products:
        price_cents = product.get("price_cents", 0)
        currency = product.get("currency", "GBP")
        currency_sym = "$" if currency == "USD" else "£" if currency == "GBP" else "€"
        interval = product.get("interval", "")
        if price_cents == 0:
            price_text = "Free"
        else:
            price_text = f"{currency_sym}{price_cents / 100:.0f}/{interval}" if interval else f"{currency_sym}{price_cents / 100:.0f}"

        features = product.get("features", [])
        features_html = ""
        for feat in features[:3]:
            features_html += f'<div style="font-size:11px;color:{text_tertiary};padding:1px 0;line-height:1.4;">&#8226; {feat}</div>'

        product_cards_html += f"""
        <div style="{card_320}">
            <div style="display:flex;align-items:center;gap:10px;width:100%;">
                <div style="width:36px;height:36px;border-radius:10px;background:{surface_primary};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:14px;color:{text_primary};line-height:120%;">{product.get("title", "")}</div>
                    <div style="font-size:11px;color:{text_tertiary};margin-top:1px;">{price_text}</div>
                </div>
            </div>
            <p style="font-size:12px;color:{text_tertiary};line-height:140%;margin:0;">{product.get("description", "")[:120]}</p>
            <div>{features_html}</div>
            <span style="background:{kliq_green};color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Join</span>
        </div>"""

    # --- Build blog cards (320px horizontal scroll) ---
    blog_cards_html = ""
    for idx, blog in enumerate(blogs[:3]):
        title = blog.get("title", "Untitled")
        excerpt = blog.get("excerpt", "")
        thumbnail = blog.get("thumbnail", "")
        views = blog.get("views", 0)

        display_title = title if len(title) <= 36 else title[:33] + "..."
        display_excerpt = excerpt if len(excerpt) <= 60 else excerpt[:57] + "..."

        thumb_b64 = ""
        if thumbnail:
            thumb_b64 = _fetch_image_b64(thumbnail)
        if thumb_b64:
            img_html = f'<img src="{thumb_b64}" style="width:100%;height:140px;border-radius:8px;object-fit:cover;display:block;" />'
        else:
            img_html = f'<div style="width:100%;height:140px;border-radius:8px;background:linear-gradient(135deg,{kliq_green},{tangerine});"></div>'

        blog_cards_html += f"""
        <div style="{card_320}">
            {img_html}
            <div style="display:flex;flex-direction:column;gap:4px;">
                <p style="color:{text_tertiary};font-size:10px;margin:0;">16th April 2025</p>
                <h4 style="color:{text_primary};font-weight:600;font-size:13px;margin:0;line-height:120%;">{display_title}</h4>
                <p style="color:{text_tertiary};font-size:11px;margin:0;line-height:140%;">{display_excerpt}</p>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;width:100%;">
                <span style="background:{tangerine};color:#fff;border-radius:8px;padding:6px 14px;font-size:11px;font-weight:600;cursor:pointer;">Read now</span>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="color:{text_tertiary};font-size:10px;display:flex;align-items:center;gap:2px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        {views}
                    </span>
                    <span style="color:{text_tertiary};font-size:10px;display:flex;align-items:center;gap:2px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        0
                    </span>
                </div>
            </div>
        </div>"""

    # --- Pinned post ---
    pinned_post_html = ""
    if blogs:
        pinned = blogs[0]
        pinned_excerpt = pinned.get("excerpt", "")
        pinned_thumb = pinned.get("thumbnail", "")
        pinned_thumb_b64 = _fetch_image_b64(pinned_thumb) if pinned_thumb else ""
        pinned_img = f'<img src="{pinned_thumb_b64}" style="width:100%;height:160px;border-radius:10px;object-fit:cover;display:block;margin:10px 0;" />' if pinned_thumb_b64 else ""
        pinned_text = pinned_excerpt if len(pinned_excerpt) <= 120 else pinned_excerpt[:117] + "..."

        pinned_post_html = f"""
        <div style="padding:0 0 16px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Pinned post</h3>
                <span style="font-size:12px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
            </div>
            <div style="background:{card_bg};border-radius:12px;border:1px solid {border_color};padding:14px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    {small_avatar}
                    <div>
                        <div style="font-weight:600;font-size:13px;color:{text_primary};">{coach_name}</div>
                        <div style="font-size:10px;color:{text_tertiary};">1 hour ago</div>
                    </div>
                </div>
                {pinned_img}
                <p style="font-size:12px;color:{text_secondary};line-height:1.5;margin:6px 0 10px;">{pinned_text}</p>
                <div style="display:flex;align-items:center;gap:14px;border-top:1px solid {border_color};padding-top:8px;">
                    <span style="color:{text_tertiary};font-size:11px;display:flex;align-items:center;gap:3px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        12
                    </span>
                    <span style="color:{text_tertiary};font-size:11px;display:flex;align-items:center;gap:3px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        3
                    </span>
                </div>
            </div>
        </div>"""

    # --- Live streams (320px cards, horizontal scroll) ---
    stream_titles = [p.get("title", f"Live Session {i+1}") for i, p in enumerate(products[:2])]
    if not stream_titles:
        stream_titles = ["Live Coaching Session", "Q&A with Community"]
    live_stream_cards = ""
    for i, stitle in enumerate(stream_titles[:2]):
        days = i + 1
        live_stream_cards += f"""
        <div style="{card_320}">
            <div style="display:flex;align-items:center;gap:10px;width:100%;">
                <div style="width:40px;height:40px;border-radius:10px;background:{surface_primary};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                </div>
                <div style="flex:1;min-width:0;">
                    <span style="display:inline-block;background:#FFECE7;color:{tangerine};font-size:10px;font-weight:600;padding:2px 8px;border-radius:10px;margin-bottom:4px;">Live in {days} day{"s" if days > 1 else ""}</span>
                    <h4 style="font-weight:600;font-size:13px;color:{text_primary};margin:2px 0;line-height:120%;">{stitle[:40]}</h4>
                    <p style="font-size:11px;color:{text_tertiary};margin:0;">March {10 + i * 3}, 2025 &middot; 7:00 PM</p>
                </div>
            </div>
            <span style="background:{kliq_green};color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Join</span>
        </div>"""

    # --- Link items ---
    link_items_html = ""
    for product in products:
        title = product.get("title", "")
        if title:
            link_items_html += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:{card_bg};border-radius:10px;border:1px solid {border_color};margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:10px;min-width:0;">
                    <div style="width:28px;height:28px;border-radius:8px;background:{surface_primary};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <span style="font-size:11px;font-weight:600;color:{text_primary};">{title[0]}</span>
                    </div>
                    <span style="font-weight:500;font-size:13px;color:{text_primary};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{title}</span>
                </div>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2" style="flex-shrink:0;"><path d="M7 17L17 7M17 7H7M17 7v10"/></svg>
            </div>"""

    # --- Assemble full HTML — 1440px canvas, 393px mobile frame ---
    css_reset = """
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Sora', sans-serif; -webkit-font-smoothing: antialiased; }
        ::-webkit-scrollbar { display: none; }
    """
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap" rel="stylesheet">
        <style>{css_reset}</style>
    </head>
    <body style="background:{page_bg};margin:0;">

    <!-- OUTER: canvas -->
    <div style="display:flex;flex-direction:column;align-items:center;margin:0 auto;padding:16px 0;">

        <!-- INNER: 393px mobile webstore frame -->
        <div style="display:flex;width:393px;flex-direction:column;align-items:flex-start;background:{card_bg};border-radius:20px;box-shadow:{shadow_md};overflow:hidden;">

            <!-- NAV BAR -->
            <div style="display:flex;align-items:center;justify-content:space-between;width:100%;padding:12px 16px;border-bottom:1px solid {border_color};box-sizing:border-box;">
                <div style="display:flex;align-items:center;gap:8px;">
                    {nav_avatar}
                    <span style="font-weight:600;font-size:14px;color:{text_primary};white-space:nowrap;">{store_name[:20]}</span>
                </div>
                <div style="display:flex;gap:6px;">
                    <span style="border:1px solid {border_color};border-radius:8px;padding:5px 12px;font-size:11px;color:{text_primary};font-weight:500;cursor:pointer;">Log in</span>
                    <span style="background:{kliq_green};border-radius:8px;padding:5px 12px;font-size:11px;color:#fff;font-weight:600;cursor:pointer;">Sign up</span>
                </div>
            </div>

            <!-- TAB BAR -->
            <div style="display:flex;align-items:center;gap:4px;width:100%;padding:10px 16px;box-sizing:border-box;overflow-x:auto;">
                {tabs_html}
            </div>

            <!-- HERO BANNER -->
            <div style="width:100%;height:140px;background:{hero_bg};display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
                <h1 style="color:#fff;font-size:24px;font-weight:600;text-transform:uppercase;letter-spacing:2px;opacity:0.9;margin:0;line-height:120%;">{store_name}</h1>
            </div>

            <!-- PROFILE SECTION -->
            <div style="display:flex;width:100%;padding:16px;box-sizing:border-box;align-items:flex-start;gap:12px;">
                <!-- Avatar -->
                <div style="flex-shrink:0;">{avatar_html}</div>
                <!-- Name + niche + bio -->
                <div style="display:flex;padding:0 16px;flex-direction:column;justify-content:center;align-items:flex-start;gap:16px;flex:1 0 0;min-width:0;">
                    <div>
                        <h2 style="color:{text_primary};font-weight:600;font-size:16px;margin:0;line-height:120%;letter-spacing:-0.02em;">{store_name}</h2>
                        {"" if not niche_subtitle else f'<p style="color:{text_tertiary};font-size:12px;margin:4px 0 0;line-height:140%;">{niche_subtitle}</p>'}
                    </div>
                    {"" if not niche_pills_html else f'<div>{niche_pills_html}</div>'}
                </div>
            </div>
            <!-- Bio + CTAs below profile row -->
            <div style="width:100%;padding:0 16px 16px;box-sizing:border-box;">
                <p style="color:{text_secondary};font-size:12px;margin:0 0 12px;line-height:140%;">{short_bio[:200]}</p>
                <div style="display:flex;gap:8px;">
                    <span style="background:{kliq_green};color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Sign up</span>
                    <span style="border:1px solid {border_color};border-radius:8px;padding:8px 20px;font-size:12px;font-weight:500;color:{text_primary};cursor:pointer;">Log in</span>
                </div>
            </div>

            <!-- DIVIDER -->
            <div style="width:100%;height:1px;background:{border_color};"></div>

            <!-- CONTENT AREA -->
            <div style="width:100%;padding:16px;box-sizing:border-box;display:flex;flex-direction:column;gap:16px;">

                <!-- ASK ME ANYTHING -->
                <div style="border-radius:8px;border:1px solid #F3F4F6;background:#fff;padding:14px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{text_primary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                            <h3 style="font-weight:600;font-size:13px;color:{text_primary};letter-spacing:-0.02em;">Ask me anything</h3>
                        </div>
                        <span style="font-weight:600;font-size:14px;color:{text_primary};">$15</span>
                    </div>
                    <p style="color:{text_tertiary};font-size:11px;margin:0 0 10px;line-height:140%;">I'm here for whatever expert advice you need.</p>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <input type="text" placeholder="Got a question?" disabled style="flex:1;padding:8px 12px;border:1px solid {border_color};border-radius:8px;font-size:11px;font-family:'Sora',sans-serif;color:{text_tertiary};background:{surface_primary};outline:none;" />
                        <div style="width:32px;height:32px;border-radius:50%;background:{tangerine};display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                        </div>
                    </div>
                </div>

                <!-- PINNED POST -->
                {pinned_post_html}

                <!-- LIVE STREAMS -->
                <div>
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Live streams</h3>
                        <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                    </div>
                    <div style="display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;">
                        {live_stream_cards}
                    </div>
                </div>

                <!-- EDUCATION -->
                {"" if not blogs else f'''
                <div>
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Education</h3>
                        <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                    </div>
                    <div style="display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;">
                        {blog_cards_html}
                    </div>
                </div>
                '''}

                <!-- PROGRAMS -->
                {"" if not products else f'''
                <div>
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Programs</h3>
                        <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                    </div>
                    <div style="display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;">
                        {product_cards_html}
                    </div>
                </div>
                '''}

                <!-- FEATURED CONTENT -->
                <div>
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Featured</h3>
                        <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                    </div>
                    <div style="display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;">
                        <!-- Featured card 1 -->
                        <div style="display:flex;width:320px;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex-shrink:0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <div style="width:100%;height:140px;border-radius:8px;background:linear-gradient(135deg,{kliq_green} 0%,{tangerine} 100%);display:flex;align-items:center;justify-content:center;">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            </div>
                            <div style="display:flex;flex-direction:column;gap:4px;">
                                <span style="font-weight:600;font-size:13px;color:{text_primary};line-height:120%;">Getting Started Guide</span>
                                <span style="font-size:11px;color:{text_tertiary};line-height:140%;">Everything you need to begin your transformation journey</span>
                            </div>
                            <span style="background:{kliq_green};color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Watch now</span>
                        </div>
                        <!-- Featured card 2 -->
                        <div style="display:flex;width:320px;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex-shrink:0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <div style="width:100%;height:140px;border-radius:8px;background:linear-gradient(135deg,#DEFE9C 0%,{kliq_green} 100%);display:flex;align-items:center;justify-content:center;">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                            </div>
                            <div style="display:flex;flex-direction:column;gap:4px;">
                                <span style="font-weight:600;font-size:13px;color:{text_primary};line-height:120%;">Nutrition Blueprint</span>
                                <span style="font-size:11px;color:{text_tertiary};line-height:140%;">Meal plans, macros, and recipes tailored for your goals</span>
                            </div>
                            <span style="background:{kliq_green};color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Download</span>
                        </div>
                    </div>
                </div>

                <!-- ABOUT / SOCIAL PROOF -->
                <div style="display:flex;width:361px;padding:24px 0;flex-direction:column;align-items:center;gap:12px;box-sizing:border-box;">
                    <div style="width:100%;border-radius:8px;border:1px solid #F3F4F6;background:#fff;padding:16px;">
                        <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;margin:0 0 8px;">About</h3>
                        <p style="font-size:12px;color:{text_secondary};line-height:140%;margin:0;">{short_bio[:300] if short_bio else "Passionate coach helping you achieve your fitness and wellness goals through personalised programs and expert guidance."}</p>
                    </div>
                    <!-- Stats row -->
                    <div style="display:flex;gap:10px;width:100%;">
                        <div style="display:flex;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex:1 0 0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <span style="font-weight:600;font-size:20px;color:{text_primary};line-height:120%;letter-spacing:-0.02em;">500+</span>
                            <span style="font-size:11px;color:{text_tertiary};line-height:140%;">Members</span>
                        </div>
                        <div style="display:flex;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex:1 0 0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <span style="font-weight:600;font-size:20px;color:{text_primary};line-height:120%;letter-spacing:-0.02em;">50+</span>
                            <span style="font-size:11px;color:{text_tertiary};line-height:140%;">Programs</span>
                        </div>
                        <div style="display:flex;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex:1 0 0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <span style="font-weight:600;font-size:20px;color:{text_primary};line-height:120%;letter-spacing:-0.02em;">4.9</span>
                            <span style="font-size:11px;color:{text_tertiary};line-height:140%;">Rating</span>
                        </div>
                    </div>
                </div>

                <!-- COMMUNITY HIGHLIGHTS -->
                <div>
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                        <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Community</h3>
                        <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                    </div>
                    <div style="display:flex;flex-direction:column;gap:10px;">
                        <!-- Testimonial card -->
                        <div style="display:flex;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                <div style="width:28px;height:28px;border-radius:50%;background:#FFECE7;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="font-size:11px;font-weight:600;color:{tangerine};">S</span></div>
                                <div>
                                    <span style="font-weight:600;font-size:12px;color:{text_primary};">Sarah M.</span>
                                    <div style="display:flex;gap:1px;">
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                    </div>
                                </div>
                            </div>
                            <p style="font-size:12px;color:{text_secondary};line-height:140%;margin:0;">"This program completely changed my routine. I'm stronger, more confident, and actually enjoy working out now."</p>
                        </div>
                        <!-- Testimonial card 2 -->
                        <div style="display:flex;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;border-radius:8px;border:1px solid #F3F4F6;background:#fff;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                <div style="width:28px;height:28px;border-radius:50%;background:#EBFCFF;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="font-size:11px;font-weight:600;color:#1C3838;">J</span></div>
                                <div>
                                    <span style="font-weight:600;font-size:12px;color:{text_primary};">James T.</span>
                                    <div style="display:flex;gap:1px;">
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <svg width="10" height="10" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                    </div>
                                </div>
                            </div>
                            <p style="font-size:12px;color:{text_secondary};line-height:140%;margin:0;">"The nutrition plans alone are worth it. Lost 8kg in 3 months and never felt deprived."</p>
                        </div>
                    </div>
                </div>

                <!-- LINK ITEMS -->
                {"" if not link_items_html else f'''
                <div>
                    {link_items_html}
                </div>
                '''}

            </div>

            <!-- FOOTER -->
            <div style="display:flex;width:361px;padding:24px 0;flex-direction:column;align-items:center;gap:12px;box-sizing:border-box;margin:0 auto;">
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="{text_tertiary}"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="{text_tertiary}"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="{text_tertiary}"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 3.993L9 16z"/></svg>
                </div>
                <p style="font-weight:400;color:{text_tertiary};font-size:11px;">Powered by <span style="font-weight:600;color:{kliq_green};">KLIQ</span></p>
            </div>

        </div><!-- end 393px frame -->

    </div><!-- end 1440px canvas -->

    </body>
    </html>
    """

    # Render as a single iframe component
    components.html(full_html, height=2200, scrolling=True)

    # --- Debug Info ---
    with st.expander("Debug: Raw Generated Data"):
        st.json({"bio": bio_data, "seo": seo_data, "colors": color_data, "products": products, "blogs": blogs})

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
