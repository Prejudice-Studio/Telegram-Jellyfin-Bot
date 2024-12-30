import json
import random
import string
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from src.bot import check_banned, check_private, command_warp
from src.config import BotConfig, JellyfinConfig, ProgramConfig
from src.database.cdk import CdkModel, CdkOperate
from src.database.score import RedPacketModel, ScoreModel, ScoreOperate
from src.database.user import Role, UserModel, UsersOperate
from src.jellyfin.api import JellyfinAPI
from src.jellyfin_client import client
from src.logger import bot_logger
from src.utils import convert_to_china_timezone, generate_red_packets, get_password_hash, is_password_strong


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rep_text = (f"欢迎使用Telegram-Jellyfin-Bot，使用 <code>/help </code> 查看帮助\n"
                f"基本命令:\n"
                f"<code>/reg 账户 密码 注册码</code> 注册Jellyfin账号\n"
                f"<code>/info</code> 查看账号信息\n"
                f"<code>/bind 账户 密码</code> 绑定账户 <code>/unbind</code> 解绑\n"
                f"<code>/delete</code> 删除账号\n"
                f"<code>/sign</code> 每日签到\n"
                f"<code>/red</code> 发红包（仅限群聊内）\n"
                f"<code>/password 新密码</code> 更改账户密码\n"
                f"<code>/gencdk</code> 生成注册码\n"
                f"<code>/require BangumiID/链接/番剧名字</code> 申请增加番剧\n"
                f"<code>/checkrequire 请求ID</code> 查看番剧申请状态\n")
    
    # await update.message.reply_text(rep_text, parse_mode="HTML")
    # 菜单
    all_keyboard = [["/reg 注册账户", "/info 信息", "/bind 绑定账户", "/unbind 解绑"],
                    ["/delete 删除账户", "/sign 签到", "/red  红包", "/password 重置密码"],
                    ["/gencdk 生成cdk", "/require 番剧申请", "/checkrequire 番剧申请查询"],
                    ["/cancel 取消"]]
    reply_markup = ReplyKeyboardMarkup(all_keyboard, resize_keyboard=True)
    await update.message.reply_text(rep_text, reply_markup=reply_markup, parse_mode="HTML")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("操作取消.", reply_markup=ReplyKeyboardRemove())


@check_banned
@command_warp
@check_private
async def gen_cdk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not JellyfinConfig.USER_GEN_CDK:
        return await update.message.reply_text("用户注册码生成已关闭")
    score_data = await ScoreOperate.get_score(update.effective_user.id)
    if score_data is None or score_data.score < 200:
        return await update.message.reply_text("积分不足 (至少需要200积分).")
    quantity = 1
    if len(context.args) == 1:
        quantity = int(context.args[0])
    if quantity * 200 > score_data.score:
        return await update.message.reply_text(f"积分不足，当前积分: {score_data.score}")
    code_list = []
    for _ in range(quantity):
        code = f"reg_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}_prej"
        code_data = CdkModel(cdk=code, limit=1, expired_time=0)
        code_list.append(code)
        await CdkOperate.add_cdk(code_data)
    text = f"生成 {quantity} 个注册码\n\n" + "".join(f"{code}\n" for code in code_list)
    score_data.score -= quantity * 200
    await ScoreOperate.update_score(score_data)
    await update.message.reply_text(text)


@check_banned
@command_warp
@check_private
async def reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /reg <username> <password> <cdk>")
    username, password, reg_code = context.args[0], context.args[1], None
    if len(context.args) == 3:
        reg_code = context.args[2]
    eff_user = update.effective_user
    if not username.isalnum() or not password.isalnum():
        return await update.message.reply_text("用户名与密码不合法.")
    if not is_password_strong(password):
        return await update.message.reply_text("密码强度不够(需要至少8位字符，且包含至少一个小写字母和大写字母)。")
    user_info = await UsersOperate.get_user(eff_user.id)
    if user_info.bind_id:
        return await update.message.reply_text("你已绑定一个Jellyfin账号，无法注册。")
    cdk_info = None
    if not (user_info and user_info.role == Role.ORDINARY.value):
        # 非ORDINARY用户需要验证注册码
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
        bot_logger.error(f"Error: {e}")
        return await update.message.reply_text("[Server]创建用户失败(服务器故障或已经存在相同用户)。")
    if cdk_info:
        cdk_info.limit -= 1
        cdk_info.used_history += f"{str(eff_user.id)},"
        await CdkOperate.update_cdk(cdk_info)
    
    # 绑定 Telegram 和 Jellyfin 账号
    
    password_hash = get_password_hash(password)
    if user_info:
        user_info.account, user_info.password, user_info.bind_id = username, password_hash, ret_user[
            "Id"]
        if user_info.role == Role.SEA.value:
            user_info.role = Role.ORDINARY.value
        await UsersOperate.update_user(user_info)
    else:
        user_info = UserModel(telegram_id=eff_user.id, username=eff_user.username, fullname=eff_user.full_name,
                              account=username, password=password_hash, bind_id=ret_user["Id"], role=Role.ORDINARY.value)
        await UsersOperate.add_user(user_info)
    return await update.message.reply_text(f"注册成功，自动与Telegram绑定. 用户名: {username}")


