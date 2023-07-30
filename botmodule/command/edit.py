from contextlib import suppress

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import RPCError
from loguru import logger
from utils.cleaner import ArgCleaner
from utils.backend import default_progress_text
from botmodule import SPEEDTESTIKM, BOT_MESSAGE_LIST


async def edit(app: Client, message: Message):
    tgargs = ArgCleaner().getall(message.text)
    if len(tgargs) < 5:
        return
    edit_chat_id = int(tgargs[2])
    edit_msg_id = int(tgargs[3])
    s1 = tgargs[4]
    try:
        editmsg = BOT_MESSAGE_LIST.pop(tgargs[2]+':'+tgargs[3], None)
        if editmsg is None:
            editmsg = await app.get_messages(edit_chat_id, edit_msg_id)
        if editmsg is None:
            logger.info(f"无法获取{edit_chat_id}:{edit_msg_id}的源消息。")
            return
    except RPCError as r:
        logger.error(str(r))
        return
    if s1.startswith('$'):
        p = s1[1:].split(':')
        p1 = int(p[0])
        p2 = int(p[1])
        p3 = int(p[2])
        slavecomment = ArgCleaner().getarg(message.text, '"')[1]
        edittext = default_progress_text(p1, p2, p3, slavecomment)
        with suppress(RPCError):
            if p1 == 1:
                await editmsg.edit_text(edittext, reply_markup=SPEEDTESTIKM)
            else:
                await editmsg.edit_text(edittext)
        return
    text = ' '.join(tgargs[4:])
    reply_markup = editmsg.reply_markup
    try:
        await editmsg.edit_text(text, reply_markup=reply_markup)
    except RPCError as r:
        logger.error(str(r))
        return
    except Exception as e:
        logger.warning(str(e))
        return
