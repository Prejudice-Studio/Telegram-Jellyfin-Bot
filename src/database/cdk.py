from sqlalchemy import delete, select
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


class CdkOperate:
    @staticmethod
    async def add_cdk(cdk_data: CdkModel):
        """
        添加cdk到数据库
        :param cdk_data: cdk数据
        """
        async with CdkSessionFactory() as session:
            async with session.begin():
                session.add(cdk_data)
            await session.commit()
    
    @staticmethod
    async def get_cdk(cdk: str) -> CdkModel | None:
        """
        获取cdk
        :param cdk: cdk
        :return: cdk
        """
        async with CdkSessionFactory() as session:
            async with session.begin():
                scalar = await session.execute(select(CdkModel).filter(CdkModel.cdk == cdk).limit(1))
                return scalar.scalar_one_or_none()
    
    @staticmethod
    async def update_cdk(cdk_data: CdkModel):
        """
        更新cdk
        :param cdk_data: cdk数据
        """
        async with CdkSessionFactory() as session:
            async with session.begin():
                await session.merge(cdk_data)
            await session.commit()
    
    @staticmethod
    async def delete_cdk(cdk: str):
        """
        删除cdk
        :param cdk: cdk
        """
        async with CdkSessionFactory() as session:
            async with session.begin():
                await session.execute(delete(CdkModel).where(CdkModel.cdk == cdk))
            await session.commit()
