import asyncio
import ssl
import time
from typing import List

import aiohttp
import async_timeout
from urllib.parse import quote
from aiohttp.client_exceptions import ClientConnectorError, ContentTypeError
from aiohttp_socks import ProxyConnector, ProxyConnectionError
from loguru import logger
from utils import cleaner

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
addon = cleaner.addon
media_items = config.get_media_item()
proxies = config.get_proxy()  # 代理
netflix_url = config.config.get('netflixurl', "https://www.netflix.com/title/70143836")


def reload_config(media: list = None):
    global config, proxies, media_items
    config.reload(issave=False)
    proxies = config.get_proxy()
    media_items = config.get_media_item()
    if media is not None:
        media_items = media


class BaseCollector:
    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
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
                    return await response.content.read()


class IPCollector:
    """
    GEOIP 测试采集类
    """

    def __init__(self):
        self.tasks = []
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36'}
        self.style = config.config.get('geoip-api', 'ip-api.com')  # api来源风格 这个值取二级域名
        self.key = config.config.get('geoip-key', '')
        self.get_payload = ""
        self.url = self.get_style_url()

    def get_style_url(self):
        if self.style == "ip-api.com":
            return "http://ip-api.com/json/"
        elif self.style == "ip.sb":
            return "https://api.ip.sb/geoip/"
        elif self.style == "ipleak.net":
            return "https://ipv4.ipleak.net/json/"
        elif self.style == "ipdata.co":
            self.get_payload = f"?api-key={self.key}"
            return "https://api.ipdata.co/"
        elif self.style == "ipapi.co":
            self.get_payload = "/json/"
            return "https://ipapi.co/"

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
        elif type(hosts).__name__ == "str":
            tasks.append(asyncio.create_task(self.fetch(session, proxy=proxy, host=hosts)))
        else:
            for ip in hosts:
                task = asyncio.create_task(self.fetch(session, proxy=proxy, host=ip))
                tasks.append(task)
        self.tasks.extend(tasks)

    async def batch(self, proxyhost: list, proxyport: list):
        try:
            session_pool = []
            length = min(len(proxyhost), len(proxyport))
            for i in range(length):
                conn = ProxyConnector(host=proxyhost[i], port=proxyport[i], limit=0)
                session = aiohttp.ClientSession(connector=conn)
                session_pool.append(session)
            for i in range(length):
                self.create_tasks(session=session_pool[i], hosts=None, proxy=None)
            resdata = await self.start()
            if resdata is None:
                resdata = []
            for r in range(len(resdata)):
                if resdata[r] is None:
                    resdata[r] = {}
            for i in range(length):
                await session_pool[i].close()
            return resdata
        except Exception as e:
            logger.error(str(e))
            return []

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
            return {}
        try:
            if host:
                resp = await session.get(self.url + host + self.get_payload, proxy=proxy, timeout=12)
                ipdata = await resp.json()
                return ipdata if ipdata else None
            else:
                resp = await session.get(self.url + self.get_payload, proxy=proxy, timeout=12)
                ipdata = await resp.json()
                return ipdata if ipdata else None
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
        except ContentTypeError:
            return None
        except Exception as e:
            logger.info(str(e))
            return None


