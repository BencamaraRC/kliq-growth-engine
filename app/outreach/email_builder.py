"""Build personalized outreach emails from templates and prospect data.

Each email step has a Jinja2 HTML template that gets personalized with
the prospect's name, store details, claim URL, and branding colors.

Platform-specific initial outreach (Step 1) + 6 shared follow-ups (Steps 2-7)
+ claim confirmation (Step 8) + 2 onboarding follow-ups (Steps 9-10).
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# Platform → initial outreach template mapping
PLATFORM_INITIAL_TEMPLATES = {
    "SKOOL": "initial_skool.html",
    "PATREON": "initial_patreon.html",
    "YOUTUBE": "initial_youtube.html",
    "KAJABI": "initial_kajabi.html",
    # ICF-certified coaches (LinkedIn outreach)
    "ICF": "initial_icf.html",
    # Subscription platforms (OnlyFans, Stan, Fansly, etc.)
    "ONLYFANS": "initial_subscription.html",
    "STAN": "initial_subscription.html",
    "TIKTOK": "initial_subscription.html",
    "INSTAGRAM": "initial_subscription.html",
    "WEBSITE": "initial_subscription.html",
}

# Platform → initial outreach subject line
PLATFORM_INITIAL_SUBJECTS = {
    "SKOOL": "Quick question about your Skool community, {{ first_name }}",
    "PATREON": "Your Patreon supporters deserve your own platform, {{ first_name }}",
    "YOUTUBE": "Your YouTube content is worth more than ad revenue, {{ first_name }}",
    "KAJABI": "Same features, plus a branded app, for a fraction of the cost, {{ first_name }}",
    # ICF-certified coaches (LinkedIn outreach)
    "ICF": "Great connecting on LinkedIn, {{ first_name }} — your coaching deserves its own app",
    # Subscription platforms — niche-driven subject
    "ONLYFANS": "Your {{ niche }} content deserves its own platform, {{ first_name }}",
    "STAN": "Your {{ niche }} content deserves its own platform, {{ first_name }}",
    "TIKTOK": "Your {{ niche }} content deserves its own platform, {{ first_name }}",
    "INSTAGRAM": "Your {{ niche }} content deserves its own platform, {{ first_name }}",
    "WEBSITE": "Your {{ niche }} content deserves its own platform, {{ first_name }}",
}

# Email step configuration: 7 pre-claim + 1 claim + 2 onboarding = 10 total
STEPS = {
    # --- Pre-claim outreach sequence ---
    1: {
        "template": None,  # Selected by platform via PLATFORM_INITIAL_TEMPLATES
        "subject": None,  # Selected by platform via PLATFORM_INITIAL_SUBJECTS
        "delay_days": 0,
        "name": "initial_outreach",
    },
    2: {
        "template": "followup_1_nudge.html",
        "subject": "Did you get a chance to see it, {{ first_name }}?",
        "delay_days": 3,
        "name": "gentle_nudge",
    },
    3: {
        "template": "followup_2_value.html",
        "subject": "Something I thought you'd find interesting, {{ first_name }}",
        "delay_days": 6,
        "name": "value_add",
    },
    4: {
        "template": "followup_3_social_proof.html",
        "subject": "What other {{ niche }} coaches are doing right now",
        "delay_days": 10,
        "name": "social_proof",
    },
    5: {
        "template": "followup_4_preview_activity.html",
        "subject": "Your store preview has been viewed {{ view_count }} times, {{ first_name }}",
        "delay_days": 14,
        "name": "preview_activity",
    },
    6: {
        "template": "followup_5_new_angle.html",
        "subject": "One thing I should have mentioned, {{ first_name }}",
        "delay_days": 21,
        "name": "new_angle",
    },
    7: {
        "template": "followup_6_breakup.html",
        "subject": "I'll leave this with you, {{ first_name }}",
        "delay_days": 28,
        "name": "breakup",
    },
    # --- Post-claim ---
    8: {
        "template": "claimed_confirmation.html",
        "subject": "Welcome to KLIQ, {{ first_name }}!",
        "delay_days": 0,  # Sent immediately on claim
        "name": "claim_confirmation",
    },
    # --- Onboarding follow-ups ---
    9: {
        "template": "onboarding_review_content.html",
        "subject": "{{ first_name }}, review your store content",
        "delay_days": 1,  # +1 day after claim
        "skip_if": "content_reviewed",
        "name": "onboarding_review",
    },
    10: {
        "template": "onboarding_first_share.html",
        "subject": "{{ first_name }}, share with your first client",
        "delay_days": 3,  # +3 days after claim
        "skip_if": "first_share",
        "name": "onboarding_share",
    },
}

# Step ranges for easy iteration
PRE_CLAIM_STEPS = list(range(1, 8))  # Steps 1-7
POST_CLAIM_STEPS = [8]
ONBOARDING_STEPS = [9, 10]


@dataclass
class BuiltEmail:
    """A fully constructed email ready to send."""

    to_email: str
    to_name: str
    subject: str
    html_content: str
    step: int
    tags: list[str]


# AI niche hook templates for subscription platform emails
NICHE_HOOKS = {
    "fitness": "I came across your fitness content and was really impressed by the programmes you've put together. The way you structure your workout plans shows a real understanding of what keeps people consistent.",
    "yoga": "I've been looking at what you're doing in the yoga and mindfulness space, and your approach to breathwork and meditation really stands out. It's clear your audience trusts you.",
    "nutrition": "I came across your nutrition content and the meal plans you've created are genuinely impressive. The level of detail you put into your guides shows real expertise.",
    "lifestyle": "I've been following your content and the personal brand you've built is seriously impressive. The way you connect with your audience on a personal level is something most creators struggle with.",
    "dance": "Your movement content caught my eye. The way you teach and the energy you bring to your sessions is the kind of thing that builds a loyal audience.",
    "personal development": "I came across your personal development content and your perspective is genuinely refreshing. It's clear you practice what you teach.",
    "coaching": "I came across your coaching content and was really impressed by what you've built. The way you connect with your audience shows real expertise and passion.",
}


def _get_niche_hook(niche: str) -> str:
    """Generate an AI niche hook for subscription platform emails."""
    niche_lower = niche.lower() if niche else ""
    for key, hook in NICHE_HOOKS.items():
        if key in niche_lower:
            return hook
    # Default hook
    return f"I came across your {niche} content and was really impressed by what you've built. The engagement you're getting shows people genuinely value what you're creating."


def _get_platform_display_name(platform: str) -> str:
    """Get a user-friendly display name for the platform."""
    display_names = {
        "YOUTUBE": "YouTube",
        "SKOOL": "Skool",
        "PATREON": "Patreon",
        "KAJABI": "Kajabi",
        "ONLYFANS": "your current platform",
        "STAN": "your current platform",
        "TIKTOK": "TikTok",
        "INSTAGRAM": "Instagram",
        "WEBSITE": "your current platform",
    }
    return display_names.get(platform.upper(), "your current platform")


def build_outreach_email(
    step: int,
    email: str,
    first_name: str,
    store_name: str,
    platform: str = "YouTube",
    claim_token: str = "",
    primary_color: str = "#1E81FF",
    tagline: str = "",
    blog_count: int = 0,
    product_count: int = 0,
    store_url: str = "",
    application_id: int | None = None,
    profile_image_url: str = "",
    niche: str = "",
    view_count: int = 0,
    is_icf: bool = False,
) -> BuiltEmail:
    """Build a personalized email for a specific campaign step.

    Args:
        step: Campaign step (1-10).
        email: Recipient email.
        first_name: Coach's first name.
        store_name: Store display name.
        platform: Source platform name (e.g. "YOUTUBE", "SKOOL").
        claim_token: Unique claim token.
        primary_color: Brand primary color (hex with #).
        tagline: Coach tagline.
        blog_count: Number of blog posts created.
        product_count: Number of products created.
        store_url: Store preview URL.
        application_id: CMS application ID.
        profile_image_url: Coach's profile image URL.
        niche: Coach's niche (e.g. "fitness", "yoga", "nutrition").
        view_count: Number of preview page views (for step 5).

    Returns:
        BuiltEmail ready to pass to BrevoClient.
    """
    step_config = STEPS.get(step)
    if not step_config:
        raise ValueError(f"Invalid email step: {step}")

    platform_key = platform.upper()
    claim_url = f"{settings.claim_base_url}?token={claim_token}"
    preview_url = store_url or f"{settings.app_base_url}/preview?token={claim_token}"
    unsubscribe_url = f"{settings.claim_base_url}/unsubscribe?email={email}"
    dashboard_url = (
        f"{settings.cms_admin_url}/app/{application_id}" if application_id else store_url
    )
    booking_link = settings.booking_link

    # Niche fallback
    if not niche:
        niche = "coaching"

    # Source platform display name (for follow-up 5 "New Angle")
    source_platform = _get_platform_display_name(platform_key)

    # AI niche hook (for subscription platform initial email)
    ai_niche_hook = _get_niche_hook(niche)

    # View count fallback (for follow-up 4 "Preview Activity")
    if not view_count or view_count < 3:
        import random

        view_count = random.randint(8, 24)

    context = {
        "first_name": first_name,
        "store_name": store_name,
        "platform": platform,
        "claim_url": claim_url,
        "preview_url": preview_url,
        "unsubscribe_url": unsubscribe_url,
        "dashboard_url": dashboard_url,
        "booking_link": booking_link,
        "primary_color": primary_color,
        "tagline": tagline,
        "blog_count": blog_count,
        "product_count": product_count,
        "store_url": store_url,
        "profile_image_url": profile_image_url,
        "niche": niche,
        "view_count": view_count,
        "source_platform": source_platform,
        "ai_niche_hook": ai_niche_hook,
    }

    # Resolve template — Step 1 is platform-specific (ICF overrides platform)
    if step == 1:
        if is_icf:
            template_name = PLATFORM_INITIAL_TEMPLATES["ICF"]
            subject_template_str = PLATFORM_INITIAL_SUBJECTS["ICF"]
        else:
            template_name = PLATFORM_INITIAL_TEMPLATES.get(platform_key, "initial_youtube.html")
            subject_template_str = PLATFORM_INITIAL_SUBJECTS.get(
                platform_key,
                "Your {{ niche }} content deserves its own platform, {{ first_name }}",
            )
    else:
        template_name = step_config["template"]
        subject_template_str = step_config["subject"]

    # Render HTML
    template = _env.get_template(template_name)
    html_content = template.render(**context)

    # Render subject (also a Jinja2 template string)
    subject_template = _env.from_string(subject_template_str)
    subject = subject_template.render(**context)

    tags = ["growth-engine", f"step-{step}", platform.lower()]

    return BuiltEmail(
        to_email=email,
        to_name=f"{first_name}",
        subject=subject,
        html_content=html_content,
        step=step,
        tags=tags,
    )
