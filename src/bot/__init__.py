from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.jellyfin_client import UsersData, check_server_connectivity


def check_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        tg_id = update.effective_user.id
        user_info = UsersData.get_user_by_id(tg_id)
        if not user_info:
            return await update.message.reply_text("Unauthorized")
        if user_info.role != 1 and tg_id != BotConfig.ADMIN:
            return await update.message.reply_text("Unauthorized")
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def command_warp(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not check_server_connectivity():
            return await update.message.reply_text("Server is closed, please try again later.")
        return await func(update, context, *args, **kwargs)
    
    return wrapper
