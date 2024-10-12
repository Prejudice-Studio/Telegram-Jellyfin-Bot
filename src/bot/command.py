import logging
import random
import string
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot import check_admin, command_warp
from src.config import BotConfig, JellyfinConfig
from src.jellyfin_client import RegCodeData, UsersData, client
from src.model import JellyfinModel, RegCode, UserModel


async def get_user_info(username: str):
    """
    获取 Jellyfin 用户信息
    :param username: Telegram ID/Fullname or Jellyfin username
    :return:
    """
    je_id = None
    if username.isdigit():
        # 根据tg id 查询
        if user_info := UsersData.get_user_by_id(int(username)):
            je_id = user_info.bind.ID
        elif user_info := next((u for u in UsersData.userList if username == u.TelegramFullName), None):
            je_id = user_info.bind.ID
    if not je_id:
        try:
            all_user = client.jellyfin.get_users()
        except Exception as e:
            logging.error(f"Error: {e}")
            return None, None
        je_data = next((u for u in all_user if u["Name"] == username), None)
        if not je_data:
            return None, None
        je_id = je_data["Id"]
    try:
        jellyfin_user = client.jellyfin.get_user(je_id)
        user_info = next((u for u in UsersData.userList if u.bind.ID == je_id), None)
        return jellyfin_user, user_info
    except Exception as e:
        logging.error(f"Error: {e}")
        return None, None


# noinspection PyUnusedLocal
class AdminCommand:
    
    # 管理员生成注册码
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
        await update.message.reply_text(f"Generated {quantity} registration codes.\n\n" + "".join(f"{code}\n" for code in code_list))
    
    # 管理员查看用户信息
    @staticmethod
    async def checkinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            return await update.message.reply_text("Usage: /checkinfo <jellyfin_username>")
        username = context.args[0]
        jellyfin_user, user_info = await get_user_info(username)
        if not jellyfin_user:
            return await update.message.reply_text("User not found.")
        last_login = jellyfin_user.get("LastLoginDate", "N/A")
        device_name = jellyfin_user.get("LastLoginDeviceName", "N/A")
        # 检查积分和签到信息
        if not user_info:
            await update.message.reply_text(
                    f"User found in Jellyfin, but not bind Telegram.\n"
                    f"Username: {jellyfin_user['Name']}\n"
                    f"Last Login: {last_login}\n"
                    f"Last Device: {device_name}")
        else:
            await update.message.reply_text(
                    f"----------Telegram----------\n"
                    f"TelegramID: {user_info.TelegramID}\n"
                    f"TelegramFullName: {user_info.TelegramFullName}\n"
                    f"----------Jellyfin----------\n"
                    f"Username: {jellyfin_user['Name']}\n"
                    f"Password: {user_info.bind.password}\n"
                    f"Last Login: {last_login}\n"
                    f"Last Device: {device_name}\n"
                    f"----------Score----------\n"
                    f"Score: {user_info.score}\n"
                    f"Last Sign-in: {user_info.last_sign_in}")
    
    # 管理员删除 Jellyfin 用户
    @staticmethod
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
    
    # 设置管理员
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
                             f"{code.expired_time if code.expired_time is not None else 'NoExpired'}\n")
        await update.message.reply_text("All registration codes:\n\n" + ret_text, parse_mode='HTML')


