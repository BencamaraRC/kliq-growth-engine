"""Slack alerting for Growth Engine events.

Sends notifications for:
- Pipeline errors (scraping failures, AI generation failures)
- Store claimed (conversions!)
- Daily digest summary (prospects discovered, stores created, claims)
"""

import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SlackMessage:
    """A structured Slack notification."""

    text: str
    blocks: list[dict] | None = None


def _send_webhook(message: SlackMessage) -> bool:
    """Send a message via Slack incoming webhook."""
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook not configured, skipping notification")
        return False

    payload = {"text": message.text}
    if message.blocks:
        payload["blocks"] = message.blocks

    try:
        response = httpx.post(
            settings.slack_webhook_url,
            json=payload,
            timeout=10,
        )
        if response.status_code == 200:
            logger.debug("Slack notification sent")
            return True
        else:
            logger.error(f"Slack webhook failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Slack notification error: {e}")
        return False


def notify_pipeline_error(
    stage: str,
    prospect_id: int | None = None,
    error: str = "",
):
    """Alert on pipeline failures."""
    prospect_text = f" (prospect #{prospect_id})" if prospect_id else ""
    msg = SlackMessage(
        text=f":rotating_light: *Pipeline Error*{prospect_text}\n*Stage:* {stage}\n*Error:* {error}",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Pipeline Error"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Stage:*\n{stage}"},
                    {"type": "mrkdwn", "text": f"*Prospect:*\n{prospect_id or 'N/A'}"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error[:500]}```",
                },
            },
        ],
    )
    return _send_webhook(msg)


def notify_store_claimed(
    prospect_name: str,
    email: str,
    platform: str,
    application_id: int | None = None,
):
    """Celebrate a conversion!"""
    msg = SlackMessage(
        text=f":tada: *Store Claimed!* {prospect_name} ({email}) from {platform}",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Store Claimed!"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Coach:*\n{prospect_name}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                    {"type": "mrkdwn", "text": f"*Platform:*\n{platform}"},
                    {"type": "mrkdwn", "text": f"*App ID:*\n{application_id or 'N/A'}"},
                ],
            },
        ],
    )
    return _send_webhook(msg)


def notify_daily_digest(
    prospects_discovered: int,
    stores_created: int,
    emails_sent: int,
    claims: int,
    errors: int,
):
    """Daily summary of Growth Engine activity."""
    conversion_rate = (
        f"{(claims / emails_sent * 100):.1f}%" if emails_sent > 0 else "N/A"
    )

    msg = SlackMessage(
        text=f":bar_chart: *Daily Growth Engine Digest*\nDiscovered: {prospects_discovered} | Stores: {stores_created} | Emails: {emails_sent} | Claims: {claims}",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Daily Growth Engine Digest"},
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Prospects Discovered:*\n{prospects_discovered}",
                    },
                    {"type": "mrkdwn", "text": f"*Stores Created:*\n{stores_created}"},
                    {"type": "mrkdwn", "text": f"*Emails Sent:*\n{emails_sent}"},
                    {"type": "mrkdwn", "text": f"*Claims:*\n{claims}"},
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Conversion Rate:*\n{conversion_rate}"},
                    {"type": "mrkdwn", "text": f"*Errors:*\n{errors}"},
                ],
            },
        ],
    )
    return _send_webhook(msg)


def format_error_message(stage: str, prospect_id: int | None, error: str) -> str:
    """Format a pipeline error into a human-readable string."""
    prospect_text = f" (prospect #{prospect_id})" if prospect_id else ""
    return f"Pipeline Error{prospect_text} | Stage: {stage} | Error: {error}"


def format_digest_message(
    prospects_discovered: int,
    stores_created: int,
    emails_sent: int,
    claims: int,
    errors: int,
) -> dict:
    """Format daily digest metrics into a summary dict."""
    conversion_rate = (claims / emails_sent * 100) if emails_sent > 0 else 0.0
    return {
        "prospects_discovered": prospects_discovered,
        "stores_created": stores_created,
        "emails_sent": emails_sent,
        "claims": claims,
        "errors": errors,
        "conversion_rate": round(conversion_rate, 1),
    }