class SubCollector(BaseCollector):
    """
    订阅采集器，默认采集clash配置文件
    """

    @logger.catch()
    def __init__(self, suburl: str, include: str = '', exclude: str = ''):
        """
        这里在初始化中读取了subconverter的相关配置，但是由于sunconverter无人维护，容易出问题，因此之后我不会再维护此功能。也就是在下载订阅时
        订阅转换
        """
        super().__init__()
        self.text = None
        self._headers = {'User-Agent': 'clash'}  # 这个请求头是获取流量信息的关键
        self.subconverter = config.config.get('subconverter', {})
        self.cvt_enable = self.subconverter.get('enable', False)
        self.url = suburl
        self.include = include
        self.exclude = exclude
        self.codeurl = quote(suburl, encoding='utf-8')
        self.code_include = quote(include, encoding='utf-8')
        self.code_exclude = quote(exclude, encoding='utf-8')
        self.cvt_host = str(self.subconverter.get('host', '127.0.0.1:25500'))
        self.cvt_url = f"http://{self.cvt_host}/sub?target=clash&new_name=true&url={self.codeurl}" \
                       + f"&include={self.code_include}&exclude={self.code_exclude}"
        self.sub_remote_config = self.subconverter.get('remoteconfig', '')
        self.config_include = quote(self.subconverter.get('include', ''), encoding='utf-8')  # 这两个
        self.config_exclude = quote(self.subconverter.get('exclude', ''), encoding='utf-8')
        # print(f"配置文件过滤,包含：{self.config_include} 排除：{self.config_exclude}")
        if self.config_include or self.config_exclude:
            self.cvt_url = f"http://{self.cvt_host}/sub?target=clash&new_name=true&url={self.cvt_url}" \
                           + f"&include={self.code_include}&exclude={self.code_exclude}"
        if self.sub_remote_config:
            self.sub_remote_config = quote(self.sub_remote_config, encoding='utf-8')
            self.cvt_url = self.cvt_url + "&config=" + self.sub_remote_config

    async def start(self, proxy=None):
        try:
            with async_timeout.timeout(20):
                async with aiohttp.ClientSession(headers=self._headers) as session:
                    async with session.get(self.url, proxy=proxy) as response:
                        return response
        except Exception as e:
            logger.error(e)
            return None

    @logger.catch()
    async def getSubTraffic(self, proxy=proxies):
        """
        获取订阅内的流量
        :return: str
        """
        _headers = {'User-Agent': 'clash'}
        try:
            async with aiohttp.ClientSession(headers=_headers) as session:
                async with session.get(self.url, proxy=proxy, timeout=20) as response:
                    info = response.headers.get('subscription-userinfo', "")
                    info = info.split(';')
                    info2 = {'upload': 0, 'download': 0, 'total': 0, 'expire': 0}
                    for i in info:
                        try:
                            i1 = i.strip().split('=')
                            info2[i1[0]] = float(i1[1]) if i1[1] else 0
                        except IndexError:
                            pass
                    logger.info(str(info2))
                    traffic_up = info2.get('upload', 0) / 1024 / 1024 / 1024
                    traffic_download = info2.get('download', 0) / 1024 / 1024 / 1024
                    traffic_use = traffic_up + traffic_download
                    traffic_total = info2.get('total', 0) / 1024 / 1024 / 1024
                    expire_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(info2.get('expire', time.time())))
                    if expire_time.startswith('1970') and traffic_total and traffic_use:
                        expire_time = '长期有效'
                return [traffic_up, traffic_download, traffic_use, traffic_total, expire_time]
        except asyncio.exceptions.TimeoutError:
            logger.info("获取订阅超时")
            return []
        except ClientConnectorError as c:
            logger.warning(c)
            return []

    async def getSubConfig(self, save_path: str = "./", proxy=proxies, inmemory: bool = False):
        """
        获取订阅配置文件
        :param save_path: 订阅保存路径
        :param proxy:
        :param inmemory: 直接返回数据到内存，不保存到本地
        :return: 获得一个文件: sub.yaml, bool : True or False
        """
        _headers = {'User-Agent': 'clash-meta'}
        # suburl = self.url
        suburl = self.cvt_url if self.cvt_enable else self.url
        cvt_text = "subconverter状态: {}".format("已启用" if self.cvt_enable else "未启用")
        logger.info(cvt_text)
        try:
            async with aiohttp.ClientSession(headers=_headers) as session:
                async with session.get(suburl, proxy=proxy, timeout=20) as response:
                    if response.status == 200:
                        data = b''
                        if inmemory:
                            while True:
                                chunk = await response.content.read()
                                if not chunk:
                                    logger.info("获取订阅成功")
                                    break
                                data += chunk
                            return data
                        with open(save_path, 'wb+') as fd:
                            while True:
                                chunk = await response.content.read()
                                if not chunk:
                                    logger.info("获取订阅成功")
                                    break
                                fd.write(chunk)
                        return True
                    return False
        except asyncio.exceptions.TimeoutError:
            logger.info("获取订阅超时")
            return False
        except ClientConnectorError as c:
            logger.warning(c)
            return False


