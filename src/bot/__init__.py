import json
import logging
from asyncio import sleep
from datetime import datetime
from functools import wraps

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.config import BotConfig
from src.database.user import Role, UserModel, UsersOperate
from src.utils import check_server_connectivity, is_user_in_group
from src.logger import bot_logger

last_check_time = 0
server_close = False


def check_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update:
            return
        q_id = None
        if update.message and update.message.sender_chat:
            q_id = update.message.sender_chat.id
        elif update.effective_user:
            q_id = update.effective_user.id
        if not q_id:
            return
        if q_id == BotConfig.ADMIN:
            return await func(update, context, *args, **kwargs)
        user_data = await UsersOperate.get_user(q_id)
        if not user_data:
            return
        if user_data.role != Role.ADMIN.value:
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
            user_data = await UsersOperate.get_user(eff_user.id)
        if user_data.role == Role.BANNED.value:
            return
        if eff_user.id == BotConfig.ADMIN or user_data.role == Role.ADMIN.value:
            return await func(update, context, *args, **kwargs)
        if user_data.fullname != eff_user.full_name or user_data.username != eff_user.username:
            user_data.username = eff_user.username
            user_data.fullname = eff_user.full_name
            await UsersOperate.update_user(user_data)
        user_ex_data = json.loads(str(user_data.data)) if user_data.data else {}
        keyboard = []
        if not user_ex_data.get("check_pass", False):
            if BotConfig.MUST_JOIN_CHANNEL and (
            not await is_user_in_group(context.bot, BotConfig.CHANNEL_CHAT_ID, update.effective_user.id)):
                keyboard.append(
                    [InlineKeyboardButton(text="点击加入频道", url=f"https://t.me/{BotConfig.CHANNEL_CHAT_ID[1:]}")])
            if BotConfig.MUST_JOIN_GROUP and (
            not await is_user_in_group(context.bot, BotConfig.GROUP_CHAT_ID, update.effective_user.id)):
                keyboard.append(
                    [InlineKeyboardButton(text="点击加入群组", url=f"https://t.me/{BotConfig.GROUP_CHAT_ID[1:]}")])
            if keyboard:
                await update.message.reply_text("请先加入频道和群组", reply_markup=InlineKeyboardMarkup(keyboard))
                return
            else:
                user_ex_data["check_pass"] = False
                user_data.data = json.dumps(user_ex_data)
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
                bot_logger.info(f"Server check close")
                server_close = True
                return await update.message.reply_text("服务器已经关闭，请稍后再试。")
            else:
                bot_logger.info(f"Server check successful")
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
