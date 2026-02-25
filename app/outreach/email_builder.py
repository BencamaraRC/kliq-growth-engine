"""Build personalized outreach emails from templates and prospect data.

Each email step has a Jinja2 HTML template that gets personalized with
the prospect's name, store details, claim URL, and branding colors.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# Email step configuration
STEPS = {
    1: {
        "template": "store_ready.html",
        "subject": "{{ first_name }}, your KLIQ store is ready!",
        "delay_days": 0,
    },
    2: {
        "template": "reminder_1.html",
        "subject": "{{ first_name }}, your store is waiting for you",
        "delay_days": 3,
    },
    3: {
        "template": "reminder_2.html",
        "subject": "Last chance to claim {{ store_name }}",
        "delay_days": 7,
    },
    4: {
        "template": "claimed_confirmation.html",
        "subject": "Welcome to KLIQ, {{ first_name }}!",
        "delay_days": 0,  # Sent immediately on claim
    },
}


@dataclass
class BuiltEmail:
    """A fully constructed email ready to send."""

    to_email: str
    to_name: str
    subject: str
    html_content: str
    step: int
    tags: list[str]


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
) -> BuiltEmail:
    """Build a personalized email for a specific campaign step.

    Args:
        step: Campaign step (1-4).
        email: Recipient email.
        first_name: Coach's first name.
        store_name: Store display name.
        platform: Source platform name.
        claim_token: Unique claim token.
        primary_color: Brand primary color (hex with #).
        tagline: Coach tagline.
        blog_count: Number of blog posts created.
        product_count: Number of products created.
        store_url: Store preview URL.
        application_id: CMS application ID.

    Returns:
        BuiltEmail ready to pass to BrevoClient.
    """
    step_config = STEPS.get(step)
    if not step_config:
        raise ValueError(f"Invalid email step: {step}")

    claim_url = f"{settings.claim_base_url}?token={claim_token}"
    unsubscribe_url = f"{settings.claim_base_url}/unsubscribe?email={email}"
    dashboard_url = f"https://admin.joinkliq.io/app/{application_id}" if application_id else store_url

    context = {
        "first_name": first_name,
        "store_name": store_name,
        "platform": platform,
        "claim_url": claim_url,
        "unsubscribe_url": unsubscribe_url,
        "dashboard_url": dashboard_url,
        "primary_color": primary_color,
        "tagline": tagline,
        "blog_count": blog_count,
        "product_count": product_count,
        "store_url": store_url,
    }

    # Render HTML
    template = _env.get_template(step_config["template"])
    html_content = template.render(**context)

    # Render subject (also a Jinja2 template string)
    subject_template = _env.from_string(step_config["subject"])
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
