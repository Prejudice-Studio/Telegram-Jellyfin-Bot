from src.emby.api import EmbyRequest
from src.emby.api.req import json_response


class System:
    def __init__(self, client: EmbyRequest):
        self.client = client
    
    @json_response
    async def info(self):
        """
        获取系统信息
        :return:
        """
        return await self.client.get("System/Info/Public")
