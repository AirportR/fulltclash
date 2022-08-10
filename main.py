from pyrogram import Client
import bot
from botmodule import init_bot


if __name__ == "__main__":
    app = Client("my_bot", proxy=init_bot.proxies)
    bot.loader(app)
    app.run()
