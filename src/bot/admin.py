import os
import random
import string
import subprocess
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

import toml
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot import check_admin, check_private, command_warp
from src.config import BotConfig
from src.database.cdk import CdkModel, CdkOperate
from src.database.score import ScoreModel, ScoreOperate
from src.database.user import Role, UserModel, UsersOperate
from src.init_check import client
from src.utils import convert_to_china_timezone, get_password_hash, get_user_info, is_integer


# noinspection PyUnusedLocal
@check_admin
async def shelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_text = (f"欢迎使用Telegram-Emby-Bot，以下为管理员命令部分\n"
                f"基本命令:\n"
                f"<code>/summon [limit] [quantity] [validity_hours]</code> 生成注册码 (limit：限制数，quantity：数量，validity_hours：有效小时数)\n"
                f"<code>/checkinfo [Emby用户名/Telegram用户ID/Fullname]</code> 查看用户信息\n"
                f"<code>/deleteAccount [ID/名字/TG昵称]</code> 删除用户\n"
                f"<code>/clearUser [id/name]</code> 清除某个用户全部数据\n"
                f"<code>/move [id/name] [new_tg_id]</code> 迁移用户数据到新的tg账户\n"
                f"<code>/setGroup [id/name] [group]</code> 设置用户权限\n"
                f"<code>/cdks</code> 查看所有注册码\n"
                f"<code>/update</code> 更新Bot\n"
                f"<code>/resetpw [id/username] [pw]</code> 设置用户密码\n"
                f"<code>/setScore [id/username] [score]</code> 设置用户积分\n"
                f"<code>/setCDKgen [true/false]</code> 是否允许用户生成注册码\n"
                f"<code>/deleteCDK [cdk]</code> 删除某个注册码\n"
                f"<code>/setCdkLimit [cdk] [limit]</code> 设置注册码使用次数\n"
                f"<code>/setCdkTime [cdk] [hours]</code> 设置注册码有效时间\n"
                f"<code>/requireList</code> 查看番剧请求列表\n"
                f"<code>/getconfig</code> 获取配置\n"
                f"<code>/setconfig [key] [value]</code> 设置配置\n")
    all_keyboard = [["/summon", "/checkinfo", "/deleteAccount"],
                    ["/clearUser", "/move", "/requireList"],
                    ["/setGroup", "/cdks", "/update"],
                    ["/resetpw", "/setScore", "/setCDKgen"],
                    ["/deleteCDK", "/setCdkLimit", "/setCdkTime"],
                    ["/getconfig", "/setconfig", "/cancel 取消"]]
    reply_markup = ReplyKeyboardMarkup(all_keyboard, resize_keyboard=True)
    if update.effective_chat.type == "private":
        await update.message.reply_text(rep_text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(rep_text, parse_mode="HTML")


@check_admin
async def set_cdk_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setCdkLimit <cdk> <limit>")
    cdk = context.args[0]
    limit = int(context.args[1])
    cdk_info = await CdkOperate.get_cdk(cdk)
    if not cdk_info:
        return await update.message.reply_text("注册码未找到")
    cdk_info.limit += limit
    await CdkOperate.update_cdk(cdk_info)
    await update.message.reply_text(f"成功设置 {cdk} 的 limit 为 {cdk_info.limit}.")


@check_admin
async def clear_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /clear_user <id/name>")
    _, user_info = await get_user_info(context.args[0], only_tg_info=True)
    if not user_info:
        return await update.message.reply_text("用户未找到")
    tg_id = user_info.telegram_id
    await UsersOperate.delete(tg_id)
    await ScoreOperate.delete(tg_id)
    await update.message.reply_text(f"成功清除用户 {user_info.fullname} 的所有数据.")


@check_admin
async def move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /move <id/name> <new_tg_id>")
    old_id, new_id = context.args
    _, user_info = await get_user_info(old_id, only_tg_info=True)
    if not user_info:
        return await update.message.reply_text("用户未找到")
    user_info.telegram_id = int(new_id)
    n_info = await UsersOperate.get_user(int(new_id))
    if n_info:
        # await UsersOperate.delete(int(new_id))
        keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("确认", callback_data=f"move_{old_id}_{new_id}"), InlineKeyboardButton("取消", callback_data="cancel")]])
        await update.message.reply_text(f"新账户 {n_info.fullname} {n_info.telegram_id}已存在，将会覆盖,是否确认?", reply_markup=keyboard)
        return
    user_info.telegram_id = int(new_id)
    await UsersOperate.update_user(user_info)
    if score_data := await ScoreOperate.get_score(old_id):
        score_data.telegram_id = int(new_id)
        await ScoreOperate.update_score(score_data)
    await update.message.reply_text(f"成功将用户 {user_info.fullname} 数据迁移到新账户 {new_id}.")


