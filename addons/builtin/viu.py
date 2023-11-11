import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

# collector section
viuurl = "https://www.viu.com/"


async def fetch_viu(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    viu检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.get(viuurl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                if res.history:
                    location = res.history[0].headers.get('Location', '').split('/')
                    try:
                        region = location[4]
                        if region == 'no-service':
                            Collector.info['viu'] = "失败"
                        else:
                            region2 = region.upper()
                            Collector.info['viu'] = "解锁({})".format(region2)
                    except IndexError:
                        Collector.info['viu'] = "未知"
                else:
                    Collector.info['viu'] = "未知"
            else:
                Collector.info['viu'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("viu请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_viu(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("viu请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_viu(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_viu(Collector, session, proxy=proxy))


# cleaner section
def get_viu_info(ReCleaner):
    """
    获得viu解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁（地区代码）、失败、N/A]
    """
    try:
        if 'viu' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("viu解锁：" + str(ReCleaner.data.get('viu', "N/A")))
            return ReCleaner.data.get('viu', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Viu",
    "TASK": task,
    "GET": get_viu_info
}
