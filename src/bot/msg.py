from telegram import Update
from telegram.ext import ContextTypes


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.chat_id == -1002370650432:
        await context.bot.copyMessage(chat_id=-1002531979765, message_thread_id=1632, from_chat_id=-1002370650432,
                                      message_id=update.channel_post.message_id)
