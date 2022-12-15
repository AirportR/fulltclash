import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton


# collector section
hbomax_url = "https://www.hbomax.com/"


async def fetch_hbomax(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    Hbomax检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection:
    :return:
    """
    try:
        async with session.get(hbomax_url, proxy=proxy, timeout=5) as hbo:
            if hbo.status == 200:
                if hbo.history:
                    a = hbo.history[0]
                    if 'availability' in a.headers.get('Location', ''):
                        Collector.info['hbomax'] = "失败"
                    else:
                        Collector.info['hbomax'] = "未知"
                else:
                    Collector.info['hbomax'] = "解锁"
                    regioninfo = hbo.headers.get('Set-Cookie', '')
                    if regioninfo:
                        region = regioninfo[12:14]
                        Collector.info['hbomax'] = "解锁({})".format(region)
            else:
                Collector.info['hbomax'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("Hbomax请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_hbomax(Collector, session=session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("Hbomax请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_hbomax(Collector, session=session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_hbomax(Collector, session, proxy=proxy))


# cleaner section
def get_hbomax_info(ReCleaner):
    """
    获得hbo解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'hbomax' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("Hbomax 状态：" + str(ReCleaner.data['hbomax']))
            return ReCleaner.data['hbomax']
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

b9 = InlineKeyboardButton("✅Hbomax", callback_data='✅Hbomax')
