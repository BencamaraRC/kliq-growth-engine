"""Growth Engine database models (PostgreSQL).

These are the Growth Engine's own tables — NOT the CMS tables.
CMS models are in app/cms/models.py.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- Enums ---


class Platform(str, enum.Enum):
    YOUTUBE = "youtube"
    SKOOL = "skool"
    PATREON = "patreon"
    WEBSITE = "website"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


class ProspectStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    SCRAPED = "scraped"
    CONTENT_GENERATED = "content_generated"
    STORE_CREATED = "store_created"
    EMAIL_SENT = "email_sent"
    CLAIMED = "claimed"
    REJECTED = "rejected"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


# --- Models ---


class Prospect(Base):
    """A coach/creator discovered on a competitor platform."""

    __tablename__ = "prospects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[ProspectStatus] = mapped_column(
        Enum(ProspectStatus), default=ProspectStatus.DISCOVERED
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Primary platform
    primary_platform: Mapped[Platform] = mapped_column(Enum(Platform))
    primary_platform_id: Mapped[str] = mapped_column(String(255))
    primary_platform_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Profile data
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    banner_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    niche_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Metrics
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    content_count: Mapped[int] = mapped_column(Integer, default=0)

    # Brand
    brand_colors: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # KLIQ store (populated after store creation)
    kliq_application_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kliq_store_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    claim_token: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    discovered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    store_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scraped_content: Mapped[list["ScrapedContentRecord"]] = relationship(back_populates="prospect")
    scraped_pricing: Mapped[list["ScrapedPricingRecord"]] = relationship(back_populates="prospect")
    generated_content: Mapped[list["GeneratedContent"]] = relationship(back_populates="prospect")
    campaign_events: Mapped[list["CampaignEvent"]] = relationship(back_populates="prospect")
    platform_profiles: Mapped[list["PlatformProfile"]] = relationship(back_populates="prospect")


class PlatformProfile(Base):
    """A prospect's profile on a specific platform (supports multi-platform)."""

    __tablename__ = "platform_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    platform_id: Mapped[str] = mapped_column(String(255))
    platform_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prospect: Mapped["Prospect"] = relationship(back_populates="platform_profiles")


class ScrapedContentRecord(Base):
    """A piece of content scraped from a platform."""

    __tablename__ = "scraped_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    content_type: Mapped[str] = mapped_column(String(50))  # video, post, course, blog
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)  # transcript or full text
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    engagement_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prospect: Mapped["Prospect"] = relationship(back_populates="scraped_content")


class ScrapedPricingRecord(Base):
    """A pricing tier scraped from a platform."""

    __tablename__ = "scraped_pricing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    tier_name: Mapped[str] = mapped_column(String(255))
    price_amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    interval: Mapped[str] = mapped_column(String(20), default="month")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits: Mapped[list | None] = mapped_column(JSON, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prospect: Mapped["Prospect"] = relationship(back_populates="scraped_pricing")


class GeneratedContent(Base):
    """AI-generated content for a prospect's KLIQ store."""

    __tablename__ = "generated_content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"))
    content_type: Mapped[str] = mapped_column(String(50))  # bio, blog, product, seo, color
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_content_id: Mapped[int | None] = mapped_column(
        ForeignKey("scraped_content.id"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prospect: Mapped["Prospect"] = relationship(back_populates="generated_content")


class Campaign(Base):
    """An outreach campaign targeting discovered coaches."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT
    )
    platform_filter: Mapped[Platform | None] = mapped_column(Enum(Platform), nullable=True)
    niche_filter: Mapped[list | None] = mapped_column(JSON, nullable=True)
    min_followers: Mapped[int] = mapped_column(Integer, default=0)
    email_sequence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["CampaignEvent"]] = relationship(back_populates="campaign")


class CampaignEvent(Base):
    """Tracks email sends, opens, clicks, and claims for a campaign."""

    __tablename__ = "campaign_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    prospect_id: Mapped[int] = mapped_column(ForeignKey("prospects.id"))
    step: Mapped[int] = mapped_column(Integer)  # 1=store_ready, 2=reminder_1, 3=reminder_2, 4=claimed
    email_status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus), default=EmailStatus.PENDING
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    brevo_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="events")
    prospect: Mapped["Prospect"] = relationship(back_populates="campaign_events")
