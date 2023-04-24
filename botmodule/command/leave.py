import asyncio

from loguru import logger
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import RPCError
from botmodule.init_bot import admin, config
from utils.check import get_telegram_id_from_message as get_id
from utils import message_delete_queue as mdq


async def leavechat(client: Client, message: Message):
    try:
        if config.config.get('anti-group', False):
            for user in message.new_chat_members:
                if str(user.is_self) == "True":
                    ID = get_id(message)
                    if ID not in admin:
                        await message.reply("❌ 机器人已启动防拉群模式，请联系管理员拉群")
                        await asyncio.sleep(1)
                        await client.leave_chat(message.chat.id)
        return
    except RPCError as r:
        logger.error(str(r))
    except Exception as e:
        logger.error(str(e))


async def set_anti_group(_: Client, message: Message):
    ID = get_id(message)
    if ID not in admin:
        backmsg = await message.reply("⚠️您不是bot的管理员，无法使用该命令")
        mdq.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return
    try:
        if config.config.get('anti-group', True):
            config.yaml['anti-group'] = False
            config.reload()
            logger.info("关闭了防拉群")
            backmsg = await message.reply("关闭了防拉群")
            mdq.put_nowait((backmsg.chat.id, backmsg.id, 10))
        else:
            config.yaml['anti-group'] = True
            config.reload()
            logger.info("开启了防拉群")
            backmsg = await message.reply("开启了防拉群")
            mdq.put_nowait((backmsg.chat.id, backmsg.id, 10))
    except RPCError as r:
        logger.error(str(r))
    except Exception as e:
        logger.error(str(e))