# noinspection PyUnusedLocal
@check_banned
@command_warp
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if not user_info or not user_info.bind_id:
        return await update.message.reply_text("无Jellyfin账号与该Telegram账号绑定.")
    try:
        jellyfin_user = await client.Users.get_user(user_info.bind_id)
    except Exception as e:
        bot_logger.error(f"Error: {e}")
        return await update.message.reply_text("[Server]服务器发生错误，请检查日志")
    bot_logger.info(f"Jellyfin user: {jellyfin_user}")
    if not jellyfin_user:
        return await update.message.reply_text("用户未找到.")
    
    last_login = convert_to_china_timezone(jellyfin_user.get("LastLoginDate", "N/A"))
    score_data = await ScoreOperate.get_score(update.effective_user.id)
    if not score_data:
        score = 0
        checkin_time = "N/A"
    else:
        score, checkin_time = score_data.score, score_data.checkin_time
    checkin_time_v = checkin_time if checkin_time is not None else 0
    limits = Role(user_info.role).name
    await update.message.reply_text(
            f"----------Telegram----------\n"
            f"TelegramID: {user_info.telegram_id}\n"
            f"Telegram昵称: {user_info.fullname}\n"
            f"用户组: {limits}\n"
            f"----------Jellyfin----------\n"
            f"用户名: {jellyfin_user['Name']}\n"
            f"上次登录: {last_login}\n"
            f"----------Score----------\n"
            f"积分: {score}\n"
            f"上次签到: {convert_to_china_timezone(checkin_time_v)}")


