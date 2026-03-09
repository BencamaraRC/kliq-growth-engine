"""Tests for the email builder — template rendering and personalization."""

import pytest

from app.outreach.email_builder import (
    ONBOARDING_STEPS,
    PLATFORM_INITIAL_SUBJECTS,
    PLATFORM_INITIAL_TEMPLATES,
    PRE_CLAIM_STEPS,
    STEPS,
    build_outreach_email,
)


class TestEmailSteps:
    """Test that all 10 email steps are configured."""

    def test_all_steps_defined(self):
        assert set(STEPS.keys()) == {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

    def test_step_1_is_platform_specific(self):
        # Step 1 template/subject is None — resolved by platform at build time
        assert STEPS[1]["template"] is None
        assert STEPS[1]["subject"] is None
        assert STEPS[1]["delay_days"] == 0

    def test_step_2_gentle_nudge_day_3(self):
        assert STEPS[2]["delay_days"] == 3
        assert STEPS[2]["template"] == "followup_1_nudge.html"

    def test_step_3_value_add_day_6(self):
        assert STEPS[3]["delay_days"] == 6
        assert STEPS[3]["template"] == "followup_2_value.html"

    def test_step_4_social_proof_day_10(self):
        assert STEPS[4]["delay_days"] == 10
        assert STEPS[4]["template"] == "followup_3_social_proof.html"

    def test_step_5_preview_activity_day_14(self):
        assert STEPS[5]["delay_days"] == 14
        assert STEPS[5]["template"] == "followup_4_preview_activity.html"

    def test_step_6_new_angle_day_21(self):
        assert STEPS[6]["delay_days"] == 21
        assert STEPS[6]["template"] == "followup_5_new_angle.html"

    def test_step_7_breakup_day_28(self):
        assert STEPS[7]["delay_days"] == 28
        assert STEPS[7]["template"] == "followup_6_breakup.html"

    def test_step_8_is_claimed_confirmation(self):
        assert STEPS[8]["template"] == "claimed_confirmation.html"
        assert STEPS[8]["delay_days"] == 0

    def test_pre_claim_steps(self):
        assert PRE_CLAIM_STEPS == [1, 2, 3, 4, 5, 6, 7]

    def test_onboarding_steps(self):
        assert ONBOARDING_STEPS == [9, 10]


class TestPlatformTemplates:
    """Test platform-specific initial outreach templates."""

    def test_all_platforms_have_templates(self):
        for platform in ["SKOOL", "PATREON", "YOUTUBE", "KAJABI", "ONLYFANS", "STAN"]:
            assert platform in PLATFORM_INITIAL_TEMPLATES

    def test_all_platforms_have_subjects(self):
        for platform in ["SKOOL", "PATREON", "YOUTUBE", "KAJABI", "ONLYFANS", "STAN"]:
            assert platform in PLATFORM_INITIAL_SUBJECTS

    def test_subscription_platforms_share_template(self):
        assert PLATFORM_INITIAL_TEMPLATES["ONLYFANS"] == "initial_subscription.html"
        assert PLATFORM_INITIAL_TEMPLATES["STAN"] == "initial_subscription.html"
        assert PLATFORM_INITIAL_TEMPLATES["TIKTOK"] == "initial_subscription.html"


class TestBuildEmail:
    """Test email building and personalization."""

    def test_build_step_1_youtube(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike's Fitness",
            platform="YOUTUBE",
            claim_token="abc123",
            niche="fitness",
        )
        assert email.to_email == "coach@example.com"
        assert email.to_name == "Mike"
        assert "Mike" in email.subject
        assert "YouTube" in email.subject
        assert "abc123" in email.html_content
        assert email.step == 1
        assert "growth-engine" in email.tags

    def test_build_step_1_skool(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Sarah",
            store_name="Sarah Fitness",
            platform="SKOOL",
            claim_token="token123",
        )
        assert "Skool" in email.subject
        assert "Sarah" in email.subject
        assert "skool" in email.tags

    def test_build_step_1_subscription(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Alex",
            store_name="Alex Yoga",
            platform="ONLYFANS",
            claim_token="token123",
            niche="yoga",
        )
        assert "yoga" in email.subject
        assert "Alex" in email.subject
        # Should NOT mention the platform name
        assert "OnlyFans" not in email.html_content

    def test_build_step_2_followup(self):
        email = build_outreach_email(
            step=2,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            claim_token="token123",
        )
        assert "Did you get a chance" in email.subject
        assert email.step == 2

    def test_build_step_8_confirmation(self):
        email = build_outreach_email(
            step=8,
            email="coach@example.com",
            first_name="Sarah",
            store_name="Sarah Wellness",
            application_id=42,
        )
        assert "Sarah" in email.subject
        assert "Welcome" in email.subject
        assert email.step == 8

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError, match="Invalid email step"):
            build_outreach_email(
                step=99,
                email="test@test.com",
                first_name="Test",
                store_name="Test Store",
            )

    def test_platform_tag_added(self):
        email = build_outreach_email(
            step=1,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            platform="SKOOL",
            claim_token="token",
        )
        assert "skool" in email.tags

    def test_niche_in_social_proof(self):
        email = build_outreach_email(
            step=4,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            niche="fitness",
            claim_token="token",
        )
        assert "fitness" in email.subject

    def test_view_count_in_preview_activity(self):
        email = build_outreach_email(
            step=5,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            claim_token="token",
            view_count=15,
        )
        assert "15" in email.subject

    def test_booking_link_in_followups(self):
        email = build_outreach_email(
            step=2,
            email="coach@example.com",
            first_name="Mike",
            store_name="Mike Fit",
            claim_token="token",
        )
        assert "calendly" in email.html_content or "booking" in email.html_content.lower()


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
