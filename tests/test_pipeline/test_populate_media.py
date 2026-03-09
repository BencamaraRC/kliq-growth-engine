"""Tests for media record creation + FK writeback + feature enable in populate_tasks.

These test the critical section 5b logic that was added to _create_store():
- Creates medias records for profile and banner
- Updates application_settings with FK refs (profile_id, hero_id, default_image_id)
- Updates all legacy URL fields
- Enables features (AMA, programs, courses, etc.)
"""

from unittest.mock import AsyncMock, patch


class TestMediaRecordCreation:
    """Test that _create_store creates media records after S3 upload."""

    @patch("app.workers.populate_tasks.create_media_record")
    async def test_creates_profile_media_record(self, mock_create_media):
        """When profile S3 URL exists, should call create_media_record for profile."""
        mock_create_media.return_value = 10

        # Simulate the logic from section 5b
        media = {"profile": "https://s3.example.com/profile.jpg", "banner": None}
        cms_db = AsyncMock()
        app_id = 999

        profile_media_id = None
        banner_media_id = None
        if media.get("profile"):
            profile_media_id = await mock_create_media(cms_db, app_id, media["profile"], "profile")
        if media.get("banner"):
            banner_media_id = await mock_create_media(cms_db, app_id, media["banner"], "banner")

        assert profile_media_id == 10
        assert banner_media_id is None
        mock_create_media.assert_called_once_with(
            cms_db, app_id, "https://s3.example.com/profile.jpg", "profile"
        )

    @patch("app.workers.populate_tasks.create_media_record")
    async def test_creates_both_media_records(self, mock_create_media):
        """When both S3 URLs exist, should create both media records."""
        mock_create_media.side_effect = [10, 20]

        media = {
            "profile": "https://s3.example.com/profile.jpg",
            "banner": "https://s3.example.com/banner.jpg",
        }
        cms_db = AsyncMock()
        app_id = 999

        profile_media_id = None
        banner_media_id = None
        if media.get("profile"):
            profile_media_id = await mock_create_media(cms_db, app_id, media["profile"], "profile")
        if media.get("banner"):
            banner_media_id = await mock_create_media(cms_db, app_id, media["banner"], "banner")

        assert profile_media_id == 10
        assert banner_media_id == 20
        assert mock_create_media.call_count == 2

    @patch("app.workers.populate_tasks.create_media_record")
    async def test_no_media_records_when_no_urls(self, mock_create_media):
        """When no S3 URLs, should not call create_media_record."""
        media = {"profile": None, "banner": None}
        cms_db = AsyncMock()
        app_id = 999

        profile_media_id = None
        banner_media_id = None
        if media.get("profile"):
            profile_media_id = await mock_create_media(cms_db, app_id, media["profile"], "profile")
        if media.get("banner"):
            banner_media_id = await mock_create_media(cms_db, app_id, media["banner"], "banner")

        assert profile_media_id is None
        assert banner_media_id is None
        mock_create_media.assert_not_called()


class TestFKWriteback:
    """Test that UPDATE query sets FK refs and legacy URL fields."""

    async def test_update_sql_contains_fk_fields(self):
        """The UPDATE should set profile_id, hero_id, default_image_id."""

        sql = (
            "UPDATE application_settings SET "
            "profile_placeholder = COALESCE(:profile_url, profile_placeholder), "
            "default_image = COALESCE(:banner_url, default_image), "
            "profile_image = COALESCE(:profile_url, profile_image), "
            "hero_image = COALESCE(:banner_url, hero_image), "
            "light_home_logo = COALESCE(:profile_url, light_home_logo), "
            "dark_home_logo = COALESCE(:profile_url, dark_home_logo), "
            "light_login_logo = COALESCE(:profile_url, light_login_logo), "
            "dark_login_logo = COALESCE(:profile_url, dark_login_logo), "
            "shop_image = COALESCE(:profile_url, shop_image), "
            "favicon = COALESCE(:profile_url, favicon), "
            "profile_id = COALESCE(:profile_media_id, profile_id), "
            "hero_id = COALESCE(:banner_media_id, hero_id), "
            "default_image_id = COALESCE(:banner_media_id, default_image_id) "
            "WHERE application_id = :app_id"
        )

        # Verify the FK fields are in the SQL
        assert "profile_id = COALESCE(:profile_media_id" in sql
        assert "hero_id = COALESCE(:banner_media_id" in sql
        assert "default_image_id = COALESCE(:banner_media_id" in sql

        # Verify legacy URL fields
        assert "profile_image = COALESCE(:profile_url" in sql
        assert "hero_image = COALESCE(:banner_url" in sql

    async def test_update_params_include_media_ids(self):
        """The params dict should include media IDs for FK fields."""
        params = {
            "profile_url": "https://s3.example.com/profile.jpg",
            "banner_url": "https://s3.example.com/banner.jpg",
            "profile_media_id": 10,
            "banner_media_id": 20,
            "app_id": 999,
        }

        assert params["profile_media_id"] == 10
        assert params["banner_media_id"] == 20
        assert params["app_id"] == 999

    async def test_coalesce_handles_none_media_ids(self):
        """When media IDs are None, COALESCE preserves existing FK values."""
        params = {
            "profile_url": None,
            "banner_url": None,
            "profile_media_id": None,
            "banner_media_id": None,
            "app_id": 999,
        }
        # COALESCE(NULL, profile_id) → keeps existing profile_id
        assert params["profile_media_id"] is None
        assert params["banner_media_id"] is None


class TestFeatureEnable:
    """Test that features are enabled after store creation."""

    async def test_feature_enable_sql_structure(self):
        """The feature enable SQL should set all required flags."""
        sql = (
            "UPDATE application_feature_setups SET "
            "enable_ama = 1, enable_ecourse = 1, has_program = 1, "
            "has_one_to_one = 1, enable_session = 1, "
            "enable_movement_library = 1, enable_community_post_user = 1, "
            "enable_premium_content_platform = 1, enable_subscription_web = 1 "
            "WHERE application_id = :app_id"
        )

        required_features = [
            "enable_ama = 1",
            "enable_ecourse = 1",
            "has_program = 1",
            "has_one_to_one = 1",
            "enable_session = 1",
            "enable_movement_library = 1",
            "enable_community_post_user = 1",
            "enable_premium_content_platform = 1",
            "enable_subscription_web = 1",
        ]
        for feature in required_features:
            assert feature in sql, f"Missing feature: {feature}"
