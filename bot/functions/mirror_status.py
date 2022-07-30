from psutil import cpu_percent, virtual_memory, disk_usage
from time import time
from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from bot import (
    AUTHORIZED_CHATS,
    dispatcher,
    status_reply_dict,
    status_reply_dict_lock,
    download_dict,
    download_dict_lock,
    botStartTime,
    DOWNLOAD_DIR,
)
from bot.helper.tg_helper.msg_utils import (
    sendMessage,
    deleteMessage,
    auto_delete_message,
    sendStatusMessage,
    update_all_messages,
)
from bot.helper.others.bot_utils import get_readable_file_size, get_readable_time, turn
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands

@Client.on_message(filters.command(BotCommands.StatusCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def mirror_status(c:Client, m:Message):
    with download_dict_lock:
        if len(download_dict) == 0:
            currentTime = get_readable_time(time() - botStartTime)
            free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)
            message = "No Active Downloads !\n___________________________"
            message += (
                f"\n<b>CPU:</b> {cpu_percent()}% | <b>FREE:</b> {free}"
                f"\n<b>RAM:</b> {virtual_memory().percent}% | <b>UPTIME:</b> {currentTime}"
            )
            reply_message = await sendMessage(message, c, m)
            await auto_delete_message(c,m,reply_message)
            return
    index = m.chat.id
    with status_reply_dict_lock:
        if index in status_reply_dict.keys():
            await deleteMessage(c, status_reply_dict[index])
            del status_reply_dict[index]
    await sendStatusMessage(c, m)
    await deleteMessage(c, m)


@Client.on_callback_query(filters.regex("status") & filters.chat(sorted(AUTHORIZED_CHATS)))
async def status_pages(c: Client, cb: CallbackQuery):
    data = cb.data
    data = data.split(" ")
    await cb.answer()
    done = turn(data)
    if done:
        await update_all_messages()
    else:
        await cb.message.delete()
