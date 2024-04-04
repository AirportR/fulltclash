import asyncio

import aiohttp
from aiohttp import ClientResponse
from loguru import logger

try:
    import re2 as re
except ImportError:
    import re
from utils import retry

openaiurl = "https://chat.openai.com/favicon.ico"
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
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/102.0.5005.63 Safari/537.36',
    }
    region = ""
    task1 = asyncio.create_task(session.get('https://api.openai.com/compliance/cookie_requirements', headers=h1,
                                            proxy=proxy, timeout=5))
    task2 = asyncio.create_task(session.get('https://ios.chat.openai.com/', headers=h2,
                                            proxy=proxy, timeout=5))
    task3 = asyncio.create_task(session.get(openaiurl2, headers=_headers, proxy=proxy, timeout=5))
    task4 = asyncio.create_task(session.get(openaiurl, headers=_headers, proxy=proxy, timeout=5))
    resp = await asyncio.gather(*[task1, task2, task3, task4])

    resp1: "ClientResponse" = resp[0]
    resp2: "ClientResponse" = resp[1]
    resp3: "ClientResponse" = resp[2]
    resp4: "ClientResponse" = resp[3]
    if resp1 and resp2 and resp3 and resp4:
        if resp4.status == 403:
            text4 = await resp4.text()
            if text4.find('Please stand by, while we are checking your browser') > 0:
                collector.info['OpenAI'] = "-"
                return
            if text4.find('Unable to load site') > 0:
                collector.info['OpenAI'] = "失败1"
                return
            index = text4.find("Sorry, you have been blocked")
            if index > 0:
                collector.info['OpenAI'] = "失败2"
                return
            index2 = text4.find("You do not have access to chat.openai.com.")
            if index2 > 0:
                collector.info['OpenAI'] = "失败2"
                return
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
        resp3.close()
        resp4.close()
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


def task(collector, session, proxy):
    return asyncio.create_task(fetch_openai(collector, session, proxy=proxy))


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
    from utils import script_demo
    await script_demo(fetch_openai, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
