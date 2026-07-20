from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News
from models.history import History



# 检查收藏状态: 当前用户 是否 收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 是否有收藏记录
    return result.scalar_one_or_none() is not None


# 添加收藏
async def add_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    """
    添加新闻收藏
    将指定用户和新闻的收藏关系保存到数据库

    :param db: 异步数据库会话对象
    :param user_id: 用户ID，表示收藏者
    :param news_id: 新闻ID，表示被收藏的新闻
    :return: 保存成功后的Favorite对象（包含数据库生成的id和created_at）
    """
    # 创建收藏对象
    favorite = Favorite(user_id=user_id, news_id=news_id)
    # 添加到数据库会话
    db.add(favorite)
    # 提交事务，将数据持久化到数据库
    await db.commit()
    # 刷新对象，获取数据库自动生成的字段（如id、created_at）
    await db.refresh(favorite)
    # 返回创建成功的收藏对象
    return favorite


async def remove_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


# 获取收藏列表：获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 总量 + 收藏的新闻列表
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取收藏列表 - 联表查询 join() + 收藏时间的排序 + 分页
    # select(查询主体模型类，字段别名).join(联合查询的模型类，联合查询的条件).where().order_by().offset().limit()
    # 别名：Favorite.created_at.label("favorite_time")
    offset = (page - 1) * page_size
    # [
    #     (新闻对象, 收藏时间, 收藏ID)
    # ]
    query = (
        select(
            News,
            Favorite.created_at.label("favorite_time"),
            Favorite.news_id.label("favorite_id")
        )
        .join(Favorite,Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()
    return rows, total


# 清空收藏列表：当前用户的收藏列表
async def remove_all_favorite(
        db: AsyncSession,
        user_id: int,
):
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    # 返回一个删除的数量
    return result.rowcount or 0


# 添加浏览记录
async def add_news_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    """
    添加新闻浏览记录
    将指定用户和新闻的浏览关系保存到数据库

    :param db: 异步数据库会话对象
    :param user_id: 用户ID，表示浏览者
    :param news_id: 新闻ID，表示被浏览的新闻
    :return: 保存成功后的History对象（包含数据库生成的id和created_at）
    """
    # 创建浏览记录对象
    history = History(user_id=user_id, news_id=news_id)
    # 添加到数据库会话
    db.add(history)
    # 提交事务，将数据持久化到数据库
    await db.commit()
    # 刷新对象，获取数据库自动生成的字段（如id、created_at）
    await db.refresh(history)
    # 返回创建成功的浏览记录对象
    return history
