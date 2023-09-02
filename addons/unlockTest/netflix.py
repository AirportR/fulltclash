import asyncio
import aiohttp
from aiohttp import ClientConnectorError, ServerDisconnectedError
from loguru import logger
from aiohttp_socks import ProxyConnectionError
import requests

# from utils.collector import config

# collector section
netflix_url1 = "https://www.netflix.com/title/70143836"  # 非自制
netflix_url2 = "https://www.netflix.com/title/81280792"  # 自制


def fetch_netflix_old(Collector, proxy=None, flag=1, reconnection=3):
    """
    新版Netflix检测
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," +
                  "application/signed-exchange;v=b3;q=0.9",
        "accept-language": "zh-CN,zh;q=0.9",
        "upgrade-insecure-requests": "1",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36'
    }

    try:
        if flag == 1:
            res = requests.get(netflix_url1, proxies=proxy, timeout=5, headers=headers)
            if res.status_code == 200:
                text = res.text
                try:
                    locate = text.find("preferredLocale")
                    if locate > 0:
                        region = text[locate + 29:locate + 31]
                        Collector.info['netflix_new'] = f"解锁({region})"
                    else:
                        region = "未知"
                        Collector.info['netflix_new'] = f"解锁({region})"
                except IndexError as e:
                    print(e)
                    Collector.info['netflix_new'] = "N/A"
            elif res.status_code == 403:
                if reconnection == 0:
                    print("不支持非自制剧,正在检测自制剧...")
                    fetch_netflix_new(Collector, proxy, flag=flag + 1, reconnection=5)
                    return
                fetch_netflix_new(Collector, proxy, flag=flag, reconnection=reconnection - 1)

            elif res.status_code == 503:
                print("非自制剧服务不可用(被banIP),正在检测自制剧...")
                fetch_netflix_new(Collector, proxy, flag=flag + 1, reconnection=5)
                return
            else:
                print("不支持非自制剧,正在检测自制剧...")
                fetch_netflix_new(Collector, proxy, flag=flag + 1, reconnection=reconnection)

        elif flag == 2:
            res = requests.get(netflix_url2, proxies=proxy, timeout=5)
            if res.status_code == 200:
                Collector.info['netflix_new'] = "自制"
            elif res.status_code == 403:
                if reconnection == 0:
                    Collector.info['netflix_new'] = "失败"
                    return
                fetch_netflix_new(Collector, proxy, flag=flag, reconnection=reconnection - 1)
            elif res.status_code == 503:
                Collector.info['netflix_new'] = "-"
                return
            else:
                Collector.info['netflix_new'] = "失败"

    except requests.exceptions.RequestException as e:
        print("Netflix请求发生错误:" + str(e))
        if reconnection != 0 and reconnection > 27:
            fetch_netflix_new(Collector, proxy, flag=flag, reconnection=reconnection - 1)
        else:
            Collector.info['netflix_new'] = "连接错误"


async def fetch_netflix(Collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=2):
    """
    requests版本实现，若发现aiohttp的版本检测异常，可尝试此版本
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," +
                  "application/signed-exchange;v=b3;q=0.9",
        "accept-language": "zh-CN,zh;q=0.9",
        "upgrade-insecure-requests": "1",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/102.0.5005.63 Safari/537.36'
    }
    import requests
    seesion = requests.session()
    resp = seesion.get(netflix_url1, proxies=proxy)
    print(resp.status_code)
    print(resp.text[:1000])


async def fetch_netflix_new(Collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=30,
                            netflixurl: str = None):
    """
    新版Netflix检测
    :param flag
    :param Collector: 采集器
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
        "sec-ch-ua": r"\"Not_A Brand\";v=\"99\", \"Google Chrome\";v=\"109\", \"Chromium\";v=\"109\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": r"\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/102.0.5005.63 Safari/537.36'
    }
    netflix_url = netflix_url1 if netflixurl is None else netflixurl
    try:
        if flag == 1:
            async with session.get(netflix_url, proxy=proxy, timeout=5, headers=headers) as res:
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
                    except IndexError as e:
                        logger.error(e)
                        Collector.info['netflix_new'] = "N/A"
                elif res.status == 403:
                    if reconnection == 0:
                        logger.info("不支持非自制剧，正在检测自制剧...")
                        await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                        return
                    await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                elif res.status == 503:
                    logger.info("非自制剧服务不可用（被banIP），正在检测自制剧...")
                    await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                    return
                else:
                    logger.info("不支持非自制剧，正在检测自制剧...")
                    await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=reconnection)
        elif flag == 2:
            async with session.get(netflix_url2, proxy=proxy, timeout=5) as res:
                if res.status == 200:  # 解锁自制
                    Collector.info['netflix_new'] = "自制"
                elif res.status == 403:
                    if reconnection == 0:
                        Collector.info['netflix_new'] = "失败"
                        return
                    await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                elif res.status == 503:
                    Collector.info['netflix_new'] = "-"
                    return
                else:
                    Collector.info['netflix_new'] = "失败"
        else:
            return
    except ClientConnectorError as c:
        logger.warning("Netflix请求发生错误:" + str(c))
        if reconnection != 0 and reconnection > 27:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['netflix_new'] = "连接错误"
    except ServerDisconnectedError as s:
        logger.warning("Netflix请求发生错误:" + str(s))
        if reconnection != 0 and reconnection > 27:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['netflix_new'] = "-"

    except asyncio.exceptions.TimeoutError:
        logger.warning("Netflix请求超时，正在重新发送请求......")
        if reconnection > 27:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['netflix_new'] = "超时"
    except ProxyConnectionError as p:
        logger.warning("似乎目标端口未开启监听")
        logger.warning(str(p))


# def retry(count=5):
#     def wrapper(func):
#         async def inner(*args, **kwargs):
#             for _ in range(count):
#                 result = await func(*args, **kwargs)
#                 if result is True:
#                     break


def task(Collector, session, proxy, netflixurl: str = None):
    return asyncio.create_task(fetch_netflix_new(Collector, session, proxy=proxy, netflixurl=netflixurl))


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
            logger.info("netflix解锁：" + str(ReCleaner.data.get('netflix_new', "N/A")))
            return ReCleaner.data.get('netflix_new', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Netflix",
    "TASK": task,
    "GET": get_netflix_info_new
}

if __name__ == '__main__':
    class FakeColl:
        def __init__(self):
            self.info = {}


    coll = FakeColl()
    proxies = {'http': 'http://localhost:1112', 'https': 'http://localhost:1112'}
    fetch_netflix_old(coll, proxy=proxies)
    print(coll.info)
