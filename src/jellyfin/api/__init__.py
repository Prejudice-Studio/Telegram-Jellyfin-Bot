from typing import Optional

from src.jellyfin.api.req import JellyfinRequest
from src.jellyfin.api.user import Users


class Jellyfin:
    def __init__(self, url: str, auth: int, api_key: Optional[str] = None):
        super().__init__()
        self.JellyfinReq = JellyfinRequest(url, auth, api_key)
        self.Users = Users(self.JellyfinReq)
        
