import multiprocessing
import os

import toml
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

# noinspection PyUnresolvedReferences
import src.bot.admin as AdminCommand
# noinspection PyUnresolvedReferences
import src.bot.require as Require
# noinspection PyUnresolvedReferences
import src.bot.user as UserCommand
# noinspection PyUnresolvedReferences
from src.bot import callback
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
    
    def load_handlers(application):
        if os.path.exists('command.toml'):
            data = toml.load('command.toml')
        else:
            data = toml.loads("""
            [user_commands]
            start = "UserCommand.start"
            help = "UserCommand.start"
            reg = "UserCommand.reg"
            info = "UserCommand.info"
            delete = "UserCommand.delete_account"
            sign = "UserCommand.sign"
            bind = "UserCommand.bind"
            unbind = "UserCommand.unbind"
            password = "UserCommand.reset_pw"
            gencdk = "UserCommand.gen_cdk"
            red = "UserCommand.red_packet"
            require = "Require.require"
            checkrequire = "Require.check_require"
            cancel = "UserCommand.cancel"
            
            [admin_commands]
            shelp = "AdminCommand.shelp"
            summon = "AdminCommand.summon"
            checkinfo = "AdminCommand.checkinfo"
            deleteAccount = "AdminCommand.delete_account"
            setGroup = "AdminCommand.set_group"
            cdks = "AdminCommand.get_all_cdk"
            update = "AdminCommand.update"
            setScore = "AdminCommand.set_score"
            setCDKgen = "AdminCommand.set_gen_cdk"
            deleteCDK = "AdminCommand.del_cdk"
            setCdkLimit = "AdminCommand.set_cdk_limit"
            setCdkTime = "AdminCommand.set_cdk_time"
            requireList = "Require.require_list"
            resetpw = "AdminCommand.resetpw"
            clearUser = "AdminCommand.clear_user"
            move =  "AdminCommand.move"
            
            [callback_queries]
            confirm_delete = "callback.confirm_delete"
            confirm_unbind = "callback.confirm_unbind"
            cancel = "callback.cancel"
            red_ = "callback.receive_red_packet"
            redinfo_ = "callback.red_info"
            withdraw_ = "callback.withdraw_red"
            reqb_ = "Require.require_choose"
            req_ = "Require.require_submit"
            reqa_ = "Require.require_action"
            admdelje_ = "callback.admin_delete_je"
            """)
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
    
    bot_logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot_process = multiprocessing.Process(target=run_bot)
    api_process = multiprocessing.Process(target=run_flask)
    
    bot_process.start()
    api_process.start()
    
    bot_process.join()
    api_process.join()
