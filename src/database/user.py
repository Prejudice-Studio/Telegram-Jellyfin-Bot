from enum import Enum

from sqlalchemy import delete, select, update, String, Boolean, insert
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import Config, EmbyConfig
from src.database import create_database
from src.emby.api.user import Users

class UsersDatabaseModel(AsyncAttrs, DeclarativeBase):
    pass


class Role(Enum):
    """角色(权限)"""
    BANNED = 0
    SEA = 1
    ADMIN = 2
    ORDINARY = 3
    STAR = 4


class UserModel(UsersDatabaseModel):
    """用户"""
    __tablename__ = 'user'
    telegram_id: Mapped[int] = mapped_column(primary_key=True, index=True)  # Telegram ID
    username: Mapped[str] = mapped_column(nullable=True)  # 用户名
    fullname: Mapped[str] = mapped_column(nullable=True)  # TG 全名
    role: Mapped[int] = mapped_column(default=Role.SEA.value)
    config: Mapped[str] = mapped_column(nullable=True)  # 用户配置 后期预留，可能塞json进去
    account: Mapped[str] = mapped_column(nullable=True)  # 账户
    password: Mapped[str] = mapped_column(nullable=True)  # 密码 hash
    bind_id: Mapped[str] = mapped_column(nullable=True)  # 绑定的Emby账户ID
    data: Mapped[str] = mapped_column(nullable=True)  # 预留的其他配置


class EmbyUserModel(UsersDatabaseModel):
    __tablename__ = 'emby_user'
    embyusername: Mapped[str] = mapped_column(String, primary_key=True, index=True)  # Emby用户名
    Enabled: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否启用
    Id: Mapped[str] = mapped_column(String, unique=True, index=True , nullable=True)  # Emby用户ID
    LastLoginDate: Mapped[str] = mapped_column(String, nullable=True)  # 最后登录时间
    LastActivityDate: Mapped[str] = mapped_column(String, nullable=True)  # 最后活动时间
    IsAdministrator: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否管理员


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
    
    @staticmethod
    async def delete(telegram_id: int):
        """
        删除用户
        :param telegram_id: Telegram ID
        """
        async with UsersSessionFactory() as session:
            async with session.begin():
                await session.execute(delete(UserModel).filter_by(telegram_id=telegram_id))
    
    @staticmethod
    async def get_emby_user_count() -> int:
        """
        获取Emby用户数量
        :return: Emby用户数量
        """
        async with UsersSessionFactory() as session:
            async with session.begin():
                scalar = await session.execute(select(EmbyUserModel).count())
                return scalar.scalar_one()
            
    @staticmethod
    async def sync_emby_user():
        """
        从Emby同步用户
        """
        async with UsersSessionFactory() as session:
            async with session.begin():
                try:
                    embyapi = Users()
                    allusersinfo = await embyapi.get_users()
                    emby_usernames = {userinfo['Name'] for userinfo in allusersinfo}

                    # 更新或插入 Emby 用户
                    for userinfo in allusersinfo:
                        embyusername = userinfo['Name']
                        embyuserid = userinfo['Id']
                        last_login_date = userinfo.get('LastLoginDate')
                        last_activity_date = userinfo.get('LastActivityDate')
                        is_administrator = userinfo['Policy']['IsAdministrator']

                        embyuser = await session.execute(select(EmbyUserModel).filter_by(embyusername=embyusername).limit(1))
                        embyuser = embyuser.scalar_one_or_none()
                        if embyuser:
                            await session.execute(update(EmbyUserModel).filter_by(embyusername=embyusername).
                                                  values(Id=embyuserid,
                                                         LastLoginDate=last_login_date,
                                                         LastActivityDate=last_activity_date,
                                                         IsAdministrator=is_administrator))
                        else:
                            await session.execute(insert(EmbyUserModel).values(embyusername=embyusername,
                                                                             Id=embyuserid,
                                                                             LastLoginDate=last_login_date,
                                                                             LastActivityDate=last_activity_date,
                                                                             IsAdministrator=is_administrator))

                    # 删除数据库中不存在于 Emby 的用户
                    existing_emby_usernames = {embyuser['embyusername'] for embyuser in await session.execute(select(EmbyUserModel.embyusername))}
                    for embyusername in existing_emby_usernames - emby_usernames:
                        await session.execute(delete(EmbyUserModel).filter_by(embyusername=embyusername))
                except Exception as e:
                    print(f"Error syncing Emby users: {e}")
                    # 在这里可以添加更详细的日志记录或其他错误处理逻辑

    @staticmethod
    async def add_Emby_database_user(emby_username: str):
        """
        添加Emby用户到数据库
        :param emby_username: Emby用户名
        """
        async with UsersSessionFactory() as session:
                await session.execute(insert(EmbyUserModel).values(embyusername=emby_username,
                                                                  Id=None,
                                                                  LastLoginDate=None,
                                                                  LastActivityDate=None,
                                                                  IsAdministrator=False))