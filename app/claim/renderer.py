"""HTML renderers for the claim flow and onboarding pages.

All pages use the KLIQ design system: Sora font, kliqGreen #1C3838,
tangerine #FF9F88, ivory #FFFDF9. Mobile-first centered card layout.
"""

from app.preview.renderer import _fetch_image_b64

# ─── Design Tokens ────────────────────────────────────────────────────────────

KLIQ_GREEN = "#1C3838"
TANGERINE = "#FF9F88"
IVORY = "#FFFDF9"
CARD_BG = "#FFFFFF"
TEXT_PRIMARY = "#101828"
TEXT_SECONDARY = "#1D2939"
TEXT_TERTIARY = "#667085"
BORDER = "#EAECF0"
SURFACE = "#F9FAFB"
POSITIVE = "#039855"
NEGATIVE = "#D92D20"
SHADOW = "0 4px 8px -2px rgba(16,24,40,0.1), 0 2px 4px -2px rgba(16,24,40,0.06)"

_HEAD = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Sora',sans-serif;-webkit-font-smoothing:antialiased;}}
body{{background:{IVORY};min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px 16px;}}
.card{{background:{CARD_BG};border-radius:16px;box-shadow:{SHADOW};width:100%;max-width:480px;padding:40px 32px;}}
.logo{{text-align:center;margin-bottom:24px;}}
.logo span{{font-weight:700;font-size:22px;color:{KLIQ_GREEN};letter-spacing:-0.02em;}}
input[type="password"],input[type="email"]{{width:100%;padding:10px 14px;border:1px solid {BORDER};border-radius:8px;font-size:14px;font-family:'Sora',sans-serif;outline:none;transition:border-color 0.15s;}}
input:focus{{border-color:{KLIQ_GREEN};box-shadow:0 0 0 2px rgba(28,56,56,0.1);}}
input[readonly]{{background:{SURFACE};color:{TEXT_TERTIARY};cursor:default;}}
label{{display:block;font-size:13px;font-weight:600;color:{TEXT_PRIMARY};margin-bottom:6px;}}
.field{{margin-bottom:16px;}}
.btn{{display:block;width:100%;padding:12px 24px;background:{KLIQ_GREEN};color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;font-family:'Sora',sans-serif;cursor:pointer;transition:background 0.15s;}}
.btn:hover{{background:#0E2325;}}
.btn:disabled{{opacity:0.6;cursor:not-allowed;}}
.btn-outline{{display:inline-block;padding:8px 16px;border:1px solid {KLIQ_GREEN};color:{KLIQ_GREEN};border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;transition:background 0.15s;}}
.btn-outline:hover{{background:{SURFACE};}}
.error-box{{background:#FEF3F2;border:1px solid #FECDCA;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:{NEGATIVE};}}
.footer{{text-align:center;margin-top:24px;font-size:12px;color:{TEXT_TERTIARY};}}
.footer strong{{color:{KLIQ_GREEN};}}
</style>
"""

_FOOTER_HTML = f"""
<div class="footer">Powered by <strong>KLIQ</strong></div>
"""


def render_claim_page(
    prospect: dict,
    content_counts: dict,
    errors: list[str] | None = None,
) -> str:
    """Render the claim page with password form.

    Args:
        prospect: Prospect dict with name, email, profile_image_url, etc.
        content_counts: Dict with blog_count and product_count.
        errors: Optional list of validation error messages to display.
    """
    first_name = prospect.get("first_name") or (prospect.get("name", "").split()[0] if prospect.get("name") else "Coach")
    email = prospect.get("email", "")
    token = prospect.get("claim_token", "")
    store_name = prospect.get("name", "Your Store")
    profile_url = prospect.get("profile_image_url", "")
    blog_count = content_counts.get("blog_count", 0)
    product_count = content_counts.get("product_count", 0)

    # Avatar
    profile_b64 = _fetch_image_b64(profile_url) if profile_url else ""
    initial = first_name[0].upper() if first_name else "K"
    if profile_b64:
        avatar = f'<img src="{profile_b64}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;" />'
    else:
        avatar = f'<div style="width:48px;height:48px;border-radius:50%;background:{KLIQ_GREEN};display:flex;align-items:center;justify-content:center;"><span style="color:#fff;font-weight:600;font-size:18px;">{initial}</span></div>'

    # Stats line
    stats_parts = []
    if blog_count:
        stats_parts.append(f"{blog_count} blog post{'s' if blog_count != 1 else ''}")
    if product_count:
        stats_parts.append(f"{product_count} program{'s' if product_count != 1 else ''}")
    stats_line = " and ".join(stats_parts) + " created for you" if stats_parts else "Your personalized store is ready"

    # Error HTML
    error_html = ""
    if errors:
        msgs = "".join(f"<div>{e}</div>" for e in errors)
        error_html = f'<div class="error-box">{msgs}</div>'

    return f"""{_HEAD}
<title>Claim Your Store | KLIQ</title>
</head>
<body>
<div class="card">
    <div class="logo"><span>KLIQ</span></div>

    <!-- Greeting -->
    <div style="text-align:center;margin-bottom:24px;">
        <div style="display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:12px;">
            {avatar}
            <div style="text-align:left;">
                <div style="font-weight:600;font-size:15px;color:{TEXT_PRIMARY};">{store_name}</div>
                <div style="font-size:12px;color:{TEXT_TERTIARY};">{stats_line}</div>
            </div>
        </div>
        <h1 style="font-size:24px;font-weight:700;color:{KLIQ_GREEN};line-height:130%;margin-bottom:4px;">Hi {first_name}, your store is ready</h1>
        <p style="font-size:14px;color:{TEXT_SECONDARY};">Set your password to claim it.</p>
    </div>

    <!-- Form -->
    {error_html}
    <form method="POST" action="/claim" id="claim-form">
        <input type="hidden" name="token" value="{token}" />

        <div class="field">
            <label>Email</label>
            <input type="email" value="{email}" readonly />
        </div>

        <div class="field">
            <label>Password</label>
            <div style="position:relative;">
                <input type="password" name="password" id="pw" placeholder="At least 8 characters" required minlength="8" />
                <button type="button" onclick="togglePw('pw')" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:{TEXT_TERTIARY};font-size:12px;">Show</button>
            </div>
        </div>

        <div class="field">
            <label>Confirm Password</label>
            <div style="position:relative;">
                <input type="password" name="password_confirm" id="pw2" placeholder="Re-enter your password" required minlength="8" />
                <button type="button" onclick="togglePw('pw2')" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:{TEXT_TERTIARY};font-size:12px;">Show</button>
            </div>
            <div id="match-error" style="color:{NEGATIVE};font-size:12px;margin-top:4px;display:none;">Passwords do not match</div>
        </div>

        <button type="submit" class="btn" id="submit-btn">Claim My Store</button>
    </form>

    <p style="text-align:center;font-size:11px;color:{TEXT_TERTIARY};margin-top:12px;">
        By claiming your store, you agree to KLIQ's Terms of Service.
    </p>

    {_FOOTER_HTML}
</div>

<script>
function togglePw(id){{
    var el=document.getElementById(id);
    var btn=el.nextElementSibling;
    if(el.type==='password'){{el.type='text';btn.textContent='Hide';}}
    else{{el.type='password';btn.textContent='Show';}}
}}
document.getElementById('claim-form').addEventListener('submit',function(e){{
    var pw=document.getElementById('pw').value;
    var pw2=document.getElementById('pw2').value;
    var err=document.getElementById('match-error');
    if(pw!==pw2){{e.preventDefault();err.style.display='block';return;}}
    if(pw.length<8){{e.preventDefault();err.textContent='Password must be at least 8 characters';err.style.display='block';return;}}
    err.style.display='none';
    var btn=document.getElementById('submit-btn');
    btn.disabled=true;btn.textContent='Activating...';
}});
document.getElementById('pw2').addEventListener('input',function(){{
    document.getElementById('match-error').style.display='none';
}});
</script>
</body>
</html>"""


def render_welcome_page(prospect: dict, content_counts: dict) -> str:
    """Render the post-claim onboarding page."""
    first_name = prospect.get("first_name") or (prospect.get("name", "").split()[0] if prospect.get("name") else "Coach")
    store_name = prospect.get("name", "Your Store")
    store_url = prospect.get("kliq_store_url", "")
    app_id = prospect.get("kliq_application_id")
    dashboard_url = f"https://admin.joinkliq.io/app/{app_id}" if app_id else store_url
    blog_count = content_counts.get("blog_count", 0)
    product_count = content_counts.get("product_count", 0)

    # Step cards
    def _step(num, title, desc, cta_text, cta_url):
        return f"""
        <div style="display:flex;gap:14px;padding:16px;background:{CARD_BG};border-left:3px solid {TANGERINE};border-radius:0 8px 8px 0;border:1px solid {BORDER};border-left:3px solid {TANGERINE};">
            <div style="width:28px;height:28px;border-radius:50%;background:{TANGERINE};display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="color:#fff;font-weight:700;font-size:13px;">{num}</span>
            </div>
            <div style="flex:1;">
                <div style="font-weight:600;font-size:14px;color:{TEXT_PRIMARY};margin-bottom:4px;">{title}</div>
                <div style="font-size:13px;color:{TEXT_TERTIARY};line-height:150%;margin-bottom:10px;">{desc}</div>
                <a href="{cta_url}" target="_blank" class="btn-outline">{cta_text}</a>
            </div>
        </div>"""

    steps_html = f"""
    {_step(1, "Explore Your Store", "See what we've built. Review your products, blog posts, and branding.", "View Store", store_url or dashboard_url)}
    {_step(2, "Customize Your Content", "Update product descriptions, prices, and add your own content.", "Open Dashboard", dashboard_url)}
    {_step(3, "Connect Stripe", "Start accepting payments by connecting your Stripe account.", "Set Up Payments", f"{dashboard_url}/payments" if dashboard_url else "#")}
    {_step(4, "Share Your Store", "Send your store link to clients and share on social media.", "Copy Link", "#")}
    """

    return f"""{_HEAD}
<title>Welcome to KLIQ</title>
<style>
@keyframes confettiFall{{
    0%{{transform:translateY(-10px) rotate(0deg);opacity:1;}}
    100%{{transform:translateY(100vh) rotate(720deg);opacity:0;}}
}}
.confetti{{position:fixed;top:-10px;width:8px;height:8px;z-index:1000;animation:confettiFall 3s ease-out forwards;pointer-events:none;}}
</style>
</head>
<body>
<div class="card" style="position:relative;z-index:1;">

    <!-- Success Header -->
    <div style="text-align:center;margin-bottom:28px;">
        <div style="width:56px;height:56px;border-radius:50%;background:#ECFDF3;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{POSITIVE}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <h1 style="font-size:26px;font-weight:700;color:{KLIQ_GREEN};line-height:130%;">Welcome to KLIQ, {first_name}!</h1>
        <p style="font-size:15px;color:{TEXT_SECONDARY};margin-top:4px;">{store_name} is now live</p>
    </div>

    <!-- What We Built -->
    <div style="background:{SURFACE};border-radius:10px;padding:16px;margin-bottom:24px;">
        <div style="font-weight:600;font-size:13px;color:{TEXT_PRIMARY};margin-bottom:12px;">What we built for you</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:32px;height:32px;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{KLIQ_GREEN}" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                </div>
                <span style="font-size:13px;color:{TEXT_SECONDARY};">{blog_count} blog post{'s' if blog_count != 1 else ''}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:32px;height:32px;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{KLIQ_GREEN}" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                </div>
                <span style="font-size:13px;color:{TEXT_SECONDARY};">{product_count} program{'s' if product_count != 1 else ''}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:32px;height:32px;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{KLIQ_GREEN}" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                </div>
                <span style="font-size:13px;color:{TEXT_SECONDARY};">Custom branding</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:32px;height:32px;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{KLIQ_GREEN}" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
                </div>
                <span style="font-size:13px;color:{TEXT_SECONDARY};">SEO optimized</span>
            </div>
        </div>
    </div>

    <!-- Next Steps -->
    <div style="margin-bottom:24px;">
        <div style="font-weight:600;font-size:15px;color:{TEXT_PRIMARY};margin-bottom:12px;">Your next steps</div>
        <div style="display:flex;flex-direction:column;gap:10px;">
            {steps_html}
        </div>
    </div>

    <!-- Share URL -->
    <div style="margin-bottom:24px;">
        <label>Your store link</label>
        <div style="display:flex;gap:8px;margin-top:6px;">
            <input type="text" id="store-url" value="{store_url or dashboard_url}" readonly style="flex:1;padding:10px 14px;border:1px solid {BORDER};border-radius:8px;font-size:13px;font-family:'Sora',sans-serif;background:{SURFACE};color:{TEXT_PRIMARY};" />
            <button onclick="copyUrl()" id="copy-btn" style="padding:10px 16px;background:{KLIQ_GREEN};color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Sora',sans-serif;white-space:nowrap;">Copy</button>
        </div>
    </div>

    <!-- Help -->
    <div style="background:{SURFACE};border-radius:10px;padding:16px;text-align:center;">
        <div style="font-weight:600;font-size:14px;color:{TEXT_PRIMARY};margin-bottom:4px;">Need help?</div>
        <p style="font-size:13px;color:{TEXT_TERTIARY};line-height:150%;">Our team is here to help you succeed. Reply to your welcome email or contact <a href="mailto:growth@joinkliq.io" style="color:{KLIQ_GREEN};font-weight:600;text-decoration:none;">growth@joinkliq.io</a></p>
    </div>

    {_FOOTER_HTML}
</div>

<script>
function copyUrl(){{
    var el=document.getElementById('store-url');
    navigator.clipboard.writeText(el.value).then(function(){{
        var btn=document.getElementById('copy-btn');
        btn.textContent='Copied!';
        setTimeout(function(){{btn.textContent='Copy';}},2000);
    }});
}}
// Confetti
(function(){{
    var colors=['{KLIQ_GREEN}','{TANGERINE}','#DEFE9C','#9CF0FF','#39938F'];
    for(var i=0;i<30;i++){{
        var c=document.createElement('div');
        c.className='confetti';
        c.style.left=Math.random()*100+'vw';
        c.style.background=colors[Math.floor(Math.random()*colors.length)];
        c.style.animationDelay=Math.random()*1.5+'s';
        c.style.animationDuration=(2+Math.random()*2)+'s';
        c.style.borderRadius=Math.random()>0.5?'50%':'0';
        document.body.appendChild(c);
    }}
    setTimeout(function(){{
        document.querySelectorAll('.confetti').forEach(function(el){{el.remove();}});
    }},5000);
}})();
</script>
</body>
</html>"""


def render_error_page(
    title: str,
    message: str,
    cta_url: str | None = None,
    cta_text: str | None = None,
) -> str:
    """Render a generic error page."""
    cta_html = ""
    if cta_url and cta_text:
        cta_html = f'<a href="{cta_url}" class="btn" style="display:inline-block;width:auto;margin-top:16px;">{cta_text}</a>'

    return f"""{_HEAD}
<title>{title} | KLIQ</title>
</head>
<body>
<div class="card" style="text-align:center;">
    <div class="logo"><span>KLIQ</span></div>
    <div style="width:56px;height:56px;border-radius:50%;background:#FEF3F2;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{NEGATIVE}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
    </div>
    <h1 style="font-size:22px;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:8px;">{title}</h1>
    <p style="font-size:14px;color:{TEXT_SECONDARY};line-height:150%;">{message}</p>
    {cta_html}
    {_FOOTER_HTML}
</div>
</body>
</html>"""


def render_already_claimed_page(prospect: dict) -> str:
    """Render the 'already claimed' page with a link to the dashboard."""
    app_id = prospect.get("kliq_application_id")
    store_url = prospect.get("kliq_store_url", "")
    dashboard_url = f"https://admin.joinkliq.io/app/{app_id}" if app_id else store_url
    first_name = prospect.get("first_name") or (prospect.get("name", "").split()[0] if prospect.get("name") else "Coach")

    return f"""{_HEAD}
<title>Store Already Claimed | KLIQ</title>
</head>
<body>
<div class="card" style="text-align:center;">
    <div class="logo"><span>KLIQ</span></div>
    <div style="width:56px;height:56px;border-radius:50%;background:#ECFDF3;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{POSITIVE}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
    </div>
    <h1 style="font-size:22px;font-weight:700;color:{TEXT_PRIMARY};margin-bottom:8px;">You're all set, {first_name}!</h1>
    <p style="font-size:14px;color:{TEXT_SECONDARY};line-height:150%;margin-bottom:20px;">This store has already been claimed. Log in to your dashboard to manage it.</p>
    <a href="{dashboard_url}" class="btn" style="display:inline-block;width:auto;">Go to Dashboard</a>
    {_FOOTER_HTML}
</div>
</body>
</html>"""
