from threading import Thread
from speedtest import Speedtest
from telegram.ext import CommandHandler
from bot import LOGGER, dispatcher
from bot.helper.tg_helper.filters import CustomFilters
from bot.helper.tg_helper.list_of_commands import BotCommands
from bot.helper.tg_helper.msg_utils import sendSpeedTestMessage,sendMessage,editMessage,auto_delete_message
import json

def testspeed(update, context):
    wait_message = sendMessage("Please wait",context.bot, update.message)
    try:
        s = Speedtest(secure=True)
        editMessage("Testing download speed", wait_message)
        dl = s.download()
        editMessage("Testing upload speed", wait_message)
        up = s.upload()
        res = s.results
        editMessage("Getting test results", wait_message)
        link = res.share()
        download = int(round(dl / 1000000.0, 0))
        upload = int(round(up / 1000000.0, 0))
        msg=f"""
<b><u>-- Speed Test Results --</u>

Download: {download} Mbps
Upload: {upload} Mbps
Ping: {res.ping} ms
Server: 
<code>{json.dumps(res.server,indent=4)}</code>
</b>"""
        LOGGER.info(f"Download: {download} Mbps; Upload:{upload} Mbps")
        sendSpeedTestMessage(msg, context.bot, update.message, link)
        Thread(
            target=auto_delete_message, args=(context.bot, update.message, wait_message)
        ).start()
    except Exception as e:
        editMessage("Something went wrong, Check logs",wait_message)
        LOGGER.error(f"{e}")
    return

SPEEDTEST_HANDLER = CommandHandler(
    BotCommands.SpeedTestCommand, testspeed, filters=CustomFilters.sudo_user, run_async=True
)
dispatcher.add_handler(SPEEDTEST_HANDLER)
