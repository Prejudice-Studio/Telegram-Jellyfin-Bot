import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .clean import clean_memory


def start_scheduler():
    logging.info("Starting scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(clean_memory, 'interval', hours=2)
    scheduler.start()

    # async_scheduler = AsyncIOScheduler()
