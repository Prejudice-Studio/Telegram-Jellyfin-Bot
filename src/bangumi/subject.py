from src.bangumi.req import BangumiRequest, json_response


class Subject:
    
    def __init__(self, client: BangumiRequest):
        self.client = client
    
    @json_response
    async def search(self, keyword: str, s_type: int = 2, responseGroup="small", start: int = 0, max_results: int = 8):
        """
        获取系统信息
        :return:
        """
        return await self.client.get(f"search/subject/{keyword}", params={
            "type": s_type, "responseGroup": responseGroup, "start": start, "max_results": max_results})
