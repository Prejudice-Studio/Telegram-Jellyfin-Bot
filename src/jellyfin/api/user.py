from typing import Optional

from src.jellyfin.api import JellyfinRequest


def info():
    return (
        "Path,Genres,SortName,Studios,Writer,Taglines,LocalTrailerCount,"
        "OfficialRating,CumulativeRunTimeTicks,ItemCounts,"
        "Metascore,AirTime,DateCreated,People,Overview,"
        "CriticRating,CriticRatingSummary,Etag,ShortOverview,ProductionLocations,"
        "Tags,ProviderIds,ParentId,RemoteTrailers,SpecialEpisodeNumbers,"
        "MediaSources,VoteCount,RecursiveItemCount,PrimaryImageAspectRatio"
    )


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
    
    async def delete_user(self, user_id: Optional[str] = "{UserID}"):
        """
        删除用户
        :param user_id: 用户ID
        :return:
        """
        return await self.client.delete(f'Users/{user_id}')
    
    async def get_user_views(self, user_id: Optional[str] = "{UserID}"):
        """
        获取用户视图
        :param user_id:
        :return:
        """
        return await self.client.get(f'Users/{user_id}/Views')
    
    async def get_user_media_folders(self, user_id: Optional[str] = "{UserID}", fields=None):
        """
        获取用户媒体文件夹
        :param user_id:
        :param fields:
        :return:
        """
        return await self.client.get(f'Users/{user_id}/Items', params={
            "fields": fields
        })
    
    async def new_user(self, name: str, password: str):
        """
        创建新用户
        :param name:
        :param password:
        :return:
        """
        return self.client.post("Users/New", {
            "name": name,
            "Password": password
        })
    
    async def get_item(self, item_id: str, user_id: Optional[str] = "{UserID}"):
        """
        获取项目
        :param user_id:
        :param item_id:
        :return:
        """
        return await self.client.get(f'Users/{user_id}/Items/{item_id}', params={
            'Fields': info()
        })
    
    async def get_items(self, item_ids: list, user_id: Optional[str] = "{UserID}"):
        return self.client.get(f"Users/{user_id}/Items", params={
            'Ids': ','.join(str(x) for x in item_ids),
            'Fields': info()
        })
    
    async def change_password(self, old_pw: str = "", new_pw: str = "", user_id: Optional[str] = "{UserID}"):
        """
        重置密码
        :param old_pw:
        :param new_pw:
        :param user_id:
        :return:
        """
        if new_pw == "":
            return await self.client.post(f'Users/{user_id}/Password', json={"resetPassword": True})
        return await self.client.post(f'Users/{user_id}/Password', json={
            "CurrentPw": old_pw,
            "NewPw": new_pw
        })
