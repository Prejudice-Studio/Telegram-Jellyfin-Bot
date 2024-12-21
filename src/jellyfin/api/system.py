from httpx import Response

from src.jellyfin.api import JellyfinRequest


class System():
    def __init__(self, client: JellyfinRequest):
        self.client = client
    
    async def info(self) -> dict:
        """
        获取系统信息
        :return:
        """
        return await self.client.get("System/Info/Public")
