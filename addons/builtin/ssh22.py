import asyncio

import socket

import async_timeout
import socks
import aiohttp
from loguru import logger
from aiohttp_socks import ProxyConnector
from utils import retry

SUC_LIST = []


@retry(2)
async def fetch_ssh(collector, session: aiohttp.ClientSession, proxy: str = None):
    """
    解锁检测
    :param collector: 采集器
    :param session:
    :param proxy:
    :return:
    """
    ip = ""
    if SUC_LIST:
        ip = SUC_LIST[-1]
        if len(SUC_LIST) > 10:
            SUC_LIST.clear()
    else:
        async with session.get('http://ip-api.com/json/', proxy=proxy, timeout=5) as ipres:
            if ipres.status == 200:
                ipdata = await ipres.json()
                ip = ipdata.get('query', '')

        if not ip:
            collector.info['ssh'] = "-"
            return True
    _sport = 22
    _host = ip
    conn = session.connector

    try:
        if type(conn) is ProxyConnector:
            paddr = conn._proxy_host
            pport = conn._proxy_port
        else:
            parsed = proxy.removeprefix("http://").removesuffix("/").split(":")
            paddr = parsed[0]
            pport = int(parsed[1])
        mysocket = socks.socksocket(type=socket.SOCK_STREAM)
        mysocket.set_proxy(socks.PROXY_TYPE_SOCKS5, addr=paddr, port=pport)

        mysocket.settimeout(10)

        async def check():

            async with async_timeout.timeout(10):
                mysocket.connect((_host, _sport))
                reader, writer = await asyncio.open_connection(sock=mysocket)
                a = await reader.read(1024)
                if a:
                    writer.close()
                    await writer.wait_closed()
                    if b"ssh" in a or b"SSH" in a:
                        collector.info['ssh'] = "允许访问"
                    else:
                        collector.info['ssh'] = "-"
                else:
                    collector.info['ssh'] = "无法访问"
                return True

        try:
            res = await check()
        except (TimeoutError, OSError):
            return False
        finally:
            mysocket.close()
        if res is True:
            SUC_LIST.append(ip)

    except Exception as e:
        logger.warning(str(e))
    return True


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_ssh(Collector, session, proxy=proxy))


# cleaner section
def get_ssh_info(ReCleaner):
    """
    获得解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁、失败、N/A]
    """
    try:
        if 'ssh' not in ReCleaner.data:
            return "N/A"
        else:
            return ReCleaner.data.get('ssh', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "SSH",
    "TASK": task,
    "GET": get_ssh_info
}


async def demo():
    script_func = fetch_ssh

    class FakeColl:
        def __init__(self):
            self.info = {}
            self.data = self.info

    fakecl = FakeColl()

    session = aiohttp.ClientSession()
    await script_func(fakecl, session, proxy='http://127.0.0.1:11112')
    print(fakecl.info)
    await session.close()


if __name__ == "__main__":
    asyncio.run(demo())
