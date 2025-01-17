import json
import random
from asyncio import sleep

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import command_warp
from src.database.score import ScoreModel, ScoreOperate
from src.database.user import Role, UsersOperate
from src.init_check import client
from src.logger import bot_logger
from src.utils import base64_decode, base64_encode, get_user_info


# noinspection PyUnusedLocal
@command_warp
async def admin_delete_je(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    je_id = int(query.data.split("_")[1])
    Emby_user, user_info = await get_user_info(je_id)
    if not Emby_user:
        return await query.answer("用户不存在")
    je_id = Emby_user["Id"]
    if user_info:
        if user_info.role != Role.ADMIN.value:
            user_info.role = Role.SEA.value
            await UsersOperate.update_user(user_info)
        await UsersOperate.clear_bind(user_info.telegram_id)
    try:
        if not await client.Users.delete_user(je_id):
            return await update.message.reply_text("[Server]删除用户失败[2]")
    except Exception as e:
        bot_logger.error(f"Error: {e}")
        return await update.message.reply_text("[Server]删除用户失败[1]")
    await query.answer(f"成功删除JE用户{Emby_user['Name']}")
    await query.delete_message()


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
        if packet_data.status == 1:
            return await query.answer("红包已经被领完")
        elif packet_data.status == 2:
            return await query.answer("红包已经被撤回")
        if not packet_data.data:
            return await query.answer("红包数据错误")
        history = packet_data.history.split(",") if packet_data.history else []
        if any(query.from_user.id == int(entry.split('#')[0]) for entry in history[:-1]):
            return await query.answer("您已经领过这个红包了")
        all_packet = json.loads(packet_data.data)
        if len(all_packet) == 0:
            packet_data.status = 1
            await ScoreOperate.update_red_packet(packet_data)
            return await query.answer("红包已经被领完")
        e_score = random.choice(all_packet)
        all_packet.remove(e_score)
        # 红包领取部分
        from_user_score = await ScoreOperate.get_score(query.from_user.id)
        if not from_user_score:
            from_user_score = ScoreModel(telegram_id=query.from_user.id, score=e_score)
            await ScoreOperate.add_score(from_user_score)
        else:
            from_user_score.score += e_score
            await ScoreOperate.update_score(from_user_score)
        packet_data.current_amount -= e_score
        packet_data.history += f"{query.from_user.id}#{base64_encode(query.from_user.full_name)}#{e_score},"
        packet_data.data = json.dumps(all_packet)
        rec_count = len(history) if len(history) != 0 else 0
        if rec_count == packet_data.count:  # 领完
            packet_data.status = 1
        await ScoreOperate.update_red_packet(packet_data)
        await query.answer(f"您收到了 {e_score} 积分，当前总积分 {from_user_score.score}")
    else:
        await query.answer("红包未找到")


# noinspection PyUnusedLocal
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
                      f"状态: {'未领完' if packet_data.status == 0 else '已领完或撤回'}"
        if his_t != "":
            ret_message += f"\n领取历史:\n{his_t}"
        rep = await update.effective_message.reply_text(ret_message)
        await query.answer()
        await sleep(30)
        await rep.delete()
    else:
        await query.answer("红包未找到")


# noinspection PyUnusedLocal
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


# noinspection PyUnusedLocal
async def move_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    from_info = await UsersOperate.get_user(query.from_user.id)
    if from_info.telegram_id != Role.ADMIN.value:
        return await query.answer("权限不足")
    _, from_id, to_id = query.data.split("_")
    from_info = await UsersOperate.get_user(int(from_id))
    to_info = await UsersOperate.get_user(int(to_id))
    if not to_info:
        from_info.telegram_id = int(to_id)
        await UsersOperate.update_user(from_info)
        return await query.answer("已经将用户移动到该ID")
    to_info.telegram_id = int(to_id)
    to_info.account = from_info.account
    to_info.password = from_info.password
    to_info.role = from_info.role
    to_info.bind_id = from_info.bind_id
    to_info.data = from_info.data
    to_info.config = from_info.config
    await UsersOperate.update_user(to_info)
    await UsersOperate.clear_bind(int(from_id))
    await query.answer("已经将用户移动到该ID")
    await query.delete_message()
    
    