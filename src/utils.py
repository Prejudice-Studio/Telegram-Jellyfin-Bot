import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

import pytz

from src.config import Config


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
