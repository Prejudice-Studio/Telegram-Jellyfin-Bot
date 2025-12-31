import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .clean import clean_memory
from src.database.user import UsersOperate
from src.config import BotConfig

async def start_scheduler():
    logging.info("Starting scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(clean_memory, 'interval', hours=2)
    syncembyuser = await UsersOperate.sync_emby_user
    syncInterval = BotConfig.EMBY_USERS_SYNC_INTERVAL
    scheduler.add_job(syncembyuser, 'interval', minutes=syncInterval)
    scheduler.start()
    logging.info("Scheduler started")

    # async_scheduler = AsyncIOScheduler()
