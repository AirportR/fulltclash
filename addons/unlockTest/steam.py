import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton


# collector section


async def fetch_steam(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    steam货币检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    steamurl = "https://store.steampowered.com/app/761830"
    try:
        async with session.get(steamurl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.text()
                index = resdata.find('priceCurrency')
                region = resdata[index + 24:index + 27]
                Collector.info['steam货币'] = f"解锁({region})" if index > 0 else "失败"
            else:
                Collector.info['steam货币'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("steam货币请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_steam(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("steam货币请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_steam(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_steam(Collector, session, proxy=proxy))


# cleaner section
def get_steam_info(ReCleaner):
    """
    获得steam货币地区信息
    :param ReCleaner:
    :return: str: 地区信息: [（地区代码）、失败、N/A]
    """
    try:
        if 'steam货币' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("steam货币：" + str(ReCleaner.data.get('steam货币', "N/A")))
            return ReCleaner.data.get('steam货币', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅steam货币", callback_data='✅steam货币')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("steam货币")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
