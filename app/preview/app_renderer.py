"""iOS app preview HTML renderer.

Generates a complete HTML document showing an animated KLIQ mobile app preview
inside an iPhone device frame. Matches the real KLIQ app home screen layout:
greeting header, bio card, AMA bar, courses, live streams, recent blog, posts.
"""

import json
from datetime import datetime

from app.preview.renderer import _fetch_image_b64


def render_app_preview(
    prospect: dict,
    generated_content: list[dict],
    claim_url: str | None = None,
    scraped_thumbnails: list[str] | None = None,
) -> str:
    """Return complete HTML string for the animated iOS app preview.

    Args:
        prospect: Dict of prospect fields (from the prospects table).
        generated_content: List of dicts from generated_content table rows.
            Each must have at least 'content_type', 'title', and 'body' keys.
        claim_url: Optional URL to the claim page. When provided, a floating
            "Claim Your App for FREE" banner is shown at the bottom.
        scraped_thumbnails: Optional list of thumbnail URLs from scraped content.

    Returns:
        Full HTML document string.
    """
    # --- Parse generated content ---
    bio_data: dict = {}
    _seo_data: dict = {}
    color_data: dict = {}
    products: list[dict] = []
    blogs: list[dict] = []

    for r in generated_content:
        body = r.get("body", "{}")
        try:
            parsed = json.loads(body) if body else {}
        except (json.JSONDecodeError, TypeError):
            parsed = {}

        ct = r.get("content_type", "")
        if ct == "bio":
            bio_data = parsed
        elif ct == "seo":
            _seo_data = parsed
        elif ct == "colors":
            color_data = parsed  # noqa: F841
        elif ct == "product":
            parsed["title"] = r.get("title", "")
            products.append(parsed)
        elif ct == "blog":
            parsed["title"] = r.get("title", "")
            blogs.append(parsed)

    # Extract first product price for revenue notifications
    product_price_display = "$29"
    for _p in products:
        _pc = _p.get("price_cents", 0)
        if _pc > 0:
            _cur = _p.get("currency", "USD")
            _sym = "$" if _cur == "USD" else "\u00a3" if _cur == "GBP" else "\u20ac"
            product_price_display = f"{_sym}{_pc / 100:.0f}"
            break

    # --- KLIQ Design Tokens ---
    tangerine = "#FF9F88"
    kliq_green = "#1C3838"
    page_bg = "#FFFDF9"
    card_bg = "#FFFFFF"
    text_primary = "#101828"
    text_secondary = "#1D2939"
    text_tertiary = "#667085"
    border_color = "#F3F4F6"
    surface_primary = "#F9FAFB"

    coach_name = prospect.get("name", "Coach")
    coach_first = coach_name.split()[0] if coach_name else "Coach"
    store_name = bio_data.get("store_name", coach_name)
    short_bio = bio_data.get("short_bio", prospect.get("bio", ""))
    long_bio = bio_data.get("long_bio", short_bio)  # noqa: F841
    profile_img = prospect.get("profile_image_url", "")

    # Niche tags
    raw_niche_tags = prospect.get("niche_tags", [])
    if isinstance(raw_niche_tags, str):
        try:
            niche_tags = json.loads(raw_niche_tags)
        except (json.JSONDecodeError, TypeError):
            niche_tags = []
    else:
        niche_tags = raw_niche_tags or []  # noqa: F841

    # Avatar HTML
    profile_b64 = _fetch_image_b64(profile_img) if profile_img else ""
    initial = coach_name[0] if coach_name else "K"
    if profile_b64:
        greeting_avatar = f'<img src="{profile_b64}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;display:block;flex-shrink:0;" />'
        ama_avatar = f'<img src="{profile_b64}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;flex-shrink:0;" />'
    else:
        greeting_avatar = f'<div style="width:48px;height:48px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="color:#fff;font-weight:600;font-size:18px;line-height:1;">{initial}</span></div>'
        ama_avatar = f'<div style="width:32px;height:32px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="color:#fff;font-weight:600;font-size:12px;">{initial}</span></div>'

    # --- Build image pool (variety across sections) ---
    banner_img_url = prospect.get("banner_image_url", "")
    banner_b64 = _fetch_image_b64(banner_img_url) if banner_img_url else ""

    # Fetch scraped thumbnails as b64
    thumb_b64s: list[str] = []
    for url in (scraped_thumbnails or []):
        b64 = _fetch_image_b64(url)
        if b64:
            thumb_b64s.append(b64)

    # Image pool: scraped thumbs first, then banner, then profile
    image_pool: list[str] = thumb_b64s[:]
    if banner_b64:
        image_pool.append(banner_b64)
    if profile_b64:
        image_pool.append(profile_b64)

    def _get_card_bg(index: int) -> str:
        """Return a CSS background value cycling through the image pool."""
        if image_pool:
            return f"url({image_pool[index % len(image_pool)]}) center/cover"
        return f"linear-gradient(135deg,{kliq_green},{tangerine})"

    # Date for greeting
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%B %-d")

    # --- iOS Push Notification Toasts (top-center, blur style) ---
    ios_notifications_html = f"""
        <div class="ios-toast" style="animation-delay:6s;">
            <div style="background:rgba(255,255,255,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:16px;padding:14px 16px;box-shadow:0 8px 32px rgba(0,0,0,0.12);display:flex;align-items:center;gap:12px;min-width:340px;max-width:380px;">
                <div style="width:38px;height:38px;border-radius:10px;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:16px;color:#fff;font-weight:700;">K</span>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:13px;color:{text_primary};line-height:1.3;">{store_name}</div>
                    <div style="font-size:12px;color:{text_tertiary};margin-top:1px;">$15.00 received &middot; AMA question from Sarah M.</div>
                </div>
                <span style="font-size:11px;color:{text_tertiary};flex-shrink:0;">now</span>
            </div>
        </div>
        <div class="ios-toast" style="animation-delay:12s;">
            <div style="background:rgba(255,255,255,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:16px;padding:14px 16px;box-shadow:0 8px 32px rgba(0,0,0,0.12);display:flex;align-items:center;gap:12px;min-width:340px;max-width:380px;">
                <div style="width:38px;height:38px;border-radius:10px;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:16px;color:#fff;font-weight:700;">K</span>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:13px;color:{text_primary};line-height:1.3;">{store_name}</div>
                    <div style="font-size:12px;color:{text_tertiary};margin-top:1px;">$29/mo subscriber &middot; New member joined</div>
                </div>
                <span style="font-size:11px;color:{text_tertiary};flex-shrink:0;">now</span>
            </div>
        </div>
        <div class="ios-toast" style="animation-delay:18s;">
            <div style="background:rgba(255,255,255,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:16px;padding:14px 16px;box-shadow:0 8px 32px rgba(0,0,0,0.12);display:flex;align-items:center;gap:12px;min-width:340px;max-width:380px;">
                <div style="width:38px;height:38px;border-radius:10px;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:16px;color:#fff;font-weight:700;">K</span>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:13px;color:{text_primary};line-height:1.3;">{store_name}</div>
                    <div style="font-size:12px;color:{text_tertiary};margin-top:1px;">{product_price_display} earned &middot; Program purchase</div>
                </div>
                <span style="font-size:11px;color:{text_tertiary};flex-shrink:0;">now</span>
            </div>
        </div>
    """

    # --- Live stream cards (horizontal scroll, large image cards with overlay) ---
    stream_titles = [p.get("title", f"Live Session {i + 1}") for i, p in enumerate(products[:3])]
    if len(stream_titles) < 2:
        stream_titles = ["Live Coaching Session", "Q&A with Community", "Beginner Workout"]

    live_cards_html = ""
    for i, stitle in enumerate(stream_titles[:3]):
        days = i + 1
        time_pill = f"Live in {days} day{'s' if days > 1 else ''}" if i == 0 else f"{days} days ago"
        _live_bg = _get_card_bg(i)
        live_cards_html += f"""
            <div class="fade-in" style="flex-shrink:0;width:240px;height:340px;border-radius:12px;overflow:hidden;position:relative;scroll-snap-align:start;">
                <div style="width:100%;height:100%;background:{_live_bg};"></div>
                <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,0.65) 100%);"></div>
                <div style="position:absolute;top:12px;left:12px;">
                    <span style="background:{'#FFECE7' if i == 0 else 'rgba(0,0,0,0.5)'};color:{tangerine if i == 0 else '#fff'};font-size:11px;font-weight:600;padding:5px 12px;border-radius:10px;">{time_pill}</span>
                </div>
                <div style="position:absolute;bottom:14px;left:14px;right:14px;">
                    <h4 style="font-weight:600;font-size:15px;color:#fff;margin:0 0 4px;line-height:130%;text-shadow:0 1px 3px rgba(0,0,0,0.3);">{stitle[:40]}</h4>
                    <p style="font-size:12px;color:rgba(255,255,255,0.8);margin:0;">8th August 2025</p>
                </div>
            </div>"""

    # --- Course cards (horizontal scroll, large image cards with overlay) ---
    course_cards_html = ""
    for idx, product in enumerate(products):
        title = product.get("title", "")
        display_title = title if len(title) <= 35 else title[:32] + "..."

        # Offset by 3 so courses use different images than live streams
        _course_bg = _get_card_bg(idx + 3)

        course_cards_html += f"""
            <div class="fade-in" style="flex-shrink:0;width:240px;height:280px;border-radius:12px;overflow:hidden;position:relative;scroll-snap-align:start;">
                <div style="width:100%;height:100%;background:{_course_bg};"></div>
                <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,0.65) 100%);"></div>
                <div style="position:absolute;bottom:14px;left:14px;right:14px;">
                    <h4 style="font-weight:600;font-size:15px;color:#fff;margin:0 0 8px;line-height:130%;text-shadow:0 1px 3px rgba(0,0,0,0.3);">{display_title}</h4>
                    <div style="display:flex;gap:6px;">
                        <span style="background:rgba(255,255,255,0.2);backdrop-filter:blur(4px);color:#fff;font-size:11px;font-weight:500;padding:4px 10px;border-radius:6px;">1 Module</span>
                        <span style="background:rgba(255,255,255,0.2);backdrop-filter:blur(4px);color:#fff;font-size:11px;font-weight:500;padding:4px 10px;border-radius:6px;">1 Lesson</span>
                    </div>
                </div>
            </div>"""

    # --- Recent posts (text card with likes/reply) ---
    recent_post_html = ""
    if short_bio:
        post_text = short_bio[:180] if len(short_bio) > 180 else short_bio
        recent_post_html = f"""
            <div class="fade-in" style="background:{card_bg};border-radius:12px;border:1px solid {border_color};padding:14px;display:flex;flex-direction:column;gap:10px;">
                <p style="font-size:14px;color:{text_secondary};line-height:170%;margin:0;">{post_text}</p>
                <div style="display:flex;align-items:center;gap:16px;padding-top:4px;">
                    <span style="color:{text_tertiary};font-size:13px;display:flex;align-items:center;gap:4px;cursor:pointer;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        1 like
                    </span>
                    <span style="color:{text_tertiary};font-size:13px;cursor:pointer;">Reply</span>
                </div>
            </div>"""

    # --- Recent blog cards (full-width image cards with overlay text) ---
    blog_cards_html = ""
    for blog_idx, blog in enumerate(blogs[:3]):
        title = blog.get("title", "Untitled")
        thumbnail = blog.get("thumbnail", "")
        display_title = title if len(title) <= 50 else title[:47] + "..."

        # Try blog's own thumbnail first, then use image pool
        thumb_b64 = ""
        if thumbnail:
            thumb_b64 = _fetch_image_b64(thumbnail)

        if thumb_b64:
            bg_style = f"url({thumb_b64}) center/cover"
        else:
            # Offset by 6 so blogs use different images than live/courses
            bg_style = _get_card_bg(blog_idx + 6)

        blog_cards_html += f"""
            <div class="fade-in" style="width:100%;height:220px;border-radius:16px;overflow:hidden;position:relative;">
                <div style="width:100%;height:100%;background:{bg_style};"></div>
                <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 30%,rgba(0,0,0,0.6) 100%);"></div>
                <div style="position:absolute;bottom:16px;left:16px;right:16px;">
                    <h4 style="font-weight:600;font-size:16px;color:#fff;margin:0 0 4px;line-height:130%;text-shadow:0 1px 3px rgba(0,0,0,0.3);">{display_title}</h4>
                    <p style="font-size:12px;color:rgba(255,255,255,0.8);margin:0;">29 Sep, 2025</p>
                </div>
            </div>"""

    # --- CSS ---
    css = f"""
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Sora', sans-serif; -webkit-font-smoothing: antialiased; }}
        ::-webkit-scrollbar {{ display: none; }}
        html {{ scroll-behavior: smooth; }}
        body {{ background: #F9FAFB; display:flex; flex-direction:column; align-items:center; min-height:100vh; }}

        .device-frame {{
            width:393px; background:#000; border-radius:44px;
            padding:8px;
            box-shadow: 0 24px 48px rgba(0,0,0,0.2), 0 0 0 1px rgba(255,255,255,0.1) inset;
            margin:32px auto;
            position:relative;
        }}
        .dynamic-island {{
            width:126px; height:36px; background:#000; border-radius:18px;
            position:absolute; top:16px; left:50%; transform:translateX(-50%); z-index:20;
        }}
        .device-screen {{
            background:{page_bg}; border-radius:36px; overflow:hidden; overflow-y:auto;
            display:flex; flex-direction:column; position:relative;
        }}

        .content-feed {{
            display:flex; flex-direction:column; gap:24px; padding:0 20px 20px;
        }}

        .section-title {{
            font-weight:600; font-size:17px; color:{text_primary}; letter-spacing:-0.02em; line-height:130%;
        }}
        .section-header {{
            display:flex; align-items:baseline; justify-content:space-between; margin-bottom:12px;
        }}
        .see-all {{
            font-size:13px; color:{tangerine}; cursor:pointer; font-weight:500; text-decoration:none;
        }}

        .hscroll {{
            display:flex; gap:12px; overflow-x:auto; scroll-snap-type:x mandatory;
            padding-bottom:4px; margin:0 -20px; padding-left:20px; padding-right:20px;
        }}

        /* Fade-in on scroll */
        .fade-in {{
            opacity:0; transform:translateY(16px);
            transition: opacity 0.5s ease-out, transform 0.5s ease-out;
        }}
        .fade-in.visible {{
            opacity:1; transform:translateY(0);
        }}

        /* iOS push notifications */
        @keyframes iosNotifSlide {{
            0% {{ transform:translateY(-120%); opacity:0; }}
            5% {{ transform:translateY(0); opacity:1; }}
            25% {{ transform:translateY(0); opacity:1; }}
            30% {{ transform:translateY(-120%); opacity:0; }}
            100% {{ transform:translateY(-120%); opacity:0; }}
        }}
        .ios-toast {{
            position:fixed; top:24px; left:50%; transform:translate(-50%,-120%); z-index:100;
            opacity:0;
            animation: iosNotifSlide 24s ease-in-out infinite;
        }}
    """

    # --- Bottom Tab Nav (4 tabs: Home, Feed, Chat, Profile) ---
    bottom_tab_nav = f"""
    <div style="display:flex;align-items:center;justify-content:space-around;padding:10px 0 6px;background:#fff;border-top:1px solid {border_color};">
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="{kliq_green}" stroke="none"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
            <span style="font-size:10px;font-weight:600;color:{kliq_green};">Home</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="1.8"><rect x="4" y="4" width="16" height="16" rx="2"/><line x1="4" y1="10" x2="20" y2="10"/><line x1="10" y1="4" x2="10" y2="20"/></svg>
            <span style="font-size:10px;font-weight:500;color:{text_tertiary};">Feed</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="1.8"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/></svg>
            <span style="font-size:10px;font-weight:500;color:{text_tertiary};">Chat</span>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="1.8"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span style="font-size:10px;font-weight:500;color:{text_tertiary};">Profile</span>
        </div>
    </div>"""

    # --- Assemble full HTML ---
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{css}</style>
</head>
<body>

    {ios_notifications_html}

    <div class="device-frame">
        <div class="dynamic-island"></div>
        <div class="device-screen">

            <!-- iOS STATUS BAR (black text on ivory) -->
            <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 24px 0;">
                <span style="font-weight:600;font-size:15px;color:{text_primary};letter-spacing:-0.02em;">9:41</span>
                <div style="display:flex;align-items:center;gap:5px;">
                    <svg width="17" height="12" viewBox="0 0 17 12" fill="none"><path d="M1 8.5h2v3H1zM5 6h2v5.5H5zM9 3.5h2V12H9zM13 1h2v10.5h-2z" fill="{text_primary}"/></svg>
                    <svg width="16" height="12" viewBox="0 0 16 12" fill="none"><path d="M8 3.58c1.95 0 3.72.8 5 2.08l1.42-1.42A9.01 9.01 0 008 .58c-2.8 0-5.34 1.19-7.12 3.08L2.3 5.08A7.01 7.01 0 018 3.58z" fill="{text_primary}"/><path d="M8 6.58c1.18 0 2.25.48 3.03 1.26L12.46 6.4A6.01 6.01 0 008 4.58c-1.88 0-3.57.86-4.68 2.2l1.42 1.42A4.01 4.01 0 018 6.58z" fill="{text_primary}"/><circle cx="8" cy="10.58" r="2" fill="{text_primary}"/></svg>
                    <svg width="25" height="12" viewBox="0 0 25 12" fill="none"><rect x="0.5" y="0.5" width="21" height="11" rx="2" stroke="rgba(0,0,0,0.25)"/><rect x="2" y="2" width="18" height="8" rx="1" fill="{text_primary}"/><path d="M23 4.5v3a1.5 1.5 0 000-3z" fill="rgba(0,0,0,0.25)"/></svg>
                </div>
            </div>

            <!-- GREETING HEADER -->
            <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 20px 8px;">
                <div>
                    <h1 style="font-size:22px;font-weight:600;color:{text_primary};margin:0;line-height:130%;">Hello, {coach_first}</h1>
                    <p style="font-size:14px;color:{text_tertiary};margin:4px 0 0;">{day_name}, {date_str}</p>
                </div>
                {greeting_avatar}
            </div>

            <!-- BIO ANNOUNCEMENT CARD -->
            {"" if not short_bio else f'''
            <div style="margin:12px 20px 0;padding:16px;border-radius:12px;background:linear-gradient(135deg,{kliq_green} 0%,#2a5555 100%);">
                <p style="font-size:11px;color:{tangerine};font-weight:600;margin:0 0 6px;text-transform:uppercase;letter-spacing:0.5px;">New post by {coach_first}</p>
                <p style="font-size:14px;color:#fff;line-height:160%;margin:0;">{short_bio[:180]}</p>
            </div>
            '''}

            <!-- ASK ME ANYTHING BAR -->
            <div style="display:flex;align-items:center;gap:10px;margin:16px 20px 4px;padding:10px 14px;border-radius:24px;background:#fff;border:1px solid {border_color};">
                {ama_avatar}
                <span style="flex:1;font-size:14px;color:{text_tertiary};">Ask {coach_first} anything</span>
                <div style="width:32px;height:32px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2" fill="none"/></svg>
                </div>
            </div>

            <!-- CONTENT FEED -->
            <div class="content-feed" style="padding-top:20px;">

                <!-- LIVE STREAM -->
                {"" if not stream_titles else f'''
                <section>
                    <div class="section-header">
                        <h2 class="section-title">Live stream</h2>
                        <div style="width:32px;height:32px;border-radius:50%;background:{surface_primary};display:flex;align-items:center;justify-content:center;cursor:pointer;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2.5" stroke-linecap="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                        </div>
                    </div>
                    <div class="hscroll">
                        {live_cards_html}
                    </div>
                </section>
                '''}

                <!-- COURSES -->
                {"" if not products else f'''
                <section>
                    <div class="section-header">
                        <h2 class="section-title">Courses</h2>
                        <a class="see-all" href="#">View all ({len(products) * 4 + 8})</a>
                    </div>
                    <div class="hscroll">
                        {course_cards_html}
                    </div>
                </section>
                '''}

                <!-- RECENT POSTS -->
                {"" if not recent_post_html else f'''
                <section>
                    <div class="section-header">
                        <h2 class="section-title">{coach_first} post</h2>
                        <div style="width:32px;height:32px;border-radius:50%;background:{surface_primary};display:flex;align-items:center;justify-content:center;cursor:pointer;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2.5" stroke-linecap="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                        </div>
                    </div>
                    {recent_post_html}
                </section>
                '''}

                <!-- RECENT BLOG -->
                {"" if not blogs else f'''
                <section>
                    <div class="section-header">
                        <h2 class="section-title">Recent blog</h2>
                        <a class="see-all" href="#">View all ({len(blogs) * 4 + 8})</a>
                    </div>
                    <div style="display:flex;flex-direction:column;gap:14px;">
                        {blog_cards_html}
                    </div>
                </section>
                '''}

            </div><!-- end content-feed -->

            <!-- BOTTOM TAB NAV -->
            {bottom_tab_nav}

            <!-- HOME INDICATOR -->
            <div style="display:flex;justify-content:center;padding:6px 0 4px;background:#fff;">
                <div style="width:134px;height:5px;border-radius:3px;background:#000;opacity:0.2;"></div>
            </div>

        </div><!-- end device-screen -->
    </div><!-- end device-frame -->

