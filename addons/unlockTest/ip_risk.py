import asyncio
import json

import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from pyrogram.types import InlineKeyboardButton

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
        async with session.get('http://ip-api.com/json/', proxy=proxy, timeout=5) as ipres:
            if ipres.status == 200:
                ipdata = await ipres.json()
                ip = ipdata.get('query', '')
        if ip != '':
            url = baseurl + ip
        else:
            Collector.info['iprisk'] = "N/A"
            return
        async with session.get(url, proxy=proxy, timeout=5) as res:
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
            info_pre = info_str[index+88:index+160] if index > 0 else "{}"
            index2 = info_pre.find("}")
            info_str2 = info_pre[:index2+1] if index2 > 0 else "{}"
            info = json.loads(info_str2)
            score = info.get('score', '无')
            risk = info.get('risk', '无').capitalize()
            return risk + f"({score})"
    except Exception as e:
        logger.error(e)
        return "N/A"


# bot_setting_board

button = InlineKeyboardButton("✅落地IP风险", callback_data='✅落地IP风险')

if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    from utils.collector import Collector as CL, media_items

    media_items.clear()
    media_items.append("iprisk")
    cl = CL()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cl.start("127.0.0.1", 1122))
    print(cl.info)
