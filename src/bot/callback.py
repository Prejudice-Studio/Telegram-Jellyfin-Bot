import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import command_warp
from src.database.user import UsersOperate
from src.jellyfin_client import client


# noinspection PyUnusedLocal
@command_warp
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info and user_info.bind_id:
        try:
            ret = client.jellyfin.delete_user(user_info.bind_id)
            logging.info(f"[Server]Delete user: {ret}")
        except Exception as e:
            logging.error(e)
            await update.effective_user.send_message("Delete failed.")
        await UsersOperate.clear_bind(update.effective_user.id)
        await update.effective_user.send_message("Account deleted successful.")
    else:
        await update.effective_user.send_message("Can't find the account.")
    await query.delete_message()


# noinspection PyUnusedLocal
@command_warp
async def confirm_unbind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info:
        await UsersOperate.clear_bind(update.effective_user.id)
        await update.effective_user.send_message("Unbind successful.")
    else:
        await update.effective_user.send_message("No bound Jellyfin account found.")
    await query.delete_message()


# noinspection PyUnusedLocal
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Operation canceled.")
    await query.delete_message()
