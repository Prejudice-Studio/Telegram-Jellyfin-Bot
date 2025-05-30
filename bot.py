import multiprocessing
import os

import toml
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, InlineQueryHandler, ConversationHandler, \
    MessageHandler, filters

# noinspection PyUnresolvedReferences
import src.bot.admin as AdminCommand
# noinspection PyUnresolvedReferences
import src.bot.require as Require
# noinspection PyUnresolvedReferences
import src.bot.user as UserCommand
# noinspection PyUnresolvedReferences
from src.bot import callback
from src.bot.callback import user_reg_cb, user_reg_username, user_reg_pw, cancel
from src.bot.inline import inline_query
from src.bot.msg import forward_message
from src.config import BotConfig, Config
from src.logger import bot_logger
from src.webhook.api import run_flask

if Config.PROXY and Config.PROXY != "":
    os.environ['https_proxy'] = Config.PROXY
    os.environ['http_proxy'] = Config.PROXY


def run_bot():
    application = (Application.builder()
                   .token(BotConfig.BOT_TOKEN)
                   .concurrent_updates(True)
                   .connect_timeout(60)
                   .get_updates_connect_timeout(60)
                   .get_updates_read_timeout(60)
                   .get_updates_write_timeout(60)
                   .read_timeout(60)
                   .write_timeout(60)
                   .base_url(BotConfig.BASE_URL)
                   .build())

    # noinspection PyShadowingNames
    def load_handlers(application):
        if os.path.exists('command.toml'):
            data = toml.load('command.toml')
        else:
            data = toml.load('command.production.toml')
        # 用户命令
        for command, handler in data['user_commands'].items():
            application.add_handler(CommandHandler(command, eval(handler)))
        # 管理员命令
        for command, handler in data['admin_commands'].items():
            application.add_handler(CommandHandler(command, eval(handler)))
        # 回调
        for pattern, handler in data['callback_queries'].items():
            application.add_handler(CallbackQueryHandler(eval(handler), pattern=pattern))

    load_handlers(application)
    # 内联查询
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, forward_message))

    # 对话
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(user_reg_cb, pattern="user_reg_")
        ],
        states={
            1: [MessageHandler(filters=~filters.UpdateType.EDITED_MESSAGE, callback=user_reg_username)],
            2: [MessageHandler(filters=~filters.UpdateType.EDITED_MESSAGE, callback=user_reg_pw)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    bot_logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot_process = multiprocessing.Process(target=run_bot)
    api_process = multiprocessing.Process(target=run_flask)

    bot_process.start()
    api_process.start()

    bot_process.join()
    api_process.join()
