"""Platform adapter base classes and data models.

Every platform (YouTube, Skool, Patreon, etc.) implements PlatformAdapter.
Adding a new platform = create a new file that implements this interface.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    YOUTUBE = "youtube"
    SKOOL = "skool"
    PATREON = "patreon"
    WEBSITE = "website"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


@dataclass
class ScrapedProfile:
    """Normalized profile data from any platform."""

    platform: Platform
    platform_id: str
    name: str
    bio: str = ""
    profile_image_url: str = ""
    banner_image_url: str = ""
    email: Optional[str] = None
    website_url: Optional[str] = None
    social_links: dict = field(default_factory=dict)
    follower_count: int = 0
    subscriber_count: int = 0
    member_count: int = 0
    niche_tags: list[str] = field(default_factory=list)
    location: Optional[str] = None
    brand_colors: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)


@dataclass
class ScrapedContent:
    """A piece of content from any platform."""

    platform: Platform
    platform_id: str
    content_type: str  # "video", "post", "course", "tier", "blog"
    title: str = ""
    description: str = ""
    body: str = ""  # Full text content or transcript
    url: str = ""
    thumbnail_url: str = ""
    media_urls: list[str] = field(default_factory=list)
    published_at: Optional[str] = None
    view_count: int = 0
    engagement_count: int = 0
    tags: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)


@dataclass
class ScrapedPricing:
    """A pricing tier from any platform."""

    platform: Platform
    platform_id: str
    tier_name: str
    price_amount: float
    currency: str = "USD"
    interval: str = "month"  # "month", "year", "one_time"
    description: str = ""
    benefits: list[str] = field(default_factory=list)
    member_count: int = 0


class PlatformAdapter(ABC):
    """Abstract base for all platform scrapers.

    Each platform implements this interface. Adding a new platform
    (e.g., TikTok) requires only creating a new file that implements
    these methods.
    """

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Return the platform enum value."""
        ...

    @abstractmethod
    async def discover_coaches(
        self,
        search_queries: list[str],
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Discover fitness/wellness coaches on this platform.

        Args:
            search_queries: e.g. ["fitness coach", "yoga instructor", "personal trainer"]
            max_results: Maximum number of profiles to return.

        Returns:
            List of normalized profile data.
        """
        ...

    @abstractmethod
    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape full profile details for a specific coach."""
        ...

    @abstractmethod
    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape recent content (videos, posts, courses) from a coach's profile."""
        ...

    @abstractmethod
    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """Scrape pricing tiers if available on this platform."""
        ...

    async def extract_email(self, profile: ScrapedProfile) -> Optional[str]:
        """Attempt to find email from profile data.

        Default implementation checks bio and description for email patterns.
        Override for platform-specific logic.
        """
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

        if profile.bio:
            match = re.search(email_pattern, profile.bio)
            if match:
                return match.group()

        return None

    async def extract_social_links(self, text: str) -> dict:
        """Extract social media links from text (bio, description, etc.)."""
        links = {}
        patterns = {
            "instagram": r"(?:instagram\.com|instagr\.am)/([a-zA-Z0-9_.]+)",
            "tiktok": r"tiktok\.com/@([a-zA-Z0-9_.]+)",
            "twitter": r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)",
            "facebook": r"facebook\.com/([a-zA-Z0-9.]+)",
            "youtube": r"youtube\.com/(?:@|channel/|c/)([a-zA-Z0-9_-]+)",
            "linkedin": r"linkedin\.com/in/([a-zA-Z0-9_-]+)",
            "skool": r"skool\.com/([a-zA-Z0-9_-]+)",
            "patreon": r"patreon\.com/([a-zA-Z0-9_-]+)",
        }
        for platform_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                links[platform_name] = match.group(0)
        return links
