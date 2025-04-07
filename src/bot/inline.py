from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, helpers, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram.ext import ContextTypes

from src.bot import check_banned


@check_banned
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query or query == "help":
        results = [InlineQueryResultArticle(
            id=str(uuid4()),
            title="1.输入注册码来分享给别人一键注册！",
            input_message_content=InputTextMessageContent("输入help获取帮助")
        ), InlineQueryResultArticle(
            id=str(uuid4()),
            title="其他功能仍在更新ing",
            input_message_content=InputTextMessageContent("输入help获取帮助")
        ),
        ]
        await update.inline_query.answer(results)
        return

    if "cdk_" in query:
        split_result = query.split("\n", 1)
        cdk = split_result[0]
        send_text = split_result[1] if len(split_result) > 1 else ""
        bot = context.bot
        url = helpers.create_deep_linked_url(bot.username, cdk)
        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text="点击链接注册", url=url)
        )
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="点击发送（下面的所有提示内容均可更改哦）",
                reply_markup=keyboard,
                input_message_content=InputTextMessageContent(send_text),
            )
        ]
        await update.inline_query.answer(results)
        return
