import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
myvideourl = "https://www.myvideo.net.tw/serviceAreaBlock.do"


async def fetch_myvideo(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    Myvideo检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.get(myvideourl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.text()
                index = resdata.find('很抱歉，MyVideo僅提供台灣IP使用')
                Collector.info['myvideo'] = "失败" if index > 0 else "解锁"
            else:
                Collector.info['myvideo'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("myvideo请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_myvideo(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("myvideo请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_myvideo(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_myvideo(Collector, session, proxy=proxy))


# cleaner section
def get_myvideo_info(ReCleaner):
    """
    获得myvideo解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'myvideo' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("myvideo解锁：" + str(ReCleaner.data.get('myvideo', "N/A")))
            return ReCleaner.data.get('myvideo', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅Myvideo", callback_data='✅Myvideo')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("myvideo")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
