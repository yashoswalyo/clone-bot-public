from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from bot import AUTHORIZED_CHATS, LOGGER, dispatcher
from bot.helper.mirror.upload.gdrive_helper import GoogleDriveHelper
from bot.helper.tg_helper.msg_utils import sendMessage, editMessage, sendMarkup
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper import make_buttons

@Client.on_message(filters.command(BotCommands.ListCommand) & filters.chat(sorted(AUTHORIZED_CHATS)))
async def list_buttons(c: Client, m: Message):
    user_id = m.from_user.id
    if len(m.text.split(" ", maxsplit=1)) < 2:
        return await sendMessage('Send a search key along with command', c, m)
    buttons = make_buttons.ButtonMaker()
    buttons.sbutton("Folders", f"types {user_id} folders")
    buttons.sbutton("Files", f"types {user_id} files")
    buttons.sbutton("Both", f"types {user_id} both")
    buttons.sbutton("Cancel", f"types {user_id} cancel")
    button = InlineKeyboardMarkup(buttons.build_menu(2))
    await sendMarkup('Choose option to list.', c, m, button)

@Client.on_callback_query(filters.regex("types") & filters.chat(sorted(AUTHORIZED_CHATS)))
async def select_type(c:Client, cb:CallbackQuery):
    user_id = cb.from_user.id
    msg = cb.message
    key = msg.reply_to_message.text.split(" ", maxsplit=1)[1]
    data = cb.data
    data = data.split(" ")
    if user_id != int(data[1]):
        return await cb.answer(text="Not Yours!", show_alert=True)
    elif data[2] == 'cancel':
        await cb.answer()
        return await editMessage("Search has been canceled!", msg)
    cb.answer()
    item_type = data[2]
    await editMessage(f"<b>Searching for <i>{key}</i></b>", msg)
    await _list_drive(key,msg,item_type)

async def _list_drive(key, bmsg, item_type):
    LOGGER.info(f"listing: {key}")
    gdrive = GoogleDriveHelper()
    msg, button = gdrive.drive_list(key, isRecursive=True, itemType=item_type)
    if button:
        await editMessage(msg, bmsg, button)
    else:
        await editMessage(f'No result found for <i>{key}</i>', bmsg)
