from datetime import datetime, timezone
from typing import Optional

import pytz


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
        return time_data
