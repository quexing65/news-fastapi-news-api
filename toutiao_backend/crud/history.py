from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History


# 检查浏览历史
async def check_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    # 是否有浏览记录
    return result.scalar_one_or_none()


# 添加历史记录
async def add_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    history = History(user_id=user_id, news_id=news_id)
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history
