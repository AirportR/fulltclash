import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger


# collector section
async def fetch_youtube(collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    bingai解锁测试
    """
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/114.0.0.0 Safari/537.36',
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en",
        "upgrade-insecure-requests": "1",
    }
    youtubeCookie = {
        'YSC': 'BiCUU3-5Gdk',
        'CONSENT': 'YES+cb.20220301-11-p0.en+FX+700',
        'GPS': '1',
        'VISITOR_INFO1_LIVE': '4VwPMkB7W5A',
        '_gcl_au': '1.1.1809531354.1646633279',
        'PREF': 'tz=Asia.Shanghai'
    }
    youtubeurl = "https://www.youtube.com/premium"
    try:
        async with session.get(youtubeurl, proxy=proxy, timeout=5, headers=headers, cookies=youtubeCookie) as resp:
            if resp.status != 200:
                collector.info['youtube'] = "N/A"
                return

            elif resp.history:
                collector.info['youtube_status_code'] = resp.history[0].status
                collector.info['youtube'] = resp.history[0].headers.get('Location', 'None')
                return
            text = await resp.text()
            collector.info['youtube_status_code'] = resp.status
            collector.info['youtube'] = text
    except ClientConnectorError as c:
        logger.warning("Youtube请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_youtube(collector, session=session, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['youtube'] = "连接错误"
    except asyncio.exceptions.TimeoutError:
        logger.warning("Youtube请求超时，正在重新发送请求......")
        if reconnection != 0:
            await fetch_youtube(collector, session=session, proxy=proxy, reconnection=reconnection - 1)
        else:
            collector.info['youtube'] = "超时"


def task(collector, session, proxy):
    return asyncio.create_task(fetch_youtube(collector, session, proxy=proxy))


# cleaner section
def get_youtube_info(self):
    """
    :return: str: 解锁信息: [解锁(台湾)、失败]
    """
    try:
        if 'youtube' not in self.data:
            logger.warning("采集器内无数据: Youtube")
            return "N/A"
        else:
            try:
                text = self.data['youtube']
                if text.find('www.google.cn') != -1:
                    return "送中(CN)"

                idx0 = text.find('YouTube and YouTube Music ad-free, offline, and in the background')
                if self.data['youtube_status_code'] == 302:
                    return "重定向"
                elif text.find('Premium is not available in your country') != -1 or idx0 == -1:
                    return "失败"
                elif self.data['youtube_status_code'] == 200:
                    idx = text.find('"countryCode"')
                    region = text[idx:idx + 17].replace('"countryCode":"', "")
                    if idx == -1 and idx0 != -1:
                        region = "US"
                    logger.info(f"Youtube解锁地区: {region}")
                    return f"解锁({region})"
                else:
                    return "未知"
            except KeyError:
                logger.warning("无法读取Youtube解锁信息")
                return "N/A"
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Youtube(新)",
    "TASK": task,
    "GET": get_youtube_info
}


# bot_setting_board

async def demo():
    class FakeColl:
        def __init__(self):
            self.info = {}
            self.data = self.info

    fakecl = FakeColl()
    session = aiohttp.ClientSession()
    await fetch_youtube(fakecl, session)
    print(get_youtube_info(fakecl))
    await session.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(demo())
