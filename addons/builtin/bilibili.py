import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger

biliurl1 = "https://api.bilibili.com/pgc/player/web/playurl?avid=50762638&cid=100279344&qn=0&type=&otype" \
           "=json&ep_id=268176&fourk=1&fnver=0&fnval=16&session=926c41d4f12e53291b284b94f555e7df&module=bangumi"
biliurl2 = "https://api.bilibili.com/pgc/player/web/playurl?avid=18281381&cid=29892777&qn=0&type=&otype" \
           "=json&ep_id=183799&fourk=1&fnver=0&fnval=16&session=926c41d4f12e53291b284b94f555e7df&module=bangumi"
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'


# collector section
async def fetch_bilibili(collector, session: aiohttp.ClientSession, flag=1, proxy=None):
    """
    bilibili解锁测试，先测仅限台湾地区的限定资源，再测港澳台的限定资源
    """
    headers = {
        'user-agent': ua,
    }
    try:
        if flag == 1:
            res = await session.get(biliurl1, proxy=proxy, timeout=5, headers=headers)
        elif flag == 2:
            res = await session.get(biliurl2, proxy=proxy, timeout=5, headers=headers)
        else:
            return
        if res.status != 200:
            collector.info['bilibili'] = "N/A"
            return True
        text = await res.json()
        message = text.get("message", "")
        if message == "抱歉您所在地区不可观看！" and flag == 1:
            await fetch_bilibili(collector, session, flag=flag + 1, proxy=proxy)
        elif message == "抱歉您所在地区不可观看！" and flag == 2:
            collector.info['bilibili'] = "失败"
        elif message == "success" and flag == 1:
            collector.info['bilibili'] = "解锁(台湾)"
        elif message == "success" and flag == 2:
            collector.info['bilibili'] = "解锁(港澳台)"
        else:
            collector.info['bilibili'] = "N/A"
        return True
    except ClientConnectorError as c:
        logger.warning("bilibili请求发生错误:" + str(c))
        return False
    except asyncio.exceptions.TimeoutError:
        logger.warning("bilibili请求超时，正在重新发送请求......")
        return False


def task(collector, session, proxy):
    return asyncio.create_task(fetch_bilibili(collector, session, proxy=proxy))


# cleaner section
def get_bilibili_info(self):
    """

        :return: str: 解锁信息: [解锁(台湾)、解锁(港澳台)、失败、N/A]
        """
    try:
        if 'bilibili' not in self.data:
            logger.warning("采集器内无数据: bilibili")
            return "N/A"
        else:
            try:
                info = self.data['bilibili']
                if info is None:
                    logger.warning("无法读取bilibili解锁信息")
                    return "N/A"
                else:
                    logger.info("bilibili情况: " + info)
                    return info
            except KeyError:
                logger.warning("无法读取bilibili解锁信息")
                return "N/A"
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Bilibili",
    "TASK": task,
    "GET": get_bilibili_info
}


async def demo():
    from utils import script_demo
    await script_demo(fetch_bilibili, proxy='http://127.0.0.1:11112')


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(demo())
