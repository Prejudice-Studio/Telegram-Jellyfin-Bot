from src.config import JellyfinConfig
from src.jellyfin.api import JellyfinAPI

client = JellyfinAPI(JellyfinConfig.BASE_URL, 1, JellyfinConfig.API_KEY)


class ConnectError(Exception):
    pass


async def check_server_connectivity() -> bool:
    """
    检查服务器连接性
    :return: bool
    """
    try:
        info = await client.System.info()
        if info.status_code == 200:
            return True
        else:
            return False
    except ConnectError:
        return False
