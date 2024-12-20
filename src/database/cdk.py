from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import Config
from src.database import create_database


class CdkDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class CdkModel(CdkDatabaseModel):
    """cdk"""
    __tablename__ = 'cdk'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    cdk: Mapped[str] = mapped_column(index=True, nullable=False)  # cdk
    limit: Mapped[int] = mapped_column(default=1)  # 使用次数
    expired_time: Mapped[int] = mapped_column(nullable=True)  # 过期时间
    used_history: Mapped[str] = mapped_column(nullable=True)  # 使用历史 可能考虑往里面塞一个json
    other: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


create_database("cdk", CdkDatabaseModel)
DATABASE_URL = f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "cdk.db"}'
ENGINE = create_async_engine(DATABASE_URL, echo=Config.SQLALCHEMY_LOG)
CdkSessionFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)
