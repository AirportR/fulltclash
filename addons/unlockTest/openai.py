import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

# collector section
from pyrogram.types import InlineKeyboardButton

openaiurl = "https://chat.openai.com/favicon.ico"
# openaiurl = "https://chat.openai.com"
openaiurl2 = "https://chat.openai.com/cdn-cgi/trace"
SUPPORT_REGION = ['AL', 'DZ', 'AD', 'AO', 'AG', 'AR', 'AM', 'AU', 'AT', 'AZ', 'BS', 'BD', 'BB', 'BE', 'BZ', 'BJ', 'BT',
                  'BA', 'UA',
                  'BW', 'BR', 'BG', 'BF', 'CV', 'CA', 'CL', 'CO', 'KM', 'CR', 'HR', 'CY', 'DK', 'DJ', 'DM', 'DO', 'EC',
                  'SV',
                  'EE', 'FJ', 'FI', 'FR', 'GA', 'GM', 'GE', 'DE', 'GH', 'GR', 'GD', 'GT', 'GN', 'GW', 'GY', 'HT', 'HN',
                  'HU',
                  'IS', 'IN', 'ID', 'IQ', 'IE', 'IL', 'JM', 'JP', 'JO', 'KZ', 'KE', 'KI', 'KW', 'KG', 'LV', 'LB',
                  'LS',
                  'LR', 'LI', 'LT', 'LU', 'MG', 'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MR', 'MU', 'MX', 'MC', 'MN', 'ME',
                  'MA',
                  'MZ', 'MM', 'NA', 'NR', 'NP', 'NL', 'NZ', 'NI', 'NE', 'NG', 'MK', 'NO', 'OM', 'PK', 'PW', 'PA', 'PG',
                  'PE',
                  'PH', 'PL', 'PT', 'QA', 'RO', 'RW', 'KN', 'LC', 'VC', 'WS', 'SM', 'ST', 'SN', 'RS', 'SC', 'SL', 'SG',
                  'SK',
                  'SI', 'SB', 'ZA', 'ES', 'LK', 'SR', 'SE', 'CH', 'TH', 'TG', 'TO', 'TT', 'TN', 'TR', 'TV', 'UG', 'AE',
                  'US',
                  'UY', 'VU', 'ZM', 'BO', 'BN', 'CG', 'CZ', 'VA', 'FM', 'MD', 'PS', 'KR', 'TW', 'TZ', 'TL', 'GB']


async def fetch_openai(Collector, session: aiohttp.ClientSession, proxy=None, reconnection=2):
    """
    openai封锁检测
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    # openaiurl1 = "https://chat.openai.com"  # openaiurl
    # openaiurl2 = "https://chat.openai.com/cdn-cgi/trace"
    try:
        _headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                          'Chrome/102.0.5005.63 Safari/537.36',
        }
        async with session.get(openaiurl, headers=_headers, proxy=proxy, timeout=10) as res:
            res1_status = res.status
            if res.status == 403:
                # ct = res.headers.get('Content-Type', 'None')
                # if 'text/html' in ct:
                #     Collector.info['OpenAI'] = "失败"
                #     return
                text = await res.text()
                if text.find('Please stand by, while we are checking your browser') > 0:
                    logger.info("OpenAI检测到CloudFlare拦截")
                    Collector.info['OpenAI'] = "CloudFlare拦截"

                index = text.find("Sorry, you have been blocked")
                index2 = text.find("Unable to load site")
                if index > 0 or index2 > 0:
                    Collector.info['OpenAI'] = "失败"
                    return
                index2 = text.find("You do not have access to chat.openai.com.")
                if index2 > 0:
                    Collector.info['OpenAI'] = "失败"
                    return

            else:
                Collector.info['OpenAI'] = "未知"
        async with session.get(openaiurl2, headers=_headers, proxy=proxy, timeout=10) as res2:
            if res2.status == 200 and (res1_status == 200 or res1_status == 403):
                text2 = await res2.text()
                index2 = text2.find("loc=")
                if index2 > 0:
                    region = text2[index2 + 4:index2 + 6]
                    if region in SUPPORT_REGION:
                        Collector.info['OpenAI'] = f"解锁({region})"
                    else:
                        Collector.info['OpenAI'] = f"待解({region})"
                else:
                    Collector.info['OpenAI'] = "未知"
            else:
                Collector.info['OpenAI'] = "N/A"

    except ClientConnectorError as c:
        logger.warning("OpenAI请求发生错误:" + str(c))
        if reconnection != 0:
            await fetch_openai(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['OpenAI'] = "连接错误"
            return
    except asyncio.exceptions.TimeoutError:
        if reconnection != 0:
            logger.warning("OpenAI请求超时，正在重新发送请求......")
            await fetch_openai(Collector, session, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['OpenAI'] = "超时"
            return


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
        if 'OpenAI' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            # logger.info("OpenAI解锁：" + str(ReCleaner.data.get('OpenAI', "N/A")))
            return ReCleaner.data.get('OpenAI', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


button = InlineKeyboardButton("✅OpenAI", callback_data='✅OpenAI')
SCRIPT = {
    "MYNAME": "OpenAI",
    "TASK": task,
    "GET": get_openai_info
}


async def demo():
    class FakeColl:
        def __init__(self):
            self.info = {}
            self.data = self.info

    fakecl = FakeColl()

    session = aiohttp.ClientSession()
    await fetch_openai(fakecl, session, proxy='http://127.0.0.1:1112')
    print(get_openai_info(fakecl))
    await session.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(demo())
