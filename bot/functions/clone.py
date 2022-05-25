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
    arguments = message.text.split(" ", maxsplit=1)
    reply_to = message.reply_to_message
    link = ""
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
    is_appdrive = is_appdrive_link(link)
    is_gdflix = is_gdflix_link(link)
    is_driveapp = is_driveapp_link(link)
    is_driveace = is_driveace_link(link)
    is_drivelinks = is_drivelinks_link(link)
    is_drivebit = is_drivebit_link(link)
    is_drivesharer = is_drivesharer_link(link)
    is_hubdrive = is_hubdrive_link(link)
    is_drivehub = is_drivehub_link(link)
    is_katdrive = is_katdrive_link(link)
    is_kolop = is_kolop_link(link)
    is_drivefire = is_drivefire_link(link)
    if (is_gdtot or is_appdrive or is_gdflix or is_driveapp or is_driveace or is_drivelinks or is_drivebit or is_drivesharer or is_hubdrive or is_drivehub or is_katdrive or is_kolop or is_drivefire):
        try:
            msg = sendMessage(f"<b>Processing:</b> <code>{link}</code>", bot, message)
            LOGGER.info(f"Processing: {link}")
            if is_appdrive:
                link = unified(link)
            if is_gdtot:
                link = gdtot(link)
            if is_driveace:
                link = unified(link)
            if is_gdflix:
                link = unified(link)
            if is_driveapp:
                link = unified(link)
            if is_drivelinks:
                link = unified(link)
            if is_drivebit:
                link = unified(link)
            if is_drivesharer:
                link = unified(link)
            if is_hubdrive:
                link = udrive(link)
            if is_drivehub:
                link = udrive(link)
            if is_katdrive:
                link = udrive(link)
            if is_kolop:
                link = udrive(link)
            if is_drivefire:
                link = udrive(link)
            deleteMessage(bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(bot, msg)
            return sendMessage(str(e), bot, message)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
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
            result, button = gd.clone(link)
            deleteMessage(bot, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = "".join(SystemRandom().choices(ascii_letters + digits, k=12))
            clone_status = CloneStatus(drive, size, message, gid)
            with download_dict_lock:
                download_dict[message.message_id] = clone_status
            sendStatusMessage(message, bot)
            result, button = drive.clone(link)
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
        if (is_gdtot or is_appdrive or is_gdflix or is_driveapp or is_driveace or is_drivelinks or is_drivebit or is_drivesharer or is_hubdrive or is_drivehub or is_katdrive or is_kolop or is_drivefire):
            gd.deletefile(link)
    else:
        sendMessage(
            "Send Gdrive or GDToT/AppDrive/DriveApp/GDFlix/DriveAce/DriveLinks/DriveBit/DriveSharer/HubDrive/DriveHub/KatDrive/Kolop/DriveFire Link along with command or by replying to the link by command",
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
