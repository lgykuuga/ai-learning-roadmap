"""
config.py — 数据库连接配置
============================
异步引擎连接 SQLite（本地文件数据库，不需要装任何东西）
想切 PostgreSQL 时只需改下面两行 URL
"""
# 导入标准库 os，用来读取操作系统环境变量。
import os

# SQLite（默认） — 文件数据库，零配置
# os.getenv 会优先读取名为 DATABASE_URL 的环境变量，没有配置时再使用第二个参数。
DATABASE_URL = os.getenv(
    # 第一个参数是环境变量名称。
    "DATABASE_URL",
    # 第二个参数是默认值：使用 aiosqlite 驱动访问当前目录的 roadmap.db。
    "sqlite+aiosqlite:///./roadmap.db",
)

# 切 PostgreSQL 时取消下面注释，注释掉上面：
# DATABASE_URL = "postgresql+asyncpg://roadmap:roadmap123@localhost:5432/roadmap"

# 同步 URL（seed/create_all 用）
# 连续调用 replace，把异步驱动名替换为同步驱动名，得到 seed 脚本需要的连接地址。
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
