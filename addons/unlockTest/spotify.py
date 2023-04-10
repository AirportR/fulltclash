import asyncio

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

# collector section
_data = {
    'birth_day': 23,
    'birth_month': 11,
    'birth_year': 2000,
    'collect_personal_info': 'undefined',
    'creation_flow': '',
    'creation_point': 'https%3A%2F%2Fwww.spotify.com%2Fhk-en%2F',
    'displayname': 'Gay%20Lord',
    'gender': 'male',
    'iagree': 1,
    'key': 'a1e486e2729f46d6bb368d6b2bcda326',
    'platform': 'www',
    'referrer': '',
    'send-email': 0,
    'thirdpartyemail': 0,
    'identifier_token': 'AgE6YTvEzkReHNfJpO114514'
}
_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/102.0.5005.63 Safari/537.36',
    'Accept-Language': 'en'
}
spotifyurl = "https://spclient.wg.spotify.com/signup/public/v1/account"


async def fetch_spotify(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    spotify检测
    :param Collector: 采集器
    :param session: aiohttp.ClientSession()类
    :param proxy: 默认None即可
    :param reconnection: 重连次数
    :return:
    """
    try:
        async with session.post(spotifyurl, data=_data, headers=_headers, proxy=proxy, timeout=5) as res:
            if res.status == 200:
                resdata = await res.json()
                status = resdata.get('status', "")
                if status:
                    if status == 320 or status == 120:
                        Collector.info['spotify'] = "禁止注册"
                    elif status == 311:
                        region = resdata.get('country', "")
                        is_country_launched = resdata.get('is_country_launched', '')
                        if region and is_country_launched:
                            Collector.info['spotify'] = f"允许注册({region})"
                    else:
                        Collector.info['spotify'] = "未知"
                else:
                    Collector.info['spotify'] = "N/A"
            else:
                Collector.info['spotify'] = "未知"
    except ClientConnectorError as c:
        logger.warning("Spotify请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_spotify(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['spotify'] = "连接错误"
    except asyncio.exceptions.TimeoutError:
        logger.warning("Spotify请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_spotify(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['spotify'] = "超时"


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_spotify(Collector, session, proxy=proxy))


# cleaner section
def get_spotify_info(ReCleaner):
    """
    获得spotify解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'spotify' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            # logger.info("spotify(解锁)：" + str(ReCleaner.data.get('spotify', "N/A")))
            return ReCleaner.data.get('spotify', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Spotify",
    "TASK": task,
    "GET": get_spotify_info
}
