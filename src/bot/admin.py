import logging
import os
import random
import string
import subprocess
import sys
from datetime import datetime
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

from src.bot import check_admin
from src.config import JellyfinConfig
from src.database.cdk import CdkModel, CdkOperate
from src.database.score import ScoreModel, ScoreOperate
from src.database.user import UsersOperate
from src.jellyfin_client import client
from src.utils import convert_to_china_timezone, get_user_info


@check_admin
async def set_code_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setRegCodeUsageLimit <cdk> <limit>")
    cdk = context.args[0]
    limit = int(context.args[1])
    cdk_info = await CdkOperate.get_cdk(cdk)
    if not cdk_info:
        return await update.message.reply_text("Registration code not found.")
    cdk_info.limit += limit
    await CdkOperate.update_cdk(cdk_info)
    await update.message.reply_text(f"Successfully set the usage limit of registration code {cdk} to {cdk_info.limit}.")


@check_admin
async def set_code_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setRegCodeTime <cdk> <hours>")
    cdk = context.args[0]
    hours = int(context.args[1])
    cdk_info = await CdkOperate.get_cdk(cdk)
    if not cdk_info:
        return await update.message.reply_text("Registration code not found.")
    if cdk_info.expired_time == 0:
        return await update.message.reply_text("The registration code does not have an expiration time.")
    cdk_info.expired_time = cdk_info.expired_time + hours * 3600
    await CdkOperate.update_cdk(cdk_info)
    await update.message.reply_text(f"Successfully set the expiration time of registration code {cdk} "
                                    f"to {convert_to_china_timezone(cdk_info.expired_time)} hours.")


@check_admin
async def del_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /deleteRegCode <cdk>")
    cdk = context.args[0]
    if cdk == "all":
        await CdkOperate.delete_all_cdk()
        return await update.message.reply_text("Successfully deleted all registration codes.")
    cdk_info = await CdkOperate.get_cdk(cdk)
    if not cdk_info:
        return await update.message.reply_text("Registration code not found.")
    await CdkOperate.delete_cdk(cdk)
    await update.message.reply_text(f"Successfully deleted registration code {cdk}.")


@check_admin
async def set_gen_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /setRegCodeGenerateStatus <true/false>")
    if context.args[0] not in ["true", "false"]:
        return await update.message.reply_text("Usage: /setRegCodeGenerateStatus <true/false>")
    JellyfinConfig.USER_GEN_CDK = context.args[0] == "true"
    JellyfinConfig.save_to_toml()
    await update.message.reply_text(f"Successfully set the registration code generation to {context.args[0]}.")


@check_admin
async def summon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /summon <usage_limit> <quantity> [validity_hours]")
    usage_limit = int(context.args[0])
    quantity = int(context.args[1])
    validity_hours = int(context.args[2]) if len(context.args) > 2 else None
    code_list = []
    for _ in range(quantity):
        code = f"reg_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}_prej"
        code_data = CdkModel(cdk=code, limit=usage_limit, expired_time=0)
        code_list.append(code)
        if validity_hours:
            code_data.expired_time = int(datetime.now().timestamp()) + validity_hours * 3600
        await CdkOperate.add_cdk(code_data)
    text = f"Generated {quantity} registration codes.\n\n" + "".join(f"{code}\n" for code in code_list)
    if len(text) > 4096:
        file_buffer = BytesIO()
        file_buffer.write(text.encode('utf-8'))
        file_buffer.seek(0)
        await update.message.reply_document(document=file_buffer, filename="registration_codes.txt")
    else:
        await update.message.reply_text(text)


