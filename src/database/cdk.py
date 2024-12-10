from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CdkDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class CDK(CdkDatabaseModel):
    """cdk"""
    __tablename__ = 'cdk'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    cdk: Mapped[str] = mapped_column(index=True)  # cdk
    limit: Mapped[int] = mapped_column()  # 使用次数
    expired_time: Mapped[int] = mapped_column()  # 过期时间
    used_history: Mapped[str] = mapped_column()  # 使用历史 可能考虑往里面塞一个json
