import json
import logging
import os
import random
import string
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from jellyfin_apiclient_python import JellyfinClient
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 用户信息结构:
@dataclass
class BaseModel:
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


@dataclass
class JellyfinModel(BaseModel):
    username: str
    password: str
    ID: str


@dataclass
class UserModel(BaseModel):
    TelegramID: int
    TelegramFullName: str
    bind: JellyfinModel
    last_sign_in: str = ""
    score: int = 0
    role: int = 0


@dataclass
class UsersModel(BaseModel):
    userList: list[UserModel]
    
    def __post_init__(self):
        # 构建字典以便于查找
        self.user_dict = {user.TelegramID: user for user in self.userList}
    
    def get_user_by_id(self, telegram_id: int) -> Optional[UserModel]:
        # 使用字典查找用户
        return self.user_dict.get(telegram_id)


# 注册码息结构:
@dataclass
class RegCode(BaseModel):
    code: str
    usage_limit: int
    expired_time: Optional[int] = None


@dataclass
class RegCodesModel(BaseModel):
    regCodes: list[RegCode]
    
    def __post_init__(self):
        self.reg_dict = {reg_data.code: reg_data for reg_data in self.regCodes}
    
    def get_code_data(self, code: str) -> Optional[RegCode]:
        return self.reg_dict.get(code)


# 数据处理的类
class DataOperation:
    @staticmethod
    def load_user_info(filename: str = "Users.json") -> UsersModel:
        if not os.path.exists(filename):
            return UsersModel(userList=[])
        with open(filename, "r") as f:
            data = json.load(f)
            data = data["userList"]
            users = []
            for entry in data:
                bind_info = entry.get("bind", {})
                jellyfin_model = JellyfinModel(
                        username=bind_info.get("username", ""),
                        password=bind_info.get("password", ""),
                        ID=bind_info.get("ID", "")
                )
                user_model = UserModel(
                        TelegramID=entry.get("TelegramID", 0),
                        TelegramFullName=entry.get("TelegramFullName", ""),
                        score=entry.get("score", 0),
                        bind=jellyfin_model,
                        role=entry.get("role", 0),
                        last_sign_in=entry.get("last_sign_in", None)
                )
                users.append(user_model)
        
        return UsersModel(userList=users)
    
    @staticmethod
    def save_user_info(users_model: UsersModel, filename: str = "Users.json"):
        with open(filename, "w") as f:
            f.write(users_model.to_json())
    
    @staticmethod
    def load_reg_code(filename: str = "RegCode.json") -> RegCodesModel:
        if not os.path.exists(filename):
            return RegCodesModel(regCodes=[])
        with open(filename, "r") as f:
            data = json.load(f)
            data = data["regCodes"]
            reg_codes = []
            for entry in data:
                reg_code = RegCode(
                        code=entry.get("code", ""),
                        usage_limit=entry.get("usage_limit", 0),
                        expired_time=entry.get("expired_time", None)
                )
                reg_codes.append(reg_code)
        return RegCodesModel(regCodes=reg_codes)
    
    @staticmethod
    def save_reg_code(codes_model: RegCodesModel, filename: str = "RegCode.json"):
        with open(filename, "w") as f:
            f.write(codes_model.to_json())


UsersData = DataOperation.load_user_info("Users.json")
RegCodeData = DataOperation.load_reg_code("RegCode.json")

# 连接信息
server_url = 'YOUR_SERVER_IP:PORT'
# account = 'Administrators Username'
# password = 'Administrators Password'
access_token = 'Your_Jellyfin_Token'

# 连接服务器
# 初始化 Jellyfin 客户端
client = JellyfinClient()
client.config.data["auth.ssl"] = False
client.config.data["app.name"] = 'telegram'
client.config.data["app.version"] = '0.0.1'
client.auth.connect_to_address(server_url)
auth_config = {"Servers": [{"AccessToken": access_token, "address": server_url}]}
client.authenticate(auth_config, discover=False)
client.start()


# 注册用户
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
    existing_users = client.jellyfin.get_users()
    if any(user['Name'] == username for user in existing_users):
        return await update.message.reply_text("The username already exists.")
    ret_user = client.jellyfin.new_user(username, password)
    reg_code_info.usage_limit -= 1
    DataOperation.save_reg_code(RegCodeData)
    
    # 绑定 Telegram 和 Jellyfin 账号
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if user_info:
        user_info.bind = JellyfinModel(username=username, password=password, ID=ret_user["Id"])
        user_info.TelegramFullName = update.effective_user.full_name
    else:
        user_info = UserModel(TelegramID=update.effective_user.id, TelegramFullName=update.effective_user.full_name,
                              bind=JellyfinModel(username=username, password=password, ID=ret_user["Id"]))
        UsersData.userList.append(user_info)
        UsersData.user_dict[update.effective_user.id] = user_info
    await update.message.reply_text(f"Registration successful. Username: {username}")
    DataOperation.save_user_info(UsersData)


