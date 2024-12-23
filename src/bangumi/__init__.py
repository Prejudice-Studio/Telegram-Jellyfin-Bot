from src.bangumi.req import BangumiRequest
from src.bangumi.subject import Subject


class BangumiAPI:
    def __init__(self, access_token: str):
        super().__init__()
        self.BangumiReq = BangumiRequest(access_token)
        self.Subject = Subject(self.BangumiReq)
