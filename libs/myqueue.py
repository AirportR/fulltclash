import asyncio

import loguru
from pyrogram import Client

import botmodule

q = asyncio.Queue(maxsize=1)


async def bot_task_queue(client: Client, message, task_type: str, qu: asyncio.Queue):
    """
    一个简单的任务队列
    :param client:
    :param message:
    :param task_type: 测试类型
    :param qu:
    :return:
    """
    if "test" in task_type and "url" not in task_type:
        await botmodule.test(client, message)
    elif "testurl" in task_type:
        await botmodule.testurl(client, message)
    elif "analyze" in task_type and "url" not in task_type:
        await botmodule.analyze(client, message)
    elif "analyzeurl" in task_type:
        await botmodule.analyzeurl(client, message)
    elif "outbound" in task_type and "url" not in task_type:
        await botmodule.analyze(client, message, test_type="outbound")
    elif "outboundurl" in task_type:
        await botmodule.analyzeurl(client, message, test_type="outbound")
    elif "speed" in task_type and "url" not in task_type:
        await botmodule.speed(client, message)
    elif "speedurl" in task_type:
        await botmodule.speedurl(client, message)
    elif "delay" in task_type and "url" not in task_type:
        await botmodule.test(client, message)
    else:
        try:
            m1 = await message.reply("⚠️未识别的测试类型，任务取消~")
            await asyncio.sleep(10)
            await m1.delete()
            await message.delete()
        except Exception as e:
            loguru.logger.warning(str(e))
    await qu.get()
    qu.task_done()
