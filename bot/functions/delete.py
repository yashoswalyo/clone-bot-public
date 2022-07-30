from threading import Thread
from telegram.ext import CommandHandler
from pyrogram import enums, filters,Client
from pyrogram.types import Message

from bot import OWNER_ID, SUDO_USERS, LOGGER
from bot.helper.tg_helper.msg_utils import auto_delete_message, sendMessage
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.mirror.upload import gdrive_helper
from bot.helper.others.bot_utils import is_gdrive_link

@Client.on_message(filters.command(BotCommands.DeleteCommand) & (filters.user(OWNER_ID) | filters.user(sorted(SUDO_USERS))))
async def deletefile(c: Client, m: Message):
    args = m.text.split(" ", maxsplit=1)
    reply_to = m.reply_to_message
    if len(args) > 1:
        link = args[1]
    elif reply_to is not None:
        link = reply_to.text
    else:
        link = ""
    if is_gdrive_link(link):
        LOGGER.info(link)
        drive = gdrive_helper.GoogleDriveHelper()
        msg = drive.deletefile(link)
    else:
        msg = (
            "Send Gdrive link along with command or by replying to the link by command"
        )
    reply_message = await sendMessage(msg, c, m)
    #Thread(target=auto_delete_message, args=(context.bot, update.message, reply_message)).start()
    await auto_delete_message(c,m,reply_message)

# delete_handler = CommandHandler(
#     command=BotCommands.DeleteCommand,
#     callback=deletefile,
#     filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
#     run_async=True,
# )
# dispatcher.add_handler(delete_handler)
