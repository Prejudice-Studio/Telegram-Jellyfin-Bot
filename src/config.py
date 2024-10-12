import logging
import os
from pathlib import Path

import toml

ROOT_PATH: Path = Path(__file__ + '/../..').resolve()


class BaseConfig:
    """
    配置管理的基类。
    """
    
    @classmethod
    def update_from_toml(cls, path: str, section: str = None):
        try:
            config = toml.load(path)
            items = config.get(section, {}) if section else config
            for key, value in items.items():
                if hasattr(cls, key.upper()):
                    setattr(cls, key.upper(), value)
        except Exception as err:
            logging.error(f'Error occurred while loading config file: {err}')


class Config(BaseConfig):
    """
    全局配置
    """
    
    PROXY: str = None  # 代理
    MAX_RETRY: int = 3  # 重试次数
    LOG_LEVE: int = 20  # 日志等级


class BotConfig(BaseConfig):
    """
    机器人配置
    """
    ADMIN: int = 0  # 管理员账号
    BOT_TOKEN: str = ""  # 机器人 Token
    BASE_URL: str = "https://api.telegram.org/bot"  # 自定义URL
    TIMEOUT: int = 10  # bot请求/读取超时时间


class JellyfinConfig(BaseConfig):
    """
    Jellyfin配置
    """
    BASE_URL: str = ""  # Jellyfin URL
    API_KEY: str = ""  # Jellyfin API Key


_toml_file_path = os.path.join(ROOT_PATH, 'config.toml')
Config.update_from_toml(_toml_file_path)
BotConfig.update_from_toml(_toml_file_path, 'Bot')
JellyfinConfig.update_from_toml(_toml_file_path, 'Jellyfin')
