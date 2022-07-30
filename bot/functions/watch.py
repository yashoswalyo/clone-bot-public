import asyncio
from threading import Thread
from telegram.ext import CommandHandler, CallbackQueryHandler
from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from time import sleep
from re import split as re_split

from bot import AUTHORIZED_CHATS, DOWNLOAD_DIR, dispatcher
from bot.helper.tg_helper.msg_utils import sendMessage, sendMarkup, editMessage
from bot.helper.tg_helper import make_buttons
from bot.helper.others.bot_utils import get_readable_file_size, is_url
from bot.helper.mirror.download.youtube_dl_download_helper import (
    YoutubeDLHelper
)
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper.filters import CustomFilters
from .mirror import MirrorListener

listener_dict = {}


async def _watch(c:Client, m:Message, isZip=False, isLeech=False, multi=0):
    mssg = m.text
    user_id = m.from_user.id
    msg_id = m.id

    try:
        link = mssg.split(" ")[1].strip()
        if link.isdigit():
            multi = int(link)
            raise IndexError
        elif link.startswith(("|", "pswd:", "args:")):
            raise IndexError
    except:
        link = ""
    try:
        name_arg = mssg.split("|", maxsplit=1)
        if "args: " in name_arg[0]:
            raise IndexError
        else:
            name = name_arg[1]
        name = re_split(r" pswd: | args: ", name)[0]
        name = name.strip()
    except:
        name = ""
    try:
        pswd = mssg.split(" pswd: ")[1]
        pswd = pswd.split(" args: ")[0]
    except:
        pswd = None

    try:
        args = mssg.split(" args: ")[1]
    except:
        args = None

    if m.from_user.username:
        tag = f"@{m.from_user.username}"
    else:
        tag = m.from_user.mention(m.from_user.first_name)

    reply_to = m.reply_to_message
    if reply_to is not None:
        if len(link) == 0:
            link = reply_to.text.strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention(reply_to.from_user.first_name)

    if not is_url(link):
        help_msg = "<b>Send link along with command line:</b>"
        help_msg += "\n<code>/command</code> {link} |newname pswd: mypassword [zip] args: x:y|x1:y1"
        help_msg += "\n\n<b>By replying to link:</b>"
        help_msg += (
            "\n<code>/command</code> |newname pswd: mypassword [zip] args: x:y|x1:y1"
        )
        help_msg += "\n\n<b>Args Example:</b> args: playliststart:^10|match_filter:season_number=18|matchtitle:S1"
        help_msg += "\n\n<b>NOTE:</b> Add `^` before integer, some values must be integer and some string."
        help_msg += " Like playlist_items:10 works with string so no need to add `^` before the number"
        help_msg += " but playlistend works only with integer so you must add `^` before the number like example above."
        help_msg += "\n\nCheck all arguments from this <a href='https://github.com/yt-dlp/yt-dlp/blob/a3125791c7a5cdf2c8c025b99788bf686edd1a8a/yt_dlp/YoutubeDL.py#L194'>FILE</a>."
        return await sendMessage(help_msg, c, m)

    listener = MirrorListener(c, m, isZip, isLeech=isLeech, pswd=pswd, tag=tag)
    buttons = make_buttons.ButtonMaker()
    best_video = "bv*+ba/b"
    best_audio = "ba/b"
    ydl = YoutubeDLHelper(listener)
    try:
        result = ydl.extractMetaData(link, name, args, True)
    except Exception as e:
        msg = str(e).replace("<", " ").replace(">", " ")
        return await sendMessage(tag + " " + msg, c, m)
    if "entries" in result:
        for i in ["144", "240", "360", "480", "720", "1080", "1440", "2160"]:
            video_format = f"bv*[height<={i}][ext=mp4]"
            buttons.sbutton(f"{i}-mp4", f"qu {msg_id} {video_format} t")
            video_format = f"bv*[height<={i}][ext=webm]"
            buttons.sbutton(f"{i}-webm", f"qu {msg_id} {video_format} t")
        buttons.sbutton("Audios", f"qu {msg_id} audio t")
        buttons.sbutton("Best Videos", f"qu {msg_id} {best_video} t")
        buttons.sbutton("Best Audios", f"qu {msg_id} {best_audio} t")
        buttons.sbutton("Cancel", f"qu {msg_id} cancel")
        YTBUTTONS = InlineKeyboardMarkup(buttons.build_menu(3))
        listener_dict[msg_id] = [listener, user_id, link, name, YTBUTTONS, args]
        bmsg = await sendMarkup("Choose Playlist Videos Quality:", c, m, YTBUTTONS)
    else:
        formats = result.get("formats")
        formats_dict = {}
        if formats is not None:
            for frmt in formats:
                if not frmt.get("tbr") or not frmt.get("height"):
                    continue

                if frmt.get("fps"):
                    quality = f"{frmt['height']}p{frmt['fps']}-{frmt['ext']}"
                else:
                    quality = f"{frmt['height']}p-{frmt['ext']}"

                if frmt.get("filesize"):
                    size = frmt["filesize"]
                elif frmt.get("filesize_approx"):
                    size = frmt["filesize_approx"]
                else:
                    size = 0

                if quality in list(formats_dict.keys()):
                    formats_dict[quality][frmt["tbr"]] = size
                else:
                    subformat = {}
                    subformat[frmt["tbr"]] = size
                    formats_dict[quality] = subformat

            for _format in formats_dict:
                if len(formats_dict[_format]) == 1:
                    qual_fps_ext = re_split(r"p|-", _format, maxsplit=2)
                    height = qual_fps_ext[0]
                    fps = qual_fps_ext[1]
                    ext = qual_fps_ext[2]
                    if fps != "":
                        video_format = f"bv*[height={height}][fps={fps}][ext={ext}]"
                    else:
                        video_format = f"bv*[height={height}][ext={ext}]"
                    size = list(formats_dict[_format].values())[0]
                    buttonName = f"{_format} ({get_readable_file_size(size)})"
                    buttons.sbutton(str(buttonName), f"qu {msg_id} {video_format}")
                else:
                    buttons.sbutton(str(_format), f"qu {msg_id} dict {_format}")
        buttons.sbutton("Audios", f"qu {msg_id} audio")
        buttons.sbutton("Best Video", f"qu {msg_id} {best_video}")
        buttons.sbutton("Best Audio", f"qu {msg_id} {best_audio}")
        buttons.sbutton("Cancel", f"qu {msg_id} cancel")
        YTBUTTONS = InlineKeyboardMarkup(buttons.build_menu(2))
        listener_dict[msg_id] = [
            listener,
            user_id,
            link,
            name,
            YTBUTTONS,
            args,
            formats_dict,
        ]
        bmsg = await sendMarkup("Choose Video Quality:", c, m, YTBUTTONS)
    await _auto_cancel(bmsg,msg_id)
    # Thread(target=_auto_cancel, args=(bmsg, msg_id)).start()
    if multi > 1:
        await asyncio.sleep(3)
        nextmsg = type(
            "nextmsg",
            (object,),
            {
                "chat_id": m.chat.id,
                "message_id": m.reply_to_message.id + 1,
            },
        )
        nextmsg = await sendMessage(mssg.split(" ")[0], c, nextmsg)
        nextmsg.from_user.id = m.from_user.id
        multi -= 1
        await asyncio.sleep(3)
        await _watch(c,nextmsg,isZip, isLeech, multi)
        # Thread(target=_watch, args=(bot, nextmsg, isZip, isLeech, multi)).start()