{f'''
    <!-- FLOATING CLAIM BANNER -->
    <div id="claim-banner" style="
        position:fixed;bottom:0;left:0;right:0;z-index:1000;
        background:linear-gradient(135deg, {kliq_green} 0%, #0E2325 100%);
        padding:16px 24px;
        display:flex;align-items:center;justify-content:center;gap:16px;
        box-shadow:0 -4px 20px rgba(0,0,0,0.15);
        transform:translateY(100%);
        animation:slideUpBanner 0.5s ease-out 2s forwards;
    ">
        <div style="display:flex;align-items:center;gap:12px;flex:1;justify-content:center;flex-wrap:wrap;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FF9F88" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
            </svg>
            <span style="color:#fff;font-size:15px;font-weight:600;font-family:Sora,sans-serif;">
                This app was built for you, {coach_first}!
            </span>
            <a href="{claim_url}" style="
                display:inline-flex;align-items:center;gap:8px;
                background:#FF9F88;color:{kliq_green};
                padding:10px 24px;border-radius:8px;
                font-size:14px;font-weight:700;font-family:Sora,sans-serif;
                text-decoration:none;white-space:nowrap;
                transition:transform 0.15s, box-shadow 0.15s;
            " onmouseover="this.style.transform=&apos;scale(1.05)&apos;;this.style.boxShadow=&apos;0 4px 12px rgba(255,159,136,0.4)&apos;"
               onmouseout="this.style.transform=&apos;scale(1)&apos;;this.style.boxShadow=&apos;none&apos;">
                Claim Your App for FREE
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </a>
        </div>
        <button onclick="document.getElementById(&apos;claim-banner&apos;).style.display=&apos;none&apos;" style="
            background:none;border:none;color:rgba(255,255,255,0.6);cursor:pointer;
            padding:4px;font-size:18px;line-height:1;flex-shrink:0;
        " onmouseover="this.style.color=&apos;#fff&apos;" onmouseout="this.style.color=&apos;rgba(255,255,255,0.6)&apos;">&times;</button>
    </div>
    <style>
        @keyframes slideUpBanner {{
            from {{ transform:translateY(100%); }}
            to {{ transform:translateY(0); }}
        }}
    </style>
''' if claim_url else ''}

<script>
(function(){{
    // IntersectionObserver fade-in on scroll
    var observer=new IntersectionObserver(function(entries){{
        entries.forEach(function(entry){{
            if(entry.isIntersecting){{
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }}
        }});
    }},{{threshold:0.15,rootMargin:'0px 0px -40px 0px'}});
    document.querySelectorAll('.fade-in').forEach(function(el){{observer.observe(el);}});
}})();
</script>
</body>
</html>"""

    return full_html
