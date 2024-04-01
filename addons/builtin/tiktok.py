import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

from utils import retry


# collector section
@retry(2)
async def fetch_tiktok(collector, session: aiohttp.ClientSession, proxy=None):
    """
    tiktok解锁测试,检查测速是否被ban
    :param collector:
    :param session:
    :param proxy:
    :return:
    """
    tiktokurl = 'https://www.tiktok.com'
    try:
        # async with aiohttp.ClientSession() as session:
        async with session.get(tiktokurl, proxy=proxy, timeout=5) as resq:
            if resq.status == 200:
                response_text = await resq.text()
                region = response_text.find('"region":')
                if region != -1:
                    region = response_text[region:].split('"')[3]
                    # print("Tiktok Region: ", region)
                    collector.info['tiktok'] = f"解锁({region})"
                else:
                    # print("Tiktok Region: Not found")
                    collector.info['tiktok'] = "失败"
            else:
                collector.info['tiktok'] = "未知"
        return True
    except ClientConnectorError as c:
        logger.warning("tiktok请求发生错误:" + str(c))
        await fetch_tiktok(collector, session=session, proxy=proxy)
        collector.info['tiktok'] = "连接错误"
        return False
    except asyncio.exceptions.TimeoutError:
        await fetch_tiktok(collector, session=session, proxy=proxy)
        collector.info['tiktok'] = "超时"
        return False


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_tiktok(Collector, session, proxy=proxy))


# cleaner section
def get_tiktok_info(ReCleaner):
    """
    获取tiktok解锁信息
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'tiktok' not in ReCleaner.data:
            return "N/A"
        else:
            return ReCleaner.data.get('tiktok', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Tiktok",
    "TASK": task,
    "GET": get_tiktok_info
}


async def demo():
    from utils import script_demo
    await script_demo(fetch_tiktok, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
