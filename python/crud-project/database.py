"""
database.py — 异步 + 同步双引擎
=================================
注意点 1: 异步引擎用于 FastAPI handler，同步引擎用于 seed 脚本和 create_all
注意点 2: async_sessionmaker 是 SQLAlchemy 2.0 的方式
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL, SYNC_DATABASE_URL

# 异步引擎 — 生产/API用
async_engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 同步引擎 — seed/create_all 用
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# 声明式基类
Base = declarative_base()


async def get_db():
    """异步 session 依赖注入"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
