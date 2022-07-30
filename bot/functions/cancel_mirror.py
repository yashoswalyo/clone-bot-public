from time import sleep
from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from bot import (
    AUTHORIZED_CHATS,
    download_dict,
    dispatcher,
    download_dict_lock,
    SUDO_USERS,
    OWNER_ID,
)
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.msg_utils import sendMessage, sendMarkup
from bot.helper.others.bot_utils import getDownloadByGid, MirrorStatus, getAllDownload
from bot.helper.tg_helper import make_buttons

@Client.on_message(filters.command(BotCommands.CancelMirror) & (filters.user(sorted(SUDO_USERS)) | filters.chat(sorted(AUTHORIZED_CHATS)) ))
async def cancel_mirror(c: Client, m: Message):
    args = m.text.split(" ", maxsplit=1)
    user_id = m.from_user.id
    if len(args) > 1:
        gid = args[1]
        dl = getDownloadByGid(gid)
        if not dl:
            return await sendMessage(
                f"GID: <code>{gid}</code> Not Found.", c, m
            )
    elif m.reply_to_message:
        mirror_message = m.reply_to_message
        with download_dict_lock:
            keys = list(download_dict.keys())
            try:
                dl = download_dict[mirror_message.id]
            except:
                dl = None
        if not dl:
            return await sendMessage(
                "This is not an active task!", c, m
            )
    elif len(args) == 1:
        msg = f"Reply to an active <code>/{BotCommands.MirrorCommand}</code> message which was used to start the download or send <code>/{BotCommands.CancelMirror} GID</code> to cancel it!"
        return await sendMessage(msg, c, m)

    if (
        OWNER_ID != user_id
        and dl.m.from_user.id != user_id
        and user_id not in SUDO_USERS
    ):
        return await sendMessage("This task is not for you!", c, m)

    if dl.status() == MirrorStatus.STATUS_ARCHIVING:
        await sendMessage(
            "Archival in Progress, You Can't Cancel It.", c, m
        )
    elif dl.status() == MirrorStatus.STATUS_EXTRACTING:
        await sendMessage(
            "Extract in Progress, You Can't Cancel It.", c, m
        )
    elif dl.status() == MirrorStatus.STATUS_SPLITTING:
        await sendMessage(
            "Split in Progress, You Can't Cancel It.", c, m
        )
    else:
        dl.download().cancel_download()


def cancel_all(status):
    gid = ""
    while True:
        dl = getAllDownload(status)
        if dl:
            if dl.gid() != gid:
                gid = dl.gid()
                dl.download().cancel_download()
                sleep(1)
        else:
            break

@Client.on_message(filters.command(BotCommands.CancelAllCommand) & (filters.user(OWNER_ID) | filters.user(sorted(SUDO_USERS))))
async def cancell_all_buttons(c: Client, m: Message):
    buttons = make_buttons.ButtonMaker()
    buttons.sbutton("Downloading", "canall down")
    buttons.sbutton("Uploading", "canall up")
    buttons.sbutton("Cloning", "canall clone")
    buttons.sbutton("All", "canall all")
    button = InlineKeyboardMarkup(buttons.build_menu(2))
    await sendMarkup("Choose tasks to cancel.", c, m, button)

@Client.on_callback_query(filters.regex("canall"))
async def cancel_all_update(c: Client, cb:CallbackQuery):
    query = cb
    user_id = cb.from_user.id
    data = query.data
    data = data.split(" ")
    if CustomFilters._owner_query(user_id):
        await query.answer("Ok", show_alert=True)
        await query.message.delete()
        cancel_all(data[1])
    else:
        await query.answer(
            text="You don't have permission to use these buttons!", 
            show_alert=True
        )


# cancel_mirror_handler = CommandHandler(
#     BotCommands.CancelMirror,
#     cancel_mirror,
#     filters=(CustomFilters.authorized_chat | CustomFilters.authorized_user),
#     run_async=True,
# )

# cancel_all_handler = CommandHandler(
#     BotCommands.CancelAllCommand,
#     cancell_all_buttons,
#     filters=CustomFilters.owner_filter | CustomFilters.sudo_user,
#     run_async=True,
# )

# cancel_all_buttons_handler = CallbackQueryHandler(
#     cancel_all_update, pattern="canall", run_async=True
# )

# dispatcher.add_handler(cancel_all_handler)
# dispatcher.add_handler(cancel_mirror_handler)
# dispatcher.add_handler(cancel_all_buttons_handler)
