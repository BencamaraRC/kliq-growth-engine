"""Brevo (SendinBlue) email client for transactional outreach emails.

Wraps the Brevo API to send personalized HTML emails with tracking.
Uses the sib-api-v3-sdk for API calls.
"""

import logging
from dataclasses import dataclass

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Result of sending an email via Brevo."""

    success: bool
    message_id: str | None = None
    error: str | None = None


class BrevoClient:
    """Brevo transactional email client."""

    def __init__(self, api_key: str | None = None):
        config = sib_api_v3_sdk.Configuration()
        config.api_key["api-key"] = api_key or settings.brevo_api_key
        self._api = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(config)
        )
        self._sender_email = settings.brevo_sender_email
        self._sender_name = settings.brevo_sender_name

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        tags: list[str] | None = None,
        params: dict | None = None,
    ) -> EmailResult:
        """Send a transactional email via Brevo.

        Args:
            to_email: Recipient email address.
            to_name: Recipient display name.
            subject: Email subject line.
            html_content: Full HTML email body.
            tags: Tags for tracking/filtering in Brevo dashboard.
            params: Additional template parameters.

        Returns:
            EmailResult with success status and message_id.
        """
        email = sib_api_v3_sdk.SendSmtpEmail(
            sender={"email": self._sender_email, "name": self._sender_name},
            to=[{"email": to_email, "name": to_name}],
            subject=subject,
            html_content=html_content,
            tags=tags or ["growth-engine"],
            params=params or {},
            headers={
                "List-Unsubscribe": f"<mailto:unsubscribe@joinkliq.io?subject=unsubscribe-{to_email}>",
            },
        )

        try:
            response = self._api.send_transac_email(email)
            message_id = response.message_id
            logger.info(f"Email sent to {to_email}: message_id={message_id}")
            return EmailResult(success=True, message_id=message_id)

        except ApiException as e:
            logger.error(f"Brevo API error sending to {to_email}: {e}")
            return EmailResult(success=False, error=str(e))

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return EmailResult(success=False, error=str(e))
