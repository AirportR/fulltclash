import asyncio
import json
import aiohttp
import async_timeout
from aiohttp.client_exceptions import ClientConnectorError
from loguru import logger
from libs import cleaner

"""
这是整个项目最为核心的功能模块之一 —> 采集器。它负责从网络上采集想要的数据。到现在，已经设计了：
1、采集器基类（BaseCollector）。一个简单的采集器示例。
2、IP采集器（IPCollector）。负责采集ip的相关信息
3、订阅采集器（SubCollector）。负责从网络上获取订阅文件
4、采集器（Collector）。负责各种流媒体解锁信息的采集
5、一个批量测试延迟的函数，基于clash core
需要注意的是，这些类/函数仅作采集工作，并不负责清洗。我们需要将拿到的数据给cleaner类清洗。

** 开发建议 **
如果你想自己添加一个流媒体测试项，建议继承Collector类，重写类中的create_tasks方法，以及自定义自己的流媒体测试函数 fetch_XXX()
"""
config = cleaner.ConfigManager()
media_items = config.get_media_item()
proxies = config.get_proxy()  # 代理


def reload_config(media: list = None):
    global config, proxies, media_items
    config.reload(issave=False)
    proxies = config.get_proxy()
    media_items = config.get_media_item()
    if media:
        media_items = media
    #print(media_items)


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