@check_admin
async def checkinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("使用方法: /checkinfo <jellyfin用户名/Telegram用户ID/Fullname>")
    username = context.args[0]
    jellyfin_user, user_info = await get_user_info(username)
    if not jellyfin_user:
        return await update.message.reply_text("未发现用户.")
    last_login = convert_to_china_timezone(jellyfin_user.get("LastLoginDate", "N/A"))
    # 检查积分和签到信息
    if not user_info:
        await update.message.reply_text(
                f"发现Jellyfin用户，但未绑定Telegram.\n"
                f"用户名: {jellyfin_user['Name']}\n"
                f"上次登录: {last_login}\n")
    else:
        score_data = await ScoreOperate.get_score(update.effective_user.id)
        if not score_data:
            score = 0
            checkin_time = "N/A"
        else:
            score = score_data.score
            checkin_time = score_data.checkin_time
        checkin_time_v = checkin_time if checkin_time is not None else 0
        message = (
            f"----------Telegram----------\n"
            f"TelegramID: {user_info.telegram_id}\n"
            f"Telegram昵称: {user_info.fullname}\n"
            f"----------Jellyfin----------\n"
            f"用户名: {jellyfin_user['Name']}\n"
            f"上次登录: {last_login}\n"
            f"----------Score----------\n"
            f"积分: {score}\n"
            f"上次签到时间: {convert_to_china_timezone(checkin_time_v)}"
        )
        
        if update.effective_chat.type == "private":
            message = message.replace(
                    f"Username: {jellyfin_user['Name']}",
                    f"Username: {jellyfin_user['Name']}\n"
            )
        
        await update.message.reply_text(message)


@check_admin
async def deleteAccountBy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /deleteAccountBy <jellyfin_username>")
    username = context.args[0]
    jellyfin_user, user_info = await get_user_info(username)
    if not jellyfin_user:
        return await update.message.reply_text("User not found.")
    je_id = jellyfin_user["Id"]
    try:
        if not await client.Users.delete_user(je_id):
            return await update.message.reply_text("[Server]Failed to delete user.")
    except Exception as e:
        logging.error(f"Error: {e}")
        return await update.message.reply_text("[Server]Failed to delete user.")
    await update.message.reply_text(f"Successfully deleted user {username} from Jellyfin and the system.")


async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /op <telegram_id>")
    tg_id = int(context.args[0])
    user_info = await UsersOperate.get_user(tg_id)
    if not user_info:
        return await update.message.reply_text("User not found.")
    user_info.role = 2
    await UsersOperate.update_user(user_info)
    await update.message.reply_text(f"Successfully set {user_info.fullname} as an administrator.")


# noinspection PyUnusedLocal
@check_admin
async def get_all_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_list = await CdkOperate.get_all_cdk()
    ret_text = ""
    for code in code_list:
        if (code.expired_time == 0 or code.expired_time > datetime.now().timestamp()) and code.limit > 0:
            ret_text += (f"Code <code>{code.cdk}</code> Usage limit: {code.limit} Expired time: "
                         f"{convert_to_china_timezone(code.expired_time) if code.expired_time is not None else 'NoExpired'}\n")
    
    text = "All registration codes:\n\n" + ret_text
    if len(text) > 4096:
        file_buffer = BytesIO()
        file_buffer.write(text.encode('utf-8'))
        file_buffer.seek(0)
        await update.message.reply_document(document=file_buffer, filename="codes.txt")
    else:
        await update.message.reply_text(text)


# noinspection PyUnusedLocal
@check_admin
async def update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        subprocess.run(['git', 'pull'], check=True)
        await update.message.reply_text("Git sync completed, the bot is restarting")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except subprocess.CalledProcessError:
        await update.message.reply_text("Update failed, please check the log")


@check_admin
async def set_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setscore <id/username> <score>")
    u_name = context.args[0]
    score = int(context.args[1])
    _, user_info = await get_user_info(u_name)
    if not user_info:
        return await update.message.reply_text("User not found.")
    score_data = await ScoreOperate.get_score(user_info.telegram_id)
    if not score_data:
        score_data = ScoreModel(telegram_id=user_info.telegram_id, score=score)
        await ScoreOperate.add_score(score_data)
        return await update.message.reply_text(f"Successfully set the score of user {u_name} to {score}.")
    score_data.score = score
    await ScoreOperate.update_score(score_data)
    await update.message.reply_text(f"Successfully set the score of user {user_info.fullname} to {score}.")
