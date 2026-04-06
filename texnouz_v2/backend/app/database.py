from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.local_dsn,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Barcha jadvallarni yaratish (alembic o'rniga tez ishga tushirish uchun)"""
    async with engine.begin() as conn:
        from app.models import base  # noqa — all models import qilinadi
        await conn.run_sync(Base.metadata.create_all)