# noinspection PyUnusedLocal
@check_banned
@command_warp
@check_private
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if not user_info or user_info.account == "":
        return await update.message.reply_text("无Jellyfin账号与该Telegram账号绑定。")
    # 二次确认
    keyboard = [[InlineKeyboardButton("确认", callback_data='confirm_delete'),
                 InlineKeyboardButton("取消", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("你确定要删除账号吗？", reply_markup=reply_markup)


# noinspection PyUnusedLocal
@check_banned
@check_private
async def sign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score_info = await ScoreOperate.get_score(update.effective_user.id)
    if not score_info:
        score_info = ScoreModel(telegram_id=update.effective_user.id)
        score_info = await ScoreOperate.add_score(score_info)
        score_info.checkin_time = 0
    last_sign_date = datetime.fromtimestamp(score_info.checkin_time).date()
    if last_sign_date == datetime.now().date():
        return await update.message.reply_text("今天已经签到过了。")
    points = random.randint(1, 10)
    score_info.score += points
    score_info.checkin_time = int(datetime.now().timestamp())
    await ScoreOperate.update_score(score_info)
    await update.message.reply_text(f"签到成功! 你获得了 {points} 积分。当前积分: {score_info.score}")


@check_banned
@command_warp
@check_private
async def bind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        return await update.message.reply_text("使用方法: /bind 用户名 密码")
    username, password = context.args
    user_client = JellyfinAPI(JellyfinConfig.BASE_URL, 2)
    try:
        jellyfin_user = await user_client.JellyfinReq.login(username, password)
    except Exception as e:
        bot_logger.error(f"Error: {e}")
        return await update.message.reply_text("[Server]Failed to connect to Jellyfin.")
    if not jellyfin_user:
        return await update.message.reply_text("用户名或密码错误.")
    eff_user = update.effective_user
    # 绑定 Telegram 账号
    user_info = await UsersOperate.get_user(eff_user.id)
    password_hash = get_password_hash(password)
    if user_info:
        if user_info.bind_id:
            return await update.message.reply_text("你已绑定一个Jellyfin账号。请先解绑")
        user_info.account, user_info.password, user_info.bind_id = username, password_hash, jellyfin_user["User"][
            "Id"]
        if user_info.role == Role.SEA.value:
            user_info.role = Role.ORDINARY.value
        await UsersOperate.update_user(user_info)
        await update.message.reply_text(f"成功与Jellyfin用户 {username} 绑定.")
    else:
        user_info = UserModel(telegram_id=eff_user.id, username=eff_user.username, fullname=eff_user.full_name,
                              account=username, password=password_hash, bind_id=jellyfin_user["User"]["Id"], role=Role.ORDINARY.value)
        await UsersOperate.add_user(user_info)
        await update.message.reply_text(f"成功与Jellyfin用户 {username} 绑定.")


# noinspection PyUnusedLocal
@check_banned
@command_warp
@check_private
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


@check_banned
@command_warp
@check_private
async def reset_pw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if not user_info or not user_info.bind_id:
        return await update.effective_chat.send_message("该Telegram账号未绑定现有Jellyfin账号.")
    if len(context.args) != 1:
        return await update.message.reply_text("使用方法: /password 新密码")
    new_password = context.args[0]
    if not is_password_strong(new_password):
        return await update.message.reply_text("密码强度不够(需要至少8位字符，且包含至少一个小写字母和大写字母).")
    try:
        await client.Users.change_password("", new_password, user_info.bind_id)
        user_info.password = get_password_hash(new_password)
        await UsersOperate.update_user(user_info)
        return await update.message.reply_text("密码修改成功.")
    except Exception as e:
        bot_logger.error(f"Error: {e}")
        return await update.message.reply_text("[Server]密码更改失败.")


@check_banned
async def red_packet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "group" and update.effective_chat.type != "supergroup":
        return await update.message.reply_text("请在群聊内使用")
    score_data = await ScoreOperate.get_score(update.effective_user.id)
    if len(context.args) < 2:
        return await update.message.reply_text("使用方法: /red {总金额} {个数} {Mode} 不填与0为随机，1为均分\n"
                                               "高级设置 /red {总金额} {个数} {Mode} {均值} {标准差} （控制红包金额分布）")
    total, count = context.args[0], context.args[1]
    mode = "0"
    mean, std_dev = 2, 9
    if len(context.args) >= 3:
        mode = context.args[2]
        if len(context.args) == 5:
            mean = int(context.args[3])
            std_dev = int(context.args[4])
    
    if not total.isdigit() or not count.isdigit() or not mode.isdigit():
        return await update.message.reply_text("请确保输入数字.")
    total, count, mode = int(total), int(count), int(mode)
    if total < 1 or count < 1:
        return await update.message.reply_text("请确保输入数字大于0.")
    if not score_data or score_data.score < total:
        return await update.message.reply_text("积分不足.")
    if count > total:
        return await update.message.reply_text("请确保红包数量大于红包总积分.")
    if mode == 0:
        red_data = generate_red_packets(total, count, mean, std_dev)
    elif mode == 1:
        if total % count != 0:
            return await update.message.reply_text("均分模式下请确保总积分能被红包数量整除.")
        red_data = [total // count for _ in range(count)]
    else:
        return await update.message.reply_text("模式错误.")
    new_packet = RedPacketModel(telegram_id=update.effective_user.id, amount=total, count=count, type=mode, current_amount=total,
                                create_time=int(datetime.now().timestamp()), data=json.dumps(red_data))
    await ScoreOperate.add_red_packet(new_packet)
    score_data.score -= total
    await ScoreOperate.update_score(score_data)
    keyboard = [[InlineKeyboardButton("点击领取红包", callback_data=f'red_{new_packet.id}')],
                [InlineKeyboardButton("查看红包详情", callback_data=f'redinfo_{new_packet.id}'),
                 InlineKeyboardButton("撤回红包", callback_data=f'withdraw_{new_packet.id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if BotConfig.REDPACKET_IMG != "":
        if ProgramConfig.REDPACKET_FILEID:
            await update.effective_chat.send_photo(ProgramConfig.REDPACKET_FILEID,
                                                   caption=f"用户{update.effective_user.full_name}发出了一个红包，总积分{total}, 数量{count}, 模式{mode}",
                                                   reply_markup=reply_markup)
        else:
            msg = await update.effective_chat.send_photo(open(BotConfig.REDPACKET_IMG, "rb"),
                                                         caption=f"用户{update.effective_user.full_name}发出了一个红包，总积分{total}, 数量{count}, 模式{mode}",
                                                         reply_markup=reply_markup)
            ProgramConfig.REDPACKET_FILEID = msg.photo[-1].file_id
    else:
        await update.effective_chat.send_message(
                f"用户{update.effective_user.full_name}发出了一个红包，总积分{total}, 数量{count}, 模式{mode}",
                reply_markup=reply_markup)
