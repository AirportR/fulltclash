import asyncio
from pyrogram import Client

import botmodule

q = asyncio.Queue(maxsize=1)


async def bot_task_queue(client: Client, message, task_type:str, qu: asyncio.Queue):
    """
    一个简单的任务队列
    :param client:
    :param message:
    :param task_type: 测试类型
    :param qu:
    :return:
    """
    if task_type == "test":
        await botmodule.test(client, message)
    elif task_type == "testurl":
        await botmodule.testurl(client, message)
    elif task_type == "analyze":
        await botmodule.analyze(client, message)
    elif task_type == "analyzeurl":
        await botmodule.analyzeurl(client, message)
    elif task_type == "outbound":
        await botmodule.analyze(client, message, test_type="outbound")
    elif task_type == "outboundurl":
        await botmodule.analyzeurl(client, message, test_type="outbound")
    await qu.get()
    qu.task_done()

