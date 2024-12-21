from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.database.user import UserModel, UsersOperate
from src.jellyfin_client import check_server_connectivity


def check_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not (update and update.effective_user):
            return
        user_data = await UsersOperate.get_user(update.effective_user.id)
        if not user_data:
            return
        if user_data.role != 2 and update.effective_user.id != BotConfig.ADMIN:
            return
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def check_banned(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not (update and update.effective_user):
            return await func(update, context, *args, **kwargs)
        
        user_data = await UsersOperate.get_user(update.effective_user.id)
        if not user_data:
            await UsersOperate.add_user(UserModel(telegram_id=update.effective_user.id,
                                                  username=update.effective_user.username,
                                                  role=1,
                                                  fullname=update.effective_user.full_name,
                                                  ))
            return await func(update, context, *args, **kwargs)
        if user_data.role == 0:
            return
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def command_warp(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not check_server_connectivity():
            return await update.message.reply_text("Server is closed, please try again later.")
        return await func(update, context, *args, **kwargs)
    
    return wrapper
