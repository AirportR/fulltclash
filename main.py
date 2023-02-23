from pyrogram import Client
from libs import bot
from botmodule import init_bot


if __name__ == "__main__":
    app = Client("my_bot",
                 api_id=init_bot.api_id,
                 api_hash=init_bot.api_hash,
                 bot_token=init_bot.bot_token,
                 proxy=init_bot.proxies,
                 ipv6=False)
    bot.loader(app)
    app.run()
