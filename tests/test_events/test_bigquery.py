"""Tests for BigQuery event logging."""

from datetime import datetime, timezone

from app.events.bigquery import BUFFER_SIZE, BigQueryLogger, GrowthEvent


class TestGrowthEvent:
    def test_to_bq_row(self):
        event = GrowthEvent(
            event_type="prospect_discovered",
            prospect_id=42,
            platform="youtube",
            timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        )
        row = event.to_bq_row()
        assert row["event_type"] == "prospect_discovered"
        assert row["prospect_id"] == 42
        assert row["platform"] == "youtube"
        assert "2024-01-15" in row["timestamp"]

    def test_to_bq_row_optional_fields(self):
        event = GrowthEvent(event_type="store_claimed")
        row = event.to_bq_row()
        assert row["event_type"] == "store_claimed"
        assert row["prospect_id"] is None
        assert row["campaign_id"] is None
        assert row["email_step"] is None

    def test_to_bq_row_with_properties(self):
        event = GrowthEvent(
            event_type="email_sent",
            properties={"step": 1, "template": "store_ready"},
        )
        row = event.to_bq_row()
        assert "step" in row["properties"]
        assert "store_ready" in row["properties"]

    def test_timestamp_auto_generated(self):
        event = GrowthEvent(event_type="test")
        assert event.timestamp is not None
        assert event.timestamp.tzinfo is not None


class TestBigQueryLogger:
    def test_buffer_accumulates(self):
        logger = BigQueryLogger()
        logger.log(GrowthEvent(event_type="test_1"))
        logger.log(GrowthEvent(event_type="test_2"))
        assert logger.buffer_size == 2

    def test_flush_clears_buffer(self):
        logger = BigQueryLogger()
        logger.log(GrowthEvent(event_type="test"))
        assert logger.buffer_size == 1
        # Flush without a real BQ client — buffer should still clear
        logger.flush()
        assert logger.buffer_size == 0

    def test_log_event_convenience(self):
        logger = BigQueryLogger()
        logger.log_event("prospect_discovered", prospect_id=1, platform="youtube")
        assert logger.buffer_size == 1

    def test_auto_flush_at_buffer_size(self):
        logger = BigQueryLogger()
        for i in range(BUFFER_SIZE):
            logger.log(GrowthEvent(event_type=f"event_{i}"))
        # Buffer should have been flushed
        assert logger.buffer_size == 0

    def test_buffer_size_constant(self):
        assert BUFFER_SIZE == 50
