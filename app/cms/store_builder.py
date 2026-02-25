"""Store builder — replicates ApplicationController::store from RCWL-CMS.

Creates a complete KLIQ webstore by writing directly to the CMS MySQL
database. This replicates the exact bootstrap flow from the Laravel
ApplicationController::store method (lines 67-196).

All records are created with status_id=1 (Inactive/Draft).
When the coach claims the store, status flips to 2 (Active).
"""

import json
import logging
import secrets
import uuid

import bcrypt
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cms.models import (
    Application,
    ApplicationColor,
    ApplicationFeatureSetup,
    ApplicationRole,
    ApplicationSetting,
    AudioSetting,
    CMSUser,
    EmailTemplate,
    EmailTemplateType,
    PermissionGroup,
    PermissionModule,
    PermissionReference,
    ReferralPoint,
    Role,
    UserApplication,
    UserDetail,
    UserRole,
)
from app.scrapers.color_extractor import BrandColors

logger = logging.getLogger(__name__)

# CMS constants
STATUS_INACTIVE = 1  # Draft — not visible
STATUS_ACTIVE = 2
USER_TYPE_COACH_ADMIN = 3
CURRENCY_USD = 2
SUPER_ADMIN_ID = 1
DEFAULT_REFERRAL_POINTS = 100


class StoreCreationResult:
    """Result of creating a store in the CMS."""

    def __init__(
        self,
        application_id: int,
        guid: str,
        user_id: int,
        role_id: int,
        temp_password: str,
        store_url: str,
    ):
        self.application_id = application_id
        self.guid = guid
        self.user_id = user_id
        self.role_id = role_id
        self.temp_password = temp_password
        self.store_url = store_url


