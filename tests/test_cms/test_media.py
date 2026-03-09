"""Tests for CMS media record creation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.cms.media import create_media_record


class TestCreateMediaRecord:
    """Test create_media_record() inserts correct data and returns media ID."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        result = MagicMock()
        result.lastrowid = 42
        session.execute.return_value = result
        return session

    async def test_returns_media_id(self, mock_session):
        """Should return the auto-increment ID from the INSERT."""
        media_id = await create_media_record(
            mock_session, application_id=100, url="https://s3.example.com/profile.jpg", name="profile"
        )
        assert media_id == 42

    async def test_passes_correct_params(self, mock_session):
        """Should pass application_id, url, name, and meta JSON to the INSERT."""
        await create_media_record(
            mock_session, application_id=100, url="https://s3.example.com/img.jpg", name="banner"
        )
        call_args = mock_session.execute.call_args
        params = call_args[0][1]  # second positional arg = params dict
        assert params["app_id"] == 100
        assert params["url"] == "https://s3.example.com/img.jpg"
        assert params["name"] == "banner"
        assert "image/jpeg" in params["meta"]

    async def test_default_name_is_image(self, mock_session):
        """When no name provided, defaults to 'image'."""
        await create_media_record(
            mock_session, application_id=1, url="https://example.com/x.jpg"
        )
        params = mock_session.execute.call_args[0][1]
        assert params["name"] == "image"

    async def test_sql_contains_medias_table(self, mock_session):
        """The SQL statement should target the medias table."""
        await create_media_record(
            mock_session, application_id=1, url="https://example.com/x.jpg"
        )
        sql_text = str(mock_session.execute.call_args[0][0])
        assert "INSERT INTO medias" in sql_text

    async def test_thumbnail_url_same_as_url(self, mock_session):
        """thumbnail_url should be set to the same value as url."""
        await create_media_record(
            mock_session, application_id=1, url="https://example.com/x.jpg"
        )
        sql_text = str(mock_session.execute.call_args[0][0])
        # The SQL uses :url for both url and thumbnail_url columns
        assert "thumbnail_url" in sql_text

    async def test_returns_none_when_lastrowid_is_none(self):
        """If the DB returns None for lastrowid, function returns None."""
        session = AsyncMock()
        result = MagicMock()
        result.lastrowid = None
        session.execute.return_value = result

        media_id = await create_media_record(
            session, application_id=1, url="https://example.com/x.jpg"
        )
        assert media_id is None
