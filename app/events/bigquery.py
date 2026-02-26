"""BigQuery event logging for Growth Engine pipeline events.

Logs structured events for analytics:
- prospect_discovered: New coach found on a platform
- content_generated: AI content created for a prospect
- store_created: KLIQ webstore built and ready
- email_sent: Outreach email dispatched
- email_opened / email_clicked: Engagement tracking
- store_claimed: Coach activated their store (conversion!)
- pipeline_error: Something went wrong

Events are buffered and flushed in batches to reduce API calls.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Flush buffer every N events or every N seconds
BUFFER_SIZE = 50
FLUSH_INTERVAL_SECONDS = 30


@dataclass
class GrowthEvent:
    """A structured event for BigQuery."""

    event_type: str
    prospect_id: int | None = None
    platform: str | None = None
    campaign_id: int | None = None
    email_step: int | None = None
    application_id: int | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_bq_row(self) -> dict:
        """Convert to BigQuery-compatible row dict."""
        return {
            "event_type": self.event_type,
            "prospect_id": self.prospect_id,
            "platform": self.platform,
            "campaign_id": self.campaign_id,
            "email_step": self.email_step,
            "application_id": self.application_id,
            "properties": str(self.properties) if self.properties else None,
            "timestamp": self.timestamp.isoformat(),
        }


class BigQueryLogger:
    """Buffered event logger that writes to BigQuery.

    Events are accumulated in memory and flushed periodically
    or when the buffer is full.
    """

    def __init__(self):
        self._buffer: list[GrowthEvent] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        self._client = None
        self._table_ref = None

    def _get_client(self):
        """Lazy-init BigQuery client."""
        if self._client is None:
            try:
                from google.cloud import bigquery

                self._client = bigquery.Client(project=settings.gcp_project_id)
                self._table_ref = (
                    f"{settings.gcp_project_id}.{settings.gcp_dataset}"
                    f".{settings.bigquery_events_table}"
                )
            except Exception as e:
                logger.warning(f"BigQuery client init failed: {e}")
        return self._client

    def log(self, event: GrowthEvent):
        """Add an event to the buffer. Flushes if buffer is full."""
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= BUFFER_SIZE:
                self._flush_locked()

    def log_event(
        self,
        event_type: str,
        prospect_id: int | None = None,
        platform: str | None = None,
        campaign_id: int | None = None,
        email_step: int | None = None,
        application_id: int | None = None,
        **properties,
    ):
        """Convenience method to log a single event."""
        event = GrowthEvent(
            event_type=event_type,
            prospect_id=prospect_id,
            platform=platform,
            campaign_id=campaign_id,
            email_step=email_step,
            application_id=application_id,
            properties=properties,
        )
        self.log(event)

    def flush(self):
        """Flush the buffer to BigQuery."""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self):
        """Internal flush (caller must hold the lock)."""
        if not self._buffer:
            return

        events = list(self._buffer)
        self._buffer.clear()
        self._last_flush = time.time()

        client = self._get_client()
        if client is None:
            logger.debug(f"BigQuery not configured, dropping {len(events)} events")
            return

        rows = [e.to_bq_row() for e in events]

        try:
            errors = client.insert_rows_json(self._table_ref, rows)
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
            else:
                logger.info(f"Flushed {len(rows)} events to BigQuery")
        except Exception as e:
            logger.error(f"BigQuery flush failed: {e}")

    def maybe_flush(self):
        """Flush if enough time has elapsed since last flush."""
        with self._lock:
            elapsed = time.time() - self._last_flush
            if elapsed >= FLUSH_INTERVAL_SECONDS and self._buffer:
                self._flush_locked()

    @property
    def buffer_size(self) -> int:
        """Current number of events in the buffer."""
        with self._lock:
            return len(self._buffer)


# Module-level singleton
_logger: BigQueryLogger | None = None


def get_bq_logger() -> BigQueryLogger:
    """Get or create the singleton BigQuery logger."""
    global _logger
    if _logger is None:
        _logger = BigQueryLogger()
    return _logger


def log_event(event_type: str, **kwargs):
    """Top-level convenience function for logging events."""
    get_bq_logger().log_event(event_type, **kwargs)
