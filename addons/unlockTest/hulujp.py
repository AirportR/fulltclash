import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton


# collector section


async def fetch_hulujp(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    Hulu JP检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    hulujpurl = "https://id.hulu.jp"  # Hulu jp
    try:
        _headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36',
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "zh-CN,zh;q=0.9",
            "sec-ch-ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\", \"Google Chrome\";v=\"108\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
        async with session.get(hulujpurl, headers=_headers, proxy=proxy, timeout=5) as res:
            if res.history:
                a = res.history[0]
                location = a.headers.get('Location', '')
                if location:
                    index = location.find('restrict')
                    Collector.info['Hulu JP'] = "失败" if index > 0 else "解锁"
                else:
                    Collector.info['Hulu JP'] = "未知"
            else:
                Collector.info['Hulu JP'] = "未知"
    except ClientConnectorError as c:
        logger.warning("Hulu JP'请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_hulujp(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("Hulu JP'请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_hulujp(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_hulujp(Collector, session, proxy=proxy))


# cleaner section
def get_hulujp_info(ReCleaner):
    """
    获得Hulu JP'解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'Hulu JP' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            # logger.info("Hulu JP解锁：" + str(ReCleaner.data.get('Hulu JP', "N/A")))
            return ReCleaner.data.get('Hulu JP', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅Hulu JP", callback_data='✅Hulu JP')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("Hulu JP")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