# noinspection PyUnusedLocal
class UserCommand:
    # 注册用户
    @staticmethod
    @command_warp
    async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 3:
            return await update.message.reply_text("Usage: /reg <username> <password> <reg_code>")
        username, password, reg_code = context.args
        if not username.isalnum() or not password.isalnum():
            return await update.message.reply_text("The username and password must be alphanumeric.")
        
        reg_code_info = RegCodeData.get_code_data(reg_code)
        if not reg_code_info:
            return await update.message.reply_text("Unavailable registration code")
        if reg_code_info.usage_limit <= 0:
            return await update.message.reply_text("The registration code has been used up")
        if reg_code_info.expired_time and reg_code_info.expired_time < datetime.now().timestamp():
            return await update.message.reply_text("The registration code has expired")
        # 检查 Jellyfin 是否已有该用户
        try:
            existing_users = client.jellyfin.get_users()
            if any(user['Name'] == username for user in existing_users):
                return await update.message.reply_text("The username already exists.")
            ret_user = client.jellyfin.new_user(username, password)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to create user.")
        reg_code_info.usage_limit -= 1
        RegCodeData.save()
        
        # 绑定 Telegram 和 Jellyfin 账号
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if user_info:
            user_info.bind = JellyfinModel(username=username, password=password, ID=ret_user["Id"])
            user_info.TelegramFullName = update.effective_user.full_name
            UsersData.save()
        else:
            user_info = UserModel(TelegramID=update.effective_user.id, TelegramFullName=update.effective_user.full_name,
                                  bind=JellyfinModel(username=username, password=password, ID=ret_user["Id"]))
            UsersData.add_user(user_info)
        await update.message.reply_text(f"Registration successful. Username: {username}")
    
    # 查询用户信息
    @staticmethod
    @command_warp
    async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if not user_info or user_info.bind.username == "":
            return await update.message.reply_text("No Jellyfin account is bound to this Telegram account.")
        try:
            jellyfin_user = client.jellyfin.get_user(user_info.bind.ID)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to connect to Jellyfin.")
        logging.info(f"Jellyfin user: {jellyfin_user}")
        if not jellyfin_user:
            return await update.message.reply_text("Jellyfin user not found.")
        
        last_login = jellyfin_user.get("LastLoginDate", "N/A")
        device_name = jellyfin_user.get("LastLoginDeviceName", "N/A")
        await update.message.reply_text(
                f"----------Telegram----------\n"
                f"TelegramID: {user_info.TelegramID}\n"
                f"TelegramFullName: {user_info.TelegramFullName}\n"
                f"----------Jellyfin----------\n"
                f"Username: {jellyfin_user['Name']}\n"
                f"Last Login: {last_login}\n"
                f"Last Device: {device_name}\n"
                f"----------Score----------\n"
                f"Score: {user_info.score}\n"
                f"Last Sign-in: {user_info.last_sign_in}")
    
    # 删除账号
    @staticmethod
    @command_warp
    async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if not user_info or user_info.bind.username == "":
            return await update.message.reply_text("No Jellyfin account is bound to this Telegram account.")
        # 二次确认
        keyboard = [[InlineKeyboardButton("Confirm", callback_data='confirm_delete'),
                     InlineKeyboardButton("Cancel", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Are you sure you want to delete the account", reply_markup=reply_markup)
    
    # 签到功能
    @staticmethod
    async def sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if not user_info:
            user_info = UserModel(TelegramID=update.effective_user.id, TelegramFullName=update.effective_user.full_name,
                                  bind=JellyfinModel(username="", password="", ID=""))
            UsersData.add_user(user_info)
        
        today = datetime.now().date().strftime("%Y-%m-%d")
        if user_info.last_sign_in == today:
            return await update.message.reply_text("You have already signed in today.")
        
        points = random.randint(1, 10)
        user_info.score += points
        user_info.last_sign_in = today
        UsersData.save()
        await update.message.reply_text(f"Sign-in successful! You earned {points} point(s). Current points: {user_info.score}.")
    
    # 绑定已有 Jellyfin 账号
    @staticmethod
    @command_warp
    async def bind(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 2:
            return await update.message.reply_text("Usage: /bind <username> <password>")
        username, password = context.args
        try:
            jellyfin_user = client.jellyfin.login(JellyfinConfig.BASE_URL, username, password)
        except Exception as e:
            logging.error(f"Error: {e}")
            return await update.message.reply_text("[Server]Failed to connect to Jellyfin.")
        if not jellyfin_user:
            return await update.message.reply_text("username or password error.")
        logging.info(f"Jellyfin user: {jellyfin_user}")
        # 绑定 Telegram 账号
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if user_info:
            if user_info.bind.username == "":
                user_info.bind = JellyfinModel(username=username, password=password, ID=jellyfin_user["User"]["Id"])
                user_info.TelegramFullName = update.effective_user.full_name
                await update.message.reply_text(f"Successful binding {username}.")
                UsersData.save()
            else:
                await update.message.reply_text("You have already bound a Jellyfin account.")
        else:
            user_info = UserModel(TelegramID=update.effective_user.id, TelegramFullName=update.effective_user.full_name,
                                  bind=JellyfinModel(username=username, password=password, ID=jellyfin_user["User"]["Id"]))
            UsersData.add_user(user_info)
            await update.message.reply_text(f"Successful binding {username}.")
    
    # 解绑 Jellyfin 账号
    @staticmethod
    @command_warp
    async def unbind(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_info = UsersData.get_user_by_id(update.effective_user.id)
        if not user_info or user_info.bind.username == "":
            return await update.effective_user.send_message("This Telegram account is not bound to the specified Jellyfin account.")
        # 二次确认解绑
        keyboard = [[InlineKeyboardButton("Confirm", callback_data='confirm_unbind'),
                     InlineKeyboardButton("Cancel", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_user.send_message(f"Are you sure you want to unbind your Jellyfin account:{user_info.bind.username}?",
                                                 reply_markup=reply_markup)
