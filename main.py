import sys
from sqlite3 import OperationalError

from utils import bot
from glovar import app as app1, bot_info, app2
from pyrogram import idle
from botmodule import init_bot

bot_token = init_bot.bot_token


# app1 is bot,app2 is user bot.
def start():
    try:
        app1.start()
        bot.loader(app1)
        if app2 is not None:
            app2.start()
            bot.user_loder(app2)
        bot_info(app1, app2)
        idle()
        app1.stop()
        if app2 is not None:
            app2.stop()
    except OperationalError as err:
        if str(err) == "database is locked":
            print(f"Bot的会话数据库已被锁定，这可能是之前启动时出现了错误，"
                  f"尝试删除当前文件夹下的 {app1.name}.session 与 {app1.name}.session-journal 文件")
            sys.exit()
        else:
            raise


if __name__ == "__main__":
    start()
