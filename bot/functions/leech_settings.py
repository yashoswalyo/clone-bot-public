from os import remove as osremove, path as ospath, mkdir
from PIL import Image
from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery, User
from bot import (
    AS_DOC_USERS,
    AS_MEDIA_USERS,
    AUTHORIZED_CHATS,
    LOGGER,
    dispatcher,
    AS_DOCUMENT,
    app,
    AUTO_DELETE_MESSAGE_DURATION,
    DB_URI,
)
from bot.helper.tg_helper.msg_utils import (
    sendMessage,
    sendMarkup,
    editMessage,
    auto_delete_message,
)
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper import make_buttons
from bot.helper.others.database_handler import DbManger


def getleechinfo(from_user:User):
    user_id = from_user.id
    name = from_user.first_name + " " + from_user.last_name
    buttons = make_buttons.ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    if user_id in AS_DOC_USERS or user_id not in AS_MEDIA_USERS and AS_DOCUMENT:
        ltype = "DOCUMENT"
        buttons.sbutton("Send As Media", f"leechset {user_id} med")
    else:
        ltype = "MEDIA"
        buttons.sbutton("Send As Document", f"leechset {user_id} doc")

    if ospath.exists(thumbpath):
        thumbmsg = "Exists"
        buttons.sbutton("Delete Thumbnail", f"leechset {user_id} thumb")
    else:
        thumbmsg = "Not Exists"

    if AUTO_DELETE_MESSAGE_DURATION == -1:
        buttons.sbutton("Close", f"leechset {user_id} close")

    button = InlineKeyboardMarkup(buttons.build_menu(1))

    text = (
        f"<u>Leech Settings for <a href='tg://user?id={user_id}'>{name}</a></u>\n"
        f"Leech Type <b>{ltype}</b>\n"
        f"Custom Thumbnail <b>{thumbmsg}</b>"
    )
    return text, button


async def editLeechType(message:Message, cb:CallbackQuery):
    msg, button = getleechinfo(cb.from_user)
    await editMessage(msg, message, button)

@Client.on_message(filters.command(BotCommands.LeechSetCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def leechSet(c: Client, m: Message):
    msg, button = getleechinfo(m.from_user)
    choose_msg = await sendMarkup(msg, c, m, button)
    await auto_delete_message(c,m,choose_msg)

@Client.on_callback_query(filters.regex("leechset") & filters.chat(sorted(AUTHORIZED_CHATS)))
async def setLeechType(c:Client, cb:CallbackQuery):
    LOGGER.info(cb.data)
    message = cb.message
    user_id = cb.from_user.id
    data = cb.data
    data = data.split(" ")
    if user_id != int(data[1]):
        await cb.answer(text="Not Yours!", show_alert=True)
    elif data[2] == "doc":
        if user_id in AS_MEDIA_USERS:
            AS_MEDIA_USERS.remove(user_id)
        AS_DOC_USERS.add(user_id)
        if DB_URI is not None:
            DbManger().user_doc(user_id)
        await cb.answer(text="Your File Will Deliver As Document!",show_alert=True)
        await editLeechType(message, cb)
    elif data[2] == "med":
        if user_id in AS_DOC_USERS:
            AS_DOC_USERS.remove(user_id)
        AS_MEDIA_USERS.add(user_id)
        if DB_URI is not None:
            DbManger().user_media(user_id)
        await cb.answer(text="Your File Will Deliver As Media!", show_alert=True)
        await editLeechType(message, cb)
    elif data[2] == "thumb":
        path = f"Thumbnails/{user_id}.jpg"
        if ospath.lexists(path):
            osremove(path)
            if DB_URI is not None:
                DbManger().user_rm_thumb(user_id, path)
            await cb.answer(text="Thumbnail Removed!", show_alert=True)
            await editLeechType(message, cb)
        else:
            await cb.answer(text="Old Settings", show_alert=True)
    else:
        
        try:
            await cb.message.delete()
            await cb.message.reply_to_message.delete()
        except:
            pass

@Client.on_message(filters.command(BotCommands.SetThumbCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def setThumb(c: Client, m: Message):
    user_id = m.from_user.id
    reply_to = m.reply_to_message
    if reply_to is not None and reply_to.photo:
        path = "Thumbnails/"
        if not ospath.isdir(path):
            mkdir(path)
        photo_msg = await app.get_messages(
            m.chat.id, reply_to_message_ids=m.id
        )
        photo_dir = await app.download_media(photo_msg, file_name=path)
        des_dir = ospath.join(path, str(user_id) + ".jpg")
        Image.open(photo_dir).convert("RGB").save(des_dir, "JPEG")
        osremove(photo_dir)
        if DB_URI is not None:
            DbManger().user_save_thumb(user_id, des_dir)
        msg = f"Custom thumbnail saved for {m.from_user.mention(m.from_user.first_name)}."
        await sendMessage(msg, c, m)
    else:
        await sendMessage("Reply to a photo to save custom thumbnail.", c, m)


# leech_set_handler = CommandHandler(
#     BotCommands.LeechSetCommand,
#     leechSet,
#     filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
#     run_async=True,
# # )
# set_thumbnail_handler = CommandHandler(
#     BotCommands.SetThumbCommand,
#     setThumb,
#     filters=CustomFilters.authorized_chat | CustomFilters.authorized_user,
#     run_async=True,
# )
# but_set_handler = CallbackQueryHandler(setLeechType, pattern="leechset", run_async=True)

# # dispatcher.add_handler(leech_set_handler)
# dispatcher.add_handler(but_set_handler)
# dispatcher.add_handler(set_thumbnail_handler)
