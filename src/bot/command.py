import logging
import os
import random
import string
import subprocess
import sys
from datetime import datetime
from io import BytesIO

from sqlalchemy import or_, select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot import check_admin, check_banned, command_warp
from src.config import JellyfinConfig
from src.database.cdk import CdkModel, CdkOperate
from src.database.score import ScoreModel, ScoreOperate
from src.database.user import UserModel, UsersOperate, UsersSessionFactory
from src.jellyfin.api import JellyfinAPI
from src.jellyfin_client import client
from src.utils import convert_to_china_timezone, get_password_hash, is_password_strong


async def get_user_info(username: str | int) -> tuple[dict | None, UserModel | None]:
    """
    获取 Jellyfin 用户信息
    :param username: Telegram ID/Fullname or Jellyfin username
    :return:
    """
    je_id = None
    
    async def fetch_user_id(f_username: str):
        async with UsersSessionFactory() as f_session:
            scalars = await f_session.execute(select(UserModel).filter(
                    or_(
                            UserModel.fullname.like(f"%{f_username}%"),
                            UserModel.username.like(f"%{f_username}%")
                    )
            ).limit(1))
            logging.info(f"fetch_user_id: {scalars}")
            return scalars.scalar_one_or_none()
    
    if username.isdigit():
        user_info = await UsersOperate.get_user(int(username))
        je_id = user_info.bind_id if user_info else None
    else:
        user_info = await fetch_user_id(username)
        if user_info:
            je_id = user_info.bind_id
    if not je_id:
        try:
            all_user = await client.Users.get_users()
            je_data = next((u for u in all_user if u["Name"] == username), None)
            je_id = je_data["Id"] if je_data else None
        except Exception as e:
            logging.error(f"Error: {e}")
            return None, None
    if je_id is not None:
        try:
            jellyfin_user = await client.Users.get_user(je_id)
            async with UsersSessionFactory() as session:
                user_scalars = await session.execute(select(UserModel).filter_by(bind_id=je_id).limit(1))
                user_info = user_scalars.scalar_one_or_none()
            return jellyfin_user, user_info
        except Exception as e:
            logging.error(f"Error: {e}")
    if user_info:
        return None, user_info
    return None, None


