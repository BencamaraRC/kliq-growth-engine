"""Shared store preview HTML renderer.

Generates a complete HTML document showing an animated KLIQ webstore preview
in a 393px mobile frame. Used by both the Streamlit dashboard page and the
public FastAPI preview route.
"""

import base64
import json
import urllib.request

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


def render_store_preview(
    prospect: dict,
    generated_content: list[dict],
    *,
    claim_cta_url: str | None = None,
) -> str:
    """Return complete HTML string for the animated store preview.

    Args:
        prospect: Dict of prospect fields (from the prospects table).
        generated_content: List of dicts from generated_content table rows.
            Each must have at least 'content_type', 'title', and 'body' keys.
        claim_cta_url: If provided, a sticky "Claim Your Store" CTA bar is
            appended at the bottom of the page (used for public preview route).

    Returns:
        Full HTML document string.
    """
    # Parse generated content
    bio_data: dict = {}
    seo_data: dict = {}
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
            seo_data = parsed
        elif ct == "colors":
            color_data = parsed
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
    border_color = "#EAECF0"
    surface_primary = "#F9FAFB"
    hero_bg = color_data.get("hero_bg", kliq_green)  # noqa: F841
    creator_primary = color_data.get("primary", kliq_green)  # noqa: F841

    shadow_xs = "0 1px 2px rgba(16,24,40,0.05)"  # noqa: F841
    shadow_sm = "0 1px 3px rgba(16,24,40,0.1), 0 1px 2px rgba(16,24,40,0.06)"
    shadow_md = "0 4px 8px -2px rgba(16,24,40,0.1), 0 2px 4px -2px rgba(16,24,40,0.06)"

    coach_name = prospect.get("name", "Coach")
    coach_first = coach_name.split()[0] if coach_name else "Coach"
    store_name = bio_data.get("store_name", coach_name)
    short_bio = bio_data.get("short_bio", prospect.get("bio", ""))
    profile_img = prospect.get("profile_image_url", "")
    banner_img_url = prospect.get("banner_image_url", "")

    # Build hero banner
    banner_b64 = _fetch_image_b64(banner_img_url) if banner_img_url else ""
    _has_banner = bool(banner_b64)
    if _has_banner:
        _hero_banner_html = (
            f'<div style="width:100%;height:140px;position:relative;overflow:hidden;">'
            f'<img src="{banner_b64}" style="width:100%;height:100%;object-fit:cover;display:block;" />'
            f'<div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,0.4) 100%);display:flex;align-items:flex-end;justify-content:center;padding-bottom:12px;">'
            f'<h1 style="color:#fff;font-size:20px;font-weight:600;text-transform:uppercase;letter-spacing:2px;margin:0;line-height:120%;text-shadow:0 1px 4px rgba(0,0,0,0.4);">{store_name}</h1>'
            f'</div></div>'
        )
    else:
        _hero_banner_html = ""

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

    # Nav tabs
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

    # Reusable card style
    card_320 = "display:flex;width:320px;padding:12px;flex-direction:column;align-items:flex-start;gap:16px;flex-shrink:0;border-radius:8px;border:1px solid #F3F4F6;background:#fff;box-sizing:border-box;"

    # --- Revenue notification toasts ---
    revenue_notifications_html = f"""
        <div class="revenue-toast" style="animation-delay:14s;">
            <div style="background:#fff;border-radius:10px;padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.12);display:flex;align-items:center;gap:10px;min-width:200px;">
                <div style="width:32px;height:32px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:14px;">\U0001f4b0</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:12px;color:{text_primary};line-height:1.3;">$15.00 received</div>
                    <div style="font-size:10px;color:{text_tertiary};margin-top:1px;">AMA question from Sarah M.</div>
                </div>
            </div>
        </div>
        <div class="revenue-toast" style="animation-delay:18.5s;">
            <div style="background:#fff;border-radius:10px;padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.12);display:flex;align-items:center;gap:10px;min-width:200px;">
                <div style="width:32px;height:32px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:14px;">\U0001f504</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:12px;color:{text_primary};line-height:1.3;">$29/mo subscriber</div>
                    <div style="font-size:10px;color:{text_tertiary};margin-top:1px;">New member joined</div>
                </div>
            </div>
        </div>
        <div class="revenue-toast" style="animation-delay:23s;">
            <div style="background:#fff;border-radius:10px;padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.12);display:flex;align-items:center;gap:10px;min-width:200px;">
                <div style="width:32px;height:32px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:14px;">\U0001f389</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:12px;color:{text_primary};line-height:1.3;">{product_price_display} earned</div>
                    <div style="font-size:10px;color:{text_tertiary};margin-top:1px;">Program purchase</div>
                </div>
            </div>
        </div>
        <div class="revenue-toast" style="animation-delay:27.5s;">
            <div style="background:#fff;border-radius:10px;padding:10px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.12);display:flex;align-items:center;gap:10px;min-width:200px;">
                <div style="width:32px;height:32px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:14px;">\U0001f4fa</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:12px;color:{text_primary};line-height:1.3;">$10.00 received</div>
                    <div style="font-size:10px;color:{text_tertiary};margin-top:1px;">Live stream tip</div>
                </div>
            </div>
        </div>
    """

    # --- AMA chat sequence ---
    ama_chat_html = f"""
        <div style="display:flex;flex-direction:column;gap:8px;min-height:180px;">
            <div class="chat-bubble chat-user" style="animation-delay:0.3s;align-self:flex-end;max-width:80%;background:#FFECE7;border-radius:12px 12px 2px 12px;padding:8px 12px;">
                <p style="font-size:11px;color:{text_primary};line-height:140%;margin:0;">What diet plan do you recommend for muscle gain?</p>
            </div>
            <div id="typing-1" class="chat-bubble chat-typing" style="animation-delay:2s;align-self:flex-start;display:flex;align-items:center;gap:6px;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:12px 12px 12px 2px;padding:8px 12px;display:flex;align-items:center;gap:2px;">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
            <div class="chat-bubble chat-coach" style="animation-delay:3s;align-self:flex-start;display:flex;align-items:flex-start;gap:6px;max-width:85%;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:12px 12px 12px 2px;padding:8px 12px;">
                    <p style="font-size:10px;font-weight:600;color:{kliq_green};margin:0 0 2px;">{coach_first}</p>
                    <p style="font-size:11px;color:{text_primary};line-height:140%;margin:0;">Great question! I'd recommend a high-protein diet with lean meats, complex carbs, and healthy fats. My 8-Week Muscle Gain program has a full meal plan!</p>
                </div>
            </div>
            <div class="chat-bubble chat-user" style="animation-delay:4.5s;align-self:flex-end;max-width:80%;background:#FFECE7;border-radius:12px 12px 2px 12px;padding:8px 12px;">
                <p style="font-size:11px;color:{text_primary};line-height:140%;margin:0;">Thanks! What about supplements?</p>
            </div>
            <div id="typing-2" class="chat-bubble chat-typing" style="animation-delay:6s;align-self:flex-start;display:flex;align-items:center;gap:6px;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:12px 12px 12px 2px;padding:8px 12px;display:flex;align-items:center;gap:2px;">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
            <div class="chat-bubble chat-coach" style="animation-delay:7s;align-self:flex-start;display:flex;align-items:flex-start;gap:6px;max-width:85%;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:12px 12px 12px 2px;padding:8px 12px;">
                    <p style="font-size:10px;font-weight:600;color:{kliq_green};margin:0 0 2px;">{coach_first}</p>
                    <p style="font-size:11px;color:{text_primary};line-height:140%;margin:0;">Creatine and whey protein are essentials. I cover everything in the program \u2014 join and I'll guide you through it!</p>
                </div>
            </div>
        </div>
    """

    # --- Product cards ---
    product_cards_html = ""
    for product in products:
        price_cents = product.get("price_cents", 0)
        currency = product.get("currency", "GBP")
        currency_sym = "$" if currency == "USD" else "\u00a3" if currency == "GBP" else "\u20ac"
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

    # --- Blog cards ---
    blog_cards_html = ""
    for blog in blogs[:3]:
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

    # --- Live streams ---
    stream_titles = [p.get("title", f"Live Session {i+1}") for i, p in enumerate(products[:2])]
    if not stream_titles:
        stream_titles = ["Live Coaching Session", "Q&A with Community"]

    _live_title = stream_titles[0][:40] if stream_titles else "Live Coaching Session"
    _thumb_bg = f'url({profile_b64}) center/cover' if profile_b64 else f'linear-gradient(135deg,{kliq_green},{tangerine})'
    live_stream_cards = f"""
        <div class="live-card" style="{card_320}position:relative;">
            <div style="width:100%;height:120px;border-radius:8px;position:relative;overflow:hidden;background:{_thumb_bg};">
                <div style="position:absolute;inset:0;background:rgba(0,0,0,0.45);border-radius:8px;"></div>
                <div class="shimmer-overlay"></div>
                <div style="position:absolute;top:8px;left:8px;display:flex;align-items:center;gap:4px;background:rgba(0,0,0,0.6);border-radius:6px;padding:3px 8px;">
                    <span class="live-dot"></span>
                    <span style="color:#fff;font-size:10px;font-weight:600;letter-spacing:0.5px;">LIVE</span>
                </div>
                <div style="position:absolute;bottom:8px;right:8px;display:flex;align-items:center;gap:4px;background:rgba(0,0,0,0.6);border-radius:6px;padding:3px 8px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="#fff" stroke="none"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                    <span id="viewer-count" style="color:#fff;font-size:10px;font-weight:600;">23</span>
                </div>
                <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
                    <div style="width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.25);display:flex;align-items:center;justify-content:center;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    </div>
                </div>
            </div>
            <div style="display:flex;flex-direction:column;gap:4px;width:100%;">
                <h4 style="font-weight:600;font-size:13px;color:{text_primary};margin:0;line-height:120%;">{_live_title}</h4>
                <p style="font-size:11px;color:{text_tertiary};margin:0;">Streaming now &middot; {coach_first} is live</p>
            </div>
            <span style="background:#EF4444;color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Watch Live</span>
        </div>"""

    for i, stitle in enumerate(stream_titles[1:2]):
        days = i + 2
        live_stream_cards += f"""
        <div style="{card_320}">
            <div style="display:flex;align-items:center;gap:10px;width:100%;">
                <div style="width:40px;height:40px;border-radius:10px;background:{surface_primary};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
                </div>
                <div style="flex:1;min-width:0;">
                    <span style="display:inline-block;background:#FFECE7;color:{tangerine};font-size:10px;font-weight:600;padding:2px 8px;border-radius:10px;margin-bottom:4px;">Live in {days} day{"s" if days > 1 else ""}</span>
                    <h4 style="font-weight:600;font-size:13px;color:{text_primary};margin:2px 0;line-height:120%;">{stitle[:40]}</h4>
                    <p style="font-size:11px;color:{text_tertiary};margin:0;">March 13, 2025 &middot; 7:00 PM</p>
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

    # --- Claim CTA bar (for public preview route) ---
    claim_cta_html = ""
    if claim_cta_url:
        claim_cta_html = f"""
        <div style="position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid {border_color};padding:12px 24px;display:flex;align-items:center;justify-content:center;gap:12px;z-index:100;box-shadow:0 -2px 8px rgba(0,0,0,0.08);">
            <span style="font-size:14px;color:{text_primary};font-weight:500;">This could be your store.</span>
            <a href="{claim_cta_url}" style="background:{kliq_green};color:#fff;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;text-decoration:none;display:inline-block;">Claim Your Store</a>
        </div>
        """

    # Bottom padding if CTA is present
    bottom_pad = "padding-bottom:70px;" if claim_cta_url else ""

    # --- CSS ---
    css_reset = f"""
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Sora', sans-serif; -webkit-font-smoothing: antialiased; }}
        ::-webkit-scrollbar {{ display: none; }}

        @keyframes chatSlideRight {{ from {{ opacity:0; transform:translateX(20px); }} to {{ opacity:1; transform:translateX(0); }} }}
        @keyframes chatSlideLeft {{ from {{ opacity:0; transform:translateX(-20px); }} to {{ opacity:1; transform:translateX(0); }} }}
        @keyframes chatFadeIn {{ from {{ opacity:0; transform:translateY(6px); }} to {{ opacity:1; transform:translateY(0); }} }}
        @keyframes typingDot {{
            0%,80%,100% {{ opacity:0.3; transform:translateY(0); }}
            40% {{ opacity:1; transform:translateY(-4px); }}
        }}
        .chat-bubble {{ opacity:0; }}
        .chat-user {{ animation: chatSlideRight 0.4s ease-out forwards; }}
        .chat-coach {{ animation: chatSlideLeft 0.4s ease-out forwards; }}
        .chat-typing {{ animation: chatFadeIn 0.3s ease-out forwards; }}
        .typing-dot {{
            display:inline-block; width:6px; height:6px; border-radius:50%;
            background:#667085; margin:0 2px;
        }}
        .typing-dot:nth-child(1) {{ animation: typingDot 1.4s infinite 0s; }}
        .typing-dot:nth-child(2) {{ animation: typingDot 1.4s infinite 0.2s; }}
        .typing-dot:nth-child(3) {{ animation: typingDot 1.4s infinite 0.4s; }}

        @keyframes notifCycle {{
            0% {{ transform:translateX(110%); opacity:0; }}
            2.8% {{ transform:translateX(0); opacity:1; }}
            19.4% {{ transform:translateX(0); opacity:1; }}
            22.2% {{ transform:translateX(110%); opacity:0; }}
            100% {{ transform:translateX(110%); opacity:0; }}
        }}
        .revenue-toast {{
            position:absolute; right:12px; top:200px; z-index:10;
            transform:translateX(110%); opacity:0;
            animation: notifCycle 18s ease-in-out infinite;
        }}

        #ama-section {{
            max-height:600px; overflow:hidden;
            transition: max-height 0.8s ease-in-out, padding 0.8s ease-in-out, opacity 0.6s ease-in-out;
        }}
        #ama-section.collapsed {{
            max-height:52px; padding:10px 14px !important; opacity:0.85;
        }}

        @keyframes livePulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
        @keyframes shimmer {{
            0% {{ transform:translateX(-100%); }}
            100% {{ transform:translateX(100%); }}
        }}
        @keyframes liveGlow {{
            0%,100% {{ box-shadow:0 0 8px rgba(239,68,68,0.3); }}
            50% {{ box-shadow:0 0 16px rgba(239,68,68,0.6); }}
        }}
        .live-card {{ animation: liveGlow 2s ease-in-out infinite; border:1.5px solid #EF4444 !important; }}
        .live-dot {{
            width:8px; height:8px; border-radius:50%; background:#EF4444;
            animation: livePulse 1.5s ease-in-out infinite;
            display:inline-block;
        }}
        .shimmer-overlay {{
            position:absolute; inset:0; border-radius:8px; overflow:hidden;
        }}
        .shimmer-overlay::after {{
            content:''; position:absolute; inset:0;
            background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent);
            animation: shimmer 2.5s infinite;
        }}
    """

    # --- Assemble full HTML ---
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap" rel="stylesheet">
    <style>{css_reset}</style>
</head>
<body style="background:{page_bg};margin:0;{bottom_pad}">

<div style="display:flex;flex-direction:column;align-items:center;margin:0 auto;padding:16px 0;">

    <div style="display:flex;width:393px;flex-direction:column;align-items:flex-start;background:{card_bg};border-radius:20px;box-shadow:{shadow_md};overflow:hidden;position:relative;">

        {revenue_notifications_html}

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
        {_hero_banner_html}

        <!-- PROFILE SECTION -->
        <div style="display:flex;width:100%;padding:16px;box-sizing:border-box;align-items:flex-start;gap:12px;">
            <div style="flex-shrink:0;">{avatar_html}</div>
            <div style="display:flex;padding:0 16px;flex-direction:column;justify-content:center;align-items:flex-start;gap:16px;flex:1 0 0;min-width:0;">
                <div>
                    <h2 style="color:{text_primary};font-weight:600;font-size:16px;margin:0;line-height:120%;letter-spacing:-0.02em;">{store_name}</h2>
                    {"" if not niche_subtitle else f'<p style="color:{text_tertiary};font-size:12px;margin:4px 0 0;line-height:140%;">{niche_subtitle}</p>'}
                </div>
                {"" if not niche_pills_html else f'<div>{niche_pills_html}</div>'}
            </div>
        </div>
        <div style="width:100%;padding:0 16px 16px;box-sizing:border-box;">
            <p style="color:{text_secondary};font-size:12px;margin:0 0 12px;line-height:140%;">{short_bio[:200]}</p>
            <div style="display:flex;gap:8px;">
                <span style="background:{kliq_green};color:#fff;border-radius:8px;padding:8px 20px;font-size:12px;font-weight:600;cursor:pointer;">Sign up</span>
                <span style="border:1px solid {border_color};border-radius:8px;padding:8px 20px;font-size:12px;font-weight:500;color:{text_primary};cursor:pointer;">Log in</span>
            </div>
        </div>

        <div style="width:100%;height:1px;background:{border_color};"></div>

        <!-- CONTENT AREA -->
        <div style="width:100%;padding:16px;box-sizing:border-box;display:flex;flex-direction:column;gap:16px;">

            <!-- ASK ME ANYTHING -->
            <div id="ama-section" style="border-radius:8px;border:1px solid #F3F4F6;background:#fff;padding:14px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{text_primary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        <h3 style="font-weight:600;font-size:13px;color:{text_primary};letter-spacing:-0.02em;">Ask me anything</h3>
                        <div id="ama-typing-persistent" style="display:none;align-items:center;gap:2px;margin-left:4px;">
                            <span class="typing-dot"></span>
                            <span class="typing-dot"></span>
                            <span class="typing-dot"></span>
                        </div>
                    </div>
                    <span style="font-weight:600;font-size:14px;color:{text_primary};">$15</span>
                </div>
                <p style="color:{text_tertiary};font-size:11px;margin:0 0 10px;line-height:140%;">I'm here for whatever expert advice you need.</p>
                {ama_chat_html}
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

            <!-- FEATURED -->
            <div>
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                    <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Featured</h3>
                    <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                </div>
                <div style="display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;">
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

            <!-- ABOUT -->
            <div style="display:flex;width:361px;padding:24px 0;flex-direction:column;align-items:center;gap:12px;box-sizing:border-box;">
                <div style="width:100%;border-radius:8px;border:1px solid #F3F4F6;background:#fff;padding:16px;">
                    <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;margin:0 0 8px;">About</h3>
                    <p style="font-size:12px;color:{text_secondary};line-height:140%;margin:0;">{short_bio[:300] if short_bio else "Passionate coach helping you achieve your fitness and wellness goals through personalised programs and expert guidance."}</p>
                </div>
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

            <!-- COMMUNITY -->
            <div>
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                    <h3 style="font-weight:600;font-size:14px;color:{text_primary};letter-spacing:-0.02em;">Community</h3>
                    <span style="font-size:11px;color:{text_secondary};cursor:pointer;border:1px solid {border_color};border-radius:8px;padding:3px 10px;">See all</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:10px;">
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
            {"" if not link_items_html else f'<div>{link_items_html}</div>'}

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

    </div>

</div>

{claim_cta_html}

<script>
(function(){{
    var el=document.getElementById('viewer-count');
    if(el){{var n=23;setInterval(function(){{n+=Math.floor(Math.random()*3)+1;if(n>48)n=23;el.textContent=n;}},3000);}}
    setTimeout(function(){{var t=document.getElementById('typing-1');if(t)t.style.display='none';}},3000);
    setTimeout(function(){{var t=document.getElementById('typing-2');if(t)t.style.display='none';}},7000);
    setTimeout(function(){{
        var ama=document.getElementById('ama-section');
        if(ama)ama.classList.add('collapsed');
        var pt=document.getElementById('ama-typing-persistent');
        if(pt)pt.style.display='flex';
    }},9000);
}})();
</script>
</body>
</html>"""

    return full_html
