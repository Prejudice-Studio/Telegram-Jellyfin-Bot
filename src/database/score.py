from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import Config
from src.database import create_database


class ScoreDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class ScoreModel(ScoreDatabaseModel):
    """积分"""
    __tablename__ = 'score'
    telegram_id: Mapped[int] = mapped_column(primary_key=True, index=True)  # Telegram ID
    score: Mapped[int] = mapped_column(default=0)  # 积分
    checkin_time: Mapped[int] = mapped_column(nullable=True)  # 签到时间
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


class RedPacketModel(ScoreDatabaseModel):
    """红包"""
    __tablename__ = 'red_packet'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    telegram_id: Mapped[int] = mapped_column(index=True)  # Telegram ID 发出红包者
    amount: Mapped[int] = mapped_column(nullable=False)  # 红包金额
    status: Mapped[int] = mapped_column(default=0)  # 状态 0 未领取 1 已领完
    type: Mapped[int] = mapped_column(default=0)  # 类型 0 普通红包 1 拼手气红包
    create_time: Mapped[int] = mapped_column(nullable=True)  # 创建时间
    expired_time: Mapped[int] = mapped_column(nullable=True)  # 过期时间
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


create_database("score", ScoreDatabaseModel)
DATABASE_URL = f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "score.db"}'
ENGINE = create_async_engine(DATABASE_URL, echo=Config.SQLALCHEMY_LOG)
ScoreSessionFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)
