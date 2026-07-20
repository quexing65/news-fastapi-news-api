from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="更新时间"
    )


class Category(Base):
    __tablename__ = "news_category"

    id: Mapped[int] = mapped_column(
        Integer,                # 数据类型
        primary_key=True,       # 主键
        autoincrement=True,     # 自增
        comment="分类ID"
    )
    name: Mapped[str] = mapped_column(
        String(50),                 # 数据类型
        unique=True,                # 唯一
        nullable=False,             # 唯一 ，不能为空
        comment="分类名称"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,                # 数据类型
        default=0,              # 默认值
        nullable=False,         # 不能为空
        comment="排序"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"


# 这是新闻表
class News(Base):
    __tablename__ = "news"

    # 创建索引：提升查询速度 → 添加目录
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),  # 高频查询场景
        Index('idx_publish_time', 'publish_time')  # 按发布时间排序
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="新闻简介")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="封面图片URL")
    author: Mapped[Optional[str]] = mapped_column(String(50), comment="作者")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'), nullable=False, comment="分类ID")
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览量")
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")

    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', views={self.views})>"

