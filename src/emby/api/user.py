from typing import Optional

from src.emby.api import EmbyRequest
from src.emby.api.req import bool_response, json_response


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
    def __init__(self, client: EmbyRequest):
        self.client = client
    
    @json_response
    async def get_user(self, user_id: Optional[str] = "{UserID}"):
        """
        获取用户信息
        :param user_id: 用户Id
        :return:
        """
        return await self.client.get(f'Users/{user_id}')
    
    @json_response
    async def get_users(self):
        """
        获取所有用户
        :return:
        """
        return await self.client.get("Users")
    
    @json_response
    async def get_public_users(self):
        return await self.client.get("Users/Public")
    
    @json_response
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
    
    @bool_response
    async def delete_user(self, user_id: Optional[str] = "{UserID}"):
        """
        删除用户
        :param user_id: 用户ID
        :return: bool
        """
        return await self.client.delete(f'Users/{user_id}')
    
    @json_response
    async def get_user_views(self, user_id: Optional[str] = "{UserID}"):
        """
        获取用户视图
        :param user_id:
        :return:
        """
        return await self.client.get(f'Users/{user_id}/Views')
    
    @json_response
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
    
    @json_response
    async def new_user(self, name: str):
        """
        创建新用户
        :param name:
        :return:
        """
        return await self.client.post("Users/New", json={
            "Name": name,
        })
    
    @json_response
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
    
    @json_response
    async def get_items(self, item_ids: list, user_id: Optional[str] = "{UserID}"):
        return await self.client.get(f"Users/{user_id}/Items", params={
            'Ids': ','.join(str(x) for x in item_ids),
            'Fields': info()
        })
    
    # noinspection PyUnusedLocal
    @bool_response
    async def change_password(self, new_pw: str = "", user_id: Optional[str] = "{UserID}"):
        """
        重置密码
        :param new_pw:
        :param user_id:
        :return:
        """
        if new_pw == "":
            return await self.client.post(f'Users/{user_id}/Password', json={"resetPassword": True})
        return await self.client.post(f'Users/{user_id}/Password', json={
            "NewPw": new_pw
        })
