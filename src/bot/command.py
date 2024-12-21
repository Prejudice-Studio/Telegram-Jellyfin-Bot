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
from src.config import BotConfig, JellyfinConfig
from src.database.cdk import CdkOperate
from src.database.score import ScoreModel, ScoreOperate
from src.database.user import UserModel, UsersOperate, UsersSessionFactory
from src.jellyfin.api import JellyfinAPI
from src.jellyfin_client import client
from src.utils import convert_to_china_timezone, get_password_hash


async def get_user_info(username: str | int):
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
    return None, None


# noinspection PyUnusedLocal
class AdminCommand:
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
            code_data = RegCode(code=code, usage_limit=usage_limit, expired_time=validity_hours)
            code_list.append(code)
            if validity_hours:
                code_data.expired_time = datetime.now().timestamp() + validity_hours * 3600
            RegCodeData.regCodes.append(code_data)
            RegCodeData.reg_dict[code] = code_data
        RegCodeData.save()
        text = f"Generated {quantity} registration codes.\n\n" + "".join(f"{code}\n" for code in code_list)
        
        if len(text) > 4096:
            file_buffer = BytesIO()
            file_buffer.write(text.encode('utf-8'))
            file_buffer.seek(0)
            await update.message.reply_document(document=file_buffer, filename="registration_codes.txt")
        else:
            # Send as a text message
            await update.message.reply_text(text)
    
    @staticmethod
    @check_admin
    async def checkinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            return await update.message.reply_text("使用方法: /checkinfo <jellyfin用户名/Telegram用户ID>")
        username = context.args[0]
        jellyfin_user, user_info = await get_user_info(username)
        if not jellyfin_user:
            return await update.message.reply_text("未发现用户.")
        last_login = convert_to_china_timezone(jellyfin_user.get("上次登录时间", "N/A"))
        # 检查积分和签到信息
        if not user_info:
            await update.message.reply_text(
                    f"发现Jellyfin用户，但未绑定Telegram.\n"
                    f"用户名: {jellyfin_user['Name']}\n"
                    f"上次登录: {last_login}\n")
        else:
            message = (
                f"----------Telegram----------\n"
                f"TelegramID: {user_info.TelegramID}\n"
                f"Telegram昵称: {user_info.TelegramFullName}\n"
                f"----------Jellyfin----------\n"
                f"用户名: {jellyfin_user['Name']}\n"
                f"上次登录: {last_login}\n"
                f"----------Score----------\n"
                f"积分: {user_info.score}\n"
                f"上次签到时间: {convert_to_china_timezone(user_info.last_sign_in)}"
            )
            
            if update.effective_chat.type == "private":
                message = message.replace(
                        f"Username: {jellyfin_user['Name']}",
                        f"Username: {jellyfin_user['Name']}\n"
                        f"Password: {user_info.bind.password}"
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
            client.jellyfin.delete_user(je_id)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to delete user.")
        # 删除 UserInfo.json 中的用户信息
        if user_info:
            UsersData.remove_user(user_info)
        await update.message.reply_text(f"Successfully deleted user {username} from Jellyfin and the system.")
    
    @staticmethod
    async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != BotConfig.ADMIN:
            return await update.message.reply_text("Unauthorized")
        if len(context.args) != 1:
            return await update.message.reply_text("Usage: /op <telegram_id>")
        tg_id = int(context.args[0])
        user_info = UsersData.get_user_by_id(tg_id)
        if not user_info:
            return await update.message.reply_text("User not found.")
        user_info.role = 1
        await update.message.reply_text(f"Successfully set {user_info.TelegramFullName} as an administrator.")
        UsersData.save()
    
    # 查看注册码
    @staticmethod
    @check_admin
    async def get_all_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
        code_list = RegCodeData.regCodes
        ret_text = ""
        for code in code_list:
            if (code.expired_time is None or code.expired_time > datetime.now().timestamp()) and code.usage_limit > 0:
                ret_text += (f"Code <code>{code.code}</code> Usage limit: {code.usage_limit} Expired time: "
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


# noinspection PyUnusedLocal
class UserCommand:
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
        
        cdk_info = await CdkOperate.get_cdk(reg_code)
        if not cdk_info:
            return await update.message.reply_text("注册码不可用")
        if cdk_info.limit <= 0:
            return await update.message.reply_text("注册码已被使用")
        if cdk_info.expired_time and cdk_info.expired_time < datetime.now().timestamp():
            return await update.message.reply_text("注册码已过期")
        # 检查 Jellyfin 是否已有该用户
        try:
            existing_users = await client.Users.get_users()
            if any(user['Name'] == username for user in existing_users):
                return await update.message.reply_text("用户名已存在.")
            ret_user = await client.Users.new_user(username, password)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to create user.")
        cdk_info.limit -= 1
        await CdkOperate.update_cdk(cdk_info)
        
        # 绑定 Telegram 和 Jellyfin 账号
        user_info = await UsersOperate.get_user(eff_user.id)
        password_hash = get_password_hash(password)
        if user_info:
            user_info.fullname = eff_user.full_name
            user_info.username = eff_user.username
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
        await update.message.reply_text(
                f"----------Telegram----------\n"
                f"TelegramID: {user_info.telegram_id}\n"
                f"Telegram昵称: {user_info.fullname}\n"
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
            # jellyfin_user = client.jellyfin.login(JellyfinConfig.BASE_URL, username, password)
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
            user_info.fullname = eff_user.full_name
            user_info.username = eff_user.username
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
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if not user_info or user_info.bind.username == "":
            return await update.effective_chat.send_message("该Telegram账号未绑定现有Jellyfin账号.")
        if len(context.args) != 2:
            return await update.message.reply_text("使用方法: /changepassword 原密码 新密码")
        old_pw, new_password = context.args[0], context.args[1]
        if old_pw != user_info.bind.password:
            return await update.message.reply_text("原密码错误.")
        try:
            ret = await client.Users.login(JellyfinConfig.BASE_URL, user_info.bind.username, user_info.bind.password)
            print(ret)
            p_data = {
                "CurrentPw": user_info.bind.password,
                "NewPw": new_password
            }
            print(client.jellyfin.get_user_settings())
            client.jellyfin.users("/Password", "POST", p_data)
            user_info.bind.password = new_password
            UsersData.save()
            return await update.message.reply_text("密码修改成功.")
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to change password.")
    
    @staticmethod
    @check_banned
    @command_warp
    async def get_pw(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != "private":
            return await update.message.reply_text("请在私聊中使用.")
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if not user_info or user_info.bind.username == "":
            return await update.effective_chat.send_message("该Telegram账号未绑定现有Jellyfin账号.")
        await update.message.reply_text(f"你的密码是: <code>{user_info.bind.password}</code>", parse_mode='HTML')
