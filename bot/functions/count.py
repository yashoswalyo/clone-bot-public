from telegram.ext import CommandHandler

from bot import dispatcher
from bot.helper.mirror.upload.gdrive_helper import GoogleDriveHelper
from bot.helper.tg_helper.msg_utils import deleteMessage, sendMessage
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.others.bot_utils import is_gdrive_link, new_thread


@new_thread
def countNode(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    reply_to = update.message.reply_to_message
    link = ""
    if len(args) > 1:
        link = args[1]
        if update.message.from_user.username:
            tag = f"@{update.message.from_user.username}"
        else:
            tag = update.message.from_user.mention_html(
                update.message.from_user.first_name
            )
    if reply_to is not None:
        if len(link) == 0:
            link = reply_to.text
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    if is_gdrive_link(link):
        msg = sendMessage(f"Counting: <code>{link}</code>", context.bot, update.message)
        gd = GoogleDriveHelper()
        result = gd.count(link)
        deleteMessage(context.bot, msg)
        cc = f"\n\n<b>cc: </b>{tag}"
        sendMessage(result + cc, context.bot, update.message)
    else:
        sendMessage(
            "Send Gdrive link along with command or by replying to the link by command",
            context.bot,
            update.message,
        )


count_handler = CommandHandler(
    BotCommands.CountCommand,
    countNode,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
dispatcher.add_handler(count_handler)
