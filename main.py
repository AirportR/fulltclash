from utils import bot
from glovar import app as app1, bot_info
from pyrogram import idle
from botmodule import init_bot

bot_token = init_bot.bot_token


# app1 is bot,app2 is user bot.
def start():
    app1.start()
    # app2.start()
    bot.loader(app1)
    # bot.user_loder(app2)
    bot_info(app1)
    idle()
    app1.stop()
    # app2.stop()


if __name__ == "__main__":
    start()
