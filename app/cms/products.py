"""Create products/subscriptions in the CMS from AI-generated pricing analysis."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.pricing_analyzer import SuggestedProduct
from app.cms.models import Product
from app.cms.store_builder import STATUS_INACTIVE, SUPER_ADMIN_ID

logger = logging.getLogger(__name__)

# CMS currency mapping
CURRENCY_MAP = {"GBP": 1, "USD": 2, "EUR": 3}


async def create_products(
    session: AsyncSession,
    application_id: int,
    products: list[SuggestedProduct],
    currency_id: int = 2,
) -> list[int]:
    """Create draft products in the CMS.

    Products are created with status_id=1 (Draft), no Stripe connection.
    When the coach claims and activates, Stripe products are created via CMS.

    Args:
        session: CMS MySQL session.
        application_id: The CMS application ID.
        products: List of suggested products from pricing analyzer.
        currency_id: Currency (1=GBP, 2=USD, 3=EUR).

    Returns:
        List of created product IDs.
    """
    product_ids = []

    for order, suggested in enumerate(products):
        # Map currency string to CMS currency ID
        cur_id = CURRENCY_MAP.get(suggested.currency.upper(), currency_id)

        # Determine interval for CMS
        interval = suggested.interval or "month"
        if suggested.type == "one_time":
            interval = "one_time"

        product = Product(
            application_id=application_id,
            name=suggested.name,
            description=suggested.description[:255] if suggested.description else "",
            unit_amount=suggested.price_cents,
            currency_id=cur_id,
            interval=interval,
            interval_count=1,
            order=order,
            status_id=STATUS_INACTIVE,
            created_by=SUPER_ADMIN_ID,
            updated_by=SUPER_ADMIN_ID,
        )
        session.add(product)
        await session.flush()
        product_ids.append(product.id)

        logger.info(
            f"Created product '{suggested.name}' ({suggested.price_cents} cents) "
            f"for app {application_id}"
        )

    return product_ids
