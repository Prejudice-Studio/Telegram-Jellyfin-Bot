from functools import wraps
from typing import Any, Dict, Optional

import httpx
from httpx import Response

from src.logger import je_logger


def http_warp(func):
    @wraps(func)
    async def wrapper(self, path: str, *args, **kwargs):
        if isinstance(path, str) and "{UserID}" in path:
            if self.user_id is None:
                raise ValueError("No user_id")
            path = path.format(UserID=self.user_id)
        return await func(self, path, *args, **kwargs)
    
    return wrapper


class JellyfinRequest:
    
    def __init__(self, url: str, auth: int, api_key: Optional[str] = None):
        self.rclone_root_url = url
        self.client = httpx.AsyncClient(base_url=url)
        self.api_key = api_key
        self.user_data = None
        self.user_id = None
        
        if auth == 1:  # API key
            self.client.headers = {
                'accept': 'application/json',
                'content-type': 'application/json',
                'X-Emby-Token': api_key,
                'X-Emby-Client': 'Telegram Jellyfin Bot',
                'X-Emby-Device-Name': 'Telegram Jellyfin Bot',
                'X-Emby-Client-Version': '1.0.0',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 '
                              'Safari/537.36 Edg/114.0.1823.82'
            }
        elif auth == 2:  # 账户密码登录
            self.client.headers = {
                'accept': 'application/json',
                'content-type': 'application/json',
            }
    
    async def login(self, account: str, password: str):
        login_url = '/Users/authenticatebyname'
        login_data = {
            'Username': account,
            'Pw': password
        }
        auth = 'MediaBrowser Client="Telegram Jellyfin Bot", Device="Telegram", DeviceId="Telegram Jellyfin Bot", Version="1.0.0"'
        self.client.headers['Authorization'] = auth
        response = await self.client.post(login_url, json=login_data)
        je_logger.info(f"Login {response.status_code} {response.text}")
        if response.status_code == 200:
            json_response = response.json()
            if token := json_response.get('AccessToken'):
                auth = auth + f', Token="{token}"'
                self.client.headers['Authorization'] = auth
                self.user_data = json_response
                self.user_id = json_response['User']['Id']
                return json_response
            else:
                raise ValueError("Login failed, no token")
        else:
            raise ValueError(f"Login failed, status code: {response.status_code}, response: {response.text}")
    
    @http_warp
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, **kwargs) -> Response:
        response = await self.client.get(path, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        je_logger.info(f"GET {path} {response.status_code}")
        return response
    
    @http_warp
    async def post(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                   json: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        response = await self.client.post(path, params=params, headers=headers, json=json, **kwargs)
        response.raise_for_status()
        je_logger.info(f"POST {path} {response.status_code}")
        return response
    
    @http_warp
    async def put(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                  json: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        response = await self.client.put(path, params=params, headers=headers, json=json, **kwargs)
        response.raise_for_status()
        je_logger.info(f"PUT {path} {response.status_code}")
        return response
    
    @http_warp
    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                     **kwargs) -> Response:
        response = await self.client.delete(path, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        je_logger.info(f"DELETE {path} {response.status_code}")
        return response
    
    async def close(self):
        await self.client.aclose()
