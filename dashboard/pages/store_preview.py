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

st.title("Store Preview")
st.markdown("Preview what a generated KLIQ webstore looks like for a discovered coach.")

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

    # --- KLIQ Design Tokens (from actual production webstore) ---
    tangerine = "#FF9F88"         # CTA buttons, accents
    kliq_green = "#1C3838"        # Nav text, dark elements
    page_bg = "#FFFDF9"           # Official KLIQ ivory background
    card_bg = "#FFFFFF"           # Card surfaces
    text_primary = "#101828"      # Headings
    text_secondary = "#1D2939"    # Body text
    text_tertiary = "#667085"     # Muted/caption text
    border_color = "#EAECF0"      # Borders, separators
    hero_bg = color_data.get("hero_bg", "#2d2d2d")  # Coach-specific hero
    primary = color_data.get("primary", kliq_green)  # Coach accent (for hero overlay text)

    coach_name = prospect["name"]
    store_name = bio_data.get("store_name", coach_name)
    short_bio = bio_data.get("short_bio", prospect.get("bio", ""))
    profile_img = prospect.get("profile_image_url", "")

    # Niche tags for hero overlay
    raw_niche_tags = prospect.get("niche_tags", [])
    if isinstance(raw_niche_tags, str):
        try:
            niche_tags = json.loads(raw_niche_tags)
        except (json.JSONDecodeError, TypeError):
            niche_tags = []
    else:
        niche_tags = raw_niche_tags or []
    niche_subtitle = niche_tags[0].title() if niche_tags else bio_data.get("niche", "")

    # Nav tabs
    nav_tabs = ["Home", "Program", "Library", "Communities"]

    tabs_html = ""
    for i, tab in enumerate(nav_tabs):
        weight = "600" if i == 0 else "400"
        color = text_primary if i == 0 else text_tertiary
        tabs_html += f'<span style="color:{color};padding:8px 16px;font-size:14px;font-weight:{weight};cursor:pointer;">{tab}</span>'

    # Avatar HTML (small nav avatar + large profile avatar)
    profile_b64 = _fetch_image_b64(profile_img) if profile_img else ""
    if profile_b64:
        nav_avatar = f'<img src="{profile_b64}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />'
        avatar_html = f'<img src="{profile_b64}" style="width:90px;height:90px;border-radius:50%;border:4px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.12);object-fit:cover;" />'
    else:
        initial = coach_name[0] if coach_name else "K"
        nav_avatar = f'<div style="width:32px;height:32px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-weight:700;font-size:13px;">{initial}</span></div>'
        avatar_html = f'<div style="width:90px;height:90px;border-radius:50%;border:4px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.12);background:{kliq_green};display:flex;align-items:center;justify-content:center;"><span style="font-size:36px;font-weight:700;color:#fff;">{initial}</span></div>'

    # Small avatar for post cards
    if profile_b64:
        small_avatar = f'<img src="{profile_b64}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />'
    else:
        initial = coach_name[0] if coach_name else "K"
        small_avatar = f'<div style="width:36px;height:36px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-weight:600;font-size:14px;">{initial}</span></div>'

    # --- Niche tags overlay for hero ---
    niche_pills_html = ""
    for tag in niche_tags[:4]:
        niche_pills_html += f'<span style="background:{tangerine};color:#fff;padding:6px 16px;border-radius:20px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">{tag}</span>'

    # --- Build product cards ---
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
        for feat in features:
            features_html += f'<div style="font-size:12px;color:{text_tertiary};padding:2px 0;">&#8226; {feat}</div>'

        product_cards_html += f"""
        <div style="background:{card_bg};border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06);border:1px solid {border_color};padding:20px;width:48%;min-width:200px;box-sizing:border-box;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <div style="width:40px;height:40px;border-radius:10px;background:{page_bg};display:flex;align-items:center;justify-content:center;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                </div>
                <div>
                    <div style="font-weight:600;font-size:15px;color:{text_primary};">{product.get("title", "")}</div>
                    <div style="font-size:12px;color:{text_tertiary};">{price_text}</div>
                </div>
            </div>
            <p style="font-size:13px;color:{text_tertiary};line-height:1.4;margin:0 0 10px;">{product.get("description", "")}</p>
            {features_html}
            <div style="margin-top:14px;">
                <span style="background:{kliq_green};color:#fff;border-radius:20px;padding:8px 22px;font-size:13px;font-weight:600;cursor:pointer;display:inline-block;">Join</span>
            </div>
        </div>"""

    # --- Build blog/education cards ---
    blog_cards_html = ""
    for idx, blog in enumerate(blogs):
        title = blog.get("title", "Untitled")
        excerpt = blog.get("excerpt", "")
        thumbnail = blog.get("thumbnail", "")
        views = blog.get("views", 0)

        display_title = title if len(title) <= 42 else title[:39] + "..."
        display_excerpt = excerpt if len(excerpt) <= 80 else excerpt[:77] + "..."

        thumb_b64 = ""
        if thumbnail:
            thumb_b64 = _fetch_image_b64(thumbnail)
        if thumb_b64:
            img_html = f'<img src="{thumb_b64}" style="width:100%;height:180px;border-radius:12px;object-fit:cover;display:block;" />'
        else:
            img_html = f'<div style="width:100%;height:180px;border-radius:12px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>'

        blog_cards_html += f"""
        <div style="flex:1;min-width:240px;max-width:340px;">
            <div style="position:relative;margin-bottom:10px;">
                {img_html}
            </div>
            <p style="color:{text_tertiary};font-size:12px;margin:0 0 4px;">16th April 2025</p>
            <h4 style="color:{text_primary};font-weight:600;font-size:14px;margin:0 0 3px;line-height:1.3;">{display_title}</h4>
            <p style="color:{text_tertiary};font-size:12px;margin:0 0 10px;line-height:1.4;">{display_excerpt}</p>
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="background:{tangerine};color:#fff;border-radius:20px;padding:7px 18px;font-size:12px;font-weight:600;cursor:pointer;">Read now</span>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="color:{text_tertiary};font-size:11px;display:flex;align-items:center;gap:3px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        {views}
                    </span>
                    <span style="color:{text_tertiary};font-size:11px;display:flex;align-items:center;gap:3px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        0
                    </span>
                </div>
            </div>
        </div>"""

    # --- Pinned post (using first blog) ---
    pinned_post_html = ""
    if blogs:
        pinned = blogs[0]
        pinned_title = pinned.get("title", "")
        pinned_excerpt = pinned.get("excerpt", "")
        pinned_thumb = pinned.get("thumbnail", "")
        pinned_thumb_b64 = _fetch_image_b64(pinned_thumb) if pinned_thumb else ""
        pinned_img = f'<img src="{pinned_thumb_b64}" style="width:100%;height:220px;border-radius:12px;object-fit:cover;display:block;margin:12px 0;" />' if pinned_thumb_b64 else ""
        pinned_text = pinned_excerpt if len(pinned_excerpt) <= 150 else pinned_excerpt[:147] + "..."

        pinned_post_html = f"""
        <div style="padding:0 28px 24px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <h3 style="font-weight:600;font-size:16px;color:{text_primary};">Pinned post</h3>
                <span style="font-size:13px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:4px 12px;">See all</span>
            </div>
            <div style="background:{card_bg};border-radius:12px;border:1px solid {border_color};padding:16px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                    {small_avatar}
                    <div>
                        <div style="font-weight:600;font-size:14px;color:{text_primary};">{coach_name}</div>
                        <div style="font-size:12px;color:{text_tertiary};">1 hour ago</div>
                    </div>
                </div>
                {pinned_img}
                <p style="font-size:14px;color:{text_secondary};line-height:1.5;margin:8px 0 12px;">{pinned_text}</p>
                <div style="display:flex;align-items:center;gap:16px;border-top:1px solid {border_color};padding-top:10px;">
                    <span style="color:{text_tertiary};font-size:12px;display:flex;align-items:center;gap:4px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        12
                    </span>
                    <span style="color:{text_tertiary};font-size:12px;display:flex;align-items:center;gap:4px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        3
                    </span>
                </div>
            </div>
        </div>"""

    # --- Live streams section ---
    stream_titles = [p.get("title", f"Live Session {i+1}") for i, p in enumerate(products[:2])]
    if not stream_titles:
        stream_titles = ["Live Coaching Session", "Q&A with Community"]
    live_stream_cards = ""
    for i, stitle in enumerate(stream_titles[:2]):
        days = i + 1
        live_stream_cards += f"""
        <div style="flex:1;min-width:240px;background:{card_bg};border-radius:12px;border:1px solid {border_color};padding:16px;">
            <div style="width:48px;height:48px;border-radius:10px;background:{page_bg};display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <span style="display:inline-block;background:#FFF0EC;color:{tangerine};font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;margin-bottom:8px;">Live in {days} day{"s" if days > 1 else ""}</span>
            <h4 style="font-weight:600;font-size:14px;color:{text_primary};margin:4px 0;">{stitle}</h4>
            <p style="font-size:12px;color:{text_tertiary};margin:0 0 12px;">March {10 + i * 3}, 2025 &middot; 7:00 PM</p>
            <span style="background:{kliq_green};color:#fff;border-radius:20px;padding:6px 18px;font-size:12px;font-weight:600;cursor:pointer;display:inline-block;">Join</span>
        </div>"""

    # --- Build link items ---
    link_items_html = ""
    for product in products:
        title = product.get("title", "")
        if title:
            link_items_html += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:{card_bg};border-radius:12px;border:1px solid {border_color};margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:{page_bg};display:flex;align-items:center;justify-content:center;">
                        <span style="font-size:12px;font-weight:600;color:{text_primary};">{title[0]}</span>
                    </div>
                    <span style="font-weight:500;font-size:14px;color:{text_primary};">{title}</span>
                </div>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M7 17L17 7M17 7H7M17 7v10"/></svg>
            </div>"""

    # --- Assemble full HTML page ---
    css_reset = "* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Sora', sans-serif; }"
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap" rel="stylesheet">
        <style>{css_reset}</style>
    </head>
    <body style="background:{page_bg};">
    <div style="max-width:1440px;margin:0 auto;background:{page_bg};">

        <!-- NAV BAR -->
        <div style="background:{card_bg};display:flex;align-items:center;justify-content:space-between;padding:14px 28px;border-bottom:1px solid {border_color};">
            <div style="display:flex;align-items:center;gap:10px;">
                {nav_avatar}
                <span style="font-weight:600;font-size:15px;color:{text_primary};">{store_name}</span>
            </div>
            <div style="display:flex;align-items:center;gap:4px;">
                {tabs_html}
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="border:1px solid {border_color};border-radius:20px;padding:7px 18px;font-size:13px;color:{text_primary};font-weight:500;cursor:pointer;">Log in</span>
                <span style="background:{tangerine};border-radius:20px;padding:7px 18px;font-size:13px;color:#fff;font-weight:500;cursor:pointer;">Sign up</span>
            </div>
        </div>

        <!-- HERO BANNER -->
        <div style="height:220px;background:{hero_bg};display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;">
            <h1 style="color:#fff;font-size:42px;font-weight:600;text-transform:uppercase;letter-spacing:3px;opacity:0.9;">{store_name}</h1>
            {"" if not niche_pills_html else f'''
            <div style="position:absolute;right:28px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:8px;">
                {niche_pills_html}
            </div>
            '''}
        </div>

        <!-- PROFILE SECTION -->
        <div style="background:{card_bg};padding:0 28px 24px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="margin-top:-45px;">{avatar_html}</div>
                <div style="display:flex;gap:8px;padding-top:14px;">
                    <span style="border:1px solid {border_color};border-radius:20px;padding:7px 18px;font-size:13px;color:{text_primary};font-weight:500;cursor:pointer;">Log in</span>
                    <span style="background:{tangerine};border-radius:20px;padding:7px 18px;font-size:13px;color:#fff;font-weight:500;cursor:pointer;">Sign up</span>
                </div>
            </div>
            <h2 style="color:{text_primary};font-weight:600;font-size:18px;margin:14px 0 2px;">{store_name}</h2>
            {"" if not niche_subtitle else f'<p style="color:{text_tertiary};font-size:14px;margin:0 0 6px;">{niche_subtitle}</p>'}
            <p style="color:{text_secondary};font-size:14px;margin:0;line-height:1.5;max-width:550px;">{short_bio}</p>
        </div>

        <!-- ASK ME ANYTHING -->
        <div style="padding:24px 28px;">
            <div style="background:{card_bg};border-radius:12px;border:1px solid {border_color};padding:20px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{text_primary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    <h3 style="font-weight:600;font-size:16px;color:{text_primary};">Ask me anything</h3>
                </div>
                <p style="color:{text_tertiary};font-size:13px;margin:0 0 14px;line-height:1.4;">I'm here for whatever expert advice you need.</p>
                <div style="display:flex;align-items:center;gap:10px;">
                    <input type="text" placeholder="Got a question?" disabled style="flex:1;padding:10px 14px;border:1px solid {border_color};border-radius:10px;font-size:13px;font-family:'Sora',sans-serif;color:{text_tertiary};background:{page_bg};outline:none;" />
                    <div style="width:38px;height:38px;border-radius:50%;background:{tangerine};display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                    </div>
                </div>
            </div>
        </div>

        <!-- PINNED POST -->
        {pinned_post_html}

        <!-- LIVE STREAMS -->
        <div style="padding:0 28px 24px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <h3 style="font-weight:600;font-size:16px;color:{text_primary};">Live streams</h3>
                <span style="font-size:13px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:4px 12px;">See all</span>
            </div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                {live_stream_cards}
            </div>
        </div>

        <!-- EDUCATION -->
        {"" if not blogs else f'''
        <div style="padding:0 28px 24px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <h3 style="font-weight:600;font-size:16px;color:{text_primary};">Education</h3>
                <span style="font-size:13px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:4px 12px;">See all</span>
            </div>
            <div style="display:flex;gap:20px;flex-wrap:wrap;">
                {blog_cards_html}
            </div>
        </div>
        '''}

        <!-- PROGRAMS -->
        {"" if not products else f'''
        <div style="padding:0 28px 24px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <h3 style="font-weight:600;font-size:16px;color:{text_primary};">Programs</h3>
                <span style="font-size:13px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:4px 12px;">See all</span>
            </div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                {product_cards_html}
            </div>
        </div>
        '''}

        <!-- LINK ITEMS -->
        {"" if not link_items_html else f'''
        <div style="padding:0 28px 24px;">
            {link_items_html}
        </div>
        '''}

        <!-- FOOTER -->
        <div style="text-align:center;padding:28px;border-top:1px solid {border_color};">
            <div style="margin-bottom:10px;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="{text_tertiary}"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
            </div>
            <p style="font-weight:400;color:{text_tertiary};font-size:13px;">Powered by <span style="font-weight:600;color:{kliq_green};">KLIQ</span></p>
        </div>

    </div>
    </body>
    </html>
    """

    # Render as a single iframe component — guaranteed HTML rendering
    components.html(full_html, height=3200, scrolling=True)

    # --- Debug Info ---
    with st.expander("Debug: Raw Generated Data"):
        st.json({"bio": bio_data, "seo": seo_data, "colors": color_data, "products": products, "blogs": blogs})

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
