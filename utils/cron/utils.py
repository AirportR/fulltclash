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


message_delete_queue = MessageDeleteQueue()  # put the value as a tuple: (chat.id, msg.id, seconds)
