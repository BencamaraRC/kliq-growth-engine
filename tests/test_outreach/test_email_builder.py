"""Tests for the email builder — template rendering and personalization."""

import pytest

from app.outreach.email_builder import STEPS, build_outreach_email


class TestEmailSteps:
    """Test that all 4 email steps are configured."""

    def test_all_four_steps_defined(self):
        assert set(STEPS.keys()) == {1, 2, 3, 4}

    def test_step_1_is_store_ready(self):
        assert STEPS[1]["template"] == "store_ready.html"
        assert STEPS[1]["delay_days"] == 0

    def test_step_2_is_reminder_after_3_days(self):
        assert STEPS[2]["delay_days"] == 3

    def test_step_3_is_reminder_after_7_days(self):
        assert STEPS[3]["delay_days"] == 7

    def test_step_4_is_claimed_confirmation(self):
        assert STEPS[4]["template"] == "claimed_confirmation.html"
        assert STEPS[4]["delay_days"] == 0


class TestBuildEmail:
    """Test email building and personalization."""

    def test_build_step_1_email(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike's Fitness",
            platform="YouTube",
            claim_token="abc123",
        )
        assert email.to_email == "coach@example.com"
        assert email.to_name == "Mike"
        assert "Mike" in email.subject
        assert "abc123" in email.html_content
        assert email.step == 1
        assert "growth-engine" in email.tags

    def test_build_step_4_confirmation(self):
        email = build_outreach_email(
            step=4,
            email="coach@example.com",
            first_name="Sarah",
            store_name="Sarah Wellness",
            application_id=42,
        )
        assert "Sarah" in email.subject
        assert "Welcome" in email.subject
        assert email.step == 4

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError, match="Invalid email step"):
            build_outreach_email(
                step=99,
                email="test@test.com",
                first_name="Test",
                store_name="Test Store",
            )

    def test_brand_color_in_html(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            primary_color="#FF5733",
            claim_token="token123",
        )
        assert "#FF5733" in email.html_content

    def test_platform_tag_added(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            platform="Skool",
            claim_token="token",
        )
        assert "skool" in email.tags


class TestTrackingEventMap:
    """Test Brevo event mapping."""

    def test_event_map_has_all_types(self):
        from app.outreach.tracking import EVENT_MAP
        assert "delivered" in EVENT_MAP
        assert "opened" in EVENT_MAP
        assert "click" in EVENT_MAP
        assert "hard_bounce" in EVENT_MAP
        assert "soft_bounce" in EVENT_MAP
        assert "unsubscribed" in EVENT_MAP
