import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

# 加载 .env 文件（toutiao_backend/.env，已被 .gitignore 忽略，不会提交到仓库）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 数据库连接配置：优先从环境变量读取（生产环境推荐注入），未配置时回退本地默认值
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "mysql+aiomysql://root@localhost:3306/news_app?charset=utf8mb4",
)

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 可选：输出SQL日志
    pool_size=10,  # 设置连接池中保持的持久连接数
    max_overflow=20  # 设置连接池允许创建的额外连接数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
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
