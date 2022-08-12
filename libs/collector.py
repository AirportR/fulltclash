import asyncio
import aiohttp
import async_timeout
from aiohttp.client_exceptions import ClientConnectorError
from loguru import logger
from libs import cleaner

config = cleaner.ConfigManager()
proxies = config.get_proxy()  # 代理


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
            logger.error(e)
            return None

    async def getSubTraffic(self, proxy=None):
        """
        获取订阅内的流量
        :return: str
        """
        return await self.start(proxy=proxy)

    async def getSubConfig(self, save_path: str, proxy=proxies):
        """
        获取订阅配置文件
        :param save_path: 订阅保存路径
        :param proxy:
        :return: 获得一个文件: sub.yaml, bool : True or False
        """
        _headers = {'User-Agent': 'clash'}
        try:
            async with aiohttp.ClientSession(headers=_headers) as session:
                async with session.get(self.url, proxy=proxy, timeout=10) as response:
                    if response.status == 200:
                        with open(save_path, 'wb+') as fd:
                            while True:
                                chunk = await response.content.read()
                                if not chunk:
                                    logger.info("获取订阅成功")
                                    break
                                fd.write(chunk)
                            return True
        except asyncio.exceptions.TimeoutError:
            logger.info("获取订阅超时")
            return False
        except ClientConnectorError as c:
            logger.warning(c)
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

    async def fetch_ip(self, session: aiohttp.ClientSession, proxy=None):
        """
        ip查询
        :param session:
        :param proxy:
        :return:
        """
        try:
            res = await session.get(self.ipurl, proxy=proxy, timeout=5)
            logger.info("ip查询状态：" + str(res.status))
            if res.status != 200:
                self.info['ip'] = None
                self.info['netflix1'] = None
                self.info['netflix2'] = None
                self.info['youtube'] = None
                self.info['ne_status_code1'] = None
                self.info['ne_status_code2'] = None
                logger.warning("无法查询到代理ip")
                return self.info
            else:
                self.info['ip'] = await res.json()
        except ClientConnectorError as c:
            logger.warning(c)
            self.info['ip'] = None
            return self.info
        except Exception as e:
            logger.error(e)

    async def fetch_ninfo1(self, session: aiohttp.ClientSession, proxy=None, reconnection=2):
        """
        自制剧检测
        :param session:
        :param proxy:
        :param reconnection :重连次数
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
            logger.warning("Netflix请求发生错误:", c)
            if reconnection != 0:
                await self.fetch_ninfo1(session=session, proxy=proxy, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("Netflix请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_ninfo1(session=session, proxy=proxy, reconnection=reconnection - 1)

    async def fetch_ninfo2(self, session: aiohttp.ClientSession, proxy=None, reconnection=2):
        """
        非自制剧检测
        :param session:
        :param proxy:
        :param reconnection :重连次数
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
            logger.warning("Netflix请求发生错误:", c)
            if reconnection != 0:
                await self.fetch_ninfo2(session=session, proxy=proxy, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("Netflix请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_ninfo2(session=session, proxy=proxy, reconnection=reconnection - 1)

    async def fetch_youtube(self, session: aiohttp.ClientSession, proxy=None, reconnection=2):
        """
        Youtube解锁检测
        :param reconnection:
        :param session:
        :param proxy:
        :return:
        """
        try:
            youtube = await session.get(self.youtubeurl, proxy=proxy, timeout=5)
            if youtube.status is not None:
                self.info['youtube'] = await youtube.text()
                self.info['youtube_status_code'] = youtube.status
                logger.info("Youtube 成功访问")
            else:
                self.info['youtube'] = None
        except ClientConnectorError as c:
            logger.warning("Youtube请求发生错误:", c)
            if reconnection != 0:
                await self.fetch_youtube(session=session, proxy=proxy, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("Youtube请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_youtube(session=session, proxy=proxy, reconnection=reconnection - 1)

    async def fetch_dis(self, session: aiohttp.ClientSession, proxy=None, reconnection=2):
        """
        Disney+ 解锁检测
        :param reconnection:
        :param session:
        :param proxy:
        :return:
        """
        try:
            dis1 = await session.get(self.disneyurl1, proxy=proxy, timeout=5)
            dis2 = await session.get(self.disneyurl2, proxy=proxy, timeout=5)
            if dis1.status == 200 and dis2.status != 403:
                text1 = await dis1.text()
                index = str(text1).find('Region', 0, 400)
                region = text1[index + 8:index + 10]
                if index == -1:
                    self.info['disney'] = "待解锁"
                elif dis1.history:
                    if 300 <= dis1.history[0].status <= 399:
                        self.info['disney'] = "待解({})".format(region)
                else:
                    self.info['disney'] = "解锁({})".format(region)
            else:
                self.info['disney'] = "失败"
            logger.info("disney+ 成功访问")
        except ClientConnectorError as c:
            logger.warning("disney+请求发生错误:", c)
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("disney+请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)

    async def start(self, proxy=None):
        """
        启动采集器，采用并发操作
        :param proxy: using proxy
        :return: all content
        """
        try:
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
            done, pending = await asyncio.wait(tasks)
            await session.close()
            return self.info
        except Exception as e:
            logger.error(e)
            self.info['ip'] = "N/A"
            self.info['netflix1'] = None
            self.info['netflix2'] = None
            self.info['youtube'] = None
            self.info['ne_status_code1'] = None
            self.info['ne_status_code2'] = None
            self.info['youtube_status_code'] = None
            return self.info


async def delay(session: aiohttp.ClientSession, proxyname, testurl, hostname, port, timeout):
    url = 'http://{}:{}/proxies/{}/delay?timeout={}&url={}'.format(hostname, port, proxyname, timeout, testurl)
    async with session.get(url) as r:
        try:
            if r.status == 200:
                text = await r.json()
                return text['delay']
            else:
                logger.info(proxyname + ":" + str(await r.json()) + str(r.status))
                return -1
        except ClientConnectorError as c:
            logger.warning("连接失败:", c)
            return -1


async def delay_providers(providername, hostname='127.0.0.1', port=1123, session: aiohttp.ClientSession = None):
    healthcheckurl = 'http://{}:{}/providers/proxies/{}/healthcheck'.format(hostname, port, providername)
    url = 'http://{}:{}/providers/proxies/{}/'.format(hostname, port, providername)
    if session is None:
        session = aiohttp.ClientSession()
    try:
        await session.get(healthcheckurl)
        async with session.get(url) as r:
            if r.status == 200:
                text = await r.json()
                # 拿到延迟数据
                delays = []
                node = text['proxies']
                for n in node:
                    s = n['history'].pop()
                    de = s['delay']
                    delays.append(de)
                await session.close()
                return delays
            else:
                logger.warning("延迟测试出错:" + str(r.status))
                await session.close()
                return 0
    except ClientConnectorError as c:
        logger.warning("连接失败:", c)
        await session.close()
        return 0


async def batch_delay(proxyname: list, session: aiohttp.ClientSession = None,
                      testurl='http://www.gstatic.com/generate_204',
                      hostname='127.0.0.1', port=1123, timeout='5000'):
    """
    批量测试延迟，仅适用于不含providers的订阅
    :param timeout:
    :param port: 外部控制器端口
    :param hostname: 主机名
    :param testurl: 测试网址
    :param session: 一个连接session
    :param proxyname: 一组代理名
    :return: list: 延迟
    """
    try:
        if session is None:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for name in proxyname:
                    task = asyncio.create_task(
                        delay(session, name, testurl=testurl, hostname=hostname, port=port, timeout=timeout))
                    tasks.append(task)
                done = await asyncio.gather(*tasks)
                return done
        else:
            tasks = []
            for name in proxyname:
                task = asyncio.create_task(
                    delay(session, name, testurl=testurl, hostname=hostname, port=port, timeout=timeout))
                tasks.append(task)
            done = await asyncio.gather(*tasks)
            return done
    except Exception as e:
        logger.error(e)
        return None
