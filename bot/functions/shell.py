from subprocess import run as srun
from pyrogram import enums, filters,Client
from pyrogram.types import Message, InlineKeyboardMarkup, CallbackQuery, User
from bot import LOGGER, OWNER_ID, dispatcher
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper.msg_utils import sendMessage

@Client.on_message(filters.command(BotCommands.ShellCommand) & filters.user(OWNER_ID))
async def shell(c:Client, m:Message):
    cmd = m.text.split(" ", 1)
    if len(cmd) == 1:
        return await sendMessage("No command to execute was given.", c, m)
    cmd = cmd[1]
    process = srun(cmd, capture_output=True, shell=True)
    reply = ""
    stderr = process.stderr.decode("utf-8")
    stdout = process.stdout.decode("utf-8")
    if len(stdout) != 0:
        reply += f"*Stdout*\n<code>{stdout}</code>\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if len(stderr) != 0:
        reply += f"*Stderr*\n<code>{stderr}</code>\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(reply) > 3000:
        with open("shell_output.txt", "w") as file:
            file.write(reply)
        with open("shell_output.txt", "rb") as doc:
            await c.send_document(
                document=doc,
                file_name=doc.name,
                reply_to_message_id=m.id,
                chat_id=m.chat.id,
            )
    elif len(reply) != 0:
        await sendMessage(reply, c, m)
    else:
        await sendMessage("No Reply", c, m)

