import multiprocessing
import os

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, filters

import src.bot.admin as AdminCommand
import src.bot.require as Require
import src.bot.user as UserCommand
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
    
    # 普通命令
    application.add_handler(CommandHandler(["start", "help"], UserCommand.start))  # 帮助
    application.add_handler(CommandHandler("reg", UserCommand.reg))  # 注册账户 需要cdk（部分权限账户不需要）
    application.add_handler(CommandHandler("info", UserCommand.info))
    application.add_handler(CommandHandler("delete", UserCommand.delete_account))
    application.add_handler(CommandHandler("sign", UserCommand.sign))
    application.add_handler(CommandHandler("bind", UserCommand.bind))
    application.add_handler(CommandHandler("unbind", UserCommand.unbind))
    application.add_handler(CommandHandler("password", UserCommand.reset_pw))  # 修改密码
    application.add_handler(CommandHandler("gencdk", UserCommand.gen_cdk))  # 生成cdk
    application.add_handler(CommandHandler("red", UserCommand.red_packet))  # 发红包
    application.add_handler(CommandHandler("require", Require.require))  # 申请番剧 仅star用户
    application.add_handler(CommandHandler("checkrequire", Require.check_require))  # 番剧申请状态 仅star用户
    
    # 管理员命令
    application.add_handler(CommandHandler("shelp", AdminCommand.shelp))  # 生成注册码
    application.add_handler(CommandHandler("summon", AdminCommand.summon))  # 生成注册码
    application.add_handler(CommandHandler("checkinfo", AdminCommand.checkinfo))  # 管理员查看用户信息
    application.add_handler(CommandHandler("deleteAccount", AdminCommand.delete_account))  # 删除用户
    application.add_handler(CommandHandler("setGroup", AdminCommand.set_group))  # 设置用户权限
    application.add_handler(CommandHandler("cdks", AdminCommand.get_all_cdk))  # 查看所有注册码
    application.add_handler(CommandHandler("update", AdminCommand.update))
    application.add_handler(CommandHandler("setScore", AdminCommand.set_score))  # 设置用户积分
    application.add_handler(CommandHandler("setCDKgen", AdminCommand.set_gen_cdk))  # 是否允许用户生成注册码
    application.add_handler(CommandHandler("deleteCDK", AdminCommand.del_cdk))  # 删除某个注册码
    application.add_handler(CommandHandler("setCdkLimit", AdminCommand.set_cdk_limit))
    application.add_handler(CommandHandler("setCdkTime", AdminCommand.set_cdk_time))
    application.add_handler(CommandHandler("requireList", Require.require_list))
    
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
    bot_process = multiprocessing.Process(target=run_bot)
    api_process = multiprocessing.Process(target=run_flask)
    
    bot_process.start()
    api_process.start()
    
    bot_process.join()
    api_process.join()
