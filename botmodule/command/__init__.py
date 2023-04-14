from pyrogram.types import Message
# from utils import message_delete_queue


async def common_command(_, __: Message):
    pass
    # backmsg = await message.reply("如果你看到这条消息，说明你的权限回调工作正常。\n另外，此函数作为最后命中的组别，请勿向用户直接暴露。")
    # message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
