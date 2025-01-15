import json
import re
from datetime import datetime
from urllib.parse import urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot import check_admin, check_banned, check_private
from src.config import BotConfig
from src.database.bangumi import BangumiOperate, BangumiRequireModel, ReqStatue
from src.database.user import Role, UsersOperate
from src.init_check import Bangumi_client
from src.utils import convert_to_china_timezone


async def get_bgm_info(bgm_id: str) -> str | None:
    try:
        id_info = await Bangumi_client.Subject.get_subject(bgm_id)
    except Exception:
        return None
    if not id_info:
        return None
    rep_text = (f"番剧信息:\n"
                f"<b>番剧名:</b> {id_info['name_cn']}\n"
                f"<b>原名:</b> {id_info['name']}\n"
                f"<b>上映日期:</b> {id_info['date']}\n"
                f"<b>集数:</b> {id_info['total_episodes']}\n"
                f"<b>简介:</b> {id_info['summary']}\n"
                f"<b>tag:</b> #{' #'.join(id_info['meta_tags'])}\n\n\n"
                f"<b>确认番剧信息是否正确，点击确认后将提交给管理员</b>")
    return rep_text


@check_banned
@check_private
async def check_require(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info.role not in {Role.STAR.value, Role.ADMIN.value}:
        return await update.message.reply_text("您没有权限使用此功能")
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await update.message.reply_text("Usage: /check_require <require_id>")
    req_id = int(context.args[0])
    req_info = await BangumiOperate.get_req_bgm(req_id)
    if not req_info:
        return await update.message.reply_text("请求ID不存在")
    if req_info.telegram_id != update.effective_user.id and user_info.role != Role.ADMIN.value:
        return await update.message.reply_text("您没有权限查看此请求")
    other_info = json.loads(str(req_info.other_info))
    rep_text = (f"来自 {'您' if user_info.role != update.effective_user.full_name else '用户 ' + str(req_info.telegram_id)} 的请求:\n"
                f"番剧名: {other_info['name_cn']}\n"
                f"上映日期: {other_info['date']}\n"
                f"集数: {other_info['total_episodes']}\n"
                f"Bgm链接: https://bgm.tv/subject/{req_info.bangumi_id}\n"
                f"当前状态: {str(ReqStatue(req_info.status)).replace('ReqStatue.', '')}")
    if user_info.role == Role.ADMIN.value:
        keyboard = [
            [InlineKeyboardButton("接受", callback_data=f'reqa_accepted_{req_info.id}'),
             InlineKeyboardButton("拒绝", callback_data=f'reqa_rejected_{req_info.id}'),
             InlineKeyboardButton("完成", callback_data=f'reqa_completed_{req_info.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(rep_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(rep_text)


@check_banned
@check_private
async def require(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info.role != Role.STAR.value and user_info.role != Role.ADMIN.value:
        return await update.message.reply_text("您没有权限使用此功能")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /require <message> bangumi链接或者完整的番剧名字")
    bgm, bgm_id = context.args[0], None
    if bgm.startswith("https://bgm.tv/subject"):
        # bangumi链接
        parsed_url = urlparse(bgm)
        path_parts = parsed_url.path.split("/")
        bgm_id = path_parts[-1] if path_parts and path_parts[-1].isdigit() else None
    elif bgm.startswith("https://bangumi.tv/subject"):
        # 第二个域名
        parsed_url = urlparse(bgm)
        path_parts = parsed_url.path.split("/")
        bgm_id = path_parts[-1] if path_parts and path_parts[-1].isdigit() else None
    elif bgm.isdigit():
        bgm_id = bgm_id
    else:
        # 关键词搜索
        try:
            se_info = await Bangumi_client.Subject.search(bgm)
        except Exception as e:
            return await update.message.reply_text(f"获取番剧信息失败: {e}")
        if not se_info:
            return await update.message.reply_text("未找到番剧信息")
        keyboard = []
        for item in se_info["list"]:
            keyboard.append([InlineKeyboardButton(f"{item['name_cn']}", callback_data=f'reqb_{item["id"]}')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        return await update.message.reply_text("请选择番剧", reply_markup=reply_markup)
    if not bgm_id or not bgm_id.isdigit():
        return await update.message.reply_text("番剧ID错误")
    keyboard = [[InlineKeyboardButton("确认提交", callback_data=f'req_{bgm_id}'),
                 InlineKeyboardButton("取消提交", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    rep_text = await get_bgm_info(bgm_id)
    await update.message.reply_text(rep_text, reply_markup=reply_markup, parse_mode='HTML')


# noinspection PyUnusedLocal
async def require_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_info = await UsersOperate.get_user(update.effective_user.id)
    if user_info.role != Role.STAR.value and user_info.role != Role.ADMIN.value:
        return await query.answer("您没有权限使用此功能")
    bgm_id = query.data.split("_")[1]
    rep_text = await get_bgm_info(bgm_id)
    keyboard = [[InlineKeyboardButton("确认提交", callback_data=f'req_{bgm_id}'),
                 InlineKeyboardButton("取消提交", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(rep_text, reply_markup=reply_markup, parse_mode='HTML')


async def require_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_info = await UsersOperate.get_user(query.from_user.id)
    if user_info.role != Role.STAR.value and user_info.role != Role.ADMIN.value:
        return await query.answer("您没有权限使用此功能")
    bgm_id = query.data.split("_")[1]
    if bgm_info := await BangumiOperate.is_bgm_exist(int(bgm_id)):
        await query.edit_message_text(f"已经有人请求过此番剧, 请求状态: {str(ReqStatue(bgm_info.status)).replace('ReqStatue.', '')}")
        return await query.answer()
    id_info = await Bangumi_client.Subject.get_subject(bgm_id)
    req_info = BangumiRequireModel(
            telegram_id=query.from_user.id,
            bangumi_id=int(bgm_id),
            status=ReqStatue.UNHANDLED.value,
            timestamp=int(datetime.now().timestamp()),
            other_info=json.dumps(id_info)
    )
    await BangumiOperate.add_req_bgm(req_info)
    rep_text = (f"来自 {query.from_user.full_name} 的请求:\n"
                f"番剧名: {id_info['name_cn']}\n"
                f"上映日期: {id_info['date']}\n"
                f"集数 {id_info['total_episodes']}\n"
                f"Bgm链接: https://bgm.tv/subject/{req_info.bangumi_id}\n"
                f"当前状态: 未处理")
    keyboard = [[InlineKeyboardButton("接受", callback_data=f'reqa_accepted_{req_info.id}'),
                 InlineKeyboardButton("拒绝", callback_data=f'reqa_rejected_{req_info.id}'),
                 InlineKeyboardButton("完成", callback_data=f'reqa_completed_{req_info.id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=BotConfig.ADMIN, text=rep_text, reply_markup=reply_markup)
    await query.answer()
    await query.edit_message_text(f"提交成功，Require ID <code>{req_info.id}</code>", parse_mode='HTML')


@check_admin
async def require_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action, bgm_id = query.data.split("_")[1], query.data.split("_")[2]
    action = action.upper()
    req_info = await BangumiOperate.get_req_bgm(int(bgm_id))
    if not req_info:
        return await query.answer("请求不存在")
    status_map = {
        "ACCEPTED": (ReqStatue.ACCEPTED.value, "已接受"),
        "REJECTED": (ReqStatue.REJECTED.value, "已拒绝"),
        "COMPLETED": (ReqStatue.COMPLETED.value, "已完成"),
    }
    if action in status_map:
        target_info, response_text = status_map[action]
        if req_info.status == ReqStatue[action.upper()].value:
            return await query.answer(f"请求已经是{response_text}")
        req_info.status = target_info
        await BangumiOperate.update_req_bgm(req_info)
        # noinspection PyUnresolvedReferences
        ori_msg = query.message.text
        ori_msg = re.sub(r"当前状态:\s*.*", f"当前状态: {response_text}", ori_msg)
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("接受", callback_data=f'reqa_accepted_{req_info.id}'),
                InlineKeyboardButton("拒绝", callback_data=f'reqa_rejected_{req_info.id}'),
                InlineKeyboardButton("完成", callback_data=f'reqa_completed_{req_info.id}')
            ]
        ])
        other_info = json.loads(str(req_info.other_info))
        await query.edit_message_text(ori_msg, reply_markup=reply_markup)
        await context.bot.send_message(req_info.telegram_id, f"您的请求ID: {req_info.id} 发生变化\n"
                                                             f"番名：{other_info['name_cn']}\n"
                                                             f"当前状态:{response_text}")
        await query.answer(response_text)
    else:
        await query.answer("未知操作")


# noinspection PyUnusedLocal
@check_admin
async def require_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req_list = await BangumiOperate.get_all_handle_list()
    rep_text = ""
    for req in req_list:
        other_info = json.loads(str(req.other_info))
        tg_info = await UsersOperate.get_user(req.telegram_id)
        rep_text += (f"来自 <b>{tg_info.fullname}</b> 的请求:\n"
                     f"请求ID: <code>{req.id}</code>\n"
                     f"用户ID: <code>{tg_info.telegram_id}</code>\n"
                     f"Username: @{tg_info.username if tg_info.username else "N/A"}\n"
                     f"发起时间: {convert_to_china_timezone(req.timestamp)}\n"
                     f"<b>番剧名</b>: {other_info['name_cn']}\n"
                     f"<b>上映日期</b>: {other_info['date']}\n"
                     f"<b>集数</b>: {other_info['total_episodes']}\n"
                     f"<b>Bgm链接</b>: https://bgm.tv/subject/{req.bangumi_id}\n"
                     f"当前状态: <b>{str(ReqStatue(req.status)).replace('ReqStatue.', '')}</b>\n"
                     f"============================\n")
    while len(rep_text) > 4096:
        part_text = rep_text[:4096]
        last_newline_index = part_text.rfind('\n')
        if last_newline_index != -1:
            part_text = rep_text[:last_newline_index]
        else:
            part_text = rep_text[:4096]
        await update.message.reply_text(part_text, parse_mode='HTML')
        rep_text = rep_text[len(part_text):]
    if rep_text:
        await update.message.reply_text(rep_text, parse_mode='HTML')
