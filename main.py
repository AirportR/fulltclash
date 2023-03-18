from libs import bot
from glovar import app as myapp, bot_info
from pyrogram import idle
from cron import scheduler, cron_delete_message as cdm
from botmodule import init_bot

bot_token = init_bot.bot_token


def start():
    myapp.start()
    bot.loader(myapp)
    bot_info(myapp)
    scheduler.start()
    scheduler.add_job(cdm, 'interval', seconds=10, id='delete1', name="Delete the telegram message")
    print("""# --------------------------- [ Start bot AsyncIOScheduler Successful ] ---------------------------- # """)
    idle()
    myapp.stop()


if __name__ == "__main__":
    start()
