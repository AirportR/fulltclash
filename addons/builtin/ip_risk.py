import asyncio
import json

import aiohttp
from aiohttp import ClientConnectorError

from loguru import logger

# collector section
baseurl = "https://scamalytics.com/ip/"


async def fetch_ip_risk(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    ip风险检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    try:
        ip = ""
        conn = session.connector
        if type(conn).__name__ == 'ProxyConnector':
            proxy = "http://" + conn._proxy_host + ":" + str(conn._proxy_port)
        async with aiohttp.ClientSession() as s:
            async with s.get('http://ip.sb', proxy=proxy, timeout=5,
                             headers={'user-agent': "curl"}) as ipres:
                # ipres = await session.get('http://ip.sb', proxy='http://127.0.0.1:11112', timeout=5,
                #                           headers={'user-agent': "curl"})
                if ipres.status == 200:
                    ip = await ipres.text()
            ipres.close()
            if not ip:
                async with s.get('http://ip-api.com/json/', proxy=proxy, timeout=5) as ipres:
                    if ipres.status == 200:
                        ipdata = await ipres.json()
                        ip = ipdata.get('query', '')
            if ip != '':
                url = baseurl + ip
            else:
                Collector.info['iprisk'] = "N/A"
                return
            async with s.get(url, proxy=proxy, timeout=5) as res:
                if res.status == 200:
                    data = await res.text()
                    Collector.info['iprisk'] = data
                else:
                    Collector.info['iprisk'] = "N/A"
    except ClientConnectorError as c:
        logger.warning("IP风险检测请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_ip_risk(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except asyncio.exceptions.TimeoutError:
        logger.warning("IP风险检测超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_ip_risk(Collector, session, proxy=proxy, reconnection=reconnection - 1)
    except ConnectionResetError:
        logger.warning("连接已重置")


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_ip_risk(Collector, session, proxy=proxy))


# cleaner section
def get_iprisk_info(ReCleaner):
    """
    获得ip风险信息
    :param ReCleaner:
    :return: str: 解锁信息: []
    """
    try:
        if 'iprisk' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            info_str = ReCleaner.data.get('iprisk', "N/A")
            if info_str == "N/A":
                return "N/A"
            index = info_str.find('IP Fraud Risk API')
            info_pre = info_str[index + 96:index + 205] if index > 0 else "{}"
            index2 = info_pre.find("}")
            info_str2 = info_pre[:index2 + 1] if index2 > 0 else "{}"
            info = json.loads(info_str2)
            ip = info.get('ip', '')
            if len(ip) > 15:
                iptype = "v6"
            else:
                iptype = "v4"
            score = info.get('score', '')
            risk = info.get('risk', '').capitalize()
            if score and risk:
                return risk + f"({score})({iptype})"
            return ""

    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "IP风险",
    "TASK": task,
    "GET": get_iprisk_info,
    "RANK": 2
}


async def demo():
    class FakeColl:
        def __init__(self):
            self.info = {}
            self.data = self.info

    fakecl = FakeColl()

    session = aiohttp.ClientSession()
    await fetch_ip_risk(fakecl, session, proxy='http://127.0.0.1:11112')
    print(get_iprisk_info(fakecl))
    await session.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
