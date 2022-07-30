from random import SystemRandom
from string import ascii_letters, digits
from time import sleep
from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup

from bot.helper.mirror.upload.gdrive_helper import GoogleDriveHelper
from bot.helper.tg_helper.msg_utils import (
    sendMessage,
    sendMarkup,
    deleteMessage,
    delete_all_messages,
    update_all_messages,
    sendStatusMessage,
)
from bot.helper.mirror.status.clone_status import CloneStatus
from bot import (
    AUTHORIZED_CHATS,
    SUDO_USERS,
    dispatcher,
    LOGGER,
    CLONE_LIMIT,
    STOP_DUPLICATE,
    download_dict,
    download_dict_lock,
    Interval,
)
from bot.helper.others.bot_utils import *
from bot.helper.mirror.download.link_generator import *
from bot.helper.others.exceptions import DirectDownloadLinkException


async def _clone(c:Client, m:Message, multi=0):
    temp = m.text.split(" |", maxsplit=1)
    arguments = temp[0].split(" ")
    reply_to = m.reply_to_message
    link = ""
    try:
        new_name = temp[1]
        new_name = new_name.strip()
    except Exception:
        new_name = ""
    if len(arguments) > 1:
        link = arguments[1]
        if link.isdigit():
            multi = int(link)
            link = ""
        elif m.from_user.username:
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
    is_gdtot = is_gdtot_link(link)
    is_unified = is_unified_link(link)
    is_udrive = is_udrive_link(link)
    is_sharer = is_sharer_link(link)
    is_drivehubs = is_drivehubs_link(link)
    if (is_gdtot or is_unified or is_udrive or is_sharer or is_drivehubs):
        try:
            msg = await sendMessage(f"<b>Processing:</b> <code>{link}</code>", c, m)
            LOGGER.info(f"Processing: {link}")
            if is_unified:
                link = unified(link)
            if is_gdtot:
                link = gdtot(link)
            if is_udrive:
                link = udrive(link)
            if is_sharer:
                link = sharer_pw_dl(link)
            if is_drivehubs:
                link = drivehubs(link)
            await deleteMessage(c, msg)
        except DirectDownloadLinkException as e:
            await deleteMessage(c, msg)
            return await sendMessage(str(e), c, m)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if new_name:
            name = new_name
        if res != "":
            return await sendMessage(res, c, m)
        if STOP_DUPLICATE:
            LOGGER.info("Checking File/Folder if already in Drive...")
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                return await sendMarkup(msg3, c, m, button)
        if CLONE_LIMIT is not None:
            LOGGER.info("Checking File/Folder Size...")
            if size > CLONE_LIMIT * 1024**3:
                msg2 = f"Failed, Clone limit is {CLONE_LIMIT}GB.\nYour File/Folder size is {get_readable_file_size(size)}."
                return await sendMessage(msg2, c, m)
        if multi > 1:
            sleep(2)
            nextmsg = type(
                "nextmsg",
                (object,),
                {
                    "chat_id": m.chat.id,
                    "message_id": m.reply_to_message.id + 1,
                },
            )
            nextmsg = await sendMessage(arguments[0], c, nextmsg)
            nextmsg.from_user.id = m.from_user.id
            multi -= 1
            sleep(2)
            await _clone(c,m,multi)
        if files <= 20:
            msg = await sendMessage(f"Cloning: <code>{link}</code>", c, m)
            result, button = gd.clone(link, name)
            await deleteMessage(c, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = "".join(SystemRandom().choices(ascii_letters + digits, k=12))
            clone_status = CloneStatus(drive, size, m, gid)
            with download_dict_lock:
                download_dict[m.id] = clone_status
            await sendStatusMessage(c, m)
            result, button = drive.clone(link, name)
            with download_dict_lock:
                del download_dict[m.id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    await delete_all_messages()
                else:
                    await update_all_messages()
            except IndexError:
                pass
        cc = f"\n\n<b>cc: </b>{tag}"
        if button in ["cancelled", ""]:
            await sendMessage(f"{tag} {result}", c, m)
        else:
            await sendMarkup(result + cc, c, m, button)
            LOGGER.info(f"Cloning Done: {name}")
        if (is_gdtot or is_unified or is_udrive or is_sharer):
            gd.deletefile(link)
    else:
        await sendMessage(
            "Send Gdrive or GDToT/AppDrive/DriveApp/GDFlix/DriveAce/DriveLinks/DriveBit/DriveSharer/Anidrive/Driveroot/Driveflix/Indidrive/drivehub(in)/HubDrive/DriveHub(ws)/KatDrive/Kolop/DriveFire/DriveBuzz/SharerPw Link along with command or by replying to the link by command",
            c,
            m,
        )


@Client.on_message(filters.command(BotCommands.CloneCommand) & (filters.chat(sorted(AUTHORIZED_CHATS))|filters.user(sorted(SUDO_USERS))))
async def cloneNode(c: Client, m:Message):
    await _clone(c, m)
