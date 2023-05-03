import asyncio
from pyrogram.types import Message


class MessageDeleteQueue(asyncio.Queue):
    """
    消息删除队列，用来与计划任务配合
    """

    def __init__(self):
        super().__init__()

    def put_nowait(self, item: tuple) -> None:
        """
        put the value as a tuple: (chat.id, msg.id, seconds)
        """
        super().put_nowait(item)

    def put(self, msg: Message, second=10):
        """
        快速推入删除队列，仅需要传入pyrogram.types.Message 对象，推荐使用！
        second: 设定多少秒后删除
        """
        super().put_nowait((msg.chat.id, msg.id, second))


class MessageEditQueue(asyncio.Queue):
    def __init__(self):
        super().__init__()

    def put(self, item: tuple) -> None:
        """
        格式: (chat.id, message.id, text, seconds, reply_markup)
        text 为要编辑的文本
        reply_markup 为最后一个参数，可以不填
        """
        super().put_nowait(item)

    def new_put(self, msg: Message,  second=10, ikm=None):
        """
        快速推入删除队列，仅需要传入pyrogram.types.Message 对象，推荐使用！
        second: 设定多少秒后删除
        """
        item = (msg.chat.id, msg.id, second) if ikm is None else (msg.chat.id, msg.id, second, ikm)
        super().put_nowait(item)


message_delete_queue = MessageDeleteQueue()
message_edit_queue = MessageEditQueue()
