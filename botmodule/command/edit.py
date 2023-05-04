from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import RPCError
from loguru import logger
from utils.cleaner import ArgCleaner


@logger.catch()
async def edit(app: Client, message: Message):
    tgargs = ArgCleaner().getall(message.text)
    if len(tgargs) < 5:
        return
    edit_chat_id = int(tgargs[2])
    edit_msg_id = int(tgargs[3])
    text = ' '.join(tgargs[4:])
    try:
        editmsg = await app.get_messages(edit_chat_id, edit_msg_id)
        reply_markup = editmsg.reply_markup
        await editmsg.edit_text(text, reply_markup=reply_markup)
    except RPCError as r:
        logger.error(str(r))
