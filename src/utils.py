import base64
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import pytz
from sqlalchemy import or_, select

from src.config import Config
from src.database.user import UserModel, UsersOperate, UsersSessionFactory
from src.jellyfin_client import client


def convert_to_china_timezone(time_data: Optional[int | str] = None) -> str:
    try:
        if not time_data or time_data == "N/A":
            return "N/A"  # 或其他默认值
        if isinstance(time_data, (int, float)):
            utc_time = datetime.fromtimestamp(time_data, tz=timezone.utc)
        elif isinstance(time_data, str):
            utc_time = datetime.fromisoformat(time_data.replace("Z", "+00:00"))
        else:
            utc_time = datetime.now().astimezone(timezone.utc)
        
        china_timezone = pytz.timezone('Asia/Shanghai')
        china_time = utc_time.astimezone(china_timezone)
        return china_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logging.error(f"convert_to_china_timezone error: {e}")
        return time_data


def get_password_hash(password: str) -> str:
    sha256_hash = hashlib.sha256()
    pw_string = password + Config.SALT
    sha256_hash.update(pw_string.encode('utf-8'))
    return sha256_hash.hexdigest()


def is_password_strong(password):
    """
    判断密码是否过于简单
    :param password: 待判断的密码
    :return: 如果密码复杂，返回 True；否则返回 False
    """
    # 密码长度至少8个字符
    if len(password) < 8:
        return False
    # 至少包含一个小写字母
    if not re.search(r'[a-z]', password):
        return False
    # 至少包含一个大写字母
    if not re.search(r'[A-Z]', password):
        return False
    return True


async def get_user_info(username: str | int) -> tuple[dict | None, UserModel | None]:
    """
    获取 Jellyfin 用户信息
    :param username: Telegram ID/Fullname or Jellyfin username
    :return:
    """
    je_id = None
    
    async def fetch_user_id(f_username: str):
        async with UsersSessionFactory() as f_session:
            scalars = await f_session.execute(select(UserModel).filter(
                    or_(
                            UserModel.fullname.like(f"%{f_username}%"),
                            UserModel.username.like(f"%{f_username}%")
                    )
            ).limit(1))
            logging.info(f"fetch_user_id: {scalars}")
            return scalars.scalar_one_or_none()
    
    if username.isdigit():
        user_info = await UsersOperate.get_user(int(username))
        je_id = user_info.bind_id if user_info else None
    else:
        user_info = await fetch_user_id(username)
        if user_info:
            je_id = user_info.bind_id
    if not je_id:
        try:
            all_user = await client.Users.get_users()
            je_data = next((u for u in all_user if u["Name"] == username), None)
            je_id = je_data["Id"] if je_data else None
        except Exception as e:
            logging.error(f"Error: {e}")
            return None, None
    if je_id is not None:
        try:
            jellyfin_user = await client.Users.get_user(je_id)
            async with UsersSessionFactory() as session:
                user_scalars = await session.execute(select(UserModel).filter_by(bind_id=je_id).limit(1))
                user_info = user_scalars.scalar_one_or_none()
            return jellyfin_user, user_info
        except Exception as e:
            logging.error(f"Error: {e}")
    if user_info:
        return None, user_info
    return None, None


def base64_encode(ori_str: str) -> str:
    return base64.b64encode(ori_str.encode('utf-8')).decode('utf-8')


def base64_decode(encode_str: str) -> str:
    return base64.b64decode(encode_str.encode('utf-8')).decode('utf-8')