# 查询用户信息
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if not user_info:
        return await update.message.reply_text("No Jellyfin account is bound to this Telegram account.")
    try:
        jellyfin_user = client.jellyfin.get_user(user_info.bind.ID)
    except Exception as e:
        logging.error(f"Error: {e}")
        jellyfin_user = None
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
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if not user_info:
        return await update.message.reply_text("No Jellyfin account is bound to this Telegram account.")
    # 二次确认
    keyboard = [[InlineKeyboardButton("Confirm", callback_data='confirm_delete'),
                 InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Are you sure you want to delete the account", reply_markup=reply_markup)


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if user_info:
        ret = client.jellyfin.delete_user(user_info.bind.ID)
        logging.info(f"Delete user: {ret}")
        UsersData.userList.remove(user_info)
        UsersData.user_dict.pop(update.effective_user.id)
        await update.message.reply_text("Account deleted successful.")
    else:
        await update.message.reply_text("Can't find the account.")


# 签到功能
async def sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if not user_info:
        return await update.message.reply_text("No Jellyfin account is bound to this Telegram account.")
    
    today = datetime.now().date().strftime("%Y-%m-%d")
    if user_info.last_sign_in == today:
        return await update.message.reply_text("You have already signed in today.")
    
    points = random.randint(1, 10)
    user_info.score += points
    user_info.last_sign_in = today
    DataOperation.save_user_info(UsersData)
    await update.message.reply_text(f"Sign-in successful! You earned {points} point(s). Current points: {user_info.score}.")


# 绑定已有 Jellyfin 账号
async def bind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("Usage: /bind <username> <password>")
    username, password = context.args
    jellyfin_user = client.jellyfin.login(server_url, username, password)
    if not jellyfin_user:
        return await update.message.reply_text("username or password error.")
    logging.info(f"Jellyfin user: {jellyfin_user}")
    # 绑定 Telegram 账号
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if user_info:
        await update.message.reply_text("You have already bound a Jellyfin account.")
    else:
        user_info = UserModel(TelegramID=update.effective_user.id, TelegramFullName=update.effective_user.full_name,
                              bind=JellyfinModel(username=username, password=password, ID=jellyfin_user["User"]["Id"]))
        UsersData.userList.append(user_info)
        UsersData.user_dict[update.effective_user.id] = user_info
        DataOperation.save_user_info(UsersData)
        await update.message.reply_text(f"Successful binding {username}.")


# 解绑 Jellyfin 账号
async def unbind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.effective_user.send_message("Usage: /unbind <username> <password>")
    username, password = context.args
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if not user_info:
        return await update.effective_user.send_message("This Telegram account is not bound to the specified Jellyfin account.")
    # 二次确认解绑
    keyboard = [[InlineKeyboardButton("Confirm", callback_data='confirm_unbind'),
                 InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_user.send_message(f"Are you sure you want to unbind your Jellyfin account:{username}?",
                                             reply_markup=reply_markup)


async def confirm_unbind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = UsersData.get_user_by_id(update.effective_user.id)
    if user_info:
        UsersData.user_dict.pop(update.effective_user.id)
        UsersData.userList.remove(user_info)
        DataOperation.save_user_info(UsersData)
        await update.effective_user.send_message("Unbind successful.")
    else:
        await update.effective_user.send_message("No bound Jellyfin account found.")


# 管理员生成注册码
async def summon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user_info = UsersData.get_user_by_id(tg_id)
    if user_info.role != 1 and tg_id != ADMIN:
        return await update.message.reply_text("Unauthorized")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /summon <usage_limit> <quantity> [validity_hours]")
    
    usage_limit = int(context.args[0])
    quantity = int(context.args[1])
    validity_hours = int(context.args[2]) if len(context.args) > 2 else None
    code_list = []
    for _ in range(quantity):
        code = f"reg_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}"
        code_data = RegCode(code=code, usage_limit=usage_limit, expired_time=validity_hours)
        code_list.append(code)
        if validity_hours:
            code_data.expired_time = datetime.now().timestamp() + validity_hours * 3600
        RegCodeData.regCodes.append(code_data)
        RegCodeData.reg_dict[code] = code_data
    DataOperation.save_reg_code(RegCodeData)
    await update.message.reply_text(f"Generated {quantity} registration codes.\n\n" + "".join(f"{code}\n" for code in code_list))


# 管理员查看用户信息
async def checkinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user_info = UsersData.get_user_by_id(tg_id)
    if user_info.role != 1 and tg_id != ADMIN:
        return await update.message.reply_text("Unauthorized")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /checkinfo <jellyfin_username/telegram_userid>")
    username = context.args[0]
    je_id = None
    if username.isdigit():
        # 根据tg id 查询
        user_info = UsersData.get_user_by_id(int(username))
        if user_info:
            je_id = user_info.bind.ID
    if not je_id:
        all_user = client.jellyfin.get_users()
        je_data = next((u for u in all_user if u["Name"] == username), None)
        if not je_data:
            return await update.message.reply_text("Jellyfin user not found.")
        je_id = je_data["Id"]
    try:
        jellyfin_user = client.jellyfin.get_user(je_id)
    except Exception as e:
        logging.error(f"Error: {e}")
        jellyfin_user = None
    if not jellyfin_user:
        return await update.message.reply_text("User not found.")
    last_login = jellyfin_user.get("LastLoginDate", "N/A")
    device_name = jellyfin_user.get("LastLoginDeviceName", "N/A")
    # 检查积分和签到信息
    user_info = next((u for u in UsersData.userList if u.bind.ID == je_id), None)
    if not user_info:
        await update.message.reply_text(
                f"User found in Jellyfin, but not in the system.\nUsername: {jellyfin_user['Name']}\nLast Login: {last_login}\nLast Device: {device_name}")
    else:
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


# 管理员删除 Jellyfin 用户
async def deleteAccountBy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user_info = UsersData.get_user_by_id(tg_id)
    if user_info.role != 1 and tg_id != ADMIN:
        return await update.message.reply_text("Unauthorized")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /deleteAccountBy <jellyfin_username/telegram_userid>")
    username = context.args[0]
    je_id = None
    if username.isdigit():
        # 根据tg id 查询
        user_info = UsersData.get_user_by_id(int(username))
        if user_info:
            je_id = user_info.bind.ID
    if not je_id:
        all_user = client.jellyfin.get_users()
        je_data = next((u for u in all_user if u["Name"] == username), None)
        if not je_data:
            return await update.message.reply_text("Jellyfin user not found.")
        je_id = je_data["Id"]
    try:
        jellyfin_user = client.jellyfin.get_user(je_id)
    except Exception as e:
        logging.error(f"Error: {e}")
        jellyfin_user = None
    if not jellyfin_user:
        return await update.message.reply_text("User not found.")
    
    client.jellyfin.delete_user(je_id)
    # 删除 UserInfo.json 中的用户信息
    user_info2 = next((u for u in UsersData.userList if u.bind.ID == je_id), None)
    if user_info2:
        UsersData.user_dict.pop(user_info2.TelegramID)
        UsersData.userList.remove(user_info2)
        DataOperation.save_user_info(UsersData)
    await update.message.reply_text(f"Successfully deleted user {username} from Jellyfin and the system.")


# 处理确认删除和解绑的回调
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "confirm_delete":
        await confirm_delete(update, context)
    elif query.data == "confirm_unbind":
        await confirm_unbind(update, context)


# 设置管理员
async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN:
        return await update.message.reply_text("Unauthorized")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /op <telegram_id>")
    tg_id = int(context.args[0])
    user_info = UsersData.get_user_by_id(tg_id)
    if not user_info:
        return await update.message.reply_text("User not found.")
    user_info.role = 1
    DataOperation.save_user_info(UsersData)


# 查看注册码
async def get_all_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user_info = UsersData.get_user_by_id(tg_id)
    if user_info.role != 1 and tg_id != ADMIN:
        return await update.message.reply_text("Unauthorized")
    code_list = RegCodeData.regCodes
    ret_text = ""
    for code in code_list:
        if (code.expired_time is None or code.expired_time > datetime.now().timestamp()) and code.usage_limit > 0:
            ret_text += (f"Code <code>{code.code}</code> Usage limit: {code.usage_limit} Expired time: "
                         f"{code.expired_time if code.expired_time is not None else 'NoExpired'}\n")
    
    await update.message.reply_text("All registration codes:\n\n" + ret_text, parse_mode='HTML')


# 绑定命令和处理程序
def main():
    dp = (Application.builder().token("Your_Telegram_Bot_Api_Token").concurrent_updates(True).build())
    
    dp.add_handler(CommandHandler("reg", reg))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("delete", delete_account))
    dp.add_handler(CommandHandler("sign", sign))
    dp.add_handler(CommandHandler("bind", bind))
    dp.add_handler(CommandHandler("unbind", unbind))
    dp.add_handler(CommandHandler("summon", summon))  # 管理员生成注册码
    dp.add_handler(CommandHandler("checkinfo", checkinfo))  # 管理员查看用户信息
    dp.add_handler(CommandHandler("deleteAccountBy", deleteAccountBy))  # 管理员删除用户
    dp.add_handler(CommandHandler("op", set_admin))  # 设置管理员
    dp.add_handler(CommandHandler("regcodes", get_all_code))  #
    
    dp.add_handler(CallbackQueryHandler(button))
    print("Bot started")
    dp.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
