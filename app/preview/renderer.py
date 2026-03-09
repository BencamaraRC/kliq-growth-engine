"""Shared store preview HTML renderer.

Generates a complete HTML document showing an animated KLIQ webstore preview
in a full-screen desktop layout. Used by both the Streamlit dashboard page and
the public FastAPI preview route.
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
            # Guard against empty responses or non-image content
            content_type = resp.headers.get("Content-Type", "")
            if not data or "image" not in content_type:
                return ""
            mime = content_type.split(";")[0].strip() or "image/jpeg"
            result = f"data:{mime};base64,{base64.b64encode(data).decode()}"
            _img_cache[url] = result
            return result
    except Exception:
        # Don't cache failures — allow retry on next render
        return ""


def _find_banner_from_profiles(platform_profiles: list[dict], social_links: dict) -> str:
    """Search platform profiles and social links for a usable banner image.

    Checks raw_data in platform_profiles for banner/cover/header image keys,
    then tries well-known banner URL patterns for YouTube channels.
    """
    # 1. Check raw_data in platform_profiles for image keys
    banner_keys = [
        "banner_image_url", "cover_image_url", "header_image_url",
        "banner_url", "cover_url", "header_url", "cover_image",
        "banner_image", "header_image", "bannerExternalUrl",
        "brandingSettings.image.bannerExternalUrl",
    ]
    for profile in platform_profiles:
        raw = profile.get("raw_data")
        if not raw:
            continue
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
        if isinstance(raw, dict):
            for key in banner_keys:
                val = raw.get(key)
                if val and isinstance(val, str) and val.startswith("http"):
                    img = _fetch_image_b64(val)
                    if img:
                        return img
            # Check nested branding (YouTube API format)
            branding = raw.get("brandingSettings", {})
            if isinstance(branding, dict):
                banner = branding.get("image", {}).get("bannerExternalUrl", "")
                if banner:
                    img = _fetch_image_b64(banner)
                    if img:
                        return img

    # 2. Try YouTube channel banner via platform_url or social links
    yt_url = None
    for profile in platform_profiles:
        if profile.get("platform", "").upper() == "YOUTUBE" and profile.get("platform_url"):
            yt_url = profile["platform_url"]
            break
    if not yt_url and social_links:
        yt_url = social_links.get("youtube", "")

    # 3. Try fetching banner from platform profile pages isn't reliable without API,
    #    but we can try the profile image as a last resort for a background
    return ""


def render_store_preview(
    prospect: dict,
    generated_content: list[dict],
    claim_url: str | None = None,
    platform_profiles: list[dict] | None = None,
) -> str:
    """Return complete HTML string for the animated store preview.

    Args:
        prospect: Dict of prospect fields (from the prospects table).
        generated_content: List of dicts from generated_content table rows.
            Each must have at least 'content_type', 'title', and 'body' keys.
        claim_url: Optional URL to the claim page. When provided, a floating
            "Claim Your Store for FREE" banner is shown at the bottom.
        platform_profiles: Optional list of platform profile dicts (from
            platform_profiles table) to search for banner images.

    Returns:
        Full HTML document string.
    """
    # Parse generated content
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
    card_bg = "#FFFFFF"
    text_primary = "#101828"
    text_secondary = "#1D2939"
    text_tertiary = "#667085"
    border_color = "#F3F4F6"
    surface_primary = "#F9FAFB"

    shadow_sm = "0 1px 3px rgba(16,24,40,0.1), 0 1px 2px rgba(16,24,40,0.06)"
    shadow_md = "0 4px 8px -2px rgba(16,24,40,0.1), 0 2px 4px -2px rgba(16,24,40,0.06)"
    shadow_lg = "0 12px 16px -4px rgba(16,24,40,0.08), 0 4px 6px -2px rgba(16,24,40,0.03)"

    coach_name = prospect.get("name", "Coach")
    coach_first = coach_name.split()[0] if coach_name else "Coach"
    store_name = bio_data.get("store_name", coach_name)
    short_bio = bio_data.get("short_bio", prospect.get("bio", ""))
    long_bio = bio_data.get("long_bio", short_bio)
    profile_img = prospect.get("profile_image_url", "")
    banner_img_url = prospect.get("banner_image_url", "")

    # Build hero banner — try primary URL first, then search other platforms
    banner_b64 = _fetch_image_b64(banner_img_url) if banner_img_url else ""
    if not banner_b64:
        social_links = prospect.get("social_links", {})
        if isinstance(social_links, str):
            try:
                social_links = json.loads(social_links)
            except (json.JSONDecodeError, TypeError):
                social_links = {}
        banner_b64 = _find_banner_from_profiles(
            platform_profiles or [], social_links or {}
        )
    has_banner = bool(banner_b64)

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

    # Avatar HTML
    profile_b64 = _fetch_image_b64(profile_img) if profile_img else ""
    initial = coach_name[0] if coach_name else "K"
    if profile_b64:
        nav_avatar = f'<img src="{profile_b64}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;display:block;flex-shrink:0;" />'
        small_avatar = f'<img src="{profile_b64}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;" />'
    else:
        nav_avatar = f'<div style="width:36px;height:36px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="color:#fff;font-weight:600;font-size:14px;line-height:1;">{initial}</span></div>'
        small_avatar = f'<div style="width:40px;height:40px;border-radius:50%;background:{kliq_green};display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-weight:600;font-size:14px;">{initial}</span></div>'

    # Niche pills
    niche_pills_html = ""
    for tag in niche_tags[:4]:
        niche_pills_html += f'<span style="display:inline-block;background:#FFECE7;color:{text_primary};padding:6px 16px;border-radius:20px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">{tag}</span>'

    # --- Revenue notification toasts ---
    revenue_notifications_html = f"""
        <div class="revenue-toast" style="animation-delay:6s;">
            <div style="background:#fff;border-radius:12px;padding:12px 16px;box-shadow:0 8px 24px rgba(0,0,0,0.15);display:flex;align-items:center;gap:12px;min-width:260px;">
                <div style="width:40px;height:40px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:18px;">\U0001f4b0</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:14px;color:{text_primary};line-height:1.3;">$15.00 received</div>
                    <div style="font-size:12px;color:{text_tertiary};margin-top:2px;">AMA question from Sarah M.</div>
                </div>
            </div>
        </div>
        <div class="revenue-toast" style="animation-delay:12s;">
            <div style="background:#fff;border-radius:12px;padding:12px 16px;box-shadow:0 8px 24px rgba(0,0,0,0.15);display:flex;align-items:center;gap:12px;min-width:260px;">
                <div style="width:40px;height:40px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:18px;">\U0001f504</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:14px;color:{text_primary};line-height:1.3;">$29/mo subscriber</div>
                    <div style="font-size:12px;color:{text_tertiary};margin-top:2px;">New member joined</div>
                </div>
            </div>
        </div>
        <div class="revenue-toast" style="animation-delay:18s;">
            <div style="background:#fff;border-radius:12px;padding:12px 16px;box-shadow:0 8px 24px rgba(0,0,0,0.15);display:flex;align-items:center;gap:12px;min-width:260px;">
                <div style="width:40px;height:40px;border-radius:50%;background:#ECFDF5;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:18px;">\U0001f389</span>
                </div>
                <div>
                    <div style="font-weight:600;font-size:14px;color:{text_primary};line-height:1.3;">{product_price_display} earned</div>
                    <div style="font-size:12px;color:{text_tertiary};margin-top:2px;">Program purchase</div>
                </div>
            </div>
        </div>
    """

    # --- AMA chat sequence ---
    ama_chat_html = f"""
        <div style="display:flex;flex-direction:column;gap:10px;">
            <div class="chat-bubble chat-user" style="animation-delay:0.3s;align-self:flex-end;max-width:70%;background:#FFECE7;border-radius:16px 16px 4px 16px;padding:12px 16px;">
                <p style="font-size:14px;color:{text_primary};line-height:150%;margin:0;">What diet plan do you recommend for muscle gain?</p>
            </div>
            <div id="typing-1" class="chat-bubble chat-typing" style="animation-delay:2s;align-self:flex-start;display:flex;align-items:center;gap:8px;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:16px 16px 16px 4px;padding:12px 16px;display:flex;align-items:center;gap:3px;">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
            <div class="chat-bubble chat-coach" style="animation-delay:3s;align-self:flex-start;display:flex;align-items:flex-start;gap:8px;max-width:75%;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:16px 16px 16px 4px;padding:12px 16px;">
                    <p style="font-size:12px;font-weight:600;color:{kliq_green};margin:0 0 4px;">{coach_first}</p>
                    <p style="font-size:14px;color:{text_primary};line-height:150%;margin:0;">Great question! I'd recommend a high-protein diet with lean meats, complex carbs, and healthy fats. My 8-Week Muscle Gain program has a full meal plan!</p>
                </div>
            </div>
            <div class="chat-bubble chat-user" style="animation-delay:4.5s;align-self:flex-end;max-width:70%;background:#FFECE7;border-radius:16px 16px 4px 16px;padding:12px 16px;">
                <p style="font-size:14px;color:{text_primary};line-height:150%;margin:0;">Thanks! What about supplements?</p>
            </div>
            <div id="typing-2" class="chat-bubble chat-typing" style="animation-delay:6s;align-self:flex-start;display:flex;align-items:center;gap:8px;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:16px 16px 16px 4px;padding:12px 16px;display:flex;align-items:center;gap:3px;">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
            <div class="chat-bubble chat-coach" style="animation-delay:7s;align-self:flex-start;display:flex;align-items:flex-start;gap:8px;max-width:75%;">
                {small_avatar}
                <div style="background:{surface_primary};border-radius:16px 16px 16px 4px;padding:12px 16px;">
                    <p style="font-size:12px;font-weight:600;color:{kliq_green};margin:0 0 4px;">{coach_first}</p>
                    <p style="font-size:14px;color:{text_primary};line-height:150%;margin:0;">Creatine and whey protein are essentials. I cover everything in the program \u2014 join and I'll guide you through it!</p>
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
            price_text = (
                f"{currency_sym}{price_cents / 100:.0f}/{interval}"
                if interval
                else f"{currency_sym}{price_cents / 100:.0f}"
            )

        features = product.get("features", [])
        features_html = ""
        for feat in features[:3]:
            features_html += f'<div style="font-size:13px;color:{text_tertiary};padding:2px 0;line-height:1.5;display:flex;align-items:flex-start;gap:6px;"><span style="color:{tangerine};font-size:14px;line-height:1;">&#10003;</span> {feat}</div>'

        product_cards_html += f"""
        <div class="card-hover" style="display:flex;flex-direction:column;padding:12px;gap:16px;border-radius:8px;border:1px solid {border_color};background:#fff;transition:all 0.2s;">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:48px;height:48px;border-radius:8px;background:{surface_primary};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                </div>
                <div style="flex:1;min-width:0;">
                    <div style="font-weight:600;font-size:16px;color:{text_primary};line-height:130%;">{product.get("title", "")}</div>
                    <div style="font-size:14px;color:{tangerine};font-weight:600;margin-top:2px;">{price_text}</div>
                </div>
            </div>
            <p style="font-size:14px;color:{text_tertiary};line-height:160%;margin:0;">{product.get("description", "")[:160]}</p>
            <div style="display:flex;flex-direction:column;gap:4px;">{features_html}</div>
            <button style="background:{kliq_green};color:#fff;border:none;border-radius:10px;padding:12px 28px;font-size:14px;font-weight:600;cursor:pointer;font-family:'Sora',sans-serif;align-self:flex-start;transition:opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">Join Program</button>
        </div>"""

    # --- Blog cards ---
    blog_cards_html = ""
    for blog in blogs[:3]:
        title = blog.get("title", "Untitled")
        excerpt = blog.get("excerpt", "")
        thumbnail = blog.get("thumbnail", "")

        display_title = title if len(title) <= 50 else title[:47] + "..."
        display_excerpt = excerpt if len(excerpt) <= 100 else excerpt[:97] + "..."

        thumb_b64 = ""
        if thumbnail:
            thumb_b64 = _fetch_image_b64(thumbnail)
        if thumb_b64:
            img_html = f'<img src="{thumb_b64}" style="width:100%;height:200px;border-radius:8px 8px 0 0;object-fit:cover;display:block;" />'
        else:
            img_html = f'<div style="width:100%;height:200px;border-radius:8px 8px 0 0;background:linear-gradient(135deg,{kliq_green},{tangerine});"></div>'

        blog_cards_html += f"""
        <div class="card-hover" style="display:flex;flex-direction:column;gap:16px;border-radius:8px;border:1px solid {border_color};background:#fff;overflow:hidden;transition:all 0.2s;">
            {img_html}
            <div style="padding:0 12px 12px;display:flex;flex-direction:column;gap:8px;">
                <p style="color:{text_tertiary};font-size:12px;margin:0;text-transform:uppercase;letter-spacing:0.5px;">Article</p>
                <h4 style="color:{text_primary};font-weight:600;font-size:16px;margin:0;line-height:130%;">{display_title}</h4>
                <p style="color:{text_tertiary};font-size:14px;margin:0;line-height:160%;">{display_excerpt}</p>
                <button style="background:{tangerine};color:#fff;border:none;border-radius:10px;padding:10px 24px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Sora',sans-serif;align-self:flex-start;margin-top:4px;transition:opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">Read now</button>
            </div>
        </div>"""

    # --- Live streams ---
    stream_titles = [p.get("title", f"Live Session {i + 1}") for i, p in enumerate(products[:2])]
    if not stream_titles:
        stream_titles = ["Live Coaching Session", "Q&A with Community"]

    _live_title = stream_titles[0][:50] if stream_titles else "Live Coaching Session"
    _thumb_bg = (
        f"url({profile_b64}) center/cover"
        if profile_b64
        else f"linear-gradient(135deg,{kliq_green},{tangerine})"
    )

    live_stream_main = f"""
        <div class="live-card" style="display:flex;flex-direction:column;gap:16px;border-radius:8px;border:1.5px solid #EF4444;background:#fff;overflow:hidden;position:relative;">
            <div style="width:100%;height:240px;position:relative;overflow:hidden;background:{_thumb_bg};">
                <div style="position:absolute;inset:0;background:rgba(0,0,0,0.45);"></div>
                <div class="shimmer-overlay"></div>
                <div style="position:absolute;top:16px;left:16px;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,0.6);border-radius:8px;padding:6px 12px;">
                    <span class="live-dot"></span>
                    <span style="color:#fff;font-size:12px;font-weight:600;letter-spacing:0.5px;">LIVE</span>
                </div>
                <div style="position:absolute;bottom:16px;right:16px;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,0.6);border-radius:8px;padding:6px 12px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#fff" stroke="none"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                    <span id="viewer-count" style="color:#fff;font-size:12px;font-weight:600;">23</span>
                </div>
                <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;">
                    <div style="width:56px;height:56px;border-radius:50%;background:rgba(255,255,255,0.25);display:flex;align-items:center;justify-content:center;cursor:pointer;backdrop-filter:blur(4px);">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="#fff" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    </div>
                </div>
            </div>
            <div style="padding:0 12px 12px;display:flex;flex-direction:column;gap:8px;">
                <h4 style="font-weight:600;font-size:18px;color:{text_primary};margin:0;line-height:130%;">{_live_title}</h4>
                <p style="font-size:14px;color:{text_tertiary};margin:0;">Streaming now &middot; {coach_first} is live</p>
                <button style="background:#EF4444;color:#fff;border:none;border-radius:10px;padding:12px 28px;font-size:14px;font-weight:600;cursor:pointer;font-family:'Sora',sans-serif;align-self:flex-start;margin-top:4px;">Watch Live</button>
            </div>
        </div>"""

    upcoming_streams_html = ""
    for i, stitle in enumerate(stream_titles[1:3]):
        days = i + 2
        upcoming_streams_html += f"""
        <div class="card-hover" style="display:flex;align-items:center;gap:16px;padding:12px;border-radius:8px;border:1px solid {border_color};background:#fff;transition:all 0.2s;">
            <div style="width:48px;height:48px;border-radius:8px;background:{surface_primary};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <div style="flex:1;min-width:0;">
                <span style="display:inline-block;background:#FFECE7;color:{tangerine};font-size:11px;font-weight:600;padding:3px 10px;border-radius:10px;margin-bottom:6px;">Live in {days} day{"s" if days > 1 else ""}</span>
                <h4 style="font-weight:600;font-size:15px;color:{text_primary};margin:2px 0;line-height:130%;">{stitle[:50]}</h4>
                <p style="font-size:13px;color:{text_tertiary};margin:0;">March 13, 2025 &middot; 7:00 PM</p>
            </div>
            <button style="background:{kliq_green};color:#fff;border:none;border-radius:10px;padding:10px 20px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Sora',sans-serif;flex-shrink:0;">Join</button>
        </div>"""

    # --- Pinned post ---
    pinned_post_html = ""
    if blogs:
        pinned = blogs[0]
        pinned_excerpt = pinned.get("excerpt", "")
        pinned_thumb = pinned.get("thumbnail", "")
        pinned_thumb_b64 = _fetch_image_b64(pinned_thumb) if pinned_thumb else ""
        pinned_img = (
            f'<img src="{pinned_thumb_b64}" style="width:100%;height:220px;border-radius:8px;object-fit:cover;display:block;margin:12px 0;" />'
            if pinned_thumb_b64
            else ""
        )
        pinned_text = pinned_excerpt if len(pinned_excerpt) <= 200 else pinned_excerpt[:197] + "..."

        pinned_post_html = f"""
            <div style="background:{card_bg};border-radius:8px;border:1px solid {border_color};padding:12px;">
                <div style="display:flex;align-items:center;gap:4px;margin-bottom:12px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><path d="M12 2l2.4 7.2H22l-6 4.8 2.4 7.2L12 16.4 5.6 21.2 8 14 2 9.2h7.6z"/></svg>
                    <span style="font-size:12px;font-weight:600;color:{tangerine};text-transform:uppercase;letter-spacing:0.5px;">Pinned</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    {small_avatar}
                    <div>
                        <div style="font-weight:600;font-size:15px;color:{text_primary};">{coach_name}</div>
                        <div style="font-size:12px;color:{text_tertiary};">1 hour ago</div>
                    </div>
                </div>
                {pinned_img}
                <p style="font-size:15px;color:{text_secondary};line-height:170%;margin:8px 0 16px;">{pinned_text}</p>
                <div style="display:flex;align-items:center;gap:20px;border-top:1px solid {border_color};padding-top:12px;">
                    <span style="color:{text_tertiary};font-size:13px;display:flex;align-items:center;gap:4px;cursor:pointer;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                        12
                    </span>
                    <span style="color:{text_tertiary};font-size:13px;display:flex;align-items:center;gap:4px;cursor:pointer;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{text_tertiary}" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        3
                    </span>
                </div>
            </div>"""

    # Star rating SVG helper
    star_svg = f'<svg width="14" height="14" viewBox="0 0 24 24" fill="{tangerine}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    five_stars = star_svg * 5

    # --- CSS (1440px Figma canvas → 393px mobile frame) ---
    css = f"""
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Sora', sans-serif; -webkit-font-smoothing: antialiased; }}
        ::-webkit-scrollbar {{ display: none; }}
        html {{ scroll-behavior: smooth; }}
        body {{ background: #F9FAFB; display:flex; justify-content:center; min-height:100vh; }}

        .figma-canvas {{
            display:flex; max-width:1440px; width:100%; flex-direction:column; align-items:center;
            background: #F9FAFB; margin:0 auto; min-height:100vh;
        }}

        .phone-frame {{
            width:393px; background:#fff; border-radius:20px;
            box-shadow: {shadow_lg};
            overflow:hidden; position:relative;
            margin:32px auto;
        }}

        /* Hero banner — full width edge-to-edge, no padding */
        .hero-banner {{
            width:100%; height:180px; position:relative; overflow:hidden;
        }}
        .hero-banner img {{
            width:100%; height:100%; object-fit:cover; display:block;
        }}
        .hero-gradient {{
            position:absolute; inset:0;
            background:linear-gradient(180deg,transparent 0%,rgba(0,0,0,0.35) 100%);
        }}
        /* Profile section — avatar overlaps banner bottom-left */
        .profile-section {{
            position:relative; padding:0 12px;
        }}
        .profile-avatar {{
            width:80px; height:80px; border-radius:50%; flex-shrink:0;
            border:3px solid #fff; box-shadow:{shadow_sm};
            object-fit:cover; display:block;
            margin-top:-40px; position:relative; z-index:2;
        }}
        .profile-avatar-placeholder {{
            width:80px; height:80px; border-radius:50%; flex-shrink:0;
            border:3px solid #fff; box-shadow:{shadow_sm};
            background:{kliq_green}; display:flex; align-items:center; justify-content:center;
            margin-top:-40px; position:relative; z-index:2;
        }}
        .profile-avatar-no-banner {{
            width:80px; height:80px; border-radius:50%; flex-shrink:0;
            border:3px solid #fff; box-shadow:{shadow_sm};
            object-fit:cover; display:block;
            margin-top:0; position:relative; z-index:2;
        }}
        .profile-avatar-placeholder-no-banner {{
            width:80px; height:80px; border-radius:50%; flex-shrink:0;
            border:3px solid #fff; box-shadow:{shadow_sm};
            background:{kliq_green}; display:flex; align-items:center; justify-content:center;
            margin-top:0; position:relative; z-index:2;
        }}
        .profile-name {{
            display:flex; flex-direction:column; gap:4px; padding:8px 0;
        }}

        .card-hover:hover {{ box-shadow: {shadow_md}; border-color: #D0D5DD; transform: translateY(-2px); }}

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

        @keyframes notifSlide {{
            0% {{ transform:translateX(120%); opacity:0; }}
            5% {{ transform:translateX(0); opacity:1; }}
            25% {{ transform:translateX(0); opacity:1; }}
            30% {{ transform:translateX(120%); opacity:0; }}
            100% {{ transform:translateX(120%); opacity:0; }}
        }}
        .revenue-toast {{
            position:fixed; right:24px; bottom:80px; z-index:100;
            transform:translateX(120%); opacity:0;
            animation: notifSlide 24s ease-in-out infinite;
        }}

        #ama-section {{
            max-height:800px; overflow:hidden;
            transition: max-height 0.8s ease-in-out, padding 0.8s ease-in-out, opacity 0.6s ease-in-out;
        }}
        #ama-section.collapsed {{
            max-height:60px; padding:12px 16px !important; opacity:0.85;
        }}

        @keyframes livePulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
        @keyframes shimmer {{
            0% {{ transform:translateX(-100%); }}
            100% {{ transform:translateX(100%); }}
        }}
        @keyframes liveGlow {{
            0%,100% {{ box-shadow:0 0 8px rgba(239,68,68,0.15); }}
            50% {{ box-shadow:0 0 16px rgba(239,68,68,0.35); }}
        }}
        .live-card {{ animation: liveGlow 2s ease-in-out infinite; }}
        .live-dot {{
            width:8px; height:8px; border-radius:50%; background:#EF4444;
            animation: livePulse 1.5s ease-in-out infinite;
            display:inline-block;
        }}
        .shimmer-overlay {{ position:absolute; inset:0; overflow:hidden; }}
        .shimmer-overlay::after {{
            content:''; position:absolute; inset:0;
            background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent);
            animation: shimmer 2.5s infinite;
        }}

        .section-title {{
            font-weight:600; font-size:18px; color:{text_primary}; letter-spacing:-0.02em; line-height:130%;
        }}
        .section-header {{
            display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;
        }}
        .see-all {{
            font-size:12px; color:{text_secondary}; cursor:pointer; border:1px solid {border_color};
            border-radius:8px; padding:5px 12px; font-weight:500; text-decoration:none;
            transition: background 0.2s;
        }}
        .see-all:hover {{ background:{surface_primary}; }}

        /* Horizontal scroll card rows */
        .hscroll {{
            display:flex; gap:12px; overflow-x:auto; scroll-snap-type:x mandatory;
            padding-bottom:4px;
        }}
        .hscroll > * {{ flex-shrink:0; width:320px; scroll-snap-align:start; }}
    """

    # --- Assemble full HTML (393px mobile frame on desktop canvas) ---
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{css}</style>
</head>
<body>

    {revenue_notifications_html}

    <div class="figma-canvas">
    <div class="phone-frame">

    <!-- TOP NAV BAR -->
    <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:#fff;border-bottom:1px solid {
        border_color
    };">
        <div style="display:flex;align-items:center;gap:8px;">
            {nav_avatar}
            <span style="font-weight:600;font-size:14px;color:{
        text_primary
    };white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;">{
        store_name
    }</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:12px;color:{text_tertiary};cursor:pointer;">Home</span>
            <span style="font-size:12px;color:{text_tertiary};cursor:pointer;">Program</span>
            <span style="font-size:12px;color:{text_tertiary};cursor:pointer;">Library</span>
        </div>
    </div>

    <!-- HERO BANNER (only if image is available) -->
    {
        f"""<div class="hero-banner">
        <img src="{banner_b64}" />
        <div class="hero-gradient"></div>
        {f'<div style="position:absolute;bottom:16px;right:16px;display:flex;flex-direction:column;gap:6px;z-index:2;">{niche_pills_html}</div>' if niche_pills_html else ''}
    </div>"""
        if has_banner
        else (f'<div style="padding:8px 12px;display:flex;flex-wrap:wrap;gap:6px;">{niche_pills_html}</div>' if niche_pills_html else '')
    }

    <!-- PROFILE -->
    <div class="profile-section" {"" if has_banner else 'style="padding-top:12px;"'}>
        {
        f'<img class="{"profile-avatar" if has_banner else "profile-avatar-no-banner"}" src="{profile_b64}" />'
        if profile_b64
        else f'<div class="{"profile-avatar-placeholder" if has_banner else "profile-avatar-placeholder-no-banner"}"><span style="font-size:28px;font-weight:600;color:#fff;line-height:1;">{initial}</span></div>'
    }
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div class="profile-name">
                <h1 style="font-size:18px;font-weight:600;color:{
        text_primary
    };margin:0;line-height:130%;letter-spacing:-0.02em;">{store_name}</h1>
                {
        ""
        if not niche_subtitle
        else f'<p style="font-size:13px;color:{text_tertiary};margin:0;">{niche_subtitle}</p>'
    }
            </div>
            <div style="display:flex;gap:8px;">
                <button style="border:1px solid {
        border_color
    };background:transparent;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:500;color:{
        text_primary
    };cursor:pointer;font-family:'Sora',sans-serif;">Log in</button>
                <button style="background:{
        tangerine
    };color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Sora',sans-serif;">Sign up</button>
            </div>
        </div>
    </div>

    <!-- CONTENT FEED (12px padding — narrower than banner) -->
    <div style="display:flex;flex-direction:column;gap:16px;padding:12px;align-self:stretch;">

        <!-- ASK ME ANYTHING -->
        <section>
            <div class="section-header">
                <h2 class="section-title">Ask me anything</h2>
                <span style="font-weight:600;font-size:16px;color:{text_primary};">$15</span>
            </div>
            <div id="ama-section" style="border-radius:8px;border:1px solid {
        border_color
    };background:#fff;padding:12px;">
                <p style="color:{
        text_tertiary
    };font-size:13px;margin:0 0 12px;line-height:160%;">Ask a question and get a personal response.</p>
                {ama_chat_html}
            </div>
        </section>

        <!-- PINNED POST -->
        {
        ""
        if not pinned_post_html
        else f'''
        <section>
            <div class="section-header">
                <h2 class="section-title">Pinned post</h2>
                <a class="see-all" href="#">See all</a>
            </div>
            {pinned_post_html}
        </section>
        '''
    }

        <!-- LIVE STREAMS -->
        <section>
            <div class="section-header">
                <h2 class="section-title">Live streams</h2>
                <a class="see-all" href="#">See all</a>
            </div>
            {live_stream_main}
            <div style="display:flex;flex-direction:column;gap:12px;margin-top:12px;">
                {upcoming_streams_html}
            </div>
        </section>

        <!-- EDUCATION -->
        {
        ""
        if not blogs
        else f'''
        <section id="education">
            <div class="section-header">
                <h2 class="section-title">Education</h2>
                <a class="see-all" href="#">See all</a>
            </div>
            <div class="hscroll">
                {blog_cards_html}
            </div>
        </section>
        '''
    }

        <!-- PROGRAMS -->
        {
        ""
        if not products
        else f'''
        <section id="programs">
            <div class="section-header">
                <h2 class="section-title">Programs</h2>
                <a class="see-all" href="#">See all</a>
            </div>
            <div class="hscroll">
                {product_cards_html}
            </div>
        </section>
        '''
    }

        <!-- ABOUT + STATS -->
        <section>
            <div class="section-header">
                <h2 class="section-title">About {coach_first}</h2>
            </div>
            <div style="background:{card_bg};border-radius:8px;border:1px solid {
        border_color
    };padding:12px;margin-bottom:12px;">
                <p style="font-size:14px;color:{text_secondary};line-height:180%;margin:0;">{
        long_bio[:400]
        if long_bio
        else short_bio[:400]
        if short_bio
        else "Passionate coach helping you achieve your fitness and wellness goals."
    }</p>
            </div>
            <div style="display:flex;gap:12px;">
                <div style="flex:1 0 0;display:flex;padding:12px;flex-direction:column;gap:6px;border-radius:8px;border:1px solid {
        border_color
    };background:#fff;">
                    <span style="font-weight:700;font-size:24px;color:{
        text_primary
    };line-height:120%;letter-spacing:-0.02em;">500+</span>
                    <span style="font-size:12px;color:{text_tertiary};">Members</span>
                </div>
                <div style="flex:1 0 0;display:flex;padding:12px;flex-direction:column;gap:6px;border-radius:8px;border:1px solid {
        border_color
    };background:#fff;">
                    <span style="font-weight:700;font-size:24px;color:{
        text_primary
    };line-height:120%;letter-spacing:-0.02em;">50+</span>
                    <span style="font-size:12px;color:{text_tertiary};">Programs</span>
                </div>
                <div style="flex:1 0 0;display:flex;padding:12px;flex-direction:column;gap:6px;border-radius:8px;border:1px solid {
        border_color
    };background:#fff;">
                    <div style="display:flex;align-items:center;gap:4px;">
                        <span style="font-weight:700;font-size:24px;color:{
        text_primary
    };line-height:120%;">4.9</span>
                        {star_svg}
                    </div>
                    <span style="font-size:12px;color:{text_tertiary};">Rating</span>
                </div>
            </div>
        </section>

        <!-- COMMUNITY -->
        <section id="community">
            <div class="section-header">
                <h2 class="section-title">Community</h2>
                <a class="see-all" href="#">See all</a>
            </div>
            <div class="hscroll">
                <div style="display:flex;padding:12px;flex-direction:column;gap:16px;border-radius:8px;border:1px solid {
        border_color
    };background:#fff;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="width:40px;height:40px;border-radius:50%;background:#FFECE7;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="font-size:14px;font-weight:600;color:{
        tangerine
    };">S</span></div>
                        <div>
                            <span style="font-weight:600;font-size:14px;color:{
        text_primary
    };">Sarah M.</span>
                            <div style="display:flex;gap:2px;margin-top:2px;">{five_stars}</div>
                        </div>
                    </div>
                    <p style="font-size:14px;color:{
        text_secondary
    };line-height:170%;margin:0;">"This program completely changed my routine. I'm stronger and more confident."</p>
                </div>
                <div style="display:flex;padding:12px;flex-direction:column;gap:16px;border-radius:8px;border:1px solid {
        border_color
    };background:#fff;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="width:40px;height:40px;border-radius:50%;background:#EBFCFF;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><span style="font-size:14px;font-weight:600;color:#1C3838;">J</span></div>
                        <div>
                            <span style="font-weight:600;font-size:14px;color:{
        text_primary
    };">James T.</span>
                            <div style="display:flex;gap:2px;margin-top:2px;">{five_stars}</div>
                        </div>
                    </div>
                    <p style="font-size:14px;color:{
        text_secondary
    };line-height:170%;margin:0;">"The nutrition plans alone are worth it. Lost 8kg in 3 months."</p>
                </div>
            </div>
        </section>

    </div>

    <!-- FOOTER -->
    <footer style="border-top:1px solid {
        border_color
    };padding:24px;display:flex;flex-direction:column;align-items:center;gap:12px;">
        <div style="display:flex;align-items:center;gap:16px;">
            <a href="#" style="color:{
        text_tertiary
    };"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg></a>
            <a href="#" style="color:{
        text_tertiary
    };"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg></a>
            <a href="#" style="color:{
        text_tertiary
    };"><svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 3.993L9 16z"/></svg></a>
        </div>
        <p style="font-size:12px;color:{
        text_tertiary
    };">Powered by <span style="font-weight:600;color:{kliq_green};">KLIQ</span></p>
    </footer>

    </div><!-- end phone-frame -->
    </div><!-- end figma-canvas -->

