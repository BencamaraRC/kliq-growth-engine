from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Growth Engine PostgreSQL
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug and settings.app_env == "development",
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_recycle=1800,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# RCWL-CMS MySQL (for direct store population)
cms_engine = create_async_engine(
    settings.cms_database_url,
    echo=settings.app_debug and settings.app_env == "development",
    pool_size=5,
    pool_recycle=1800,
)
cms_session = async_sessionmaker(cms_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_cms_db() -> AsyncSession:
    async with cms_session() as session:
        yield session
