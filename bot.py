import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from src.bot import callback
from src.bot.command import AdminCommand, UserCommand
from src.config import BotConfig, Config

logging.basicConfig(level=Config.LOG_LEVE, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
                   .build())
    
    # 普通命令
    application.add_handler(CommandHandler("reg", UserCommand.reg))
    application.add_handler(CommandHandler("info", UserCommand.info))
    application.add_handler(CommandHandler("delete", UserCommand.delete_account))
    application.add_handler(CommandHandler("sign", UserCommand.sign))
    application.add_handler(CommandHandler("bind", UserCommand.bind))
    application.add_handler(CommandHandler("unbind", UserCommand.unbind))
    # 管理员命令
    application.add_handler(CommandHandler("summon", AdminCommand.summon))  # 管理员生成注册码
    application.add_handler(CommandHandler("checkinfo", AdminCommand.checkinfo))  # 管理员查看用户信息
    application.add_handler(CommandHandler("deleteAccountBy", AdminCommand.deleteAccountBy))  # 管理员删除用户
    application.add_handler(CommandHandler("op", AdminCommand.set_admin))  # 设置管理员
    application.add_handler(CommandHandler("regcodes", AdminCommand.get_all_code))  #
    # 按钮回调
    application.add_handler(CallbackQueryHandler(callback.confirm_delete, pattern='confirm_delete'))
    application.add_handler(CallbackQueryHandler(callback.confirm_unbind, pattern='confirm_unbind'))
    application.add_handler(CallbackQueryHandler(callback.cancel, pattern='cancel'))
    logging.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
