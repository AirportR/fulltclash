import re
import ssl

import asyncio
import aiohttp
from aiohttp import ClientConnectorError, ServerDisconnectedError
from loguru import logger
from aiohttp_socks import ProxyConnectionError

# collector section
netflix_url1 = "https://www.netflix.com/title/70143836"  # 非自制
netflix_url2 = "https://www.netflix.com/title/81280792"  # 自制


# async def fetch_netflix(collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=3,
#                         netflixurl: str = None):
#     """
#     新版Netflix检测
#     :param flag
#     :param collector: 采集器
#     :param session:
#     :param proxy:
#     :param netflixurl: 自定义非自制剧url
#     :param reconnection: 重连次数
#     :return:
#     """
#     headers = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," +
#                   "application/signed-exchange;v=b3;q=0.9",
#         "accept-language": "zh-CN,zh;q=0.9",
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
#                       'Chrome/102.0.5005.63 Safari/537.36'
#     }
#     netflix_url = netflix_url1 if netflixurl is None else netflixurl
#     try:
#         if flag == 1:
#             async with session.get(netflix_url, proxy=proxy, timeout=15, headers=headers) as res:
#                 if res.status == 200:  # 解锁非自制
#                     text = await res.text()
#                     try:
#                         # 正则表达式模式
#                         pattern = r'"country":"([^"]+)"'
#
#                         # 匹配并提取国家名称
#                         match = re.search(pattern, text)
#                         if match:
#                             region = match.group(1)
#                             collector.info['netflix'] = f"解锁({region})"
#                         else:
#                             region = "未知"
#                             collector.info['netflix'] = f"解锁({region})"
#                     except IndexError as e:
#                         logger.error(e)
#                         collector.info['netflix'] = "N/A"
#                 elif res.status == 403:
#                     if reconnection == 0:
#                         logger.info("不支持非自制剧，正在检测自制剧...")
#                         await fetch_netflix(collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
#                         return
#                     await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
#                 elif res.status == 503:
#                     logger.info("非自制剧服务不可用（被banIP），正在检测自制剧...")
#                     await fetch_netflix(collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
#                     return
#                 else:
#                     logger.info("不支持非自制剧，正在检测自制剧...")
#                     await fetch_netflix(collector, session, flag=flag + 1, proxy=proxy, reconnection=reconnection)
#         elif flag == 2:
#             async with session.get(netflix_url2, proxy=proxy, timeout=5) as res:
#                 if res.status == 200:  # 解锁自制
#                     collector.info['netflix'] = "自制"
#                 elif res.status == 403:
#                     if reconnection == 0:
#                         collector.info['netflix'] = "失败"
#                         return
#                     await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
#                 elif res.status == 503:
#                     collector.info['netflix'] = "-"
#                     return
#                 else:
#                     collector.info['netflix'] = "失败"
#         else:
#             return
#     except ClientConnectorError as c:
#         logger.warning("Netflix请求发生错误:" + str(c))
#         if reconnection != 0:
#             await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
#         else:
#             collector.info['netflix'] = "连接错误"
#     except ServerDisconnectedError as s:
#         logger.warning("Netflix请求发生错误:" + str(s))
#         if reconnection != 0:
#             await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
#         else:
#             collector.info['netflix'] = "-"
#
#     except asyncio.exceptions.TimeoutError:
#         logger.warning("Netflix请求超时，正在重新发送请求......")
#         if reconnection != 0:
#             await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
#         else:
#             collector.info['netflix'] = "超时"
#     except ProxyConnectionError as p:
#         logger.warning("似乎目标端口未开启监听")
#         logger.warning(str(p))


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
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"15.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0'
    }
    cookies = {
        'flwssn': 'd2c72c47-49e9-48da-b7a2-2dc6d7ca9fcf',
        'nfvdid': 'BQFmAAEBEMZa4XMYVzVGf9-kQ1HXumtAKsCyuBZU4QStC6CGEGIVznjNuuTerLAG8v2-9V_kYhg5uxTB5_yyrmqc02U5l1Ts74Qquezc9AE-LZKTo3kY3g%3D%3D',
        'SecureNetflixId': 'v%3D3%26mac%3DAQEAEQABABSQHKcR1d0sLV0WTu0lL-BO63TKCCHAkeY.%26dt%3D1745376277212',
        'NetflixId': 'v%3D3%26ct%3DBgjHlOvcAxLAAZuNS4_CJHy9NKJPzUV-9gElzTlTsmDS1B59TycR-fue7f6q7X9JQAOLttD7OnlldUtnYWXL7VUfu9q4pA0gruZKVIhScTYI1GKbyiEqKaULAXOt0PHQzgRLVTNVoXkxcbu7MYG4wm1870fZkd5qrDOEseZv2WIVk4xIeNL87EZh1vS3RZU3e-qWy2tSmfSNUC-FVDGwxbI6-hk3Zg2MbcWYd70-ghohcCSZp5WHAGXg_xWVC7FHM3aOUVTGwRCU1RgGIg4KDKGr_wsTRRw6HWKqeA..',
        'gsid': '09bb180e-fbb1-4bf6-adcb-a3fa1236e323',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Apr+23+2025+10%3A47%3A11+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202411.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=f13f841e-c75d-4f95-ab04-d8f581cac53e&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fwww.netflix.com%2Fsg-zh%2Ftitle%2F81280792&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1'
    }

    netflix_url = netflix_url1 if netflixurl is None else netflixurl
    _myssl = myssl()
    try:
        task1 = asyncio.create_task(
            session.get('https://www.netflix.com/title/81280792', headers=headers, cookies=cookies, proxy=proxy)
        )
        task2 = asyncio.create_task(
            session.get('https://www.netflix.com/title/70143836', headers=headers, cookies=cookies, proxy=proxy)
        )
        response1, response2 = await asyncio.gather(task1, task2)
        tmpresult1 = await response1.text()
        tmpresult2 = await response2.text()
        result1 = "Oh no!" in tmpresult1
        result2 = "Oh no!" in tmpresult2
        if result1 and result2:
            collector.info['netflix'] = "自制"
        if not result1 and not result2:
            region_match = re.search(r'data-country="([A-Z]*)"', tmpresult1)
            region = region_match.group(1) if region_match else "Unknown"
            collector.info['netflix'] = f"解锁({region})"
        else:
            collector.info['netflix'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("Netflix请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "连接错误"
    except ServerDisconnectedError:
        if reconnection != 0:
            await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "-"

    except asyncio.exceptions.TimeoutError:
        if reconnection != 0:
            await fetch_netflix(collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['netflix'] = "超时"
    except ProxyConnectionError as p:
        logger.warning(str(p))


def task(Collector, session, proxy, netflixurl: str = None):
    return asyncio.create_task(fetch_netflix(Collector, session, proxy=proxy, netflixurl=netflixurl))


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
