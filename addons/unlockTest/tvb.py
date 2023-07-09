import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

# collector section
TVBAnywhereurl = "https://uapisfm.tvbanywhere.com.sg/geoip/check/platform/android"


async def fetch_TVBAnywhere(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    TVBAnywhere检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.get(TVBAnywhereurl, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                response_json = await res.json()
                result = response_json.get('allow_in_this_country', '')
                country = response_json.get('country', '')
                if result:
                    Collector.info['TVBAnywhere'] = f"解锁({country})" if country else "解锁"
                else:
                    Collector.info['TVBAnywhere'] = "失败"
            else:
                Collector.info['TVBAnywhere'] = "未知"
    except ClientConnectorError as c:
        logger.warning("TVBAnywhere请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_TVBAnywhere(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['TVBAnywhere'] = "连接错误"
    except asyncio.exceptions.TimeoutError:
        logger.warning("TVBAnywhere请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_TVBAnywhere(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['TVBAnywhere'] = "超时"


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_TVBAnywhere(Collector, session, proxy=proxy))


# cleaner section
def get_TVBAnywhere_info(ReCleaner):
    """
    获得TVBAnywhere解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'TVBAnywhere' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("TVBAnywhere：" + str(ReCleaner.data.get('TVBAnywhere', "N/A")))
            return ReCleaner.data.get('TVBAnywhere', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "TVB",
    "TASK": task,
    "GET": get_TVBAnywhere_info
}