class Miaospeed:
    SlaveRequestMatrixType = ['TEST_PING_RTT', 'SPEED_AVERAGE', 'UDP_TYPE', 'SPEED_PER_SECOND', 'SPEED_MAX',
                              'GEOIP_INBOUND', 'GEOIP_OUTBOUND',
                              'TEST_SCRIPT', 'TEST_PING_CONN', 'TEST_PING_RTT']
    SlaveRequestMatrixEntry = [{'Type': "SPEED_AVERAGE",
                                'Params': str({1})},
                               {'Type': "SPEED_MAX",
                                'Params': str({"Name": "test01", "Address": "127.0.0.1:1111", "Type": "Socks5"})},
                               {'Type': "SPEED_PER_SECOND",
                                'Params': str({"Name": "test01", "Address": "127.0.0.1:1111", "Type": "Socks5"})},
                               {'Type': "UDP_TYPE",
                                'Params': str({"Name": "test01", "Address": "127.0.0.1:1111", "Type": "Socks5"})},
                               ]
    SlaveRequestBasics = {'ID': '114514',
                          'Slave': '114514miao',
                          'SlaveName': 'miao1',
                          'Invoker': 'FullTclash',
                          'Version': '1.0'}
    SlaveRequestOptions = {'Filter': '',
                           'Matrices': SlaveRequestMatrixEntry}
    SlaveRequestConfigs = {
        'DownloadURL': 'https://dl.google.com/dl/android/studio/install/3.4.1.0/' +
                       'android-studio-ide-183.5522156-windows.exe',
        'DownloadDuration': 10,
        'DownloadThreading': 4,
        'PingAverageOver': 3,
        'PingAddress': 'http://www.gstatic.com/generate_204',
        'TaskThreading': 4,
        'TaskRetry': 2,
        'DNSServers': ['119.29.29.29'],
        'TaskTimeout': 5,
        'Scripts': []}
    VendorType = 'Clash'
    start_token = ''
    SlaveRequest = {'Basics': SlaveRequestBasics,
                    'Options': SlaveRequestOptions,
                    'Configs': SlaveRequestConfigs,
                    'Vendor': VendorType,
                    'RandomSequence': 'str1',
                    'Challenge': start_token}

    def __init__(self, proxyconfig: list, host: str = '127.0.0.1', port: int = 1112, ):
        """
        初始化miaospeed
        :param proxyconfig: 订阅配置的路径
        """
        self.host = host
        self.port = port
        self.nodes = proxyconfig
        self.slaveRequestNode = [{'Name': 'test01', 'Payload': str(i)} for i in self.nodes]
        self.SlaveRequest['Nodes'] = self.slaveRequestNode

    # async def start(self):
    #     start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    #     info = []
    #     resdata = {start_time: {}}
    #     from async_timeout import timeout
    #     try:
    #         async with timeout(len(self.nodes) * 10 + 1):
    #             async with websockets.connect(f'ws://{self.host}:{self.port}') as websocket:
    #                 payload = json.dumps(self.SlaveRequest)
    #                 await websocket.send(payload)
    #                 num = 0
    #                 while True:
    #                     response_str = await websocket.recv()
    #                     num += 1
    #                     logger.info(f"已接收第{num}次结果")
    #                     res1 = json.loads(response_str)
    #                     info.append(res1)
    #
    #     except asyncio.TimeoutError:
    #         logger.info("本次测试已完成")
    #     except KeyboardInterrupt:
    #         pass
    #     finally:
    #         resdata.update({start_time: info})
    #         return resdata, start_time


