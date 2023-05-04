import asyncio

import loguru
from pyrogram import Client

import botmodule

q = asyncio.Queue(maxsize=1)


async def bot_task_queue(client: Client, message, task_type: str, qu: asyncio.Queue, **kwargs):
    """
    一个简单的任务队列

    include_text: 包含过滤器
    exclude_text: 排除过滤器
    url: 订阅链接
    :param client: 客户端
    :param message: 消息对象
    :param task_type: 测试类型
    :param qu: 队列
    :return: no return
    """
    slaveid = kwargs.get('slaveid', 'local')
    if slaveid != 'local':
        await qu.get()
        qu.task_done()
        await botmodule.process(client, message, put_type=task_type, **kwargs)
    if task_type:
        await botmodule.process(client, message, put_type=task_type, **kwargs)
        await qu.get()
        qu.task_done()
