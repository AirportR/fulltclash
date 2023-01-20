import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
catchplayurl = "https://sunapi.catchplay.com/geo"


async def fetch_catchplay(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    catchplay检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        headers2 = {
            'authorization': 'Basic NTQ3MzM0NDgtYTU3Yi00MjU2LWE4MTEtMzdlYzNkNjJmM2E0Ok90QzR3elJRR2hLQ01sSDc2VEoy'
        }
        async with session.get(catchplayurl, proxy=proxy, timeout=5, headers=headers2) as res:
            if res.status == 200:
                resdata = await res.json()
                issupport = resdata.get('code', '-1')
                region = resdata.get('data', {}).get('isoCode', "N/A")
                Collector.info['catchplay'] = f"解锁({region})" if issupport == '0' else "失败"
            elif res.status == 400:
                Collector.info['catchplay'] = "失败"
            else:
                Collector.info['catchplay'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("catchplay请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_catchplay(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("catchplay请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_catchplay(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_catchplay(Collector, session, proxy=proxy))


# cleaner section
def get_catchplay_info(ReCleaner):
    """
    获得catchplay解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁（地区代码）、失败、N/A]
    """
    try:
        if 'catchplay' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("catchplay解锁：" + str(ReCleaner.data.get('catchplay', "N/A")))
            return ReCleaner.data.get('catchplay', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅Catchplay", callback_data='✅Catchplay')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("catchplay")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