async def _qual_subbuttons(task_id, qual, msg):
    buttons = make_buttons.ButtonMaker()
    task_info = listener_dict[task_id]
    formats_dict = task_info[6]
    qual_fps_ext = re_split(r"p|-", qual, maxsplit=2)
    height = qual_fps_ext[0]
    fps = qual_fps_ext[1]
    ext = qual_fps_ext[2]
    tbrs = []
    for tbr in formats_dict[qual]:
        tbrs.append(tbr)
    tbrs.sort(reverse=True)
    for index, br in enumerate(tbrs):
        if index == 0:
            tbr = f">{br}"
        else:
            sbr = index - 1
            tbr = f"<{tbrs[sbr]}"
        if fps != "":
            video_format = f"bv*[height={height}][fps={fps}][ext={ext}][tbr{tbr}]"
        else:
            video_format = f"bv*[height={height}][ext={ext}][tbr{tbr}]"
        size = formats_dict[qual][br]
        buttonName = f"{br}K ({get_readable_file_size(size)})"
        buttons.sbutton(str(buttonName), f"qu {task_id} {video_format}")
    buttons.sbutton("Back", f"qu {task_id} back")
    buttons.sbutton("Cancel", f"qu {task_id} cancel")
    SUBBUTTONS = InlineKeyboardMarkup(buttons.build_menu(2))
    await editMessage(f"Choose Video Bitrate for <b>{qual}</b>:", msg, SUBBUTTONS)


