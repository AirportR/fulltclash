from libs import bot
from glovar import app as myapp, bot_info
from pyrogram import idle
from botmodule import init_bot

bot_token = init_bot.bot_token


def start():
    myapp.start()
    bot.loader(myapp)
    bot_info(myapp)
    idle()
    myapp.stop()


if __name__ == "__main__":
    start()
