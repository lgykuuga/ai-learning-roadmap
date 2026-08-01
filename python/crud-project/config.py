"""
config.py — 数据库连接配置
============================
异步引擎连接 SQLite（本地文件数据库，不需要装任何东西）
想切 PostgreSQL 时只需改下面两行 URL
"""
import os

# SQLite（默认） — 文件数据库，零配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./roadmap.db",
)

# 切 PostgreSQL 时取消下面注释，注释掉上面：
# DATABASE_URL = "postgresql+asyncpg://roadmap:roadmap123@localhost:5432/roadmap"

# 同步 URL（seed/create_all 用）
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
