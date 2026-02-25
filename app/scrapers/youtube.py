"""YouTube platform adapter.

Uses YouTube Data API v3 for channel/video discovery and metadata.
Uses youtube-transcript-api for free transcript extraction (no quota cost).

Quota budget (10,000 units/day):
- search.list = 100 units per call
- channels.list = 1 unit per call
- videos.list = 1 unit per call
- ~50 coaches/day capacity
"""

import logging
from typing import Optional

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.config import settings
from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)

logger = logging.getLogger(__name__)

# Fitness/wellness related search queries
DEFAULT_SEARCH_QUERIES = [
    "fitness coach",
    "personal trainer",
    "yoga instructor",
    "wellness coach",
    "nutrition coach",
    "strength training coach",
    "pilates instructor",
    "CrossFit coach",
    "online fitness coaching",
    "health coach",
]


class YouTubeAdapter(PlatformAdapter):
    """YouTube platform adapter using Data API v3."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or settings.youtube_api_key
        self._youtube = None

    @property
    def platform(self) -> Platform:
        return Platform.YOUTUBE

    @property
    def youtube(self):
        if self._youtube is None:
            self._youtube = build("youtube", "v3", developerKey=self._api_key)
        return self._youtube

    async def discover_coaches(
        self,
        search_queries: list[str] | None = None,
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Discover fitness coaches via YouTube search.

        Uses search.list (100 units per call). With max_results=50 and
        multiple queries, budget carefully against the 10K daily limit.
        """
        queries = search_queries or DEFAULT_SEARCH_QUERIES
        results_per_query = max(1, max_results // len(queries))
        discovered = []
        seen_ids = set()

        for query in queries:
            if len(discovered) >= max_results:
                break

            try:
                response = (
                    self.youtube.search()
                    .list(
                        q=query,
                        type="channel",
                        part="snippet",
                        maxResults=min(results_per_query, 50),
                        relevanceLanguage="en",
                    )
                    .execute()
                )

                for item in response.get("items", []):
                    channel_id = item["snippet"]["channelId"]
                    if channel_id in seen_ids:
                        continue
                    seen_ids.add(channel_id)

                    profile = ScrapedProfile(
                        platform=Platform.YOUTUBE,
                        platform_id=channel_id,
                        name=item["snippet"]["title"],
                        bio=item["snippet"].get("description", ""),
                        profile_image_url=item["snippet"]
                        .get("thumbnails", {})
                        .get("high", {})
                        .get("url", ""),
                        raw_data=item,
                    )
                    discovered.append(profile)

            except Exception as e:
                logger.error(f"YouTube search failed for query '{query}': {e}")
                continue

        return discovered[:max_results]

    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape full channel details. Uses channels.list (1 unit)."""
        response = (
            self.youtube.channels()
            .list(
                id=platform_id,
                part="snippet,statistics,brandingSettings",
            )
            .execute()
        )

        items = response.get("items", [])
        if not items:
            raise ValueError(f"YouTube channel not found: {platform_id}")

        channel = items[0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})
        branding = channel.get("brandingSettings", {})

        # Extract social links from description
        description = snippet.get("description", "")
        social_links = await self.extract_social_links(description)

        # Extract website from channel settings
        website_url = None
        custom_url = snippet.get("customUrl", "")
        if branding.get("channel", {}).get("unsubscribedTrailer"):
            website_url = branding["channel"].get("unsubscribedTrailer")

        # Build profile
        profile = ScrapedProfile(
            platform=Platform.YOUTUBE,
            platform_id=platform_id,
            name=snippet.get("title", ""),
            bio=description,
            profile_image_url=snippet.get("thumbnails", {})
            .get("high", {})
            .get("url", ""),
            banner_image_url=branding.get("image", {}).get(
                "bannerExternalUrl", ""
            ),
            email=await self.extract_email(
                ScrapedProfile(
                    platform=Platform.YOUTUBE,
                    platform_id=platform_id,
                    name="",
                    bio=description,
                )
            ),
            website_url=website_url,
            social_links=social_links,
            follower_count=int(stats.get("subscriberCount", 0)),
            subscriber_count=int(stats.get("subscriberCount", 0)),
            niche_tags=self._extract_niche_tags(description),
            raw_data=channel,
        )

        return profile

    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape recent videos with transcripts.

        search.list (100 units) + videos.list (1 unit per batch).
        Transcripts via youtube-transcript-api (free, no quota).
        """
        # Get recent videos
        response = (
            self.youtube.search()
            .list(
                channelId=platform_id,
                type="video",
                part="snippet",
                maxResults=min(max_items, 50),
                order="date",
            )
            .execute()
        )

        video_ids = []
        video_snippets = {}
        for item in response.get("items", []):
            vid_id = item["id"].get("videoId")
            if vid_id:
                video_ids.append(vid_id)
                video_snippets[vid_id] = item["snippet"]

        if not video_ids:
            return []

        # Get video statistics in batch
        stats_response = (
            self.youtube.videos()
            .list(
                id=",".join(video_ids),
                part="statistics,contentDetails",
            )
            .execute()
        )

        stats_map = {}
        for item in stats_response.get("items", []):
            stats_map[item["id"]] = item

        # Build content list with transcripts
        content = []
        for vid_id in video_ids:
            snippet = video_snippets.get(vid_id, {})
            stats = stats_map.get(vid_id, {}).get("statistics", {})

            transcript_text = await self._get_transcript(vid_id)

            content.append(
                ScrapedContent(
                    platform=Platform.YOUTUBE,
                    platform_id=platform_id,
                    content_type="video",
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    body=transcript_text,
                    url=f"https://www.youtube.com/watch?v={vid_id}",
                    thumbnail_url=snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url", ""),
                    published_at=snippet.get("publishedAt"),
                    view_count=int(stats.get("viewCount", 0)),
                    engagement_count=int(stats.get("likeCount", 0))
                    + int(stats.get("commentCount", 0)),
                    tags=snippet.get("tags", []) if "tags" in snippet else [],
                    raw_data={"snippet": snippet, "stats": stats},
                )
            )

        return content

    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """YouTube doesn't have native pricing. Returns empty list.

        Pricing is typically found by following links from the channel
        description to Patreon, Skool, or personal websites.
        The discovery orchestrator handles this cross-platform chaining.
        """
        return []

    async def _get_transcript(self, video_id: str) -> str:
        """Extract transcript using youtube-transcript-api (free, no quota)."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join(entry["text"] for entry in transcript_list)
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            logger.debug(f"No transcript available for video {video_id}")
            return ""
        except Exception as e:
            logger.warning(f"Transcript extraction failed for {video_id}: {e}")
            return ""

    def _extract_niche_tags(self, text: str) -> list[str]:
        """Extract fitness/wellness niche tags from text."""
        niche_keywords = {
            "fitness": ["fitness", "workout", "exercise", "training"],
            "yoga": ["yoga", "vinyasa", "ashtanga", "meditation"],
            "nutrition": ["nutrition", "diet", "meal prep", "macros", "calories"],
            "strength": ["strength", "powerlifting", "weightlifting", "bodybuilding"],
            "cardio": ["cardio", "running", "hiit", "endurance"],
            "pilates": ["pilates", "barre"],
            "wellness": ["wellness", "mindfulness", "mental health", "self-care"],
            "crossfit": ["crossfit", "wod", "functional fitness"],
            "calisthenics": ["calisthenics", "bodyweight"],
            "martial_arts": ["martial arts", "mma", "boxing", "kickboxing"],
        }

        text_lower = text.lower()
        tags = []
        for tag, keywords in niche_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)
        return tags
