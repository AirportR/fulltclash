import asyncio
import re

import aiohttp
from loguru import logger

# 解锁判定方式；目前Copilot除了极少数地区未提供支持，其他的几乎都支持。和节点质量关系并不大。
UNS_REGION = ["MY", "CV", "CN", "CU", "SR", "TL", "IR", 'CI', 'KP', 'PS', 'RU', 'SH', 'SY']
try:
    from utils import retry
except ImportError:
    def retry(_=3):
        def wrapper(func):
            async def inner(*args, **kwargs):
                await func(*args, **kwargs)

            return inner

        return wrapper


@retry(3)
async def fetch_copilot(collector, session: aiohttp.ClientSession, proxy=None):
    """
    解锁检测
    :param collector: 采集器
    :param session:
    :param proxy:
    :return:
    """
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }
    url = 'https://www.bing.com/chat?toWww=1'
    async with session.get(url, headers=headers, proxy=proxy, timeout=5) as resp:
        if resp.history:
            for i in resp.history:
                if "cn.bing.com" in i.headers.get('Location', ''):
                    collector.info['copilot'] = '失败(CN)'
                    return True
        if resp.status == 200:
            text = await resp.text()
            index = text.find("b_wlcmPersLogo.copilot")
            # print("b_wlcmPersLogo.copilot:", index)
            collector.info['copilot'] = str(index)
            # return True
            try:
                region = re.search(r'Region:"(\w\w)"', text).group(1)
                # region2 = re.search(r'Region:"(.*)"', text).group(1)
                # print(region2)
                region = f"({region})"
            except (IndexError, re.error, Exception):
                region = ""
            if region == "WW":
                region = ""
            region = region.upper()
            collector.info['copilot'] = "失败" + region if index == -1 or region in UNS_REGION else '解锁' + region
            return True
    return True


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_copilot(Collector, session, proxy=proxy))


# cleaner section
def get_copilot_info(ReCleaner):
    """
    获得解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'copilot' not in ReCleaner.data:
            return "N/A"
        else:
            return ReCleaner.data.get('copilot', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "微软Copilot",
    "TASK": task,
    "GET": get_copilot_info
}


async def demo():
    from utils import script_demo
    await script_demo(fetch_copilot, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
