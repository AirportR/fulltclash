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
    in_text = kwargs.get('include_text', '')
    ex_text = kwargs.get('exclude_text', '')
    suburl = kwargs.get('url', None)
    if "test" in task_type and "url" not in task_type:
        await botmodule.test(client, message, **kwargs)
    elif "testurl" in task_type:
        await botmodule.testurl(client, message, **kwargs)
    elif "analyze" in task_type and "url" not in task_type:
        await botmodule.analyze(client, message)
    elif "analyzeurl" in task_type:
        await botmodule.analyzeurl(client, message, include_text=in_text, exclude_text=ex_text, url=suburl)
    elif "outbound" in task_type and "url" not in task_type:
        await botmodule.analyze(client, message, test_type="outbound")
    elif "outboundurl" in task_type:
        await botmodule.analyzeurl(client, message, test_type="outbound", include_text=in_text, exclude_text=ex_text, url=suburl)
    elif "speed" in task_type and "url" not in task_type:
        await botmodule.speed(client, message)
    elif "speedurl" in task_type:
        await botmodule.speedurl(client, message, include_text=in_text, exclude_text=ex_text, url=suburl)
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
