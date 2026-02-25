"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_youtube_channel():
    return {
        "platform_id": "UC_test_channel_123",
        "name": "FitCoach Pro",
        "bio": "Professional fitness coach. Email: coach@fitcoachpro.com",
        "profile_image_url": "https://yt3.example.com/photo.jpg",
        "subscriber_count": 50000,
    }
