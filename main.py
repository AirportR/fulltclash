from pyrogram import Client
from libs import bot
from botmodule import init_bot

if __name__ == "__main__":
    app = Client("my_bot", proxy=init_bot.proxies, ipv6=False)
    bot.loader(app)
    app.run()