class Collector:
    def __init__(self, script: List[str] = None):
        self.session = None
        self.tasks = []
        self._script = script
        self._headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36"}
        self._headers_json = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36", "Content-Type": 'application/json'}
        self.ipurl = "https://api.ip.sb/geoip"
        self.youtubeurl = "https://www.youtube.com/premium"
        self.youtubeHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                          'Chrome/80.0.3987.87 Safari/537.36',
            'Accept-Language': 'en'
        }
        self.youtubeCookie = {
            'YSC': 'BiCUU3-5Gdk',
            'CONSENT': 'YES+cb.20220301-11-p0.en+FX+700',
            'GPS': '1',
            'VISITOR_INFO1_LIVE': '4VwPMkB7W5A',
            '_gcl_au': '1.1.1809531354.1646633279',
            'PREF': 'tz=Asia.Shanghai'
        }
        self.info = {}
        self.disneyurl1 = "https://www.disneyplus.com/"
        self.disneyurl2 = "https://global.edge.bamgrid.com/token"
        self.daznurl = "https://startup.core.indazn.com/misl/v5/Startup"

    @logger.catch
    def create_tasks(self, session: aiohttp.ClientSession, proxy=None):
        """
        创建并发请求任务，通过media_item动态创建
        :param session:
        :param proxy: 代理
        :return: tasks: []
        """
        items = media_items if self._script is None else self._script
        try:
            if len(items) and isinstance(items, list):
                for item in items:
                    i = item
                    if i in addon.script:
                        task = addon.script[i][0]
                        self.tasks.append(task(self, session, proxy=proxy))
                        continue
                    if i == "Youtube":
                        from addons.unlockTest import youtube
                        self.tasks.append(youtube.task(self, session, proxy=proxy))
                    elif i == "Disney" or i == "Disney+":
                        task5 = asyncio.create_task(self.fetch_dis(session, proxy=proxy))
                        self.tasks.append(task5)
                    elif i == "Netflix":
                        from addons.unlockTest import netflix
                        self.tasks.append(netflix.task(self, session, proxy=proxy, netflixurl=netflix_url))
                    elif i == "TVB":
                        from addons.unlockTest import tvb
                        self.tasks.append(tvb.task(self, session, proxy=proxy))
                    elif i == "Viu":
                        from addons.unlockTest import viu
                        self.tasks.append(viu.task(self, session, proxy=proxy))
                    elif i == "Iprisk" or i == "落地IP风险":
                        from addons.unlockTest import ip_risk
                        self.tasks.append(ip_risk.task(self, session, proxy=proxy))
                    elif i == "steam货币":
                        from addons.unlockTest import steam
                        self.tasks.append(steam.task(self, session, proxy=proxy))
                    elif i == "维基百科":
                        from addons.unlockTest import wikipedia
                        self.tasks.append(wikipedia.task(self, session, proxy=proxy))
                    elif item == "OpenAI":
                        from addons.unlockTest import openai
                        self.tasks.append(openai.task(self, session, proxy=proxy))
                    else:
                        pass
            return self.tasks
        except Exception as e:
            logger.error(e)
            return []

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
            logger.error(str(e))

    async def fetch_dis(self, session: aiohttp.ClientSession, proxy=None, reconnection=2):
        """
        Disney+ 解锁检测
        :param reconnection:
        :param session:
        :param proxy:
        :return:
        """
        try:
            if reconnection == 0:
                dis1 = await session.get(self.disneyurl1, proxy=proxy, timeout=5)
                text1 = await dis1.text()
                dis1.close()
                if dis1.status == 200:
                    # text1 = await dis1.text()
                    index = str(text1).find('Region', 0, 400)
                    region = text1[index + 8:index + 10]
                    if index == -1:
                        self.info['disney'] = "待解锁"
                    elif dis1.history:
                        if 300 <= dis1.history[0].status <= 399:
                            self.info['disney'] = "待解({})".format(region)
                        else:
                            self.info['disney'] = "未知"
                    else:
                        self.info['disney'] = "解锁({})".format(region)
                elif 399 < dis1.status:
                    self.info['disney'] = "N/A"
                    logger.info(f"disney+ 访问错误 {dis1.status}")
                else:
                    self.info['disney'] = "失败"
            else:
                dis1 = await session.get(self.disneyurl1, proxy=proxy, timeout=5)
                text1 = await dis1.text()
                dis1.close()
                dis2 = await session.get(self.disneyurl2, proxy=proxy, timeout=5)
                if dis1.status == 200 and dis2.status != 403:
                    # text1 = await dis1.text()
                    index = str(text1).find('Region', 0, 400)
                    region = text1[index + 8:index + 10]
                    if index == -1:
                        self.info['disney'] = "待解锁"
                    elif dis1.history:
                        if 300 <= dis1.history[0].status <= 399:
                            self.info['disney'] = "待解({})".format(region)
                        else:
                            self.info['disney'] = "未知"
                    else:
                        self.info['disney'] = "解锁({})".format(region)
                else:
                    self.info['disney'] = "失败"
                dis2.close()
        except ssl.SSLError:
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)
            else:
                self.info['disney'] = '证书错误'
        except ClientConnectorError as c:
            logger.warning("disney+请求发生错误:" + str(c))
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)
            else:
                self.info['disney'] = '连接错误'
        except asyncio.exceptions.TimeoutError:
            logger.warning("disney+请求超时，正在重新发送请求......")
            if reconnection != 0:
                await self.fetch_dis(session=session, proxy=proxy, reconnection=reconnection - 1)
        except ConnectionResetError:
            self.info['disney'] = '未知'
        except ProxyConnectionError as p:
            logger.warning("似乎目标端口未开启监听")
            logger.warning(str(p))

    async def start(self, host: str, port: int, proxy=None):
        """
        启动采集器，采用并发操作
        :param host:
        :param port:
        :param proxy: using proxy
        :return: all content
        """
        try:
            conn = ProxyConnector(host=host, port=port, limit=0)
            session = aiohttp.ClientSession(connector=conn, headers=self._headers)
            # if proxy is None:
            #     proxy = f"http://{host}:{port}"
            tasks = self.create_tasks(session, proxy=proxy)
            if tasks:
                try:
                    await asyncio.wait(tasks)
                except (ConnectionRefusedError, ProxyConnectionError, ssl.SSLError) as e:
                    logger.error(str(e))
                    return self.info
                finally:
                    await session.close()
            return self.info
        except Exception as e:
            logger.error(str(e))
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


