from enum import Enum
from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import Config
from src.database import create_database


class ReqStatue(Enum):
    """请求状态"""
    UNHANDLED = 0
    ACCEPTED = 1
    REJECTED = 2
    COMPLETED = 3


class BangumiDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class BangumiUserModel(BangumiDatabaseModel):
    """用户"""
    __tablename__ = 'user'
    telegram_id: Mapped[int] = mapped_column(primary_key=True, index=True)  # Telegram ID
    access_token: Mapped[str] = mapped_column(nullable=True)  # 访问令牌
    auto_update: Mapped[bool] = mapped_column(default=True)  # 自动更新（每天自动同步看完的番剧）
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


class BangumiRequireModel(BangumiDatabaseModel):
    """番剧请求"""
    __tablename__ = 'require'
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)  # 请求ID
    telegram_id: Mapped[int] = mapped_column(index=True)  # 发起者Telegram ID
    bangumi_id: Mapped[int] = mapped_column(index=True)  # 番剧ID
    status: Mapped[int] = mapped_column(default=ReqStatue.UNHANDLED.value)  # 请求状态
    timestamp: Mapped[int] = mapped_column()  # 发起时间戳


create_database("bangumi", BangumiDatabaseModel)
DATABASE_URL = f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "bangumi.db"}'
ENGINE = create_async_engine(DATABASE_URL, echo=Config.SQLALCHEMY_LOG)
BangumiSessionFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)


class BangumiOperate:
    @staticmethod
    async def add_req_bgm(data: BangumiRequireModel):
        async with BangumiSessionFactory() as session:
            async with session.begin():
                session.add(data)
    
    @staticmethod
    async def get_req_bgm(req_id: int):
        async with BangumiSessionFactory() as session:
            async with session.begin():
                scalar = await session.execute(select(BangumiRequireModel).filter(BangumiRequireModel.id == req_id).limit(1))
                return scalar.scalar_one_or_none()
    
    @staticmethod
    async def update_req_bgm(data: BangumiRequireModel):
        async with BangumiSessionFactory() as session:
            async with session.begin():
                await session.merge(data)
                