import os

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, filters

import src.bot.admin as AdminCommand
import src.bot.require as Require
import src.bot.user as UserCommand
from src.bot import callback
from src.config import BotConfig, Config
from src.logger import bot_logger

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
    
    # 普通命令
    application.add_handler(CommandHandler("reg", UserCommand.reg))
    application.add_handler(CommandHandler("info", UserCommand.info))
    application.add_handler(CommandHandler("delete", UserCommand.delete_account))
    application.add_handler(CommandHandler("sign", UserCommand.sign))
    application.add_handler(CommandHandler("bind", UserCommand.bind))
    application.add_handler(CommandHandler("unbind", UserCommand.unbind))
    application.add_handler(CommandHandler("changepassword", UserCommand.reset_pw))
    application.add_handler(CommandHandler("generateRegCode", UserCommand.gen_cdk))
    application.add_handler(CommandHandler("red", UserCommand.red_packet))
    application.add_handler(CommandHandler("require", Require.require))
    application.add_handler(CommandHandler("checkrequire", Require.check_require))
    
    # 管理员命令
    application.add_handler(CommandHandler("summon", AdminCommand.summon))  # 管理员生成注册码
    application.add_handler(CommandHandler("checkinfo", AdminCommand.checkinfo))  # 管理员查看用户信息
    application.add_handler(CommandHandler("deleteAccountBy", AdminCommand.deleteAccountBy))  # 管理员删除用户
    application.add_handler(CommandHandler("setUserGroup", AdminCommand.set_group, filters=filters.ChatType.PRIVATE & filters.Chat(
            chat_id=BotConfig.ADMIN)))  # 设置管理员
    application.add_handler(CommandHandler("regcodes", AdminCommand.get_all_code))
    application.add_handler(CommandHandler("update", AdminCommand.update))
    application.add_handler(CommandHandler("setScore", AdminCommand.set_score))
    application.add_handler(CommandHandler("setRegCodeGenerateStatus", AdminCommand.set_gen_cdk))
    application.add_handler(CommandHandler("deleteRegCode", AdminCommand.del_cdk))
    application.add_handler(CommandHandler("setRegCodeUsageLimit", AdminCommand.set_code_limit))
    application.add_handler(CommandHandler("setRegCodeTime", AdminCommand.set_code_time))
    
    # 按钮回调
    application.add_handler(CallbackQueryHandler(callback.confirm_delete, pattern='confirm_delete'))
    application.add_handler(CallbackQueryHandler(callback.confirm_unbind, pattern='confirm_unbind'))
    application.add_handler(CallbackQueryHandler(callback.cancel, pattern='cancel'))
    application.add_handler(CallbackQueryHandler(callback.receive_red_packet, pattern='red_'))
    application.add_handler(CallbackQueryHandler(callback.red_info, pattern='redinfo_'))
    application.add_handler(CallbackQueryHandler(callback.withdraw_red, pattern='withdraw_'))
    application.add_handler(CallbackQueryHandler(Require.require_choose, pattern='reqb_'))
    application.add_handler(CallbackQueryHandler(Require.require_submit, pattern='req_'))
    application.add_handler(CallbackQueryHandler(Require.require_action, pattern='reqa_'))  # 处理番剧请求
    bot_logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