async def delay_providers(providername, hostname='127.0.0.1', port=11230, session: aiohttp.ClientSession = None):
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
                      testurl=config.getGstatic(),
                      hostname='127.0.0.1', port=11230, timeout='5000'):
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


async def delay_https(session: aiohttp.ClientSession, proxy=None, testurl=config.getGstatic(),
                      timeout=10):
    # _headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    #                   'Chrome/102.0.5005.63 Safari/537.36'
    # }
    _headers2 = {'User-Agent': 'clash'}
    try:
        s1 = time.time()
        async with session.get(url=testurl, proxy=proxy, headers=_headers2,
                               timeout=timeout) as r:
            if r.status == 502:
                pass
                # logger.error("dual stack tcp shake hands failed")
            if r.status == 204 or r.status == 200:
                delay1 = time.time() - s1
                # print(delay1)
                return delay1
            else:
                return 0
    except Exception as e:
        logger.error(str(e))
        return 0


async def delay_https_task(session: aiohttp.ClientSession = None, collector=None, proxy=None, times=5):
    if session is None:
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(delay_https(session=session, proxy=proxy)) for _ in range(times)]
            result = await asyncio.gather(*tasks)
            sum_num = [r for r in result if r != 0]
            http_delay = sum(sum_num) / len(sum_num) if len(sum_num) else 0
            http_delay = "%.0fms" % (http_delay * 1000)
            # print("http平均延迟:", http_delay)
            http_delay = int(http_delay[:-2])
            if collector is not None:
                collector.info['HTTP(S)延迟'] = http_delay
            return http_delay
    else:
        tasks = [asyncio.create_task(delay_https(session=session, proxy=proxy)) for _ in range(times)]
        result = await asyncio.gather(*tasks)
        sum_num = [r for r in result if r != 0]
        http_delay = sum(sum_num) / len(sum_num) if len(sum_num) else 0
        http_delay = "%.0fms" % (http_delay * 1000)
        http_delay = int(http_delay[:-2])
        # print("http平均延迟:", http_delay)
        if collector is not None:
            collector.info['HTTP(S)延迟'] = http_delay
        return http_delay


if __name__ == "__main__":
    pass