async def _audio_subbuttons(task_id, msg, playlist=False):
    buttons = make_buttons.ButtonMaker()
    audio_qualities = [64, 128, 320]
    for q in audio_qualities:
        if playlist:
            i = "s"
            audio_format = f"ba/b-{q} t"
        else:
            i = ""
            audio_format = f"ba/b-{q}"
        buttons.sbutton(f"{q}K-mp3", f"qu {task_id} {audio_format}")
    buttons.sbutton("Back", f"qu {task_id} back")
    buttons.sbutton("Cancel", f"qu {task_id} cancel")
    SUBBUTTONS = InlineKeyboardMarkup(buttons.build_menu(2))
    await editMessage(f"Choose Audio{i} Bitrate:", msg, SUBBUTTONS)

@Client.on_callback_query(filters.regex("qu") & filters.chat(sorted(AUTHORIZED_CHATS)))
async def select_format(c:Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    data = cb.data
    msg = cb.message
    data = data.split(" ")
    task_id = int(data[1])
    try:
        task_info = listener_dict[task_id]
    except:
        return await editMessage("This is an old task", msg)
    uid = task_info[1]
    if user_id != uid and not CustomFilters._owner_query(user_id):
        return await cb.answer(text="This task is not for you!", show_alert=True)
    elif data[2] == "dict":
        await cb.answer()
        qual = data[3]
        return await _qual_subbuttons(task_id, qual, msg)
    elif data[2] == "back":
        await cb.answer()
        return await editMessage("Choose Video Quality:", msg, task_info[4])
    elif data[2] == "audio":
        await cb.answer()
        if len(data) == 4:
            playlist = True
        else:
            playlist = False
        return await _audio_subbuttons(task_id, msg, playlist)
    elif data[2] == "cancel":
        await cb.answer()
        await editMessage("Task has been cancelled.", msg)
    else:
        await cb.answer()
        listener = task_info[0]
        link = task_info[2]
        name = task_info[3]
        args = task_info[5]
        qual = data[2]
        if qual.startswith(
            "bv*["
        ):  # To not exceed telegram button bytes limits. Temp solution.
            height = re_split(r"\[|\]", qual, maxsplit=2)[1]
            qual = qual + f"+ba/b[{height}]"
        if len(data) == 4:
            playlist = True
        else:
            playlist = False
        ydl = YoutubeDLHelper(listener)
        ydl.add_download(link, "{DOWNLOAD_DIR}{task_id}", name, qual, playlist, args)
        # Thread(
        #     target=ydl.add_download,
        #     args=(link, f"{DOWNLOAD_DIR}{task_id}", name, qual, playlist, args),
        # ).start()
        await cb.message.delete()
    del listener_dict[task_id]


async def _auto_cancel(msg, msg_id):
    await asyncio.sleep(120)
    try:
        del listener_dict[msg_id]
        await editMessage("Timed out! Task has been cancelled.", msg)
    except:
        pass

@Client.on_message(filters.command(BotCommands.WatchCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def watch(c: Client, m: Message):
    await _watch(c, m)

@Client.on_message(filters.command(BotCommands.ZipWatchCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def watchZip(c: Client, m: Message):
    await _watch(c, m, True)

@Client.on_message(filters.command(BotCommands.LeechWatchCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def leechWatch(c: Client, m: Message):
    await _watch(c, m, isLeech=True)

@Client.on_message(filters.command(BotCommands.LeechZipWatchCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def leechWatchZip(c: Client, m: Message):
    await _watch(c, m, True, True)


watch_handler = CommandHandler(
    BotCommands.WatchCommand,
    watch,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
zip_watch_handler = CommandHandler(
    BotCommands.ZipWatchCommand,
    watchZip,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
leech_watch_handler = CommandHandler(
    BotCommands.LeechWatchCommand,
    leechWatch,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
leech_zip_watch_handler = CommandHandler(
    BotCommands.LeechZipWatchCommand,
    leechWatchZip,
    filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
    run_async=True,
)
quality_handler = CallbackQueryHandler(select_format, pattern="qu", run_async=True)

dispatcher.add_handler(watch_handler)
dispatcher.add_handler(zip_watch_handler)
dispatcher.add_handler(leech_watch_handler)
dispatcher.add_handler(leech_zip_watch_handler)
dispatcher.add_handler(quality_handler)
