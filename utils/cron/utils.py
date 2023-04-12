import asyncio


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


message_delete_queue = MessageDeleteQueue()  # put the value as a tuple: (chat.id, msg.id, seconds)
