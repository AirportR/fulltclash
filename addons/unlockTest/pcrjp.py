import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
pcrurl = "https://api-priconne-redive.cygames.jp"  # 非自制


async def fetch_pcr(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    公主链接检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "cache-control": "max-age=0",
            "sec-ch-ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\", \"Google Chrome\";v=\"108\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
        async with session.get(pcrurl, headers=headers, proxy=proxy, timeout=5) as res:
            if res.status == 404:
                Collector.info['公主连结'] = "解锁"
            elif res.status == 403:
                Collector.info['公主连结'] = "失败"
            else:
                Collector.info['公主连结'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("公主连结请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_pcr(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("公主连结请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_pcr(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_pcr(Collector, session, proxy=proxy))


# cleaner section
def get_pcr_info(ReCleaner):
    """
    获得公主连结解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if '公主连结' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("公主连结解锁：" + str(ReCleaner.data.get('公主连结', "N/A")))
            return ReCleaner.data.get('公主连结', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅公主连结", callback_data='✅公主连结')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("公主连结")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
