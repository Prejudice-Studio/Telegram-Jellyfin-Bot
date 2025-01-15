from typing import Optional

from src.emby.api.req import EmbyRequest
from src.emby.api.system import System
from src.emby.api.user import Users


class EmbyAPI:
    def __init__(self, url: str, auth: int, api_key: Optional[str] = None):
        super().__init__()
        self.EmbyReq = EmbyRequest(url, auth, api_key)
        self.Users = Users(self.EmbyReq)
        self.System = System(self.EmbyReq)
        
