# DNS区域检测，可一定程度判断当前节点是否是广播IP
import asyncio
import random
import string

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

from utils import retry

SCRIPT_NAME = "DNS区域"


def random_string(length: int) -> str:
    """
    生成指定长度的随机字符串,只包含字母和数字
    Args:
        length (int): 生成字符串的长度
    Returns:
        str: 随机生成的字符串
    """
    # 只包含字母和数字
    characters = string.ascii_letters + string.digits
    # 生成随机字符串
    return ''.join(random.choice(characters) for _ in range(length))


# collector section
@retry(2)
async def fetch(collector, session: aiohttp.ClientSession, proxy=None) -> bool:
    """
    XX解锁测试
    :param collector:
    :param session:
    :param proxy:
    :return:
    """
    try:
        find_dns_url = f"http://{random_string(32)}.edns.ip-api.com/json"
        async with session.get(find_dns_url, timeout=5, proxy=proxy) as resp:
            d1: dict = await resp.json()
            dns_ip = d1.get("dns", {}).get("ip", "")
        dns_ip_url = f"http://ip-api.com/json/{dns_ip}?lang=en-US"
        async with session.get(dns_ip_url, timeout=5, proxy=proxy) as resp:
            d2: dict = await resp.json()
            dns_code = d2.get("countryCode", "").upper()
            dns_as_number = d2.get("as", "").split(" ")[0]

        collector.info[SCRIPT_NAME] = f"{dns_as_number}({dns_code})" if dns_code and dns_as_number else "-"
        return True
    except (ClientConnectorError, asyncio.exceptions.TimeoutError):
        collector.info[SCRIPT_NAME] = "连接错误"
        return False


def task(collector, session, proxy):
    return asyncio.create_task(fetch(collector, session, proxy=proxy))


# cleaner section
def get(recleaner):
    """
    获取解锁信息
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if SCRIPT_NAME not in recleaner.data:
            return "N/A"
        else:
            return recleaner.data.get(SCRIPT_NAME, "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": SCRIPT_NAME,
    "TASK": task,
    "GET": get,
    "RANK": 2
}


async def demo():
    from utils import script_demo
    await script_demo(fetch, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
