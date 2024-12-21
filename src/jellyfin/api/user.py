from typing import Optional

from src.jellyfin.api import JellyfinRequest


class Users:
    def __init__(self, client: JellyfinRequest):
        self.client = client
    
    async def get_user(self, user_id: Optional[str] = "{UserID}"):
        """
        获取用户信息
        :param user_id: 用户Id
        :return:
        """
        return await self.client.get(f'Users/{user_id}')
    
    async def get_users(self):
        """
        获取所有用户
        :return:
        """
        return await self.client.get("Users")
    
    async def get_public_users(self):
        return await self.client.get("Users/Public")
    
    async def get_user_settings(self, user_id: Optional[str] = "{UserID}", client="emby"):
        """
        获取用户设置
        :param user_id:
        :param client:
        :return:
        """
        return await self.client.get("DisplayPreferences/usersettings", params={
            "userId": f"{user_id}",
            "client": client
        })
    
    async def delete_user(self, user_id: str):
        """
        删除用户
        :param user_id: 用户ID
        :return:
        """
        user_id = user_id or self.client.user_id
        if not user_id:
            raise ValueError("未提供用户ID")
        return await self.client.delete(f'Users/{user_id}')
    
    async def get_user_views(self, user_id: Optional[str] = None):
        """
        获取用户视图
        :param user_id:
        :return:
        """
        user_id = user_id or self.client.user_id
        if not user_id:
            raise ValueError("未提供用户ID")
        return await self.client.get(f'Users/{user_id}/Views')
    
    async def get_user_media_folders(self, user_id: Optional[str] = None, fields=None):
        """
        获取用户媒体文件夹
        :param user_id:
        :param fields:
        :return:
        """
        user_id = user_id or self.client.user_id
        if not user_id:
            raise ValueError("未提供用户ID")
        return await self.client.get(f'Users/{user_id}/Items', params={
            "fields": fields
        })
    
    async def new_user(self, name, password):
        return self.client.post("Users/New", {
            "name": name,
            "Password": password
        })
