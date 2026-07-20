import os
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine


def _load_database_url() -> str:
    """从环境变量或项目根目录的 .env 文件读取数据库连接串。"""
    configured_url = os.getenv("ASYNC_DATABASE_URL")
    if configured_url:
        return configured_url

    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "ASYNC_DATABASE_URL":
                return value.strip().strip("\"'")

    raise RuntimeError(
        "未配置数据库连接：请设置 ASYNC_DATABASE_URL 环境变量，"
        "或将 .env.example 复制为 .env 后填写本地数据库信息。"
    )


ASYNC_DATABASE_URL = _load_database_url()

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo = True,            # 可选：输出SQL日志
    pool_size = 10,         # 设置连接池中保持的持久连接数
    max_overflow = 20       # 设置连接池允许创建的额外连接数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine,
    class_ = AsyncSession,
    expire_on_commit = False
)

# 依赖项，用于获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
