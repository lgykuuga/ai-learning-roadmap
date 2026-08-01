"""
database.py — 异步 + 同步双引擎
=================================
注意点 1: 异步引擎用于 FastAPI handler，同步引擎用于 seed 脚本和 create_all
注意点 2: async_sessionmaker 是 SQLAlchemy 2.0 的方式
"""
# 导入异步引擎、异步 Session 工厂和异步 Session 类型，供 API 请求使用。
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# 导入同步引擎创建函数，供 seed 和建表流程使用。
from sqlalchemy import create_engine
# 导入同步 Session 工厂和 ORM 模型的声明式基类工厂。
from sqlalchemy.orm import sessionmaker, declarative_base
# 从配置模块取得异步、同步两种数据库连接地址。
from config import DATABASE_URL, SYNC_DATABASE_URL

# 异步引擎 — 生产/API用
# create_async_engine 根据异步 URL 创建连接池；pool_size 是常驻连接数，max_overflow 是临时扩容量。
async_engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
# 创建异步 Session 工厂；expire_on_commit=False 让提交后的 ORM 对象仍能读取已有属性。
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 同步引擎 — seed/create_all 用
# 使用同步 URL 创建普通 SQLAlchemy 引擎。
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
# 创建同步 Session 工厂，并关闭自动提交和自动 flush。
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# 声明式基类
# 所有 ORM 模型继承 Base 后，SQLAlchemy 就能收集它们的表结构元数据。
Base = declarative_base()


# async def 定义异步生成器依赖，FastAPI 会在每次请求时调用它。
async def get_db():
    """异步 session 依赖注入"""
    # async with 在进入时创建 Session，离开代码块时自动释放上下文资源。
    async with AsyncSessionLocal() as session:
        # try/finally 保证路由成功或抛异常时都会执行清理逻辑。
        try:
            # yield 把当前 Session 交给 Depends(get_db) 对应的路由参数。
            yield session
        # finally 中的代码无论请求是否成功都会运行。
        finally:
            # 显式关闭 Session，把占用的数据库连接归还连接池。
            await session.close()
