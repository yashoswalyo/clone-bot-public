
from pyrogram import enums, filters,Client
from pyrogram.types import Message
from bot import AUTHORIZED_CHATS, SUDO_USERS, dispatcher
from bot.helper.mirror.upload.gdrive_helper import GoogleDriveHelper
from bot.helper.tg_helper.msg_utils import deleteMessage, sendMessage
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.others.bot_utils import is_gdrive_link, new_thread

@Client.on_message(filters.command(BotCommands.CountCommand) & (filters.chat(sorted(AUTHORIZED_CHATS))|filters.user(sorted(SUDO_USERS))))
async def countNode(c: Client, m: Message):
    args = m.text.split(" ", maxsplit=1)
    reply_to = m.reply_to_message
    link = ""
    if len(args) > 1:
        link = args[1]
        if m.from_user.username:
            tag = f"@{m.from_user.username}"
        else:
            tag = m.from_user.mention(m.from_user.first_name)
    if reply_to is not None:
        if len(link) == 0:
            link = reply_to.text
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention(reply_to.from_user.first_name)
    if is_gdrive_link(link):
        msg = await sendMessage(f"Counting: <code>{link}</code>", c, m)
        gd = GoogleDriveHelper()
        result = gd.count(link)
        await deleteMessage(c, msg)
        cc = f"\n\n<b>cc: </b>{tag}"
        await sendMessage(result + cc, c, m)
    else:
        await sendMessage(
            "Send Gdrive link along with command or by replying to the link by command",
            c,
            m,
        )
