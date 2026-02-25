"""SQLAlchemy models mirroring the RCWL-CMS MySQL database schema.

These models map to the EXISTING CMS tables — the Growth Engine writes
directly to this database to create stores. We do NOT manage migrations
for these tables; they're owned by the Laravel CMS.

Column names match the CMS exactly (snake_case, same types).
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CMSBase(DeclarativeBase):
    """Separate base for CMS models (connects to MySQL, not PostgreSQL)."""
    pass


# ---------------------------------------------------------------------------
# Application (the "store")
# ---------------------------------------------------------------------------


class Application(CMSBase):
    """An application/store in the CMS. ID is NOT auto-increment."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    guid: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(45))
    email: Mapped[str] = mapped_column(String(50))
    status_id: Mapped[int] = mapped_column(Integer)
    currency_id: Mapped[int] = mapped_column(Integer, default=2)  # 2=USD
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApplicationSetting(CMSBase):
    __tablename__ = "application_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    app_version: Mapped[int] = mapped_column(Integer, default=1)
    setting_version: Mapped[int] = mapped_column(Integer, default=1)
    app_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coach_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    apple_store_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    play_store_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_placeholder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    light_home_logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dark_home_logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    light_login_logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dark_login_logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nutrition_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tab_home_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tab_library_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tab_community_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tab_shop_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tab_account_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tab_wellness_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    copyright_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cookie_privacy: Mapped[str | None] = mapped_column(String(255), nullable=True)
    terms_and_condtion_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feedback_interval_days: Mapped[int] = mapped_column(Integer, default=0)
    first_engagement_email_days: Mapped[int] = mapped_column(Integer, default=0)
    second_engagement_email_days: Mapped[int] = mapped_column(Integer, default=0)
    monthly_discount_percentage: Mapped[int] = mapped_column(Integer, default=0)
    quarterly_discount_percentage: Mapped[int] = mapped_column(Integer, default=0)
    referral_point: Mapped[int | None] = mapped_column(Integer, nullable=True)
    google_analytics_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    live_api: Mapped[str | None] = mapped_column(String(255), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    application_fee_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    talent_api: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    web_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApplicationColor(CMSBase):
    __tablename__ = "application_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    # Core colors
    primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    button_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    button_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_button: Mapped[str | None] = mapped_column(String(20), nullable=True)
    progress: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tab_dark_active: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tab_light_active: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Theme
    theme: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_theme: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Section colors
    session_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    session_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    library_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    library_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nutrition_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nutrition_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    wellness_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    wellness_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_session: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_nutrition: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_wellness: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_library: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # App chrome
    appbar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_appbar: Mapped[str | None] = mapped_column(String(20), nullable=True)
    background: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dark_background: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_background: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_dark_background: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bottom_tab_bg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_bottom_tab: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Tags
    tags: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_tags: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Overlays
    session_overlay: Mapped[str | None] = mapped_column(String(20), nullable=True)
    library_overlay: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nutrition_overlay: Mapped[str | None] = mapped_column(String(20), nullable=True)
    wellness_overlay: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Program
    program_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    program_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    on_program: Mapped[str | None] = mapped_column(String(20), nullable=True)
    program_overlay: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Meta
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApplicationFeatureSetup(CMSBase):
    __tablename__ = "application_feature_setups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    enable_google_signin: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_apple_login: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_fb_login: Mapped[bool] = mapped_column(Boolean, default=False)
    unsub_nutrition_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unsub_wellness_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unsub_community_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unsub_home_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unsub_library_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unsub_shop_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_nutrition_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_wellness_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_community_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_home_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_library_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sub_shop_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enable_switch_theme: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_referral: Mapped[bool] = mapped_column(Boolean, default=False)
    hide_signup: Mapped[bool] = mapped_column(Boolean, default=False)
    has_one_to_one: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_in_app_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_engagement_email: Mapped[bool] = mapped_column(Boolean, default=True)
    show_nutrition_filter: Mapped[bool] = mapped_column(Boolean, default=False)
    has_light_bg: Mapped[bool] = mapped_column(Boolean, default=False)
    has_program: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AudioSetting(CMSBase):
    __tablename__ = "audio_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    audio_mixing_publish_volume: Mapped[int] = mapped_column(Integer, default=90)
    audio_profile: Mapped[int] = mapped_column(Integer, default=4)
    audio_scenario: Mapped[int] = mapped_column(Integer, default=3)
    playback_signal_volume: Mapped[int] = mapped_column(Integer, default=100)
    recording_volume: Mapped[int] = mapped_column(Integer, default=100)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Users & Roles
# ---------------------------------------------------------------------------


class Role(CMSBase):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(28), nullable=True)
    user_type: Mapped[int] = mapped_column(Integer, index=True)
    status_id: Mapped[int] = mapped_column(Integer, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApplicationRole(CMSBase):
    """Links roles to applications (pivot table)."""

    __tablename__ = "application_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    role_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CMSUser(CMSBase):
    """User in the CMS. Named CMSUser to avoid conflict with Growth Engine User."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referred_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_type: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    status_id: Mapped[int] = mapped_column(Integer, index=True)
    is_test_user: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserDetail(CMSBase):
    __tablename__ = "user_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    is_signup_question_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[float | None] = mapped_column(nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(28), nullable=True)
    height: Mapped[float | None] = mapped_column(nullable=True)
    height_unit: Mapped[str | None] = mapped_column(String(28), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserRole(CMSBase):
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    role_id: Mapped[int] = mapped_column(Integer, index=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserApplication(CMSBase):
    __tablename__ = "user_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


class PermissionModule(CMSBase):
    """Read-only — we query this to get permission references for Coach Admin."""

    __tablename__ = "permission_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(28), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    user_types: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    status: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PermissionReference(CMSBase):
    """Read-only — permission references linked to modules."""

    __tablename__ = "permission_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    permission_module_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PermissionGroup(CMSBase):
    __tablename__ = "permission_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, index=True, default=0)
    permission_reference_id: Mapped[int] = mapped_column(Integer, index=True, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Email Templates
# ---------------------------------------------------------------------------


class EmailTemplateType(CMSBase):
    """Read-only — the types of email templates to create for each app."""

    __tablename__ = "email_template_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EmailTemplate(CMSBase):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    template: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    status_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Referral Points
# ---------------------------------------------------------------------------


class ReferralPoint(CMSBase):
    __tablename__ = "referral_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    referral_point: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    status_id: Mapped[int] = mapped_column(Integer, index=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class Product(CMSBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    stripe_product_id: Mapped[str | None] = mapped_column(String(28), nullable=True)
    price_id: Mapped[str | None] = mapped_column(String(28), nullable=True)
    in_app_product_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency_id: Mapped[int] = mapped_column(Integer, index=True, default=2)
    unit_amount: Mapped[int] = mapped_column(Integer, default=0)  # In cents
    interval: Mapped[str] = mapped_column(String(255), default="month")
    interval_count: Mapped[int] = mapped_column(Integer, default=1)
    number_of_sessions: Mapped[int] = mapped_column(Integer, default=0)
    order: Mapped[int] = mapped_column(Integer, default=0)
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_id: Mapped[int] = mapped_column(Integer, index=True)
    coupon_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    campaign_start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    campaign_end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# Pages (used for About page, blog content)
# ---------------------------------------------------------------------------


class Page(CMSBase):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_type_id: Mapped[int] = mapped_column(Integer, index=True)
    page_category_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    background_media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    status_id: Mapped[int] = mapped_column(Integer, index=True)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