@check_admin
async def set_cdk_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setCdkTime <cdk> <hours>")
    cdk = context.args[0]
    hours = int(context.args[1])
    cdk_info = await CdkOperate.get_cdk(cdk)
    if not cdk_info:
        return await update.message.reply_text("注册码未找到")
    if cdk_info.expired_time == 0:
        return await update.message.reply_text("此注册码永久有效")
    cdk_info.expired_time = cdk_info.expired_time + hours * 3600
    await CdkOperate.update_cdk(cdk_info)
    await update.message.reply_text(f"成功设置 {cdk} 为 {convert_to_china_timezone(cdk_info.expired_time)} 小时.")


@check_admin
async def del_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /deletecdk <cdk>")
    cdk = context.args[0]
    if cdk == "all":
        await CdkOperate.delete_all_cdk()
        return await update.message.reply_text("已成功删除所有注册码")
    cdk_info = await CdkOperate.get_cdk(cdk)
    if not cdk_info:
        return await update.message.reply_text("注册码未找到")
    await CdkOperate.delete_cdk(cdk)
    await update.message.reply_text(f"已成功删除 {cdk}")


@check_admin
async def set_gen_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /setcdkgen <true/false>")
    if context.args[0] not in ["true", "false"]:
        return await update.message.reply_text("Usage: /setcdkgen <true/false>")
    BotConfig.USER_GEN_CDK = context.args[0] == "true"
    BotConfig.save_to_toml()
    await update.message.reply_text(f"当前用户生成注册码权限 <code>{'允许' if context.args[0] == 'true' else '禁止'}</code>",
                                    parse_mode="HTML")


# noinspection PyUnusedLocal
async def get_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BotConfig.ADMIN:
        return await update.message.reply_text("无权限")
    ROOT_PATH: Path = Path(__file__ + '/../../..').resolve()
    toml_file_path = os.path.join(ROOT_PATH, 'config.toml')
    with open(toml_file_path, 'r') as f:
        text = f.read()
    if len(text) > 4096:
        await update.message.reply_document(document=toml_file_path, filename="config.toml")
    else:
        await update.message.reply_text(text)


async def set_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BotConfig.ADMIN:
        return await update.message.reply_text("无权限")
    if len(context.args) == 2:
        key, value = context.args
        section = None
    elif len(context.args) == 3:
        section, key, value = context.args
    else:
        return await update.message.reply_text("Usage: /set_config <key> <value> or /set_config <section> <key> <value>")
    ROOT_PATH: Path = Path(__file__ + '/../../..').resolve()
    toml_file_path = os.path.join(ROOT_PATH, 'config.toml')
    config = toml.load(toml_file_path)
    
    def get_origin_type(ori_v, value):
        if value.isdigit():
            return int(value)
        if not ori_v:
            return value
        elif ori_v in ["true", "false"]:
            return value == "true"
        return value
    
    try:
        if section:
            if section not in config:
                return await update.message.reply_text("Section not found")
            config[section][key] = get_origin_type((config[section]).get(key), value)
        else:
            config[key] = get_origin_type(config.get(key), value)
        with open(toml_file_path, 'w') as f:
            toml.dump(config, f)
    except Exception as e:
        return await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text(f"成功设置 {key} 为 {value},即将重启bot")
    python = sys.executable
    os.execl(python, python, *sys.argv)


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
    text = f"总共生成了 {quantity} 个激活码 \n\n" + "".join(f"{code}\n" for code in code_list)
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
        return await update.message.reply_text("使用方法: /checkinfo <Emby用户名/Telegram用户ID/Fullname>")
    username = context.args[0]
    emby_user, user_info = await get_user_info(username)
    # 检查积分和签到信息
    if not user_info and emby_user:
        last_login = convert_to_china_timezone(emby_user.get("LastLoginDate", "N/A"))
        await update.message.reply_text(
                f"找到Emby用户，但未绑定Telegram.\n"
                f"用户名: {emby_user['Name']}\n"
                f"上次登录: {last_login}\n")
    elif not emby_user and user_info:
        score_data = await ScoreOperate.get_score(user_info.telegram_id)
        if score_data:
            checkin_time_v = score_data.checkin_time if score_data.checkin_time is not None else 0
            score = score_data.score
        else:
            checkin_time_v = "N/A"
            score = 0
        await update.message.reply_text(
                f"找到Telegram用户，但未绑定Emby或服务器已关闭.\n"
                f"Telegram ID: {user_info.telegram_id}\n"
                f"Telegram NAME: {user_info.username}\n"
                f"Telegram昵称: {user_info.fullname}\n"
                f"用户组: {Role(user_info.role).name}\n"
                f"积分: {score}\n"
                f"上次签到时间: {convert_to_china_timezone(checkin_time_v)}\n")
    elif not emby_user and not user_info:
        return await update.message.reply_text("未找到用户信息（没有注册Emby且未给Bot发送过信息）")
    else:
        score_data = await ScoreOperate.get_score(user_info.telegram_id)
        if not score_data:
            score = 0
            checkin_time = "N/A"
        else:
            score = score_data.score
            checkin_time = score_data.checkin_time
        checkin_time_v = checkin_time if checkin_time is not None else 0
        limits = Role(user_info.role).name
        last_login = convert_to_china_timezone(emby_user.get("LastLoginDate", "N/A"))
        message = (
            f"----------Telegram----------\n"
            f"Telegram ID: {user_info.telegram_id}\n"
            f"Telegram NAME: {user_info.username}\n"
            f"Telegram昵称: {user_info.fullname}\n"
            f"用户组: {limits}\n"
            f"----------Emby----------\n"
            f"账户: {user_info.account}\n"
            f"用户名: {emby_user['Name']}\n"
            f"账户ID: {user_info.bind_id}\n"
            f"上次登录: {last_login}\n"
            f"----------Score----------\n"
            f"积分: {score}\n"
            f"上次签到时间: {convert_to_china_timezone(checkin_time_v)}"
        )
        
        if update.effective_chat.type == "private":
            message = message.replace(
                    f"Username: {emby_user['Name']}",
                    f"Username: {emby_user['Name']}\n"
            )
        
        await update.message.reply_text(message)


