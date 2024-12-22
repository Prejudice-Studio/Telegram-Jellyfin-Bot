from httpx import Response

from src.jellyfin.api import JellyfinRequest
from src.jellyfin.api.req import json_response


class System:
    def __init__(self, client: JellyfinRequest):
        self.client = client
    
    @json_response
    async def info(self):
        """
        获取系统信息
        :return:
        """
        return await self.client.get("System/Info/Public")
