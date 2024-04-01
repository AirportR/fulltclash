import ssl

import asyncio
import aiohttp
from aiohttp import ClientConnectorError, ServerDisconnectedError
from loguru import logger
from aiohttp_socks import ProxyConnectionError

# collector section
netflix_url1 = "https://www.netflix.com/title/70143836"  # 非自制
netflix_url2 = "https://www.netflix.com/title/81280792"  # 自制


async def fetch_netflix(collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=3,
                        netflixurl: str = None):
    """
    新版Netflix检测
    :param flag
    :param collector: 采集器
    :param session:
    :param proxy:
    :param netflixurl: 自定义非自制剧url
    :param reconnection: 重连次数
    :return:
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," +
                  "application/signed-exchange;v=b3;q=0.9",
        "accept-language": "zh-CN,zh;q=0.9",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/102.0.5005.63 Safari/537.36'
    }
    netflix_url = netflix_url1 if netflixurl is None else netflixurl
    try:
        if flag == 1:
            async with session.get(netflix_url, proxy=proxy, timeout=15, headers=headers) as res:
                if res.status == 200:  # 解锁非自制
                    text = await res.text()
                    try:
                        locate = text.find("preferredLocale")  # 定位到关键标签
                        if locate > 0:
                            region = text[locate + 29:locate + 31]
                            collector.info['netflix'] = f"解锁({region})"
                        else:
                            region = "未知"
                            collector.info['netflix'] = f"解锁({region})"
                    except IndexError as e:
                        logger.error(e)
                        collector.info['netflix'] = "N/A"
                elif res.status == 403:
                    if reconnection == 0:
                        logger.info("不支持非自制剧，正在检测自制剧...")
                        await fetch_netflix(collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                        return
                    await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                elif res.status == 503:
                    logger.info("非自制剧服务不可用（被banIP），正在检测自制剧...")
                    await fetch_netflix(collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                    return
                else:
                    logger.info("不支持非自制剧，正在检测自制剧...")
                    await fetch_netflix(collector, session, flag=flag + 1, proxy=proxy, reconnection=reconnection)
        elif flag == 2:
            async with session.get(netflix_url2, proxy=proxy, timeout=5) as res:
                if res.status == 200:  # 解锁自制
                    collector.info['netflix'] = "自制"
                elif res.status == 403:
                    if reconnection == 0:
                        collector.info['netflix'] = "失败"
                        return
                    await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                elif res.status == 503:
                    collector.info['netflix'] = "-"
                    return
                else:
                    collector.info['netflix'] = "失败"
        else:
            return
    except ClientConnectorError as c:
        logger.warning("Netflix请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "连接错误"
    except ServerDisconnectedError as s:
        logger.warning("Netflix请求发生错误:" + str(s))
        if reconnection != 0:
            await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "-"

    except asyncio.exceptions.TimeoutError:
        logger.warning("Netflix请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "超时"
    except ProxyConnectionError as p:
        logger.warning("似乎目标端口未开启监听")
        logger.warning(str(p))


async def fetch_netflix_new(collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=3,
                            netflixurl: str = None):
    """
    新版Netflix检测
    :param flag
    :param collector: 采集器
    :param session:
    :param proxy:
    :param netflixurl: 自定义非自制剧url
    :param reconnection: 重连次数
    :return:
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," +
                  "application/signed-exchange;v=b3;q=0.9",
        "accept-language": "zh-CN,zh;q=0.9",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/102.0.5005.63 Safari/537.36'
    }
    netflix_url = netflix_url1 if netflixurl is None else netflixurl
    _myssl = myssl()
    try:
        if flag == 1:
            async with session.get(netflix_url, proxy=proxy, timeout=15, headers=headers, ssl=_myssl) as res:
                if res.status == 200:  # 解锁非自制
                    text = await res.text()
                    try:
                        locate = text.find("preferredLocale")  # 定位到关键标签
                        if locate > 0:
                            region = text[locate + 29:locate + 31]
                            collector.info['netflix'] = f"解锁({region})"
                        else:
                            region = "未知"
                            collector.info['netflix'] = f"解锁({region})"
                    except IndexError as e:
                        logger.error(e)
                        collector.info['netflix'] = "N/A"
                elif res.status == 403:
                    if reconnection == 0:
                        await fetch_netflix_new(collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                        return
                    await fetch_netflix_new(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                elif res.status == 503:
                    await fetch_netflix_new(collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                    return
                else:
                    await fetch_netflix_new(collector, session, flag=flag + 1, proxy=proxy, reconnection=reconnection)
        elif flag == 2:
            async with session.get(netflix_url2, proxy=proxy, timeout=5, ssl=_myssl) as res:
                if res.status == 200:  # 解锁自制
                    collector.info['netflix'] = "自制"
                elif res.status == 403:
                    if reconnection == 0:
                        collector.info['netflix'] = "失败"
                        return
                    await fetch_netflix_new(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                elif res.status == 503:
                    collector.info['netflix'] = "-"
                    return
                else:
                    collector.info['netflix'] = "失败"
        else:
            return
    except ClientConnectorError as c:
        logger.warning("Netflix请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_netflix_new(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "连接错误"
    except ServerDisconnectedError:
        if reconnection != 0:
            await fetch_netflix_new(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "-"

    except asyncio.exceptions.TimeoutError:
        if reconnection != 0:
            await fetch_netflix_new(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "超时"
    except ProxyConnectionError as p:
        logger.warning(str(p))


def task(Collector, session, proxy, netflixurl: str = None):
    return asyncio.create_task(fetch_netflix_new(Collector, session, proxy=proxy, netflixurl=netflixurl))


# cleaner section
def get_netflix_info(ReCleaner):
    """
    获得netflix解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'netflix' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("netflix解锁：" + str(ReCleaner.data.get('netflix', "N/A")))
            return ReCleaner.data.get('netflix', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


get_netflix_info_new = get_netflix_info


def myssl() -> ssl.SSLContext:
    _myssl = ['DH+3DES', 'ECDH+3DES', 'RSA+3DES', 'RSA+HIGH', 'RSA+AES', 'ECDH+AESGCM', 'DH+AES256', 'ECDH+HIGH',
              'DH+AESGCM', 'ECDH+AES256', 'RSA+AESGCM', 'ECDH+AES128', 'DH+HIGH', 'DH+AES']
    _ciphers = ":".join(_myssl)
    _sslcontext = ssl.create_default_context()
    _sslcontext.set_ciphers(_ciphers)
    return _sslcontext


SCRIPT = {
    "MYNAME": "Netflix",
    "TASK": task,
    "GET": get_netflix_info,
    "RANK": 0
}


async def test():
    class FakeColl:
        def __init__(self):
            self.info = {}
            self.data = {}

    coll = FakeColl()
    async with aiohttp.ClientSession(connector=None) as session:
        await fetch_netflix(coll, session, proxy="http://127.0.0.1:11112")
    coll.data = coll.info
    print(get_netflix_info(coll))
    await asyncio.sleep(1)


if __name__ == '__main__':
    import sys
    print("python二进制位置: ", sys.executable)
    print("aiohttp版本: ", aiohttp.__version__)
    asyncio.run(test())
