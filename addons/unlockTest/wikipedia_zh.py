import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton


# collector section


async def fetch_wikipedia_zh(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    中文维基百科检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    wikipediaurl = "https://zh.m.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&" \
                   "prop=revisions%7Cinfo&rvprop=content%7Ctimestamp&titles=%E8%8D%94%E6%9E%9D&intestactions=edit&" \
                   "intestactionsdetail=full&rvsection=0"
    try:
        async with session.get(wikipediaurl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.json()
                is_blocked = ''
                d1 = resdata.get('query', {}).get('pages', [])
                if d1:
                    d2 = d1[0].get('actions', {}).get('edit', [])
                    if d2:
                        is_blocked = d2[0].get('code', '')
                Collector.info['维基百科(中文)'] = "禁止编辑" if is_blocked == 'blocked' else "允许编辑"
            else:
                Collector.info['维基百科'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("维基百科请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_wikipedia_zh(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("维基百科请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_wikipedia_zh(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_wikipedia_zh(Collector, session, proxy=proxy))


# cleaner section
def get_wikipedia_info(ReCleaner):
    """
    获得维基百科是否允许编辑信息
    :param ReCleaner:
    :return: str: 地区信息: [允许编辑、禁止编辑、N/A]
    """
    try:
        if '维基百科(中文)' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("维基百科(中文)：" + str(ReCleaner.data.get('维基百科(中文)', "N/A")))
            return ReCleaner.data.get('维基百科(中文)', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅维基百科(中文)", callback_data='✅维基百科(中文)')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("维基百科(中文)")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