class IPCollector:
    def __init__(self):
        self.tasks = None
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36'}
        self.url = "https://api.ip.sb/geoip/"

    def create_tasks(self, session: aiohttp.ClientSession, hosts: list = None, proxy=None):
        """
        创建采集任务
        :param session:
        :param hosts: 主机信息，因查询ip的api限制，无法查询域名，请先转换成ip
        :param proxy: 代理
        :return:
        """
        tasks = []
        if hosts is None:
            task = asyncio.create_task(self.fetch(session, proxy=proxy))
            tasks.append(task)
        else:
            for ip in hosts:
                task = asyncio.create_task(self.fetch(session, proxy=proxy, host=ip))
                tasks.append(task)
        self.tasks = tasks

    async def start(self):
        """
        启动ip信息采集，并发操作，启动之前请务必通过self.create_tasks创建任务，否则只会返回空
        :return: list | None
        """
        try:
            if self.tasks:
                done = await asyncio.gather(*self.tasks)
                return done
            else:
                return None
        except Exception as e:
            logger.error(e)
            return None

    async def fetch(self, session: aiohttp.ClientSession, proxy=None, host: str = None, reconnection=1):
        """
        获取ip地址信息
        :param session:
        :param proxy: 代理
        :param host: 一个v4地址/v6地址
        :param reconnection: 重连次数
        :return: json数据
        """
        if host == "N/A":
            return None
        try:
            if host:
                resp = await session.get(self.url + host, proxy=proxy, timeout=10)
                return await resp.json()
            else:
                resp = await session.get(self.url, proxy=proxy, timeout=10)
                return await resp.json()
        except ClientConnectorError as c:
            logger.warning("ip查询请求发生错误:" + str(c))
            if reconnection != 0:
                await self.fetch(session=session, proxy=proxy, host=host, reconnection=reconnection - 1)
            else:
                return None
        except asyncio.exceptions.TimeoutError:
            if reconnection != 0:
                logger.warning("ip查询请求超时，正在重新发送请求......")
                await self.fetch(session=session, proxy=proxy, host=host, reconnection=reconnection - 1)
            else:
                return None


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
        self.tasks = []
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36'}
        self._headers_json = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36', "Content-Type": 'application/json'}
        self.netflixurl1 = "https://www.netflix.com/title/70242311"
        self.netflixurl2 = "https://www.netflix.com/title/70143836"
        self.ipurl = "https://api.ip.sb/geoip"
        self.youtubeurl = "https://music.youtube.com"
        self.info = {}
        self.disneyurl1 = "https://www.disneyplus.com/"
        self.disneyurl2 = "https://global.edge.bamgrid.com/token"
        self.biliurl1 = "https://api.bilibili.com/pgc/player/web/playurl?avid=50762638&cid=100279344&qn=0&type=&otype" \
                        "=json&ep_id=268176&fourk=1&fnver=0&fnval=16&session=926c41d4f12e53291b284b94f555e7df&module" \
                        "=bangumi"
        self.biliurl2 = "https://api.bilibili.com/pgc/player/web/playurl?avid=18281381&cid=29892777&qn=0&type=&otype" \
                        "=json&ep_id=183799&fourk=1&fnver=0&fnval=16&session=926c41d4f12e53291b284b94f555e7df&module" \
                        "=bangumi"
        self.daznurl = "https://startup.core.indazn.com/misl/v5/Startup"

    @logger.catch
    def create_tasks(self, session: aiohttp.ClientSession, proxy=None):
        """
        创建并发请求任务，通过media_item动态创建
        :param session:
        :param proxy: 代理
        :return: tasks: []
        """
        items = media_items
        try:
            task1 = asyncio.create_task(self.fetch_ip(session=session, proxy=proxy))
            self.tasks.append(task1)
            for item in items:
                i = item.capitalize()
                if i == "Netflix":
                    task2 = asyncio.create_task(self.fetch_ninfo1(session, proxy=proxy))
                    self.tasks.append(task2)
                    task3 = asyncio.create_task(self.fetch_ninfo2(session, proxy=proxy))
                    self.tasks.append(task3)
                elif i == "Youtube":
                    task4 = asyncio.create_task(self.fetch_youtube(session, proxy=proxy))
                    self.tasks.append(task4)
                elif i == "Disney" or i == "Disney+":
                    task5 = asyncio.create_task(self.fetch_dis(session, proxy=proxy))
                    self.tasks.append(task5)
                elif i == "Bilibili":
                    task6 = asyncio.create_task(self.fetch_bilibili(session, proxy=proxy))
                    self.tasks.append(task6)
                elif i == "Dazn":
                    task7 = asyncio.create_task(self.fetch_dazn(session, proxy=proxy))
                    self.tasks.append(task7)
                else:
                    pass
            return self.tasks
        except Exception as e:
            logger.error(e)
            return None

    async def fetch_bilibili(self, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=2):
        """
        bilibili解锁测试，先测仅限台湾地区的限定资源，再测港澳台的限定资源
        :param flag: 用于判断请求的是哪个bilibili url
        :param reconnection:
        :param session:
        :param proxy:
        :return:
        """
        try:
            if flag == 1:
                res = await session.get(self.biliurl1, proxy=proxy, timeout=5)
            elif flag == 2:
                res = await session.get(self.biliurl2, proxy=proxy, timeout=5)
            else:
                return
            if res.status == 200:
                text = await res.json()
                try:
                    message = text['message']
                    if message == "抱歉您所在地区不可观看！" and flag == 1:
                        await self.fetch_bilibili(session, flag=flag + 1, proxy=proxy, reconnection=2)
                    elif message == "抱歉您所在地区不可观看！" and flag == 2:
                        self.info['bilibili'] = "失败"
                    elif message == "success" and flag == 1:
                        self.info['bilibili'] = "解锁(台湾)"
                    elif message == "success" and flag == 2:
                        self.info['bilibili'] = "解锁(港澳台)"
                    else:
                        self.info['bilibili'] = "N/A"
                except KeyError:
                    self.info['bilibili'] = "N/A"
            else:
                self.info['bilibili'] = "N/A"
        except ClientConnectorError as c:
            logger.warning("bilibili请求发生错误:" + str(c))
            if reconnection != 0:
                await self.fetch_bilibili(session=session, proxy=proxy, flag=flag, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("bilibili请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_bilibili(session=session, proxy=proxy, flag=flag, reconnection=reconnection - 1)

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
            logger.warning("Netflix请求发生错误:" + str(c))
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
            logger.warning("Netflix请求发生错误:" + str(c))
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
            logger.warning("Youtube请求发生错误:" + str(c))
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
            logger.warning("disney+请求发生错误:" + str(c))
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("disney+请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)

    async def fetch_dazn(self, session: aiohttp.ClientSession, proxy=None, reconnection=2):
        """
        Dazn解锁测试
        :param reconnection:
        :param session:
        :param proxy:
        :return:
        """
        payload = json.dumps(
            {"LandingPageKey": "generic", "Languages": "zh-CN,zh,en", "Platform": "web", "PlatformAttributes": {},
             "Manufacturer": "", "PromoCode": "", "Version": "2"})
        try:
            r = await session.post(url=self.daznurl, proxy=proxy, data=payload, timeout=5, headers=self._headers_json)
            if r.status == 200:
                text = await r.json()
                self.info['dazn'] = text
        except ClientConnectorError as c:
            logger.warning("Dazn请求发生错误:" + str(c))
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)
        except asyncio.exceptions.TimeoutError:
            logger.warning("Dazn请求超时，正在重新发送请求......")
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
            tasks = self.create_tasks(session, proxy=proxy)
            if tasks:
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
