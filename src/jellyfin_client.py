from src.bangumi import BangumiAPI
from src.config import Config, JellyfinConfig
from src.jellyfin.api import JellyfinAPI

client = JellyfinAPI(JellyfinConfig.BASE_URL, 1, JellyfinConfig.API_KEY)

ban_client = BangumiAPI(Config.BANGUMI_TOKEN)


# noinspection PyBroadException
async def check_server_connectivity() -> bool:
    """
    检查服务器连接性
    :return: bool
    """
    try:
        info = await client.System.info()
        if info:
            return True
        else:
            return False
    except Exception:
        return False
