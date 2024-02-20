import asyncio
import re

import aiohttp
from loguru import logger

try:
    from utils import retry
except ImportError:
    def retry():
        def wrapper(func):
            async def inner(*args, **kwargs):
                await func(*args, **kwargs)

            return inner

        return wrapper

openaiurl2 = "https://chat.openai.com/cdn-cgi/trace"


@retry(3)
async def fetch_openai(collector, session: aiohttp.ClientSession, proxy=None):
    """
    openai封锁检测
    :param collector: 采集器
    :param session:
    :param proxy:
    :return:
    """
    h1 = {
        'authority': 'api.openai.com',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'authorization': 'Bearer null',
        'content-type': 'application/json',
        'origin': 'https://platform.openai.com',
        'referer': 'https://platform.openai.com/',
        'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }
    h2 = {
        'authority': 'ios.chat.openai.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/' +
                  'signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9',
        'sec-ch-ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }
    region = ""
    resp1 = await session.get('https://api.openai.com/compliance/cookie_requirements', headers=h1,
                              proxy=proxy, timeout=5)
    resp2 = await session.get('https://ios.chat.openai.com/', headers=h2,
                              proxy=proxy, timeout=5)
    resp3 = await session.get(openaiurl2, proxy=proxy, timeout=5)
    if resp3.status == 200:
        text3 = await resp3.text()
        index3 = text3.find("loc=")
        if index3 > 0:
            region = text3[index3 + 4:index3 + 6].upper()
    if region:
        region = f"({region})"
    # 获取响应的文本内容
    text1 = await resp1.text()
    text2 = await resp2.text()
    resp1.close()
    resp2.close()
    # 检查是否包含特定的字符串
    result1 = re.search('unsupported_country', text1)
    result2 = re.search('VPN', text2)
    # 根据结果输出不同的信息
    if not result2 and not result1:
        collector.info['openai'] = f"解锁{region}"
    elif result2 and result1:
        collector.info['openai'] = "失败"
    elif not result1 and result2:
        collector.info['openai'] = f"仅网页{region}"
    elif result1 and not result2:
        collector.info['openai'] = f"仅APP{region}"
    else:
        collector.info['openai'] = "N/A"
    return True


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_openai(Collector, session, proxy=proxy))


# cleaner section
def get_openai_info(ReCleaner):
    """
    获得openai解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'openai' not in ReCleaner.data:
            return "N/A"
        else:
            return ReCleaner.data.get('openai', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "OpenAI",
    "TASK": task,
    "GET": get_openai_info
}


async def demo():
    # class FakeColl:
    #     def __init__(self):
    #         self.info = {}
    #         self.data = self.info
    #
    # fakecl = FakeColl()
    #
    # session = aiohttp.ClientSession()
    # await fetch_openai(fakecl, session, proxy='http://127.0.0.1:11112')
    # print(get_openai_info(fakecl))
    # await session.close()
    from utils import script_demo
    await script_demo(fetch_openai, proxy='http://127.0.0.1:11112')

if __name__ == "__main__":
    asyncio.run(demo())
