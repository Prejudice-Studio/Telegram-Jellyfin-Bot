from enum import Enum

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SystemDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class Role(Enum):
    """角色(权限)"""
    ADMIN = 1
    USER = 2
    BAN = 3


class User(SystemDatabaseModel):
    """用户"""
    __tablename__ = 'user'
    telegram_id: Mapped[int] = mapped_column(primary_key=True, index=True)  # Telegram ID
    username: Mapped[str] = mapped_column(nullable=True)  # 用户名
    fullname: Mapped[str] = mapped_column(nullable=True)  # TG 全名
    role: Mapped[int] = mapped_column(default=Role.USER.value)
    config: Mapped[str] = mapped_column(nullable=True)  # 用户配置
    account: Mapped[str] = mapped_column(nullable=True)  # 账户
    password: Mapped[str] = mapped_column(nullable=True)  # 密码
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置
