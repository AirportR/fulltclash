import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
netflix_url1 = "https://www.netflix.com/title/70143836"  # 非自制
netflix_url2 = "https://www.netflix.com/title/70242311"  # 自制


async def fetch_netflix_new(Collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=5):
    """
    新版Netflix检测
    :param flag:
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        if flag == 1:
            async with session.get(netflix_url1, proxy=proxy, timeout=5) as res:
                logger.info("非自制剧状态: " + str(res.status))
                if res.status == 200:  # 解锁非自制
                    text = await res.text()
                    try:
                        locate = text.find("preferredLocale")  # 定位到关键标签
                        if locate > 0:
                            region = text[locate + 29:locate + 31]
                            Collector.info['netflix_new'] = f"解锁({region})"
                        else:
                            region = "未知"
                            Collector.info['netflix_new'] = f"解锁({region})"
                    except Exception as e:
                        logger.error(e)
                        Collector.info['netflix_new'] = "N/A"
                elif res.status == 403:
                    if reconnection == 0:
                        logger.info("不支持非自制剧，正在检测自制剧...")
                        await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                        return
                    await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection-1)
                else:
                    logger.info("不支持非自制剧，正在检测自制剧...")
                    await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=reconnection)
        elif flag == 2:
            async with session.get(netflix_url2, proxy=proxy, timeout=5) as res:
                logger.info("自制剧状态: " + str(res.status))
                if res.status == 200:  # 解锁自制
                    Collector.info['netflix_new'] = "自制"
                elif res.status == 403:
                    if reconnection == 0:
                        Collector.info['netflix_new'] = "失败"
                        return
                    await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection-1)
                else:
                    Collector.info['netflix_new'] = "失败"
        else:
            return
    except ClientConnectorError as c:
        logger.warning("Netflix请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("Netflix请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_netflix_new(Collector, session, proxy=proxy))


# cleaner section
def get_netflix_info_new(ReCleaner):
    """
    获得hbo解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'netflix_new' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("netflix (新)解锁：" + str(ReCleaner.data.get('netflix_new', "N/A")))
            return ReCleaner.data.get('netflix_new', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅Netflix(新)", callback_data='✅Netflix(新)')

if __name__ == "__main__":
    "this is a demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from libs.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("Netflix(新)")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start(proxy="http://127.0.0.1:1111"))
    print(cl.info)
