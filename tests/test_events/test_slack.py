"""Tests for Slack alerting module."""

from app.events.slack import format_digest_message, format_error_message


class TestFormatErrorMessage:
    def test_basic_error(self):
        msg = format_error_message("scraping", prospect_id=42, error="Timeout")
        assert "Pipeline Error" in msg
        assert "prospect #42" in msg
        assert "scraping" in msg
        assert "Timeout" in msg

    def test_no_prospect_id(self):
        msg = format_error_message("ai_generation", prospect_id=None, error="API rate limit")
        assert "Pipeline Error" in msg
        assert "prospect" not in msg
        assert "ai_generation" in msg

    def test_empty_error(self):
        msg = format_error_message("populate", prospect_id=1, error="")
        assert "Pipeline Error" in msg


class TestFormatDigestMessage:
    def test_with_data(self):
        result = format_digest_message(
            prospects_discovered=50,
            stores_created=20,
            emails_sent=15,
            claims=3,
            errors=2,
        )
        assert result["prospects_discovered"] == 50
        assert result["stores_created"] == 20
        assert result["emails_sent"] == 15
        assert result["claims"] == 3
        assert result["errors"] == 2
        assert result["conversion_rate"] == 20.0  # 3/15 * 100

    def test_zero_emails_sent(self):
        result = format_digest_message(
            prospects_discovered=10,
            stores_created=5,
            emails_sent=0,
            claims=0,
            errors=0,
        )
        assert result["conversion_rate"] == 0.0

    def test_all_zeros(self):
        result = format_digest_message(
            prospects_discovered=0,
            stores_created=0,
            emails_sent=0,
            claims=0,
            errors=0,
        )
        assert result["conversion_rate"] == 0.0
        assert result["prospects_discovered"] == 0

    def test_high_conversion(self):
        result = format_digest_message(
            prospects_discovered=100,
            stores_created=50,
            emails_sent=50,
            claims=25,
            errors=0,
        )
        assert result["conversion_rate"] == 50.0
