from typing import Optional

from src.jellyfin.api import JellyfinRequest


class Users:
    def __init__(self, client: JellyfinRequest):
        self.client = client
    
    async def get_user(self, user_id: Optional[str] = None):
        """
        获取用户信息
        :param user_id: 用户Id
        :return:
        """
        user_id = user_id or self.client.user_id
        if not user_id:
            raise ValueError("未提供用户ID")
        user_url = f'/Users/{user_id}'
        return await self.client.get(user_url)
    
    async def get_users(self):
        """
        获取所有用户
        :return:
        """
        return await self.client.get("Users")
    
