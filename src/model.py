import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT_PATH: Path = Path(__file__ + '/../..').resolve()


@dataclass
class BaseModel:
    def to_json(self):
        def default(o):
            if isinstance(o, Path):
                return str(o)
            return o.__dict__
        
        return json.dumps(self, default=default, sort_keys=True, indent=4)


# 用户信息结构:
@dataclass
class JellyfinModel(BaseModel):
    username: str
    password: str
    ID: str


@dataclass
class UserModel(BaseModel):
    TelegramID: int
    TelegramFullName: str
    bind: JellyfinModel
    last_sign_in: str = ""
    score: int = 0
    role: int = 0


@dataclass
class UsersModel(BaseModel):
    userList: list[UserModel]
    
    def __init__(self, filename: str = "Users.json"):
        self.filename = ROOT_PATH / "data" / filename
        if not os.path.exists(self.filename):
            self.userList = []
            self.user_dict = {}
            return
        with open(self.filename, "r") as f:
            data = json.load(f)
            data = data["userList"]
            users = []
            for entry in data:
                bind_info = entry.get("bind", {})
                jellyfin_model = JellyfinModel(
                        username=bind_info.get("username", ""),
                        password=bind_info.get("password", ""),
                        ID=bind_info.get("ID", "")
                )
                user_model = UserModel(
                        TelegramID=entry.get("TelegramID", 0),
                        TelegramFullName=entry.get("TelegramFullName", ""),
                        score=entry.get("score", 0),
                        bind=jellyfin_model,
                        role=entry.get("role", 0),
                        last_sign_in=entry.get("last_sign_in", None)
                )
                users.append(user_model)
        
        self.userList = users
        self.user_dict = {user.TelegramID: user for user in self.userList}
    
    def get_user_by_id(self, telegram_id: int) -> Optional[UserModel]:
        return self.user_dict.get(telegram_id)
    
    def save(self):
        with open(self.filename, "w") as f:
            f.write((self.to_json()))
    
    def add_user(self, user: UserModel):
        self.userList.append(user)
        self.user_dict[user.TelegramID] = user  # 更新字典
        self.save()
    
    def remove_user_bind_info(self, user: UserModel):
        user.bind = JellyfinModel(username="", password="", ID="")
        self.save()
    
    def remove_user(self, user: UserModel):
        self.userList.remove(user)
        self.user_dict.pop(user.TelegramID)
        self.save()


# 注册码息结构
@dataclass
class RegCode(BaseModel):
    code: str
    usage_limit: int
    expired_time: Optional[int] = None


@dataclass
class RegCodesModel(BaseModel):
    regCodes: list[RegCode]
    
    def __init__(self, filename: str = "RegCode.json"):
        self.filename = ROOT_PATH / "data" / filename
        if not os.path.exists(self.filename):
            self.regCodes = []
            self.reg_dict = {}
            return
        with open(self.filename, "r") as f:
            data = json.load(f)
            data = data["regCodes"]
            reg_codes = []
            for entry in data:
                reg_code = RegCode(
                        code=entry.get("code", ""),
                        usage_limit=entry.get("usage_limit", 0),
                        expired_time=entry.get("expired_time", None)
                )
                reg_codes.append(reg_code)
        self.regCodes = reg_codes
        self.reg_dict = {reg_data.code: reg_data for reg_data in self.regCodes}
    
    def get_code_data(self, code: str) -> Optional[RegCode]:
        return self.reg_dict.get(code)
    
    def save(self):
        with open(self.filename, "w") as f:
            f.write((self.to_json()))
    
    def add_code(self, reg_code: RegCode):
        self.regCodes.append(reg_code)
        self.reg_dict[reg_code.code] = reg_code
        self.save()
    
    def remove_code(self, reg_code: RegCode):
        self.regCodes.remove(reg_code)
        self.reg_dict.pop(reg_code.code)
        self.save()
