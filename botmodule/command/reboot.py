import os
import sys

from loguru import logger
from pyrogram.errors import RPCError


async def restart_or_killme(_, message, kill=False):
    try:
        if kill:
            await message.reply("再见~")
            os.kill(os.getpid(), 2)
        else:
            await message.reply("开始重启(大约等待五秒)")
            compiled = getattr(restart_or_killme, "__compiled__", None)  # 是否处于编译状态
            if compiled:
                filename = sys.argv[0]
                os.execlp(filename, filename)
            else:
                os.execlp(sys.executable, "main.py", *sys.argv)
            sys.exit()
    except RPCError as r:
        logger.error(str(r))