{
        f'''
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
                This store was built for you, {coach_first}!
            </span>
            <a href="{claim_url}" style="
                display:inline-flex;align-items:center;gap:8px;
                background:#FF9F88;color:{kliq_green};
                padding:10px 24px;border-radius:8px;
                font-size:14px;font-weight:700;font-family:Sora,sans-serif;
                text-decoration:none;white-space:nowrap;
                transition:transform 0.15s, box-shadow 0.15s;
            " onmouseover="this.style.transform='scale(1.05)';this.style.boxShadow='0 4px 12px rgba(255,159,136,0.4)'"
               onmouseout="this.style.transform='scale(1)';this.style.boxShadow='none'">
                Claim Your Store for FREE
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </a>
        </div>
        <button onclick="document.getElementById('claim-banner').style.display='none'" style="
            background:none;border:none;color:rgba(255,255,255,0.6);cursor:pointer;
            padding:4px;font-size:18px;line-height:1;flex-shrink:0;
        " onmouseover="this.style.color='#fff'" onmouseout="this.style.color='rgba(255,255,255,0.6)'">&times;</button>
    </div>
    <style>
        @keyframes slideUpBanner {{
            from {{ transform:translateY(100%); }}
            to {{ transform:translateY(0); }}
        }}
    </style>
'''
        if claim_url
        else ""
    }

<script>
(function(){{
    var el=document.getElementById('viewer-count');
    if(el){{var n=23;setInterval(function(){{n+=Math.floor(Math.random()*3)+1;if(n>48)n=23;el.textContent=n;}},3000);}}
    setTimeout(function(){{var t=document.getElementById('typing-1');if(t)t.style.display='none';}},3000);
    setTimeout(function(){{var t=document.getElementById('typing-2');if(t)t.style.display='none';}},7000);
    setTimeout(function(){{
        var ama=document.getElementById('ama-section');
        if(ama)ama.classList.add('collapsed');
    }},9000);
}})();
</script>
</body>
</html>"""

    return full_html
