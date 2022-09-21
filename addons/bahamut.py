import asyncio
import json
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

# collector section
bahamut_url = "https://ani.gamer.com.tw/ajax/token.php?adID=89422&sn=14667"


async def fetch_bahamut(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    bahamut检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection:
    :return:
    """
    try:
        async with session.get(bahamut_url, proxy=proxy, timeout=5) as bahamut:
            if bahamut.status == 200:
                pretext = await bahamut.text()
                text = json.loads(pretext)
                try:
                    flag = text.get('animeSn', '')
                except:
                    flag = ''
                if flag:
                    Collector.info['bahamut'] = "解锁"
                    logger.info("bahamut成功访问")
                else:
                    Collector.info['bahamut'] = "失败"
            elif bahamut.status == 403:
                Collector.info['bahamut'] = "失败"
            else:
                Collector.info['bahamut'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("bahamut请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_bahamut(Collector, session=session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("bahamut请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_bahamut(Collector, session=session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_bahamut(Collector, session, proxy=proxy))


# cleaner section
def get_bahamut_info(ReCleaner):
    """
    获得bahamut解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'bahamut' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("bahamut 状态：" + str(ReCleaner.data['bahamut']))
            return ReCleaner.data['bahamut']
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

b10 = InlineKeyboardButton("✅Bahamut", callback_data='✅Bahamut')
