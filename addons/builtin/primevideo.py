import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

# collector section
primevideourl = "https://www.primevideo.com"


async def fetch_primevideo(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    bbciplayer检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.get(primevideourl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.text()
                index = resdata.find('"currentTerritory":')
                region = resdata[index + 20:index + 22]
                Collector.info['primevideo'] = f"解锁({region})" if index > 0 else "失败"
            else:
                Collector.info['primevideo'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("primevideo请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_primevideo(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("primevideo请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_primevideo(Collector, session, proxy=proxy, reconnection=reconnection - 1)


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_primevideo(Collector, session, proxy=proxy))


# cleaner section
def get_primevideo_info(ReCleaner):
    """
    获得primevideo解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁（地区代码）、失败、N/A]
    """
    try:
        if 'primevideo' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("primevideo解锁：" + str(ReCleaner.data.get('primevideo', "N/A")))
            return ReCleaner.data.get('primevideo', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Primevideo",
    "TASK": task,
    "GET": get_primevideo_info
}
