import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

from utils import retry


# collector section
@retry(2)
async def fetch(collector, session: aiohttp.ClientSession, proxy=None) -> bool:
    """
    XX解锁测试
    :param collector:
    :param session:
    :param proxy:
    :return:
    """
    try:
        collector.info["demo script"] = "demo" if session else str(proxy)
        return True
    except (ClientConnectorError, asyncio.exceptions.TimeoutError):
        collector.info['demo script'] = "连接错误"
        return False


def task(collector, session, proxy):
    return asyncio.create_task(fetch(collector, session, proxy=proxy))


# cleaner section
def get(recleaner):
    """
    获取解锁信息
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'demo script' not in recleaner.data:
            return "N/A"
        else:
            return recleaner.data.get('tiktok', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "demo script",
    "TASK": task,
    "GET": get
}


async def demo():
    from utils import script_demo
    await script_demo(fetch, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
