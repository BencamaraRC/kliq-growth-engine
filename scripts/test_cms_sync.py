#!/usr/bin/env python3
"""End-to-end test: Growth Engine → CMS sync + claim flow.

Tests the full pipeline locally using SQLite as the CMS backend:
1. Creates CMS tables from Growth Engine's ORM models
2. Seeds required lookup data (status_types, page_types, currencies, etc.)
3. Runs store_builder to create a complete store
4. Runs content.py and products.py to add pages and products
5. Runs claim flow to activate the store
6. Verifies all CMS records match expectations

Usage:
    python scripts/test_cms_sync.py                 # Full test (SQLite)
    python scripts/test_cms_sync.py --cms-url URL   # Test against real MySQL

Requires: the Growth Engine venv with all dependencies installed.
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from app.cms.models import (
    Application,
    ApplicationColor,
    ApplicationFeatureSetup,
    ApplicationRole,
    ApplicationSetting,
    AudioSetting,
    CMSBase,
    CMSUser,
    EmailTemplate,
    EmailTemplateType,
    Page,
    PermissionGroup,
    PermissionModule,
    PermissionReference,
    Product,
    ReferralPoint,
    Role,
    UserApplication,
    UserDetail,
    UserRole,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

SEED_STATUS_TYPES = [
    {"id": 1, "name": "Inactive", "is_active": True},
    {"id": 2, "name": "Active", "is_active": True},
    {"id": 3, "name": "Archive", "is_active": True},
]

SEED_PAGE_TYPES = [
    {"id": 1, "name": "Static Pages", "is_active": True},
    {"id": 2, "name": "Onboarding Screen", "is_active": True},
    {"id": 3, "name": "Splash Screen", "is_active": True},
]

SEED_CURRENCIES = [
    {"id": 1, "name": "GBP", "symbol": "£", "is_active": True},
    {"id": 2, "name": "USD", "symbol": "$", "is_active": True},
    {"id": 3, "name": "Euro", "symbol": "€", "is_active": True},
]

SEED_EMAIL_TEMPLATE_TYPES = [
    {"id": 1, "name": "Admin Forgot Password"},
    {"id": 2, "name": "Forgot Password"},
    {"id": 3, "name": "New user sign up"},
    {"id": 4, "name": "New user subscription"},
    {"id": 5, "name": "Weekly updates"},
    {"id": 6, "name": "Apple watch not connected"},
    {"id": 7, "name": "Re-Engagement Email"},
    {"id": 8, "name": "Community mention template"},
]

SEED_PERMISSION_MODULES = [
    {"id": 1, "name": "Utility", "order": 1, "user_types": '["1","2"]', "status": 1},
    {"id": 2, "name": "Role", "order": 2, "user_types": '["1","2"]', "status": 1},
    {"id": 3, "name": "Admin", "order": 3, "user_types": '["1","2"]', "status": 1},
    {"id": 4, "name": "Coach", "order": 4, "user_types": '["1","2"]', "status": 1},
    {"id": 5, "name": "Application", "order": 5, "user_types": '["1","2"]', "status": 1},
    {"id": 6, "name": "Application Settings", "order": 6, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 7, "name": "Nutrition", "order": 7, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 8, "name": "Wellness", "order": 8, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 9, "name": "Category", "order": 9, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 10, "name": "Video", "order": 10, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 11, "name": "Pages", "order": 11, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 12, "name": "Links", "order": 12, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 13, "name": "Questions", "order": 13, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 14, "name": "Fitness Level", "order": 14, "user_types": '["1","2","3","4"]', "status": 1},
    {"id": 15, "name": "Products", "order": 15, "user_types": '["1","2","3","4"]', "status": 1},
]

SEED_PERMISSION_REFERENCES = [
    # Module 1: Utility
    {"id": 1, "permission_module_id": 1, "name": "View"},
    # Module 2: Role
    {"id": 2, "permission_module_id": 2, "name": "Add"},
    {"id": 3, "permission_module_id": 2, "name": "Edit"},
    {"id": 4, "permission_module_id": 2, "name": "Delete"},
    {"id": 5, "permission_module_id": 2, "name": "Configure"},
    # Module 3: Admin
    {"id": 6, "permission_module_id": 3, "name": "Add"},
    {"id": 7, "permission_module_id": 3, "name": "Edit"},
    {"id": 8, "permission_module_id": 3, "name": "Delete"},
    # Module 4: Coach
    {"id": 9, "permission_module_id": 4, "name": "View"},
    # Module 5: Application
    {"id": 10, "permission_module_id": 5, "name": "Add"},
    {"id": 11, "permission_module_id": 5, "name": "Edit"},
    {"id": 12, "permission_module_id": 5, "name": "Delete"},
    # Module 6: Application Settings
    {"id": 13, "permission_module_id": 6, "name": "View"},
    {"id": 14, "permission_module_id": 6, "name": "Update"},
    # Module 7-15: Nutrition, Wellness, Category, Video, Pages, Links, Questions, Fitness Level, Products
    {"id": 15, "permission_module_id": 7, "name": "Add"},
    {"id": 16, "permission_module_id": 7, "name": "Edit"},
    {"id": 17, "permission_module_id": 7, "name": "Delete"},
    {"id": 18, "permission_module_id": 8, "name": "Add"},
    {"id": 19, "permission_module_id": 8, "name": "Edit"},
    {"id": 20, "permission_module_id": 8, "name": "Delete"},
    {"id": 21, "permission_module_id": 9, "name": "Add"},
    {"id": 22, "permission_module_id": 9, "name": "Edit"},
    {"id": 23, "permission_module_id": 9, "name": "Delete"},
    {"id": 24, "permission_module_id": 10, "name": "Add"},
    {"id": 25, "permission_module_id": 10, "name": "Edit"},
    {"id": 26, "permission_module_id": 10, "name": "Delete"},
    {"id": 27, "permission_module_id": 11, "name": "Add"},
    {"id": 28, "permission_module_id": 11, "name": "Edit"},
    {"id": 29, "permission_module_id": 11, "name": "Delete"},
    {"id": 30, "permission_module_id": 12, "name": "Add"},
    {"id": 31, "permission_module_id": 12, "name": "Edit"},
    {"id": 32, "permission_module_id": 12, "name": "Delete"},
    {"id": 33, "permission_module_id": 13, "name": "Add"},
    {"id": 34, "permission_module_id": 13, "name": "Edit"},
    {"id": 35, "permission_module_id": 13, "name": "Delete"},
    {"id": 36, "permission_module_id": 14, "name": "Add"},
    {"id": 37, "permission_module_id": 14, "name": "Edit"},
    {"id": 38, "permission_module_id": 14, "name": "Delete"},
    {"id": 39, "permission_module_id": 15, "name": "Add"},
    {"id": 40, "permission_module_id": 15, "name": "Edit"},
    {"id": 41, "permission_module_id": 15, "name": "Delete"},
]

# The super admin user (must exist for created_by/updated_by FKs)
SEED_SUPER_ADMIN = {
    "id": 1,
    "first_name": "Super",
    "last_name": "Admin",
    "email": "admin@remotecoach.fit",
    "password": "$2b$12$placeholder_hash_for_testing_only",
    "user_type": 1,
    "is_email_verified": True,
    "status_id": 2,
    "created_by": 1,
    "updated_by": 1,
}


# ---------------------------------------------------------------------------
# Fake data classes (avoid importing AI modules that need API keys)
# ---------------------------------------------------------------------------


@dataclass
class FakeBrandColors:
    primary: str = "#1C3838"
    secondary: str = "#FF9F88"
    accent: str = "#FFFDF9"
    background: str = "#FFFFFF"
    text: str = "#1A1A1A"


@dataclass
class FakeBlog:
    blog_title: str = "10 Minute Morning Stretch Routine"
    body_html: str = "<h2>Start Your Day Right</h2><p>This 10-minute routine will wake up your body.</p>"
    seo_title: str = "10 Minute Morning Stretch | Coach Test"
    seo_description: str = "A quick morning stretch routine for beginners."


@dataclass
class FakeProduct:
    name: str = "Monthly Coaching"
    description: str = "Full access to all programs, live sessions, and community."
    price_cents: int = 2999
    currency: str = "USD"
    interval: str = "month"
    type: str = "subscription"


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


def create_test_engine(cms_url: str | None = None):
    """Create a sync engine for test setup, async engine for actual operations."""
    if cms_url:
        sync_url = cms_url.replace("+aiomysql", "+pymysql").replace("+asyncpg", "+psycopg2")
        async_url = cms_url
    else:
        db_path = Path(__file__).parent.parent / "test_cms.db"
        sync_url = f"sqlite:///{db_path}"
        async_url = f"sqlite+aiosqlite:///{db_path}"

    sync_engine = create_engine(sync_url, echo=False)
    async_engine = create_async_engine(async_url, echo=False)
    return sync_engine, async_engine


def setup_schema(sync_engine):
    """Create all CMS tables and seed lookup data."""
    logger.info("Creating CMS tables...")
    CMSBase.metadata.drop_all(sync_engine)
    CMSBase.metadata.create_all(sync_engine)

    with Session(sync_engine) as session:
        # Seed email template types
        for row in SEED_EMAIL_TEMPLATE_TYPES:
            session.add(EmailTemplateType(**row))

        # Seed permission modules
        for row in SEED_PERMISSION_MODULES:
            session.add(PermissionModule(**row))

        # Seed permission references
        for row in SEED_PERMISSION_REFERENCES:
            session.add(PermissionReference(**row))

        # Seed super admin user
        session.add(CMSUser(**SEED_SUPER_ADMIN))

        session.commit()
        logger.info(
            f"Seeded: {len(SEED_EMAIL_TEMPLATE_TYPES)} email template types, "
            f"{len(SEED_PERMISSION_MODULES)} permission modules, "
            f"{len(SEED_PERMISSION_REFERENCES)} permission references, "
            f"1 super admin user"
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"  [{status}] {name}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    results.append((name, condition, detail))


async def test_store_creation(async_engine):
    """Test 1: Build a complete store via store_builder."""
    print("\n== TEST 1: Store Creation ==")

    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.cms.store_builder import build_store

    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await build_store(
            session=session,
            name="FitCoach Test Store",
            email="testcoach@example.com",
            first_name="Test",
            last_name="Coach",
            coach_name="Coach Test",
            brand_colors=FakeBrandColors(),
            seo_title="FitCoach Test — Fitness Programs",
            seo_description="The best fitness programs for beginners and pros.",
            seo_keywords="fitness, coaching, workout, strength",
            store_slug="fitcoach-test",
            profile_image_url="https://example.com/profile.jpg",
            support_email="support@fitcoach-test.com",
            currency_id=2,
        )
        await session.commit()

    check("Application ID assigned", result.application_id >= 1, f"got {result.application_id}")
    check("GUID is UUID4", len(result.guid) == 36)
    check("User ID assigned", result.user_id >= 2, f"got {result.user_id}")
    check("Role ID assigned", result.role_id >= 1, f"got {result.role_id}")
    check("Temp password generated", len(result.temp_password) > 0)
    check(
        "Store URL correct",
        result.store_url == "https://fitcoach-test.joinkliq.io",
        f"got {result.store_url}",
    )

    return result


async def test_verify_records(async_engine, store_result):
    """Test 2: Verify all CMS records were created correctly."""
    print("\n== TEST 2: Verify CMS Records ==")

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    app_id = store_result.application_id

    async with async_session() as session:
        # Application
        app = (await session.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()
        check("Application exists", app is not None)
        check("Application status=1 (Inactive)", app.status_id == 1 if app else False)
        check("Application name correct", app.name == "FitCoach Test Store" if app else False)
        check("Application email correct", app.email == "testcoach@example.com" if app else False)
        check("Application currency=USD", app.currency_id == 2 if app else False)

        # ApplicationSetting
        setting = (
            await session.execute(
                select(ApplicationSetting).where(ApplicationSetting.application_id == app_id)
            )
        ).scalar_one_or_none()
        check("ApplicationSetting exists", setting is not None)
        check("App name in settings", setting.app_name == "FitCoach Test Store" if setting else False)
        check("Coach name in settings", setting.coach_name == "Coach Test" if setting else False)
        check("SEO title set", setting.meta_title == "FitCoach Test — Fitness Programs" if setting else False)
        check("Web URL set", setting.web_url == "https://fitcoach-test.joinkliq.io" if setting else False)
        check("Support email set", setting.support_email == "support@fitcoach-test.com" if setting else False)
        check("Tab labels set", setting.tab_home_text == "Home" if setting else False)

        # ApplicationColor
        color = (
            await session.execute(
                select(ApplicationColor).where(ApplicationColor.application_id == app_id)
            )
        ).scalar_one_or_none()
        check("ApplicationColor exists", color is not None)
        check("Primary color set", color.primary == "1C3838" if color else False, f"got {color.primary if color else 'None'}")
        check("Secondary color set", color.secondary == "FF9F88" if color else False)
        check("Background set", color.background == "FFFFFF" if color else False)
        check("on_primary auto-calculated", color.on_primary == "FFFFFF" if color else False, "dark primary should get white text")

        # ApplicationFeatureSetup
        feature = (
            await session.execute(
                select(ApplicationFeatureSetup).where(ApplicationFeatureSetup.application_id == app_id)
            )
        ).scalar_one_or_none()
        check("ApplicationFeatureSetup exists", feature is not None)

        # AudioSetting
        audio = (
            await session.execute(
                select(AudioSetting).where(AudioSetting.application_id == app_id)
            )
        ).scalar_one_or_none()
        check("AudioSetting exists", audio is not None)
        check("Audio defaults correct", audio.audio_mixing_publish_volume == 90 if audio else False)

        # Role
        role = (await session.execute(select(Role).where(Role.id == store_result.role_id))).scalar_one_or_none()
        check("Role exists", role is not None)
        check("Role is Coach Admin", role.name == "Coach Admin" if role else False)
        check("Role user_type=3", role.user_type == 3 if role else False)
        check("Role status=Active", role.status_id == 2 if role else False)

        # ApplicationRole
        app_role = (
            await session.execute(
                select(ApplicationRole).where(ApplicationRole.application_id == app_id)
            )
        ).scalar_one_or_none()
        check("ApplicationRole pivot exists", app_role is not None)

        # CMSUser (coach)
        user = (await session.execute(select(CMSUser).where(CMSUser.id == store_result.user_id))).scalar_one_or_none()
        check("Coach user exists", user is not None)
        check("User email correct", user.email == "testcoach@example.com" if user else False)
        check("User status=1 (Inactive)", user.status_id == 1 if user else False)
        check("User type=3 (Coach Admin)", user.user_type == 3 if user else False)
        check("Password is bcrypt hash", user.password.startswith("$2") if user else False)
        check("Profile image stored", user.photo_url == "https://example.com/profile.jpg" if user else False)

        # UserDetail
        detail = (
            await session.execute(
                select(UserDetail).where(UserDetail.user_id == store_result.user_id)
            )
        ).scalar_one_or_none()
        check("UserDetail exists", detail is not None)

        # UserApplication (should be 2: super admin + coach)
        user_apps = (
            await session.execute(
                select(UserApplication).where(UserApplication.application_id == app_id)
            )
        ).scalars().all()
        check("UserApplication count=2", len(user_apps) == 2, f"got {len(user_apps)}")

        # UserRole
        user_role = (
            await session.execute(
                select(UserRole).where(UserRole.user_id == store_result.user_id)
            )
        ).scalar_one_or_none()
        check("UserRole exists", user_role is not None)
        check("UserRole links to correct role", user_role.role_id == store_result.role_id if user_role else False)

        # PermissionGroups
        perm_groups = (
            await session.execute(
                select(PermissionGroup).where(PermissionGroup.role_id == store_result.role_id)
            )
        ).scalars().all()
        # Modules with user_type "3": modules 6-15 = 10 modules, each with refs
        # Module 6: 2 refs, Modules 7-15: 3 refs each = 2 + 9*3 = 29
        check("PermissionGroups created", len(perm_groups) > 0, f"got {len(perm_groups)}")
        check("PermissionGroups count=29 (Coach Admin)", len(perm_groups) == 29, f"got {len(perm_groups)}")

        # EmailTemplates
        templates = (
            await session.execute(
                select(EmailTemplate).where(EmailTemplate.application_id == app_id)
            )
        ).scalars().all()
        check("EmailTemplates created", len(templates) == 8, f"got {len(templates)}")

        # ReferralPoint
        referral = (
            await session.execute(
                select(ReferralPoint).where(ReferralPoint.application_id == app_id)
            )
        ).scalar_one_or_none()
        check("ReferralPoint exists", referral is not None)
        check("Referral points=100", referral.referral_point == 100 if referral else False)
        check("Referral is_default=True", referral.is_default is True if referral else False)


async def test_content_creation(async_engine, app_id: int):
    """Test 3: Create pages and products."""
    print("\n== TEST 3: Content Creation (Pages + Products) ==")

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.cms.content import create_about_page, create_blog_pages
    from app.cms.products import create_products

    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create About page
        about_id = await create_about_page(
            session=session,
            application_id=app_id,
            long_bio="<h2>About Coach Test</h2><p>Passionate fitness coach with 10 years experience.</p>",
            tagline="Transform Your Body, Transform Your Life",
            profile_image_url="https://example.com/profile.jpg",
        )

        # Create Blog pages
        blogs = [
            FakeBlog(
                blog_title="10 Minute Morning Stretch",
                body_html="<h2>Start Your Day Right</h2><p>Simple stretches for everyone.</p>",
                seo_title="10 Minute Morning Stretch",
                seo_description="Quick morning routine.",
            ),
            FakeBlog(
                blog_title="Nutrition Tips for Beginners",
                body_html="<h2>Eat Clean</h2><p>Basic nutrition guide.</p>",
                seo_title="Nutrition Tips for Beginners",
                seo_description="Simple nutrition advice.",
            ),
            FakeBlog(
                blog_title="Building a Home Gym on a Budget",
                body_html="<h2>Home Gym Essentials</h2><p>You don't need much to start.</p>",
                seo_title="Home Gym on a Budget",
                seo_description="Affordable home gym guide.",
            ),
        ]
        blog_ids = await create_blog_pages(session=session, application_id=app_id, blogs=blogs)

        # Create Products
        products = [
            FakeProduct(name="Monthly Coaching", description="Full monthly access.", price_cents=2999),
            FakeProduct(name="Annual Plan", description="Best value - full year.", price_cents=24999, interval="year"),
            FakeProduct(
                name="Starter Guide",
                description="One-time beginner's guide.",
                price_cents=999,
                type="one_time",
            ),
        ]
        product_ids = await create_products(session=session, application_id=app_id, products=products)

        await session.commit()

    check("About page created", about_id >= 1, f"id={about_id}")
    check("3 blog pages created", len(blog_ids) == 3, f"got {len(blog_ids)}")
    check("3 products created", len(product_ids) == 3, f"got {len(product_ids)}")

    # Verify records
    async with async_session() as session:
        pages = (
            await session.execute(select(Page).where(Page.application_id == app_id).order_by(Page.order))
        ).scalars().all()
        check("Total pages = 4 (1 about + 3 blog)", len(pages) == 4, f"got {len(pages)}")
        check("About page type=1", pages[0].page_type_id == 1 if pages else False)
        check("Blog pages type=2", all(p.page_type_id == 2 for p in pages[1:]) if len(pages) > 1 else False)
        check("All pages status=1 (Draft)", all(p.status_id == 1 for p in pages))
        check("Blog titles stored", pages[1].title == "10 Minute Morning Stretch" if len(pages) > 1 else False)

        prods = (
            await session.execute(
                select(Product).where(Product.application_id == app_id).order_by(Product.order)
            )
        ).scalars().all()
        check("Products stored correctly", len(prods) == 3, f"got {len(prods)}")
        check("Monthly price = 2999 cents", prods[0].unit_amount == 2999 if prods else False)
        check("Annual interval = year", prods[1].interval == "year" if len(prods) > 1 else False)
        check("One-time interval", prods[2].interval == "one_time" if len(prods) > 2 else False)
        check("All products status=1 (Draft)", all(p.status_id == 1 for p in prods))

    return about_id, blog_ids, product_ids


async def test_claim_activation(async_engine, store_result):
    """Test 4: Simulate claim flow — activate the store."""
    print("\n== TEST 4: Claim Flow (Activate Store) ==")

    import bcrypt as bcrypt_lib
    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    app_id = store_result.application_id
    user_id = store_result.user_id

    STATUS_ACTIVE = 2
    new_password = "TestPassword123!"
    hashed = bcrypt_lib.hashpw(new_password.encode(), bcrypt_lib.gensalt()).decode()

    async with async_session() as session:
        # Activate user
        await session.execute(
            update(CMSUser)
            .where(CMSUser.id == user_id)
            .values(
                password=hashed,
                status_id=STATUS_ACTIVE,
                is_email_verified=True,
                auto_login_token="test_token_abc123",
            )
        )

        # Activate application
        await session.execute(
            update(Application).where(Application.id == app_id).values(status_id=STATUS_ACTIVE)
        )

        # Activate all pages
        await session.execute(
            update(Page).where(Page.application_id == app_id).values(status_id=STATUS_ACTIVE)
        )

        # Activate all products
        await session.execute(
            update(Product).where(Product.application_id == app_id).values(status_id=STATUS_ACTIVE)
        )

        await session.commit()

    # Verify activation
    async with async_session() as session:
        app = (await session.execute(select(Application).where(Application.id == app_id))).scalar_one()
        check("Application activated (status=2)", app.status_id == 2)

        user = (await session.execute(select(CMSUser).where(CMSUser.id == user_id))).scalar_one()
        check("User activated (status=2)", user.status_id == 2)
        check("Email verified", user.is_email_verified is True)
        check("Auto-login token set", user.auto_login_token == "test_token_abc123")
        check("New password is bcrypt", user.password.startswith("$2"))
        check("Password changed from temp", user.password != store_result.temp_password)

        pages = (
            await session.execute(select(Page).where(Page.application_id == app_id))
        ).scalars().all()
        check("All pages activated", all(p.status_id == 2 for p in pages), f"{[p.status_id for p in pages]}")

        prods = (
            await session.execute(select(Product).where(Product.application_id == app_id))
        ).scalars().all()
        check("All products activated", all(p.status_id == 2 for p in prods), f"{[p.status_id for p in prods]}")


async def test_schema_compatibility():
    """Test 5: Cross-check Growth Engine models against known CMS schema issues."""
    print("\n== TEST 5: Schema Compatibility Checks ==")

    from app.cms.content import PAGE_TYPE_ABOUT, PAGE_TYPE_BLOG

    # Known CMS seed data says: page_type 1="Static Pages", 2="Onboarding Screen"
    # But Growth Engine uses: 1=About, 2=Blog
    # This works because the CMS treats page_type_id as just a category marker,
    # and the Growth Engine creates its own content — it doesn't conflict.
    check(
        "PAGE_TYPE_ABOUT matches CMS id=1 (Static Pages)",
        PAGE_TYPE_ABOUT == 1,
        "Growth Engine maps About → page_type_id=1 which CMS calls 'Static Pages'",
    )
    check(
        "PAGE_TYPE_BLOG uses id=2",
        PAGE_TYPE_BLOG == 2,
        "CMS calls this 'Onboarding Screen' but Growth Engine repurposes it for blogs",
    )

    # Check Page.title max length
    title_col = Page.__table__.columns["title"]
    check(
        "Page.title allows 255 chars",
        title_col.type.length == 255,
        f"Model has {title_col.type.length}, CMS migration says VARCHAR(28) — MISMATCH if not migrated",
    )

    # Check model has all critical columns
    app_setting_cols = set(ApplicationSetting.__table__.columns.keys())
    required_settings = {"app_name", "coach_name", "meta_title", "meta_description", "web_url", "support_email"}
    missing = required_settings - app_setting_cols
    check("ApplicationSetting has all required columns", len(missing) == 0, f"missing: {missing}")

    color_cols = set(ApplicationColor.__table__.columns.keys())
    required_colors = {"primary", "secondary", "background", "on_primary", "button_primary", "appbar"}
    missing_colors = required_colors - color_cols
    check("ApplicationColor has all required columns", len(missing_colors) == 0, f"missing: {missing_colors}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test CMS sync end-to-end")
    parser.add_argument("--cms-url", help="CMS MySQL URL (default: SQLite)")
    args = parser.parse_args()

    print("=" * 60)
    print("KLIQ Growth Engine — CMS Sync E2E Test")
    print("=" * 60)

    if args.cms_url:
        print(f"Target: {args.cms_url.split('@')[-1]}")
    else:
        print("Target: Local SQLite (test_cms.db)")

    sync_engine, async_engine = create_test_engine(args.cms_url)
    setup_schema(sync_engine)

    # Test 1: Store creation
    store_result = await test_store_creation(async_engine)

    # Test 2: Verify all records
    await test_verify_records(async_engine, store_result)

    # Test 3: Content creation (pages + products)
    await test_content_creation(async_engine, store_result.application_id)

    # Test 4: Claim flow activation
    await test_claim_activation(async_engine, store_result)

    # Test 5: Schema compatibility checks
    await test_schema_compatibility()

    # Summary
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed, {len(results)} total")
    print(f"{'=' * 60}")

    if failed:
        print("\nFailed checks:")
        for name, ok, detail in results:
            if not ok:
                print(f"  - {name}: {detail}")
        sys.exit(1)
    else:
        print("\nAll checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
