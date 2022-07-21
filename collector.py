import asyncio
import time
import aiohttp
import async_timeout
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError

proxies = "http://127.0.0.1:1111"


class BaseCollector:
    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36'}

    async def status(self, url, proxy=None):
        with async_timeout.timeout(10):
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.get(url, proxy=proxy) as response:
                    return response.status

    async def fetch(self, url, proxy=None):
        with async_timeout.timeout(10):
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.get(url, proxy=proxy) as response:
                    return await response.text()


class SubCollector(BaseCollector):
    """
    订阅采集器，默认采集clash配置文件
    """

    def __init__(self, suburl: str):
        super().__init__()
        self.text = None
        self._headers = {'User-Agent': 'clash'}  # 这个请求头是获取流量信息的关键
        self.url = suburl

    async def start(self, proxy=None):
        try:
            with async_timeout.timeout(20):
                async with aiohttp.ClientSession(headers=self._headers) as session:
                    async with session.get(self.url, proxy=proxy) as response:
                        return response
        except Exception as e:
            print(e)

    async def getSubTraffic(self, proxy=None):
        """
        获取订阅内的流量
        :return: str
        """
        return await self.start(proxy=proxy)

    async def getSubConfig(self, proxy=proxies):
        """
        获取订阅配置文件
        :param proxy:
        :return: 获得一个文件: sub.yaml, bool : True or False
        """
        _headers = {'User-Agent': 'clash'}
        try:
            async with aiohttp.ClientSession(headers=_headers) as session:
                async with session.get(self.url, proxy=proxy, timeout=10) as response:
                    if response.status == 200:
                        with open('sub.yaml', 'wb+') as fd:
                            while True:
                                chunk = await response.content.read()
                                if not chunk:
                                    print("获取订阅成功")
                                    break
                                fd.write(chunk)
                            return True
        except ClientConnectorError as c:
            print(c)
            return False


class Collector:
    def __init__(self):
        self.session = None
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36'}
        self.netflixurl1 = "https://www.netflix.com/title/70242311"
        self.netflixurl2 = "https://www.netflix.com/title/70143836"
        self.ipurl = "https://api.ip.sb/geoip"
        self.youtubeurl = "https://music.youtube.com"
        self.info = {}
        self.disneyurl1 = "https://www.disneyplus.com/"
        self.disneyurl2 = "https://global.edge.bamgrid.com/token"

    async def httping(self, session: aiohttp.ClientSession, proxy=None):
        """
        访问google的延迟
        :param session:
        :param proxy:
        :return: float: 一个浮点数值，毫秒为单位
        """
        try:
            s1 = time.time()
            a1 = await session.get("http://www.gstatic.com/generate_204", proxy=proxy, timeout=5)
            # a2 = await session.get("https://www.google.com/", proxy="http://127.0.0.1:1111", timeout=10)
            # a3 = await session.get("https://www.google.com/", proxy="http://127.0.0.1:1111", timeout=10)
            # if a1.status == 200 and a2.status == 200 and a3.status == 200:
            #     delay = ((time.time() - s1) * 1000) / 3
            # else:
            #     delay = 0
            if a1.status == 204:
                delay = (time.time() - s1) * 1000
            else:
                delay = 0
            print("延迟:", "%.0fms" % delay)
            self.info['delay'] = delay
        except Exception as e:
            print("?", e)
        except ClientConnectorError as c:
            print(c)

    async def fetch_ip(self, session: aiohttp.ClientSession, proxy=None):
        """
        ip查询
        :param session:
        :param proxy:
        :return:
        """
        try:
            res = await session.get(self.ipurl, proxy=proxy, timeout=5)
            print("ip查询状态：", res.status)
            if res.status != 200:
                self.info['ip'] = None
                self.info['netflix1'] = None
                self.info['netflix2'] = None
                self.info['youtube'] = None
                self.info['ne_status_code1'] = None
                self.info['ne_status_code2'] = None
                print("无法查询到代理ip")
                return self.info
            else:
                self.info['ip'] = await res.json()
        except Exception as e:
            print(e)
        except ClientConnectorError as c:
            print(c)

    async def fetch_ninfo1(self, session: aiohttp.ClientSession, proxy=None):
        """
        自制剧检测
        :param session:
        :param proxy:
        :return:
        """
        try:
            n1 = await session.get(self.netflixurl1, proxy=proxy, timeout=5)
            if n1 is not None:
                self.info['netflix1'] = await n1.text()
                self.info['ne_status_code1'] = n1.status
            else:
                self.info['netflix1'] = None
                self.info['ne_status_code1'] = None
        except ClientConnectorError as c:
            print(c)

    async def fetch_ninfo2(self, session: aiohttp.ClientSession, proxy=None):
        """
        非自制剧检测
        :param session:
        :param proxy:
        :return:
        """
        try:
            n2 = await session.get(self.netflixurl2, proxy=proxy, timeout=5)
            if n2 is not None:
                self.info['netflix2'] = await n2.text()
                self.info['ne_status_code2'] = n2.status
            else:
                self.info['netflix2'] = None
                self.info['ne_status_code2'] = None

        except ClientConnectorError as c:
            print(c)

    async def fetch_youtube(self, session: aiohttp.ClientSession, proxy=None):
        """
        Youtube解锁检测
        :param session:
        :param proxy:
        :return:
        """
        try:
            youtube = await session.get(self.youtubeurl, proxy=proxy, timeout=5)
            if youtube.status is not None:
                self.info['youtube'] = await youtube.text()
                self.info['youtube_status_code'] = youtube.status
                print("Youtube 成功访问")
            else:
                self.info['youtube'] = None
        except ClientConnectorError as c:
            print(c)

    async def fetch_dis(self, session: aiohttp.ClientSession, proxy=None):
        """
        Disney+ 解锁检测
        :param session:
        :param proxy:
        :return:
        """
        try:
            dis1 = await session.get(self.disneyurl1, proxy=proxy, timeout=5)
            dis2 = await session.get(self.disneyurl2, proxy=proxy, timeout=5)
            if dis1.status == 200 and dis2.status != 403:
                self.info['disney'] = "解锁"
            else:
                self.info['disney'] = "失败"
            print("disney+ 成功访问")
        except ClientConnectorError as c:
            print(c)

    async def start(self, session: aiohttp.ClientSession = None, proxy=None):
        """
        启动采集器，采用并发操作
        :param session:
        :param proxy: using proxy
        :return: all content
        """
        try:
            if session is None:
                session = aiohttp.ClientSession(headers=self._headers)
                tasks = []
                task1 = asyncio.create_task(self.fetch_ip(session=session, proxy=proxy))
                tasks.append(task1)
                task2 = asyncio.create_task(self.fetch_ninfo1(session, proxy=proxy))
                tasks.append(task2)
                task3 = asyncio.create_task(self.fetch_ninfo2(session, proxy=proxy))
                tasks.append(task3)
                task4 = asyncio.create_task(self.fetch_youtube(session, proxy=proxy))
                tasks.append(task4)
                task5 = asyncio.create_task(self.fetch_dis(session, proxy=proxy))
                tasks.append(task5)
                task6 = asyncio.create_task(self.httping(session, proxy=proxy))
                tasks.append(task6)
                done, pending = await asyncio.wait(tasks)
                await session.close()
            return self.info
        except Exception as e:
            print(e)
            self.info['ip'] = "N/A"
            self.info['netflix1'] = None
            self.info['netflix2'] = None
            self.info['youtube'] = None
            self.info['ne_status_code1'] = None
            self.info['ne_status_code2'] = None
            self.info['youtube_status_code'] = None
            return self.info


