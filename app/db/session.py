from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Growth Engine PostgreSQL
engine = create_async_engine(settings.database_url, echo=settings.app_debug, pool_size=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# RCWL-CMS MySQL (for direct store population)
cms_engine = create_async_engine(settings.cms_database_url, echo=settings.app_debug, pool_size=5)
cms_session = async_sessionmaker(cms_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_cms_db() -> AsyncSession:
    async with cms_session() as session:
        yield session
