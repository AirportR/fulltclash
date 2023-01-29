import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
abemaurl = "https://api.abema.io/v1/ip/check?device=android"  # 非自制


async def fetch_abema(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    abema检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.get(abemaurl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.json()
                region = resdata.get('isoCountryCode', "N/A")
                Collector.info['abema'] = "本土解锁" if region == "JP" else "解锁({})".format(region)
            elif res.status == 403:
                Collector.info['abema'] = "失败"
            else:
                Collector.info['abema'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("Abema请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_abema(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['abema'] = "连接错误"
    except asyncio.exceptions.TimeoutError:
        logger.warning("Abema请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_abema(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['abema'] = "超时"


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_abema(Collector, session, proxy=proxy))


# cleaner section
def get_abema_info(ReCleaner):
    """
    获得abema解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'abema' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("abema解锁：" + str(ReCleaner.data.get('abema', "N/A")))
            return ReCleaner.data.get('abema', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅Abema", callback_data='✅Abema')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("Abema")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
