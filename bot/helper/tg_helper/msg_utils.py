import asyncio
from time import sleep

from telegram.error import RetryAfter
from pyrogram.errors import FloodWait
from pyrogram import enums, Client
from pyrogram.types import Message, InlineKeyboardMarkup

from bot import (
    AUTO_DELETE_MESSAGE_DURATION,
    LOGGER,
    status_reply_dict,
    status_reply_dict_lock,
    Interval,
    DOWNLOAD_STATUS_UPDATE_INTERVAL,
)
from bot.helper.others.bot_utils import get_readable_message, setInterval


async def sendMessage(text: str, c:Client, m: Message):
    try:
        return await c.send_message(
            m.chat.id,
            reply_to_message_id=m.id,
            text=text,
            disable_web_page_preview=True,
        )
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return await sendMessage(text, c, m)
    except Exception as e:
        LOGGER.error(str(e))
        return


async def sendMarkup(text: str, c:Client, m: Message, reply_markup: InlineKeyboardMarkup):
    try:
        return await c.send_message(
            m.chat.id,
            text,
            reply_to_message_id=m.id,
            parse_mode=enums.parse_mode.ParseMode.DEFAULT,
            reply_markup=reply_markup
        )
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return await sendMarkup(text, c, m, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))
        return


async def editMessage(text: str, m: Message, reply_markup=None):
    try:
        await m.edit(
            text= text,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
    except RetryAfter as r:
        LOGGER.warning(str(r))
        sleep(r.retry_after * 1.5)
        return await editMessage(text, m, reply_markup)
    except Exception as e:
        LOGGER.error(str(e))
        return


async def deleteMessage(c: Client, m: Message):
    try:
        await c.delete_messages(chat_id=m.chat.id, message_ids=m.id)
    except Exception as e:
        LOGGER.error(str(e))


async def sendLogFile(c:Client, m: Message):
    with open("log.txt", "rb") as f:
        await c.send_document(
            document=f,
            file_name=f.name,
            reply_to_message_id=m.id,
            chat_id=m.chat.id,
        )


async def auto_delete_message(c:Client, omess: Message, rmess: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        await asyncio.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            await deleteMessage(c, omess)
            await deleteMessage(c, rmess)
        except AttributeError:
            pass


async def delete_all_messages():
    async with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                await deleteMessage(Client, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


async def update_all_messages():
    msg, buttons = get_readable_message()
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                if buttons == "":
                    await editMessage(msg, status_reply_dict[chat_id])
                else:
                    await editMessage(msg, status_reply_dict[chat_id], buttons)
                status_reply_dict[chat_id].text = msg


async def sendStatusMessage(c: Client, m:Message):
    if len(Interval) == 0:
        Interval.append(
            setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages)
        )
    progress, buttons = get_readable_message()
    with status_reply_dict_lock:
        if m.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[m.chat.id]
                await deleteMessage(c, message)
                del status_reply_dict[m.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[m.chat.id]
        if buttons == "":
            message = await sendMessage(progress, c, m)
        else:
            message = await sendMarkup(progress, c, m, buttons)
        status_reply_dict[m.chat.id] = message