async def build_store(
    session: AsyncSession,
    name: str,
    email: str,
    first_name: str,
    last_name: str,
    coach_name: str | None = None,
    brand_colors: BrandColors | None = None,
    seo_title: str | None = None,
    seo_description: str | None = None,
    seo_keywords: str | None = None,
    store_slug: str | None = None,
    profile_image_url: str | None = None,
    support_email: str | None = None,
    currency_id: int = CURRENCY_USD,
) -> StoreCreationResult:
    """Create a complete KLIQ webstore.

    Replicates ApplicationController::store flow:
    1. Application
    2. ApplicationSetting
    3. ApplicationFeatureSetup
    4. ApplicationColor (with brand colors if available)
    5. AudioSetting
    6. Role (Coach Admin)
    7. ApplicationRole
    8. UserApplication (super admin link)
    9. User (Coach Admin, temp password)
    10. UserDetail
    11. UserRole
    12. PermissionGroups (all Coach Admin permissions)
    13. EmailTemplates (one per EmailTemplateType)
    14. ReferralPoint

    Args:
        session: Async MySQL session (CMS database).
        name: Store/application name.
        email: Coach's email.
        first_name: Coach's first name.
        last_name: Coach's last name.
        coach_name: Display name (defaults to first_name + last_name).
        brand_colors: Extracted brand colors for theming.
        seo_title: SEO page title.
        seo_description: SEO meta description.
        seo_keywords: SEO keywords.
        store_slug: URL-friendly store name (used for web_url).
        profile_image_url: Coach's profile image URL.
        support_email: Support email for the store.
        currency_id: Currency (1=GBP, 2=USD, 3=EUR).

    Returns:
        StoreCreationResult with IDs, temp password, and store URL.
    """
    coach_name = coach_name or f"{first_name} {last_name}"
    guid = str(uuid.uuid4())
    temp_password = secrets.token_urlsafe(16)
    hashed_password = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()

    # 1. Get next application ID (NOT auto-increment in CMS)
    app_id = await _get_next_application_id(session)

    logger.info(f"Creating store '{name}' with application_id={app_id}")

    # 2. Create Application
    application = Application(
        id=app_id,
        guid=guid,
        name=name,
        email=email,
        status_id=STATUS_INACTIVE,
        currency_id=currency_id,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(application)
    await session.flush()

    # 3. Create ApplicationSetting
    web_url = f"https://{store_slug}.joinkliq.io" if store_slug else None
    setting = ApplicationSetting(
        application_id=app_id,
        setting_version=1,
        app_version=1,
        app_name=name,
        coach_name=coach_name,
        tab_wellness_text="Wellness",
        tab_account_text="Account",
        tab_shop_text="Shop",
        tab_community_text="Community",
        tab_library_text="Library",
        tab_home_text="Home",
        nutrition_text="Nutrition",
        support_email=support_email or email,
        profile_placeholder=profile_image_url,
        meta_title=seo_title,
        meta_description=seo_description,
        meta_keywords=seo_keywords,
        web_url=web_url,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(setting)

    # 4. Create ApplicationFeatureSetup
    feature_setup = ApplicationFeatureSetup(
        application_id=app_id,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(feature_setup)

    # 5. Create ApplicationColor
    colors = _build_colors(app_id, brand_colors)
    session.add(colors)

    # 6. Create AudioSetting
    audio = AudioSetting(
        application_id=app_id,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(audio)
    await session.flush()

    # 7. Create Role (Coach Admin)
    role = Role(
        application_id=app_id,
        name="Coach Admin",
        user_type=USER_TYPE_COACH_ADMIN,
        status_id=STATUS_ACTIVE,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(role)
    await session.flush()

    # 8. ApplicationRole pivot
    app_role = ApplicationRole(
        application_id=app_id,
        role_id=role.id,
    )
    session.add(app_role)

    # 9. Link super admin to application
    super_admin_link = UserApplication(
        user_id=SUPER_ADMIN_ID,
        application_id=app_id,
    )
    session.add(super_admin_link)

    # 10. Create Coach User
    user = CMSUser(
        application_id=app_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password,
        user_type=USER_TYPE_COACH_ADMIN,
        status_id=STATUS_INACTIVE,
        photo_url=profile_image_url,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(user)
    await session.flush()

    # 11. UserDetail
    user_detail = UserDetail(
        application_id=app_id,
        user_id=user.id,
    )
    session.add(user_detail)

    # 12. Link user to application
    user_app_link = UserApplication(
        user_id=user.id,
        application_id=app_id,
    )
    session.add(user_app_link)

    # 13. UserRole
    user_role = UserRole(
        application_id=app_id,
        user_id=user.id,
        role_id=role.id,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(user_role)

    # 14. Permission groups — all Coach Admin permissions
    await _create_permission_groups(session, role.id)

    # 15. Email templates — one per EmailTemplateType
    await _create_email_templates(session, app_id)

    # 16. Referral point
    referral = ReferralPoint(
        application_id=app_id,
        referral_point=DEFAULT_REFERRAL_POINTS,
        is_default=True,
        status_id=STATUS_ACTIVE,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(referral)

    await session.flush()

    store_url = web_url or f"https://admin.joinkliq.io/app/{app_id}"

    logger.info(
        f"Store '{name}' created: app_id={app_id}, user_id={user.id}, "
        f"role_id={role.id}, url={store_url}"
    )

    return StoreCreationResult(
        application_id=app_id,
        guid=guid,
        user_id=user.id,
        role_id=role.id,
        temp_password=temp_password,
        store_url=store_url,
    )


async def _get_next_application_id(session: AsyncSession) -> int:
    """Get the next available application ID.

    The applications table does NOT use auto-increment.
    We query MAX(id) + 1 with a row lock to prevent race conditions.
    """
    result = await session.execute(
        select(func.max(Application.id)).with_for_update()
    )
    max_id = result.scalar_one_or_none()
    return (max_id or 0) + 1


def _build_colors(app_id: int, brand_colors: BrandColors | None) -> ApplicationColor:
    """Build ApplicationColor from extracted brand colors or defaults.

    Maps BrandColors (primary, secondary, accent) to the CMS's 30+ color fields.
    """
    if brand_colors:
        primary = brand_colors.primary.lstrip("#")
        secondary = brand_colors.secondary.lstrip("#")
        accent = brand_colors.accent.lstrip("#")
        bg = brand_colors.background.lstrip("#")
        text_color = brand_colors.text.lstrip("#")
    else:
        # CMS defaults
        primary = "1E81FF"
        secondary = "1A74E5"
        accent = "1E81FF"
        bg = "FFFFFF"
        text_color = "1A1A1A"

    on_primary = "FFFFFF" if _is_dark_hex(primary) else "1A1A1A"
    on_secondary = "FFFFFF" if _is_dark_hex(secondary) else "1A1A1A"

    return ApplicationColor(
        application_id=app_id,
        # Core
        primary=primary,
        on_primary=on_primary,
        secondary=secondary,
        on_secondary=on_secondary,
        button_primary=primary,
        button_secondary=secondary,
        on_button=on_primary,
        progress=primary,
        tab_dark_active=primary,
        tab_light_active=primary,
        # Theme
        theme=primary,
        on_theme=on_primary,
        # Sections — use primary/secondary/accent
        session_primary=primary,
        session_secondary=secondary,
        library_primary=secondary,
        library_secondary=accent,
        nutrition_primary=accent,
        nutrition_secondary=primary,
        wellness_primary=primary,
        wellness_secondary=accent,
        on_session=on_primary,
        on_library=on_secondary,
        on_nutrition=on_primary,
        on_wellness=on_primary,
        # App chrome
        appbar=primary,
        on_appbar=on_primary,
        background=bg,
        dark_background="121212",
        on_background=text_color,
        on_dark_background="FFFFFF",
        bottom_tab_bg=bg,
        on_bottom_tab=text_color,
        # Tags
        tags=accent,
        on_tags=on_primary,
        # Overlays
        session_overlay=primary,
        library_overlay=secondary,
        nutrition_overlay=accent,
        wellness_overlay=primary,
        # Program
        program_primary=primary,
        program_secondary=secondary,
        on_program=on_primary,
        program_overlay=primary,
        # Meta
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )


async def _create_permission_groups(session: AsyncSession, role_id: int):
    """Create permission groups for Coach Admin role.

    Replicates the PHP:
        $modules = PermissionModule::with('references')
            ->whereJsonContains('user_types', '3')
            ->orderBy('order', 'asc')->get();
        foreach ($modules as $module) {
            foreach ($module->references as $reference) {
                $role->groups()->create(['permission_reference_id' => $reference->id]);
            }
        }
    """
    # Find all permission modules that include user_type 3 (Coach Admin)
    modules_result = await session.execute(
        select(PermissionModule).where(
            PermissionModule.user_types.like('%"3"%')
        ).order_by(PermissionModule.order)
    )
    modules = modules_result.scalars().all()

    for module in modules:
        refs_result = await session.execute(
            select(PermissionReference).where(
                PermissionReference.permission_module_id == module.id
            )
        )
        references = refs_result.scalars().all()

        for ref in references:
            group = PermissionGroup(
                role_id=role_id,
                permission_reference_id=ref.id,
            )
            session.add(group)


async def _create_email_templates(session: AsyncSession, app_id: int):
    """Create email template entries for each EmailTemplateType.

    Replicates the PHP:
        $emailTemplateTypes = EmailTemplateType::all();
        foreach ($emailTemplateTypes as $type) {
            EmailTemplate::insert([...]);
        }
    """
    types_result = await session.execute(select(EmailTemplateType))
    template_types = types_result.scalars().all()

    for ttype in template_types:
        template = EmailTemplate(
            application_id=app_id,
            name=ttype.name,
            subject=ttype.name,
            template="",
            type_id=ttype.id,
            status_id=STATUS_ACTIVE,
            created_by=SUPER_ADMIN_ID,
            updated_by=SUPER_ADMIN_ID,
        )
        session.add(template)


def _is_dark_hex(hex_color: str) -> bool:
    """Check if a hex color is dark (for deciding text contrast)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return False
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < 128
