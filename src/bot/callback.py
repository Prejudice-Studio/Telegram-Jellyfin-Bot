import random
from asyncio import sleep

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import command_warp
from src.database.score import ScoreOperate
from src.database.user import Role, UsersOperate
from src.jellyfin_client import client
from src.logger import bot_logger
from src.utils import base64_decode, base64_encode


# noinspection PyUnusedLocal
@command_warp
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info and user_info.bind_id:
        try:
            ret = await client.Users.delete_user(user_info.bind_id)
            bot_logger.info(f"[Server]Delete user: {ret}")
        except Exception as e:
            bot_logger.error(e)
            await update.effective_user.send_message("账户删除失败")
        user_info.role = Role.SEA.value
        await UsersOperate.update_user(user_info)
        await UsersOperate.clear_bind(update.effective_user.id)
        await update.effective_user.send_message("账户删除成功")
    else:
        await update.effective_user.send_message("无法找到账户")
    await query.delete_message()


# noinspection PyUnusedLocal
@command_warp
async def confirm_unbind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info:
        await UsersOperate.clear_bind(update.effective_user.id)
        await update.effective_user.send_message("解绑成功")
    else:
        await update.effective_user.send_message("未绑定账户")
    await query.delete_message()


# noinspection PyUnusedLocal
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("操作取消")
    await query.delete_message()


# noinspection PyUnusedLocal
async def receive_red_packet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    packet_id = int(query.data.split("_")[1])
    packet_data = await ScoreOperate.get_red_packet(packet_id)
    if packet_data:
        if packet_data.status != 0:
            return await query.answer("红包已经被领完")
        history = packet_data.history.split(",") if packet_data.history else []
        if any(query.from_user.id == int(entry.split('#')[0]) for entry in history[:-1]):
            return await query.answer("您已经领过这个红包了")
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
        await query.answer(f"您收到了 {e_score} 积分")
    else:
        await query.answer("红包未找到")


async def red_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    packet_id = int(query.data.split("_")[1])
    packet_data = await ScoreOperate.get_red_packet(packet_id)
    if packet_data:
        history = packet_data.history.split(",") if packet_data.history else []
        his_t = ""
        for i in range(len(history) - 1):
            print(history[i].split('#'))
            his_t += f"{base64_decode(history[i].split('#')[1])}: {history[i].split('#')[2]}\n"
        ret_message = f"红包信息\n" \
                      f"总金额: {packet_data.amount}\n" \
                      f"总份数: {packet_data.count}\n" \
                      f"剩余金额: {packet_data.current_amount}\n" \
                      f"类型: {'随机' if packet_data.type == 0 else '平均'}\n" \
                      f"状态: {'已领完' if packet_data.status == 1 else '未领完'}"
        if his_t != "":
            ret_message += f"\n领取历史:\n{his_t}"
        rep = await update.effective_message.reply_text(ret_message)
        await query.answer()
        await sleep(10)
        await rep.delete()
    else:
        await query.answer("红包未找到")


async def withdraw_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    packet_id = int(query.data.split("_")[1])
    packet_data = await ScoreOperate.get_red_packet(packet_id)
    if packet_data:
        if packet_data.telegram_id != query.from_user.id:
            return await query.answer("无法撤回他人的红包")
        if packet_data.status == 1:
            return await query.answer("红包已经被领完")
        elif packet_data.status == 2:
            return await query.answer("红包已经被撤回")
        packet_data.status = 2
        await ScoreOperate.update_red_packet(packet_data)
        score_data = await ScoreOperate.get_score(packet_data.telegram_id)
        score_data.score += packet_data.current_amount
        await query.answer(f"红包已经被撤回,已经返还{packet_data.current_amount}积分")
    else:
        await query.answer("红包未找到")
