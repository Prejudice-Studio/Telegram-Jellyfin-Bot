from asyncio import sleep
from datetime import datetime
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.database.user import UserModel, UsersOperate
from src.jellyfin_client import check_server_connectivity
from src.logger import bot_logger

last_check_time = 0
server_close = False


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
        eff_user = update.effective_user
        user_data = await UsersOperate.get_user(eff_user.id)
        if not user_data:
            await UsersOperate.add_user(UserModel(telegram_id=eff_user.id,
                                                  username=eff_user.username,
                                                  role=1,
                                                  fullname=eff_user.full_name,
                                                  ))
            return await func(update, context, *args, **kwargs)
        if user_data.role == 0:
            return
        if user_data.fullname != eff_user.full_name or user_data.username != eff_user.username:
            user_data.username = eff_user.username
            user_data.fullname = eff_user.full_name
            await UsersOperate.update_user(user_data)
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def command_warp(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        global last_check_time, server_close
        if last_check_time + 60 < datetime.now().timestamp():
            last_check_time = datetime.now().timestamp()
            bot_logger.info(f"Server check")
            if not await check_server_connectivity():
                server_close = True
                return await update.message.reply_text("服务器已经关闭，请稍后再试。")
            else:
                server_close = False
        if server_close:
            return await update.message.reply_text("服务器已经关闭，请稍后再试。")
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def check_private(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not (update and update.effective_user):
            return
        if update.effective_chat.type != "private":
            rep = await update.message.reply_text("请在私聊中使用。")
            await sleep(5)
            await update.message.delete()
            await rep.delete()
            return
        return await func(update, context, *args, **kwargs)
    
    return wrapper
