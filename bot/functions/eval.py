from os import path as ospath, getcwd, chdir
from traceback import format_exc
from textwrap import indent
from io import StringIO, BytesIO
from telegram.ext import CommandHandler
from contextlib import redirect_stdout
from pyrogram import enums, filters,Client
from pyrogram.types import Message

from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper.msg_utils import sendMessage
from bot import LOGGER, OWNER_ID, dispatcher

namespaces = {}


def namespace_of(chat, m:Message, c:Client):
    if chat not in namespaces:
        namespaces[chat] = {
            "__builtins__": globals()["__builtins__"],
            "bot": c,
            "effective_message": m,
            "effective_user": m.from_user,
            "effective_chat": m.chat,
            "update":m
        }

    return namespaces[chat]


def log_input(m:Message):
    user = m.from_user.id
    chat = m.chat.id
    LOGGER.info(f"IN: {m.link} (user={user}, chat={chat})")


async def send(msg, c:Client, m:Message):
    if len(str(msg)) > 2000:
        with BytesIO(str.encode(msg)) as out_file:
            out_file.name = "output.txt"
            await c.send_document(chat_id=m.chat.id, document=out_file)
    else:
        LOGGER.info(f"OUT: '{msg}'")
        await c.send_message(
            chat_id=m.chat.id,
            text=f"`{msg}`",
            reply_to_message_id=m.id
        )

@Client.on_message(filters.command("eval") & filters.user(OWNER_ID))
async def evaluate(c:Client, m:Message):
    await send(do(eval, c, m), c, m)

@Client.on_message(filters.command("exec") & filters.user(OWNER_ID))
async def execute(c:Client, m:Message):
    await send(do(exec, c, m), c, m)


def cleanup_code(code):
    if code.startswith("```") and code.endswith("```"):
        return "\n".join(code.split("\n")[1:-1])
    return code.strip("` \n")


def do(func, c:Client, m:Message):
    log_input(m)
    content = m.text.split(" ", 1)[-1]
    body = cleanup_code(content)
    env = namespace_of(m.chat.id, m, c)

    chdir(getcwd())
    with open(ospath.join(getcwd(), "bot/functions/temp.txt"), "w") as temp:
        temp.write(body)

    stdout = StringIO()

    to_compile = f'def func():\n{indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        return f"{e.__class__.__name__}: {e}"

    func = env["func"]

    try:
        with redirect_stdout(stdout):
            func_return = func()
    except Exception as e:
        value = stdout.getvalue()
        return f"{value}{format_exc()}"
    else:
        value = stdout.getvalue()
        result = None
        if func_return is None:
            if value:
                result = f"{value}"
            else:
                try:
                    result = f"{repr(eval(body, env))}"
                except:
                    pass
        else:
            result = f"{value}{func_return}"
        if result:
            return result

@Client.on_message(filters.command("clearlocals") & filters.user(OWNER_ID))
async def clear(c: Client, m:Message):
    log_input(m)
    global namespaces
    if m.chat.id in namespaces:
        del namespaces[m.chat.id]
    await send("Cleared locals.", c, m)

@Client.on_message(filters.command(BotCommands.ExecHelpCommand) & filters.user(OWNER_ID))
async def exechelp(c: Client, m:Message):
    help_string = """
<b>Executor</b>
• /eval <i>Run Python Code Line | Lines</i>
• /exec <i>Run Commands In Exec</i>
• /clearlocals <i>Cleared locals</i>
"""
    await sendMessage(help_string, c, m)


# EVAL_HANDLER = CommandHandler(
#     ("eval"), evaluate, filters=CustomFilters.owner_filter, run_async=True
# )
# EXEC_HANDLER = CommandHandler(
#     ("exec"), execute, filters=CustomFilters.owner_filter, run_async=True
# )
# CLEAR_HANDLER = CommandHandler(
#     "clearlocals", clear, filters=CustomFilters.owner_filter, run_async=True
# )
# EXECHELP_HANDLER = CommandHandler(
#     BotCommands.ExecHelpCommand,
#     exechelp,
#     filters=CustomFilters.owner_filter,
#     run_async=True,
# )

# dispatcher.add_handler(EVAL_HANDLER)
# dispatcher.add_handler(EXEC_HANDLER)
# dispatcher.add_handler(CLEAR_HANDLER)
# dispatcher.add_handler(EXECHELP_HANDLER)