@command_warp
@check_admin
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /deleteAccount <Emby_username>")
    username = context.args[0]
    emby_user, user_info = await get_user_info(username)
    if not emby_user:
        return await update.message.reply_text("User not found.")
    je_id = emby_user["Id"]
    keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("确认删除", callback_data=f"admdelje_{je_id}"), InlineKeyboardButton("取消", callback_data="cancel")]])
    if user_info:
        return await update.message.reply_text(f"确认删除用户? \n"
                                               f"Je账户: {emby_user['Name']}\n"
                                               f"Tg信息: {user_info.fullname} {user_info.username if user_info.username else "无用户名"}\n"
                                               f"TG ID: {user_info.telegram_id}", reply_markup=keyboard)
    return await update.message.reply_text(f"确认删除用户? \n"
                                           f"JE账户{emby_user['Name']}", reply_markup=keyboard)


async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BotConfig.ADMIN:
        return await update.message.reply_text("无权限")
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setGroup <id/name> <group>")
    tg_id, group = context.args[0], context.args[1].upper()
    _, user_info = await get_user_info(context.args[0], only_tg_info=True)
    if not user_info:
        if is_integer(tg_id):
            user_info = UserModel(telegram_id=int(context.args[0]), username="Unknown", fullname="Unknown")
            try:
                await UsersOperate.add_user(user_info)
            except Exception as e:
                return await update.message.reply_text(f"添加用户失败: {e}, 请检查日志")
        else:
            return await update.message.reply_text("用户未找到")
    if group not in Role.__members__:
        return await update.message.reply_text("无效的用户组")
    user_info.role = Role[group].value
    await UsersOperate.update_user(user_info)
    await update.message.reply_text(f"成功设置 {user_info.fullname} {user_info.telegram_id} 为 {group}")


# noinspection PyUnusedLocal
@check_admin
@check_private
async def get_all_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code_list = await CdkOperate.get_all_cdk()
    ret_text = ""
    for code in code_list:
        if (code.expired_time == 0 or code.expired_time > datetime.now().timestamp()) and code.limit > 0:
            ret_text += (f"注册码<code>{code.cdk}</code> 使用次数: {code.limit} 到期时间: "
                         f"{convert_to_china_timezone(code.expired_time) if code.expired_time is not None else '永久'}\n")
    
    text = "全部注册码:\n\n" + ret_text
    if len(text) > 4096:
        file_buffer = BytesIO()
        file_buffer.write(text.encode('utf-8'))
        file_buffer.seek(0)
        await update.message.reply_document(document=file_buffer, filename="codes.txt")
    else:
        await update.message.reply_text(text, parse_mode="HTML")


# noinspection PyUnusedLocal
@check_admin
async def update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        subprocess.run(['git', 'pull'], check=True)
        await update.message.reply_text("Git 同步完成，正在重启")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except subprocess.CalledProcessError:
        await update.message.reply_text("更新失败，请检查日志")


@check_admin
async def set_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /setscore <id/username> <score>")
    u_name = context.args[0]
    score = int(context.args[1])
    _, user_info = await get_user_info(u_name, only_tg_info=True)
    if not user_info:
        return await update.message.reply_text("用户未找到")
    score_data = await ScoreOperate.get_score(user_info.telegram_id)
    if not score_data:
        score_data = ScoreModel(telegram_id=user_info.telegram_id, score=score)
        await ScoreOperate.add_score(score_data)
        return await update.message.reply_text(f"成功设置用户 {u_name} 积分为 {score}.")
    score_data.score = score
    await ScoreOperate.update_score(score_data)
    await update.message.reply_text(f"成功设置用户 {user_info.fullname} 积分为{score}.")


@command_warp
@check_admin
async def resetpw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /resetpw <id/username> <new pw>")
    u_name = context.args[0]
    je_data, user_info = await get_user_info(u_name)
    if not je_data and not user_info:
        return await update.message.reply_text("用户未找到")
    new_pw = context.args[1]
    je_id = je_data["Id"]
    
    if await client.Users.change_password(new_pw, je_id):
        if user_info:
            user_info.password = get_password_hash(new_pw)
            await UsersOperate.update_user(user_info)
        return await update.message.reply_text("成功重置密码")
    else:
        return await update.message.reply_text("重置密码失败")
