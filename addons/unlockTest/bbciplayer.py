import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
bbcurl = "https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_one_london/format/json/jsfunc/JS_callbacks0"


async def fetch_bbciplayer(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    bbciplayer检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.get(bbcurl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.text()
                issupport = resdata.find('geolocation')
                Collector.info['BBC'] = "失败" if issupport > 0 else "解锁"
            else:
                Collector.info['BBC'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("BBCiplayer请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_bbciplayer(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("BBCiplayer请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_bbciplayer(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_bbciplayer(Collector, session, proxy=proxy))


# cleaner section
def get_bbc_info(ReCleaner):
    """
    获得bbc_iplayer解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'BBC' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("BBC解锁：" + str(ReCleaner.data.get('BBC', "N/A")))
            return ReCleaner.data.get('BBC', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅BBC", callback_data='✅BBC')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("BBC")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
