import asyncio
import aiohttp
from loguru import logger

from utils import retry


@retry(3)
async def fetch_claude(collector, session: aiohttp.ClientSession, proxy=None):
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
    url = 'https://claude.ai/login'
    async with session.get(url, headers=headers, proxy=proxy, timeout=5) as resp:
        if resp.history:
            rurl = resp.history[0].headers.get('Location', '')
            if "unavailable" in rurl:
                collector.info['claude'] = "失败"
                return True
        if resp.status == 200:
            collector.info['claude'] = "解锁"
        else:
            collector.info['claude'] = str(resp.status)
    return True


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_claude(Collector, session, proxy=proxy))


# cleaner section
def get_claude_info(ReCleaner):
    """
    获得解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'claude' not in ReCleaner.data:
            return "N/A"
        else:
            return ReCleaner.data.get('claude', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Claude",
    "TASK": task,
    "GET": get_claude_info
}


async def demo():
    from utils import script_demo
    await script_demo(fetch_claude, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
