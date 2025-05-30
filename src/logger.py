import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import Config

ROOT_PATH: Path = Path(__file__ + '/../..').resolve()

emby_logger = logging.getLogger('emby')
bot_logger = logging.getLogger('bot')
scheduler_logger = logging.getLogger('scheduler')

logging.basicConfig(level=Config.LOG_LEVE, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if Config.LOGGING:
    handler = RotatingFileHandler(ROOT_PATH / 'bot.log', maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
