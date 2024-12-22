from sqlalchemy import select, update
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
    checkin_time: Mapped[int] = mapped_column(default=0)  # 签到时间
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


class RedPacketModel(ScoreDatabaseModel):
    """红包"""
    __tablename__ = 'red_packet'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    telegram_id: Mapped[int] = mapped_column(index=True)  # Telegram ID 发出红包者
    amount: Mapped[int] = mapped_column(nullable=False)  # 红包金额
    count: Mapped[int] = mapped_column(nullable=False)  # 红包个数
    current_amount: Mapped[int] = mapped_column(nullable=False)  # 当前剩余金额
    status: Mapped[int] = mapped_column(default=0)  # 状态 0 未领取 1 已领完 2 已经撤回
    type: Mapped[int] = mapped_column(default=0)  # 类型 0 随机红包 1 均分
    history: Mapped[str] = mapped_column(default="")  # 领取历史
    create_time: Mapped[int] = mapped_column(nullable=True)  # 创建时间
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


create_database("score", ScoreDatabaseModel)
DATABASE_URL = f'sqlite+aiosqlite:///{Config.DATABASES_DIR / "score.db"}'
ENGINE = create_async_engine(DATABASE_URL, echo=Config.SQLALCHEMY_LOG)
ScoreSessionFactory = async_sessionmaker(bind=ENGINE, expire_on_commit=False)


class ScoreOperate:
    @staticmethod
    async def add_score(score_data: ScoreModel) -> ScoreModel:
        """
        添加积分到数据库
        :param score_data: 积分数据
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                session.add(score_data)
        return score_data
    
    @staticmethod
    async def get_score(telegram_id: int) -> ScoreModel | None:
        """
        获取积分
        :param telegram_id: Telegram ID
        :return: 积分
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                scalar = await session.execute(select(ScoreModel).filter(ScoreModel.telegram_id == telegram_id).limit(1))
                return scalar.scalar_one_or_none()
    
    @staticmethod
    async def change_score(telegram_id: int, change_score: int) -> None:
        """
        更新积分
        :param telegram_id: Telegram ID
        :param change_score: 待变化的积分
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                await session.execute(update(ScoreModel).filter(ScoreModel.telegram_id == telegram_id).values(
                        score=ScoreModel.score + change_score))
    
    @staticmethod
    async def update_score(score_data: ScoreModel):
        """
        更新积分数据
        :param score_data: 积分数据
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                await session.merge(score_data)
    
    @staticmethod
    async def add_red_packet(red_packet_data: RedPacketModel):
        """
        添加红包到数据库
        :param red_packet_data: 红包数据
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                session.add(red_packet_data)
            
    @staticmethod
    async def get_red_packet(red_packet_id: int) -> RedPacketModel | None:
        """
        获取红包信息
        :param red_packet_id: 红包 ID
        :return: 红包
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                scalar = await session.execute(select(RedPacketModel).filter(RedPacketModel.id == red_packet_id).limit(1))
                return scalar.scalar_one_or_none()
            
    @staticmethod
    async def update_red_packet(red_packet_data: RedPacketModel):
        """
        更新红包数据
        :param red_packet_data: 红包数据
        """
        async with ScoreSessionFactory() as session:
            async with session.begin():
                await session.merge(red_packet_data)
                