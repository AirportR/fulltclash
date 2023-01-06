import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton


# collector section


async def fetch_uma(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    赛马娘检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    umaurl = "https://api-umamusume.cygames.jp/"  # 赛马娘
    try:
        _headers = {
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            #               'Chrome/102.0.5005.63 Safari/537.36',
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ALP-AL00 Build/HUAWEIALP-AL00)"
        }
        async with session.get(umaurl, headers=_headers, proxy=proxy, timeout=5) as res:
            if res.status == 404:
                Collector.info['赛马娘'] = "解锁"
            elif res.status == 403:
                Collector.info['赛马娘'] = "失败"
            else:
                Collector.info['赛马娘'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("赛马娘请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_uma(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("赛马娘请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_uma(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_uma(Collector, session, proxy=proxy))


# cleaner section
def get_uma_info(ReCleaner):
    """
    获得赛马娘解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if '赛马娘' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            # logger.info("赛马娘解锁：" + str(ReCleaner.data.get('赛马娘', "N/A")))
            return ReCleaner.data.get('赛马娘', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅赛马娘", callback_data='✅赛马娘')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("赛马娘")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
