from functools import wraps
from typing import Any, Dict, Optional

import httpx
from httpx import Response

from src.logger import emby_logger


def json_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)
        if response.status_code == 204 or response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Request failed, status code: {response.status_code}, response: {response.text}")
    
    return wrapper


class BangumiRequest:
    
    def __init__(self, access_token: Optional[str] = None):
        self.client = httpx.AsyncClient(base_url="https://api.bgm.tv/")
        self.access_token = access_token
        self.user_data = None
        self.user_id = None
        
        self.client.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Authorization': f"Bearer {access_token}",
            'User-Agent': 'enlysure/telegram-jellyfin-bot (https://github.com/Prejudice-Studio/Telegram-Jellyfin-Bot)'
        }
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, **kwargs) -> Response:
        response = await self.client.get(path, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        emby_logger.info(f"GET {path} {response.status_code}")
        return response
    
    async def post(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                   json: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        response = await self.client.post(path, params=params, headers=headers, json=json, **kwargs)
        response.raise_for_status()
        emby_logger.info(f"POST {path} {response.status_code}")
        return response
    
    async def put(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                  json: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        response = await self.client.put(path, params=params, headers=headers, json=json, **kwargs)
        response.raise_for_status()
        emby_logger.info(f"PUT {path} {response.status_code}")
        return response
    
    async def delete(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None,
                     **kwargs) -> Response:
        response = await self.client.delete(path, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        emby_logger.info(f"DELETE {path} {response.status_code}")
        return response
    
    async def close(self):
        await self.client.aclose()
