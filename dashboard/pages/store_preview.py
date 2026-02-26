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

    # --- Design Tokens ---
    primary = color_data.get("primary", "#1e7fff")
    hero_bg = color_data.get("hero_bg", "#2d2d2d")
    gray = "#888"
    light_gray = "#f5f5f5"
    black_text = "#1a1a1a"

    coach_name = prospect["name"]
    store_name = bio_data.get("store_name", coach_name)
    short_bio = bio_data.get("short_bio", prospect.get("bio", ""))
    profile_img = prospect.get("profile_image_url", "")
    follower_count = prospect.get("follower_count", 0) or 0
    subscriber_count = prospect.get("subscriber_count", 0) or 0

    # Nav tabs
    nav_tabs = ["Home"]
    if blogs:
        nav_tabs.append("Education")
    if products:
        nav_tabs.append("Programs")

    tabs_html = ""
    for i, tab in enumerate(nav_tabs):
        if i == 0:
            tabs_html += f'<span style="background:#f0f0f0;color:{black_text};padding:8px 22px;border-radius:20px;font-size:14px;font-weight:500;">{tab}</span>'
        else:
            tabs_html += f'<span style="color:{gray};padding:8px 22px;font-size:14px;font-weight:400;">{tab}</span>'

    # Avatar HTML
    profile_b64 = _fetch_image_b64(profile_img) if profile_img else ""
    if profile_b64:
        avatar_html = f'<img src="{profile_b64}" style="width:90px;height:90px;border-radius:50%;border:4px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.12);object-fit:cover;" />'
    else:
        avatar_html = f'<div style="width:90px;height:90px;border-radius:50%;border:4px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.12);background:linear-gradient(135deg,{primary}40,{primary}15);display:flex;align-items:center;justify-content:center;"><span style="font-size:36px;font-weight:700;color:{primary};">{coach_name[0] if coach_name else "K"}</span></div>'

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
            features_html += f'<div style="font-size:12px;color:{gray};padding:2px 0;">&#8226; {feat}</div>'

        product_cards_html += f"""
        <div style="background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,0.06);border:1px solid #eee;padding:20px;width:48%;min-width:200px;box-sizing:border-box;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <div style="width:40px;height:40px;border-radius:10px;background:{light_gray};display:flex;align-items:center;justify-content:center;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{primary}" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                </div>
                <div>
                    <div style="font-weight:600;font-size:15px;color:{black_text};">{product.get("title", "")}</div>
                    <div style="font-size:12px;color:{gray};">{price_text}</div>
                </div>
            </div>
            <p style="font-size:13px;color:{gray};line-height:1.4;margin:0 0 10px;">{product.get("description", "")}</p>
            {features_html}
            <div style="margin-top:14px;">
                <span style="background:{primary};color:#fff;border-radius:20px;padding:8px 22px;font-size:13px;font-weight:600;cursor:pointer;display:inline-block;">Join</span>
            </div>
        </div>"""

    # --- Build blog cards ---
    blog_cards_html = ""
    for blog in blogs:
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
                <span style="position:absolute;top:10px;right:10px;background:rgba(255,255,255,0.92);border-radius:10px;padding:3px 10px;font-size:11px;color:{gray};display:flex;align-items:center;gap:4px;">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="{gray}"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2z"/></svg>
                    Locked
                </span>
            </div>
            <p style="color:{gray};font-size:12px;margin:0 0 3px;">Featured</p>
            <h4 style="color:{black_text};font-weight:600;font-size:14px;margin:0 0 3px;line-height:1.3;">{display_title}</h4>
            <p style="color:{gray};font-size:12px;margin:0 0 10px;line-height:1.4;">{display_excerpt}</p>
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="background:{primary};color:#fff;border-radius:20px;padding:7px 18px;font-size:12px;font-weight:600;cursor:pointer;">Read Now</span>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="color:{gray};font-size:11px;display:flex;align-items:center;gap:3px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        {views}
                    </span>
                    <span style="color:{gray};font-size:11px;display:flex;align-items:center;gap:3px;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        0
                    </span>
                </div>
            </div>
        </div>"""

    # --- Build link items ---
    link_items_html = ""
    for product in products:
        title = product.get("title", "")
        if title:
            link_items_html += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:#fff;border-radius:12px;border:1px solid #eee;margin-bottom:8px;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:32px;height:32px;border-radius:8px;background:{light_gray};display:flex;align-items:center;justify-content:center;">
                        <span style="font-size:12px;font-weight:600;color:{primary};">{title[0]}</span>
                    </div>
                    <span style="font-weight:500;font-size:14px;color:{black_text};">{title}</span>
                </div>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{gray}" stroke-width="2"><path d="M7 17L17 7M17 7H7M17 7v10"/></svg>
            </div>"""

    # --- Assemble full HTML page ---
    css_reset = "* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }"
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>{css_reset}</style>
    </head>
    <body style="background: #fff;">

        <!-- NAV BAR -->
        <div style="background:#fff;display:flex;align-items:center;justify-content:space-between;padding:14px 28px;border-bottom:1px solid #eee;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:32px;height:32px;border-radius:50%;background:{primary};display:flex;align-items:center;justify-content:center;">
                    <span style="color:#fff;font-weight:700;font-size:13px;">{coach_name[0] if coach_name else "K"}</span>
                </div>
                <span style="font-weight:600;font-size:15px;color:{black_text};">{store_name}</span>
            </div>
            <div style="display:flex;align-items:center;gap:4px;">
                {tabs_html}
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="border:1px solid #d0d0d0;border-radius:20px;padding:7px 18px;font-size:13px;color:{black_text};font-weight:500;cursor:pointer;">Log in</span>
                <span style="background:{primary};border-radius:20px;padding:7px 18px;font-size:13px;color:#fff;font-weight:500;cursor:pointer;">Sign up</span>
            </div>
        </div>

        <!-- HERO BANNER -->
        <div style="height:200px;background:{hero_bg};display:flex;align-items:center;justify-content:center;">
            <h1 style="color:#fff;font-size:42px;font-weight:700;text-transform:uppercase;letter-spacing:3px;opacity:0.85;">{store_name}</h1>
        </div>

        <!-- PROFILE SECTION -->
        <div style="background:#fff;padding:0 28px 24px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="margin-top:-45px;">{avatar_html}</div>
                <div style="display:flex;gap:8px;padding-top:14px;">
                    <span style="border:1px solid #d0d0d0;border-radius:20px;padding:7px 18px;font-size:13px;color:{black_text};font-weight:500;cursor:pointer;">Log in</span>
                    <span style="background:{primary};border-radius:20px;padding:7px 18px;font-size:13px;color:#fff;font-weight:500;cursor:pointer;">Sign up</span>
                </div>
            </div>
            <h2 style="color:{black_text};font-weight:600;font-size:18px;margin:14px 0 4px;">{store_name}</h2>
            <p style="color:{gray};font-size:14px;margin:0;line-height:1.5;max-width:550px;">{short_bio}</p>
        </div>

        <!-- PROGRAMS -->
        {"" if not products else f'''
        <div style="background:#fff;padding:24px 28px;border-top:1px solid #eee;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <h3 style="color:{black_text};font-weight:600;font-size:16px;">Programs</h3>
                <span style="color:{gray};font-size:13px;cursor:pointer;border:1px solid #e0e0e0;border-radius:8px;padding:4px 12px;">See all</span>
            </div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                {product_cards_html}
            </div>
        </div>
        '''}

        <!-- EDUCATION -->
        {"" if not blogs else f'''
        <div style="background:#fff;padding:24px 28px;border-top:1px solid #eee;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;">
                <h3 style="color:{black_text};font-weight:600;font-size:16px;">Education</h3>
                <span style="color:{gray};font-size:13px;cursor:pointer;border:1px solid #e0e0e0;border-radius:8px;padding:4px 12px;">See all</span>
            </div>
            <div style="display:flex;gap:20px;flex-wrap:wrap;">
                {blog_cards_html}
            </div>
        </div>
        '''}

        <!-- LINK ITEMS -->
        {"" if not link_items_html else f'''
        <div style="background:#fff;padding:18px 28px 24px;border-top:1px solid #eee;">
            {link_items_html}
        </div>
        '''}

        <!-- FOOTER -->
        <div style="background:#fafafa;text-align:center;padding:18px;border-top:1px solid #eee;">
            <p style="font-weight:400;color:#bbb;font-size:13px;">Powered by KLIQ</p>
        </div>

    </body>
    </html>
    """

    # Render as a single iframe component — guaranteed HTML rendering
    components.html(full_html, height=2400, scrolling=True)

    # --- Debug Info ---
    with st.expander("Debug: Raw Generated Data"):
        st.json({"bio": bio_data, "seo": seo_data, "colors": color_data, "products": products, "blogs": blogs})

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