# noinspection PyUnusedLocal
class AdminCommand:
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
    @check_admin
    async def set_gen_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            return await update.message.reply_text("Usage: /setRegCodeGenerateStatus <true/false>")
        if context.args[0] not in ["true", "false"]:
            return await update.message.reply_text("Usage: /setRegCodeGenerateStatus <true/false>")
        JellyfinConfig.USER_GEN_CDK = context.args[0] == "true"
        JellyfinConfig.save_to_toml()
        await update.message.reply_text(f"Successfully set the registration code generation to {context.args[0]}.")
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
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
    
    # 查看注册码
    @staticmethod
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
    
    @staticmethod
    @check_admin
    async def update(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            subprocess.run(['git', 'pull'], check=True)
            await update.message.reply_text("Git sync completed, the bot is restarting")
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except subprocess.CalledProcessError:
            await update.message.reply_text("Update failed, please check the log")
    
    @staticmethod
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
            score_data = await ScoreOperate.add_score(score_data)
            return await update.message.reply_text(f"Successfully set the score of user {u_name} to {score}.")
        score_data.score = score
        await ScoreOperate.update_score(score_data)
        await update.message.reply_text(f"Successfully set the score of user {user_info.fullname} to {score}.")


# noinspection PyUnusedLocal
class UserCommand:
    @staticmethod
    @check_banned
    @command_warp
    async def gen_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not JellyfinConfig.USER_GEN_CDK:
            return await update.message.reply_text("Registration code generation is disabled.")
        score_data = await ScoreOperate.get_score(update.effective_user.id)
        if score_data is None or score_data.score < 200:
            return await update.message.reply_text("Insufficient points (200 points required).")
        quantity = 1
        if len(context.args) == 1:
            quantity = int(context.args[0])
        if quantity * 200 > score_data.score:
            return await update.message.reply_text(f"Insufficient points. Current points: {score_data.score}")
        code_list = []
        for _ in range(quantity):
            code = f"reg_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}_prej"
            code_data = CdkModel(cdk=code, limit=1, expired_time=0)
            code_list.append(code)
            await CdkOperate.add_cdk(code_data)
        text = f"Generated {quantity} registration codes.\n\n" + "".join(f"{code}\n" for code in code_list)
        score_data.score -= quantity * 200
        await ScoreOperate.update_score(score_data)
        await update.message.reply_text(text)
    
    @staticmethod
    @check_banned
    @command_warp
    async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 3:
            return await update.message.reply_text("Usage: /reg <username> <password> <reg_code>")
        username, password, reg_code = context.args
        eff_user = update.effective_user
        if not username.isalnum() or not password.isalnum():
            return await update.message.reply_text("用户名与密码不合法.")
        if not is_password_strong(password):
            return await update.message.reply_text("密码强度不够(需要至少8位字符，且包含至少一个小写字母和大写字母).")
        cdk_info = await CdkOperate.get_cdk(reg_code)
        if not cdk_info:
            return await update.message.reply_text("注册码不可用")
        if cdk_info.limit <= 0:
            return await update.message.reply_text("注册码已被使用")
        if cdk_info.expired_time != 0 and cdk_info.expired_time < datetime.now().timestamp():
            return await update.message.reply_text("注册码已过期")
        try:
            ret_user = await client.Users.new_user(username, password)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]创建用户失败(服务器故障或已经存在相同用户)")
        cdk_info.limit -= 1
        cdk_info.used_history += f"{str(eff_user.id)},"
        await CdkOperate.update_cdk(cdk_info)
        
        # 绑定 Telegram 和 Jellyfin 账号
        user_info = await UsersOperate.get_user(eff_user.id)
        password_hash = get_password_hash(password)
        if user_info:
            user_info.account = username
            user_info.password = password_hash
            user_info.bind_id = ret_user["Id"]
            await UsersOperate.update_user(user_info)
        else:
            user_info = UserModel(telegram_id=eff_user.id, username=eff_user.username, fullname=eff_user.full_name,
                                  account=username, password=password_hash, bind_id=ret_user["Id"])
            await UsersOperate.add_user(user_info)
        return await update.message.reply_text(f"注册成功，自动与Telegram绑定. 用户名: {username}")
    
    @staticmethod
    @check_banned
    @command_warp
    async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = await UsersOperate.get_user(update.effective_user.id)
        if not user_info or not user_info.bind_id:
            return await update.message.reply_text("无Jellyfin账号与该Telegram账号绑定.")
        try:
            jellyfin_user = await client.Users.get_user(user_info.bind_id)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to connect to Jellyfin.")
        logging.info(f"Jellyfin user: {jellyfin_user}")
        if not jellyfin_user:
            return await update.message.reply_text("用户未找到.")
        
        last_login = convert_to_china_timezone(jellyfin_user.get("LastLoginDate", "N/A"))
        score_data = await ScoreOperate.get_score(update.effective_user.id)
        if not score_data:
            score = 0
            checkin_time = "N/A"
        else:
            score = score_data.score
            checkin_time = score_data.checkin_time
        checkin_time_v = checkin_time if checkin_time is not None else 0
        limits = "无用户组"
        if user_info.role == 0:
            limits = "封禁"
        elif user_info.role == 1:
            limits = "普通用户"
        elif user_info.role == 2:
            limits = "管理员"
        await update.message.reply_text(
                f"----------Telegram----------\n"
                f"TelegramID: {user_info.telegram_id}\n"
                f"Telegram昵称: {user_info.fullname}\n"
                f"用户权限: {limits}\n"
                f"----------Jellyfin----------\n"
                f"用户名: {jellyfin_user['Name']}\n"
                f"上次登录: {last_login}\n"
                f"----------Score----------\n"
                f"积分: {score}\n"
                f"上次签到: {convert_to_china_timezone(checkin_time_v)}")
    
    @staticmethod
    @check_banned
    @command_warp
    async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = await UsersOperate.get_user(update.effective_user.id)
        if not user_info or user_info.account == "":
            return await update.message.reply_text("无Jellyfin账号与该Telegram账号绑定.")
        # 二次确认
        keyboard = [[InlineKeyboardButton("确认", callback_data='confirm_delete'),
                     InlineKeyboardButton("取消", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("你确定要删除账号吗？", reply_markup=reply_markup)
    
    @staticmethod
    @check_banned
    async def sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
        score_info = await ScoreOperate.get_score(update.effective_user.id)
        if not score_info:
            score_info = ScoreModel(telegram_id=update.effective_user.id)
            score_info = await ScoreOperate.add_score(score_info)
            score_info.checkin_time = 0
        last_sign_date = datetime.fromtimestamp(score_info.checkin_time).date()
        if last_sign_date == datetime.now().date():
            return await update.message.reply_text("今天已经签到过了.")
        points = random.randint(1, 10)
        score_info.score += points
        score_info.checkin_time = int(datetime.now().timestamp())
        await ScoreOperate.update_score(score_info)
        await update.message.reply_text(f"签到成功! 你获得了 {points} 积分. 当前积分: {score_info.score}.")
    
    @staticmethod
    @check_banned
    @command_warp
    async def bind(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != "private":
            return await update.message.reply_text("请在私聊中使用.")
        if len(context.args) != 2:
            return await update.message.reply_text("使用方法: /bind 用户名 密码")
        username, password = context.args
        user_client = JellyfinAPI(JellyfinConfig.BASE_URL, 2)
        try:
            jellyfin_user = await user_client.JellyfinReq.login(username, password)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to connect to Jellyfin.")
        if not jellyfin_user:
            return await update.message.reply_text("用户名或密码错误.")
        # logging.info(f"Jellyfin用户: {jellyfin_user}")
        eff_user = update.effective_user
        # 绑定 Telegram 账号
        user_info = await UsersOperate.get_user(eff_user.id)
        password_hash = get_password_hash(password)
        if user_info:
            if user_info.bind_id:
                return await update.message.reply_text("你已绑定一个Jellyfin账号。请先解绑")
            user_info.bind_id = jellyfin_user["User"]["Id"]
            user_info.account = username
            user_info.password = password_hash
            await UsersOperate.update_user(user_info)
            await update.message.reply_text(f"成功与Jellyfin用户 {username} 绑定.")
        else:
            user_info = UserModel(telegram_id=eff_user.id, username=eff_user.username, fullname=eff_user.full_name,
                                  account=username, password=password_hash, bind_id=jellyfin_user["User"]["Id"])
            await UsersOperate.add_user(user_info)
            await update.message.reply_text(f"成功与Jellyfin用户 {username} 绑定.")
    
    @staticmethod
    @check_banned
    @command_warp
    async def unbind(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = await UsersOperate.get_user(update.effective_user.id)
        if not user_info or not user_info.bind_id:
            return await update.effective_chat.send_message("该Telegram账号未绑定现有Jellyfin账号.")
        # 二次确认解绑
        keyboard = [[InlineKeyboardButton("确认", callback_data='confirm_unbind'),
                     InlineKeyboardButton("取消", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_chat.send_message(f"你确定与Jellyfin用户:{user_info.account}解绑吗?",
                                                 reply_markup=reply_markup)
    
    @staticmethod
    @check_banned
    @command_warp
    async def reset_pw(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != "private":
            return await update.message.reply_text("请在私聊中使用.")
        user_info = await UsersOperate.get_user(update.effective_user.id)
        if not user_info or not user_info.bind_id:
            return await update.effective_chat.send_message("该Telegram账号未绑定现有Jellyfin账号.")
        if len(context.args) != 2:
            return await update.message.reply_text("使用方法: /changepassword 原密码 新密码")
        old_pw, new_password = context.args[0], context.args[1]
        if not is_password_strong(new_password):
            return await update.message.reply_text("密码强度不够(需要至少8位字符，且包含至少一个小写字母和大写字母).")
        user_client = JellyfinAPI(JellyfinConfig.BASE_URL, 2)
        try:
            await user_client.JellyfinReq.login(user_info.account, old_pw)
            await client.Users.change_password(old_pw, new_password, user_info.bind_id)
            new_password_hash = get_password_hash(new_password)
            user_info.password = new_password_hash
            await UsersOperate.update_user(user_info)
            return await update.message.reply_text("密码修改成功.")
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]密码更改失败，请检查原密码是否正确.")
