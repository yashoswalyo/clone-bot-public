from bot import AUTHORIZED_CHATS, OWNER_ID, SUDO_USERS, dispatcher, DB_URI
from bot.helper.tg_helper.msg_utils import sendMessage
from telegram.ext import CommandHandler
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.others.database_handler import DbManger
from pyrogram import enums, filters,Client
from pyrogram.types import Message

@Client.on_message(filters.command(BotCommands.AuthorizeCommand) & filters.user(sorted(SUDO_USERS)) & filters.user(OWNER_ID))
async def authorize(c: Client, m: Message):
    reply_message = None
    message_ = None
    reply_message = m.reply_to_message
    message_ = m.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in AUTHORIZED_CHATS:
            msg = "User Already Authorized!"
        elif DB_URI is not None:
            msg = DbManger().user_auth(user_id)
            AUTHORIZED_CHATS.add(user_id)
        else:
            AUTHORIZED_CHATS.add(user_id)
            msg = "User Authorized"
    elif reply_message is None:
        # Trying to authorize a chat
        chat_id = m.chat.id
        if chat_id in AUTHORIZED_CHATS:
            msg = "Chat Already Authorized!"
        elif DB_URI is not None:
            msg = DbManger().user_auth(chat_id)
            AUTHORIZED_CHATS.add(chat_id)
        else:
            AUTHORIZED_CHATS.add(chat_id)
            msg = "Chat Authorized"
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            msg = "User Already Authorized!"
        elif DB_URI is not None:
            msg = DbManger().user_auth(user_id)
            AUTHORIZED_CHATS.add(user_id)
        else:
            AUTHORIZED_CHATS.add(user_id)
            msg = "User Authorized"
    await sendMessage(msg, c, m)

@Client.on_message(filters.command(BotCommands.UnAuthorizeCommand) & filters.user(sorted(SUDO_USERS)) & filters.user(OWNER_ID))
async def unauthorize(c: Client, m: Message):
    reply_message = None
    message_ = None
    reply_message = m.reply_to_message
    message_ = m.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(user_id)
            else:
                msg = "User Unauthorized"
            AUTHORIZED_CHATS.remove(user_id)
        else:
            msg = "User Already Unauthorized!"
    elif reply_message is None:
        # Trying to unauthorize a chat
        chat_id = m.chat.id
        if chat_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(chat_id)
            else:
                msg = "Chat Unauthorized"
            AUTHORIZED_CHATS.remove(chat_id)
        else:
            msg = "Chat Already Unauthorized!"
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in AUTHORIZED_CHATS:
            if DB_URI is not None:
                msg = DbManger().user_unauth(user_id)
            else:
                msg = "User Unauthorized"
            AUTHORIZED_CHATS.remove(user_id)
        else:
            msg = "User Already Unauthorized!"
    await sendMessage(msg, c, m)

@Client.on_message(filters.command(BotCommands.AddSudoCommand) & filters.user(OWNER_ID))
async def addSudo(c: Client, m: Message):
    reply_message = None
    message_ = None
    reply_message = m.reply_to_message
    message_ = m.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in SUDO_USERS:
            msg = "Already Sudo!"
        elif DB_URI is not None:
            msg = DbManger().user_addsudo(user_id)
            SUDO_USERS.add(user_id)
        else:
            SUDO_USERS.add(user_id)
            msg = "Promoted as Sudo"
    elif reply_message is None:
        msg = "Give ID or Reply To message of whom you want to Promote."
    else:
        # Trying to authorize someone by replying
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            msg = "Already Sudo!"
        elif DB_URI is not None:
            msg = DbManger().user_addsudo(user_id)
            SUDO_USERS.add(user_id)
        else:
            SUDO_USERS.add(user_id)
            msg = "Promoted as Sudo"
    await sendMessage(msg, c, m)

@Client.on_message(filters.command(BotCommands.RmSudoCommand) & filters.user(OWNER_ID))
async def removeSudo(c: Client, m: Message):
    reply_message = None
    message_ = None
    reply_message = m.reply_to_message
    message_ = m.text.split(" ")
    if len(message_) == 2:
        user_id = int(message_[1])
        if user_id in SUDO_USERS:
            if DB_URI is not None:
                msg = DbManger().user_rmsudo(user_id)
            else:
                msg = "Demoted"
            SUDO_USERS.remove(user_id)
        else:
            msg = "Not sudo user to demote!"
    elif reply_message is None:
        msg = "Give ID or Reply To message of whom you want to remove from Sudo"
    else:
        user_id = reply_message.from_user.id
        if user_id in SUDO_USERS:
            if DB_URI is not None:
                msg = DbManger().user_rmsudo(user_id)
            else:
                msg = "Demoted"
            SUDO_USERS.remove(user_id)
        else:
            msg = "Not sudo user to demote!"
    await sendMessage(msg, c, m)

@Client.on_message(filters.command(BotCommands.AuthorizedUsersCommand) & filters.user(sorted(SUDO_USERS)) & filters.user(OWNER_ID))
async def sendAuthChats(c: Client, m:Message):
    user = sudo = ""
    user += "\n".join(f"<code>{uid}</code>" for uid in AUTHORIZED_CHATS)
    sudo += "\n".join(f"<code>{uid}</code>" for uid in SUDO_USERS)
    await sendMessage(f"<b><u>Authorized Chats:</u></b>\n{user}\n<b><u>Sudo Users:</u></b>\n{sudo}",c,m,)
