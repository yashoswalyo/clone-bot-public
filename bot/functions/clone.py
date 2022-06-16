from random import SystemRandom
from string import ascii_letters, digits
from telegram.ext import CommandHandler
from threading import Thread
from time import sleep

from bot.helper.mirror.upload.gdrive_helper import GoogleDriveHelper
from bot.helper.tg_helper.msg_utils import (
    sendMessage,
    sendMarkup,
    deleteMessage,
    delete_all_messages,
    update_all_messages,
    sendStatusMessage,
)
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.mirror.status.clone_status import CloneStatus
from bot import (
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


def _clone(message, bot, multi=0):
    temp = message.text.split(" |", maxsplit=1)
    arguments = temp[0].split(" ")
    reply_to = message.reply_to_message
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
        elif message.from_user.username:
            tag = f"@{message.from_user.username}"
        else:
            tag = message.from_user.mention_html(message.from_user.first_name)
    if reply_to is not None:
        if len(link) == 0:
            link = reply_to.text
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    is_gdtot = is_gdtot_link(link)
    is_unified = is_unified_link(link)
    is_udrive = is_udrive_link(link)
    is_sharer = is_sharer_link(link)
    is_drivehubs = is_drivehubs_link(link)
    if (is_gdtot or is_unified or is_udrive or is_sharer or is_drivehubs):
        try:
            msg = sendMessage(f"<b>Processing:</b> <code>{link}</code>", bot, message)
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
            deleteMessage(bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(bot, msg)
            return sendMessage(str(e), bot, message)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if new_name:
            name = new_name
        if res != "":
            return sendMessage(res, bot, message)
        if STOP_DUPLICATE:
            LOGGER.info("Checking File/Folder if already in Drive...")
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                return sendMarkup(msg3, bot, message, button)
        if CLONE_LIMIT is not None:
            LOGGER.info("Checking File/Folder Size...")
            if size > CLONE_LIMIT * 1024**3:
                msg2 = f"Failed, Clone limit is {CLONE_LIMIT}GB.\nYour File/Folder size is {get_readable_file_size(size)}."
                return sendMessage(msg2, bot, message)
        if multi > 1:
            sleep(2)
            nextmsg = type(
                "nextmsg",
                (object,),
                {
                    "chat_id": message.chat_id,
                    "message_id": message.reply_to_message.message_id + 1,
                },
            )
            nextmsg = sendMessage(arguments[0], bot, nextmsg)
            nextmsg.from_user.id = message.from_user.id
            multi -= 1
            sleep(2)
            Thread(target=_clone, args=(nextmsg, bot, multi)).start()
        if files <= 20:
            msg = sendMessage(f"Cloning: <code>{link}</code>", bot, message)
            result, button = gd.clone(link, name)
            deleteMessage(bot, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = "".join(SystemRandom().choices(ascii_letters + digits, k=12))
            clone_status = CloneStatus(drive, size, message, gid)
            with download_dict_lock:
                download_dict[message.message_id] = clone_status
            sendStatusMessage(message, bot)
            result, button = drive.clone(link, name)
            with download_dict_lock:
                del download_dict[message.message_id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    delete_all_messages()
                else:
                    update_all_messages()
            except IndexError:
                pass
        cc = f"\n\n<b>cc: </b>{tag}"
        if button in ["cancelled", ""]:
            sendMessage(f"{tag} {result}", bot, message)
        else:
            sendMarkup(result + cc, bot, message, button)
            LOGGER.info(f"Cloning Done: {name}")
        if (is_gdtot or is_unified or is_udrive or is_sharer):
            gd.deletefile(link)
    else:
        sendMessage(
            "Send Gdrive or GDToT/AppDrive/DriveApp/GDFlix/DriveAce/DriveLinks/DriveBit/DriveSharer/Anidrive/Driveroot/Driveflix/Indidrive/drivehub(in)/HubDrive/DriveHub(ws)/KatDrive/Kolop/DriveFire/DriveBuzz/SharerPw Link along with command or by replying to the link by command",
            bot,
            message,
        )


@new_thread
def cloneNode(update, context):
    _clone(update.message, context.bot)


clone_handler = CommandHandler(
    BotCommands.CloneCommand,
    cloneNode,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
dispatcher.add_handler(clone_handler)
