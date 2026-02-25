"""Analyze competitor pricing and suggest KLIQ product tiers.

Takes scraped pricing tiers from competitor platforms and generates
recommended KLIQ products with prices in cents.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.ai.client import AIClient, MODEL_SONNET

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


@dataclass
class SuggestedProduct:
    name: str
    description: str
    type: str  # "subscription" or "one_time"
    price_cents: int
    currency: str = "USD"
    interval: str | None = None  # "month", "year", or None for one_time
    features: list[str] = field(default_factory=list)
    recommended: bool = False


@dataclass
class PricingAnalysis:
    products: list[SuggestedProduct]
    pricing_rationale: str


async def analyze_pricing(
    client: AIClient,
    name: str,
    niche_tags: list[str] | None = None,
    follower_count: int = 0,
    pricing_tiers: list[dict] | None = None,
    content_types: list[str] | None = None,
) -> PricingAnalysis:
    """Analyze competitor pricing and suggest KLIQ products.

    Args:
        client: AIClient instance.
        name: Coach name.
        niche_tags: Detected niches.
        follower_count: Audience size.
        pricing_tiers: Scraped pricing from competitor platforms.
            Each dict: tier_name, platform, price_amount, currency, interval,
                       description, benefits, member_count.
        content_types: Types of content available.

    Returns:
        PricingAnalysis with suggested products and rationale.
    """
    template = _env.get_template("pricing_analyzer.j2")
    prompt = template.render(
        name=name,
        niche_tags=niche_tags or [],
        follower_count=follower_count,
        pricing_tiers=pricing_tiers or [],
        content_types=content_types or ["videos", "blog posts"],
    )

    result = await client.generate_json(
        prompt=prompt,
        system="You are a pricing strategist for KLIQ, a fitness/wellness creator platform.",
        model=MODEL_SONNET,
    )

    products = []
    for p in result.get("products", []):
        price_cents = p.get("price_cents", 0)
        # Safety: if the model returned dollars instead of cents, convert
        if isinstance(price_cents, float) and price_cents < 100:
            price_cents = int(price_cents * 100)

        products.append(
            SuggestedProduct(
                name=p.get("name", "Membership"),
                description=p.get("description", ""),
                type=p.get("type", "subscription"),
                price_cents=int(price_cents),
                currency=p.get("currency", "USD"),
                interval=p.get("interval"),
                features=p.get("features", []),
                recommended=p.get("recommended", False),
            )
        )

    # Ensure at least one product if AI returned empty
    if not products:
        products = _default_products(name)

    logger.info(f"Pricing analysis for {name}: {len(products)} products suggested")

    return PricingAnalysis(
        products=products,
        pricing_rationale=result.get("pricing_rationale", ""),
    )


def _default_products(name: str) -> list[SuggestedProduct]:
    """Fallback products if AI generation fails or returns empty."""
    return [
        SuggestedProduct(
            name=f"{name} Community",
            description="Access to all content and community.",
            type="subscription",
            price_cents=999,
            currency="USD",
            interval="month",
            features=["All blog posts", "Community access", "Monthly Q&A"],
            recommended=True,
        ),
        SuggestedProduct(
            name=f"{name} Premium",
            description="Premium coaching and exclusive content.",
            type="subscription",
            price_cents=2999,
            currency="USD",
            interval="month",
            features=["Everything in Community", "1-on-1 coaching", "Custom plans"],
            recommended=False,
        ),
    ]
