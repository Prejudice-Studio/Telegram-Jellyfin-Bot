import logging
import os
from pathlib import Path

import toml

ROOT_PATH: Path = Path(__file__ + '/../..').resolve()


class BaseConfig:
    """
    配置管理的基类。
    """
    toml_file_path = os.path.join(ROOT_PATH, 'config.toml')
    section = None

    @classmethod
    def update_from_toml(cls, section: str = None):
        try:
            cls.section = section
            config = toml.load(cls.toml_file_path)
            items = config.get(section, {}) if section else config
            for key, value in items.items():
                if hasattr(cls, key.upper()):
                    setattr(cls, key.upper(), value)
        except Exception as err:
            logging.error(f'Error occurred while loading config file: {err}')

    @classmethod
    def save_to_toml(cls):
        try:
            config = toml.load(cls.toml_file_path)
            if cls.section:
                if cls.section not in config:
                    config[cls.section] = {}
                for key in dir(cls):
                    if key.isupper():
                        config[cls.section][key] = getattr(cls, key)
            else:
                for key in dir(cls):
                    if key.isupper():
                        config[key] = getattr(cls, key)
            with open(cls.toml_file_path, 'w') as f:
                toml.dump(config, f)
        except Exception as err:
            logging.error(f'Error occurred while saving config file: {err}')


class ProgramConfig(BaseConfig):
    """
    程序配置 不从本地更新
    """
    VERSION: str = "0.0.1"
    REDPACKET_FILEID: str = ""  # 红包文件ID


class Config(BaseConfig):
    """
    全局配置
    """
    LOGGING: bool = True  # 是否开启日志输出本地
    LOG_LEVE: int = 20  # 日志等级
    SQLALCHEMY_LOG = False  # 是否开启SQLAlchemy日志
    PROXY: str = None  # 代理
    MAX_RETRY: int = 3  # 重试次数
    DATABASES_DIR: Path = ROOT_PATH / 'database'  # 数据库路径
    SALT = 'Emby'  # 加密盐
    BANGUMI_TOKEN: str = ""  # Bangumi Token


class LoggerConfig(BaseConfig):
    pass


class FlaskConfig(BaseConfig):
    """
    Flask API 配置
    """
    ENABLE: bool = False  # 是否启用Flask API 主要用于webhook
    HOST: str = '0.0.0.0'
    PORT: int = 5000


class BotConfig(BaseConfig):
    """
    机器人配置
    """
    ADMIN: list = [0]  # 管理员账号
    BOT_TOKEN: str = ""  # 机器人 Token
    BASE_URL: str = "https://api.telegram.org/bot"  # 自定义URL
    TIMEOUT: int = 10  # bot请求/读取超时时间
    REDPACKET_IMG: str = ""  # 红包图片路径
    USER_GEN_CDK: bool = False  # 是否允许用户生成CDK
    USER_GEN_CDK_POINT: int = 200  # 用户生成CDK消耗的积分
    CHECKIN_POINT_MAX: int = 10  # 签到积分最大值
    CHECKIN_POINT_MIN: int = 1  # 签到积分最小值
    GROUP_CHAT_ID: str = ""  # 群组ID @channelusername
    CHANNEL_CHAT_ID: str = " " # 频道ID @channelusername
    MUST_JOIN_CHANNEL: bool = False  # 是否必须加入频道
    MUST_JOIN_GROUP: bool = False  # 是否必须加入群组


class EmbyConfig(BaseConfig):
    """
    Jellyfin配置
    """
    BASE_URL: str = ""  # Emby URL
    API_KEY: str = ""  # Emby API Key
    ADDRESS: str = "[]"  # Emby地址 json数组


Config.update_from_toml()
BotConfig.update_from_toml('Bot')
EmbyConfig.update_from_toml('Emby')
FlaskConfig.update_from_toml('Flask')
