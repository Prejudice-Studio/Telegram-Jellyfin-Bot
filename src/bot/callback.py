import logging
import random

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import command_warp
from src.database.score import ScoreOperate
from src.database.user import UsersOperate
from src.jellyfin_client import client
from src.utils import base64_encode


# noinspection PyUnusedLocal
@command_warp
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info and user_info.bind_id:
        try:
            ret = await client.Users.delete_user(user_info.bind_id)
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


# noinspection PyUnusedLocal
async def receive_red_packet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    packet_id = int(query.data.split("_")[1])
    packet_data = await ScoreOperate.get_red_packet(packet_id)
    if packet_data:
        if packet_data.status == 1:
            return await query.answer("The red packet has been received.")
        if query.from_user.id == packet_data.telegram_id:
            return await query.answer("You can't receive the red packet that you sent.")
        history = packet_data.history.split(",") if packet_data.history else []
        if query.from_user.id in history:
            return await query.answer("You have received the red packet.")
        rec_count = len(history) - 1 if len(history) != 0 else 0
        e_score = 0  # 领取的金额
        if packet_data.type == 0:
            max_p = packet_data.current_amount - packet_data.count
            e_score = random.randint(1, max_p) if max_p > 0 else 1
            if rec_count + 1 == packet_data.count:
                e_score = packet_data.current_amount
        elif packet_data.type == 1:
            e_score = packet_data.amount // packet_data.count
        
        # 红包领取部分
        await ScoreOperate.change_score(query.from_user.id, e_score)
        packet_data.current_amount -= e_score
        packet_data.history += f"{query.from_user.id}#{base64_encode(query.from_user.full_name)}#{e_score},"
        if rec_count + 1 == packet_data.count:  # 领完
            packet_data.status = 1
        await ScoreOperate.update_red_packet(packet_data)
        await query.answer("Received successfully.")
    else:
        await query.answer("The red packet has not found.")


async def red_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    packet_id = int(query.data.split("_")[1])
    packet_data = await ScoreOperate.get_red_packet(packet_id)
    if packet_data:
        history = packet_data.history.split(",") if packet_data.history else []
        his_t = ""
        for i in range(len(history)):
            his_t += f"{history[i].split('#')[1]}: {history[i].split('#')[2]}\n"
        ret_message = f"Red packet information:\n" \
                      f"Amount: {packet_data.amount}\n" \
                      f"Count: {packet_data.count}\n" \
                      f"Current amount: {packet_data.current_amount}\n" \
                      f"Type: {'Random' if packet_data.type == 0 else 'Average'}\n" \
                      f"Status: {'Received' if packet_data.status == 1 else 'Not received'}"
        if his_t != "":
            ret_message += f"\nHistory:\n{his_t}"
        await update.effective_message.reply_text(ret_message)
    else:
        await query.answer("The red packet has not found.")
