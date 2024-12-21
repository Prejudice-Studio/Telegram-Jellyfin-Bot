from enum import Enum

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import Config
from src.database import create_database


class UsersDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class Role(Enum):
    """角色(权限)"""
    BANNED = 0
    USER = 1
    ADMIN = 2


class UserModel(UsersDatabaseModel):
    """用户"""
    __tablename__ = 'user'
    telegram_id: Mapped[int] = mapped_column(primary_key=True, index=True)  # Telegram ID
    username: Mapped[str] = mapped_column(nullable=True)  # 用户名
    fullname: Mapped[str] = mapped_column(nullable=True)  # TG 全名
    role: Mapped[int] = mapped_column(default=Role.USER.value)
    config: Mapped[str] = mapped_column(nullable=True)  # 用户配置 后期预留，可能塞json进去
    account: Mapped[str] = mapped_column(nullable=True)  # 账户
    password: Mapped[str] = mapped_column(nullable=True)  # 密码 hash
    bind_id: Mapped[str] = mapped_column(nullable=True)  # 绑定的jellyfin账户ID
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


create_database("users", UsersDatabaseModel)
DATABASE_URL = f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "users.db"}'
ENGINE = create_async_engine(DATABASE_URL, echo=Config.SQLALCHEMY_LOG)
UsersSessionFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)


class UsersOperate:
    @staticmethod
    async def add_user(user_data: UserModel):
        """
        添加用户到数据库
        :param user_data: 用户数据
        """
        async with UsersSessionFactory() as session:
            async with session.begin():
                session.add(user_data)
    
    @staticmethod
    async def get_user(telegram_id: int) -> UserModel | None:
        """
        获取用户
        :param telegram_id: Telegram ID
        :return: 用户
        """
        async with UsersSessionFactory() as session:
            scalar = await session.execute(select(UserModel).filter_by(telegram_id=telegram_id).limit(1))
            return scalar.scalar_one_or_none()
    
    @staticmethod
    async def update_user(user_data: UserModel):
        """
        更新用户数据
        :param user_data: 用户数据
        """
        async with UsersSessionFactory() as session:
            async with session.begin():
                await session.merge(user_data)
    
    @staticmethod
    async def clear_bind(telegram_id: int):
        """
        解绑用户
        :param telegram_id: 用户
        """
        async with UsersSessionFactory() as session:
            async with session.begin():
                await session.execute(update(UserModel).filter_by(telegram_id=telegram_id).
                                      values(account=None, password=None, bind_id=None))
