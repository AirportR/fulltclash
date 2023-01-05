import asyncio
import json
import time

import aiohttp
import async_timeout
from urllib.parse import quote
from aiohttp.client_exceptions import ClientConnectorError, ContentTypeError
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
    if media is not None:
        media_items = media
        # print(media_items)
    # print(media_items)


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
        self.tasks = []
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/102.0.5005.63 Safari/537.36'}
        self.style = config.config.get('geoip-api', 'ip-api.com')  # api来源风格 这个值取二级域名
        self.url = self.get_style_url()

    def get_style_url(self):
        if self.style == "ip-api.com":
            return "http://ip-api.com/json/"
        elif self.style == "ip.sb":
            return "https://api.ip.sb/geoip/"

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
            session = aiohttp.ClientSession()
            length = min(len(proxyhost), len(proxyport))
            for i in range(length):
                self.create_tasks(session=session, hosts=None, proxy=f"http://{proxyhost[i]}:{proxyport[i]}")
            resdata = await self.start()
            if resdata is None:
                resdata = []
            await session.close()
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
            return None
        try:
            if host:
                resp = await session.get(self.url + host, proxy=proxy, timeout=12)
                return await resp.json()
            else:
                resp = await session.get(self.url, proxy=proxy, timeout=12)
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
        super().__init__()
        self.text = None
        self._headers = {'User-Agent': 'clash'}  # 这个请求头是获取流量信息的关键
        self.subconvertor = config.config.get('subconvertor', {})
        self.cvt_enable = self.subconvertor.get('enable', False)
        self.url = suburl
        self.codeurl = quote(suburl, encoding='utf-8')
        self.code_include = quote(include, encoding='utf-8')
        self.code_exclude = quote(exclude, encoding='utf-8')
        self.host = str(self.subconvertor.get('host', '127.0.0.1:25500'))
        self.cvt_url = f"http://{self.host}/sub?target=clash&new_name=true&url={self.codeurl}&include={self.code_include}&exclude={self.code_exclude}&emoji=true"
        self.sub_remote_config = self.subconvertor.get('remoteconfig', '')
        self.config_include = quote(self.subconvertor.get('include', ''), encoding='utf-8')  # 这两个
        self.config_exclude = quote(self.subconvertor.get('exclude', ''), encoding='utf-8')
        print(f"配置文件过滤,包含：{self.config_include} 排除：{self.config_exclude}")
        if self.config_include or self.config_exclude:
            self.cvt_url = f"http://{self.host}/sub?target=clash&new_name=true&url={self.cvt_url}&include={self.code_include}&exclude={self.code_exclude}&emoji=true"
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
                    info = info.replace(';', '').split(' ')
                    info2 = {'upload': 0, 'download': 0, 'total': 0, 'expire': 0}
                    for i in info:
                        try:
                            i1 = i.split('=')
                            info2[i1[0]] = float(i1[1]) if i1[1] else 0
                        except IndexError:
                            pass
                    logger.info(str(info2))
                    traffic_up = info2.get('upload', 0) / 1024 / 1024 / 1024
                    traffic_download = info2.get('download', 0) / 1024 / 1024 / 1024
                    traffic_use = traffic_up + traffic_download
                    traffic_total = info2.get('total', 0) / 1024 / 1024 / 1024
                    expire_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(info2.get('expire', time.time())))
                return [traffic_up, traffic_download, traffic_use, traffic_total, expire_time]
        except asyncio.exceptions.TimeoutError:
            logger.info("获取订阅超时")
            return []
        except ClientConnectorError as c:
            logger.warning(c)
            return []

    async def getSubConfig(self, save_path: str, proxy=proxies):
        """
        获取订阅配置文件
        :param save_path: 订阅保存路径
        :param proxy:
        :return: 获得一个文件: sub.yaml, bool : True or False
        """
        _headers = {'User-Agent': 'clash'}
        suburl = self.cvt_url if self.cvt_enable else self.url
        cvt_text = r"subconvertor状态: {}".format("已启用" if self.cvt_enable else "未启用")
        logger.info(cvt_text)
        try:
            async with aiohttp.ClientSession(headers=_headers) as session:
                async with session.get(suburl, proxy=proxy, timeout=20) as response:
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
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36"}
        self._headers_json = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36", "Content-Type": 'application/json'}
        self.netflixurl1 = "https://www.netflix.com/title/70242311"
        self.netflixurl2 = "https://www.netflix.com/title/70143836"
        self.ipurl = "https://api.ip.sb/geoip"
        self.youtubeurl = "https://www.youtube.com/premium"
        self.youtubeHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36',
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
            if len(items):
                for item in items:
                    i = item.capitalize()
                    # if i == "Netflix":
                    #     task1 = asyncio.create_task(self.fetch_ip(session=session, proxy=proxy))
                    #     self.tasks.append(task1)
                    #     task2 = asyncio.create_task(self.fetch_ninfo1(session, proxy=proxy))
                    #     self.tasks.append(task2)
                    #     task3 = asyncio.create_task(self.fetch_ninfo2(session, proxy=proxy))
                    #     self.tasks.append(task3) # 旧奈飞测试，已废弃
                    if i == "Youtube":
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
                    elif i == "Hbomax":
                        from addons.unlockTest import hbomax
                        self.tasks.append(hbomax.task(self, session, proxy=proxy))
                    elif i == "Bahamut":
                        from addons.unlockTest import bahamut
                        self.tasks.append(bahamut.task(self, session, proxy=proxy))
                    elif i == "Netflix":
                        from addons.unlockTest import netflix
                        self.tasks.append(netflix.task(self, session, proxy=proxy))
                    elif i == "Abema":
                        from addons.unlockTest import abema
                        self.tasks.append(abema.task(self, session, proxy=proxy))
                    elif i == "Bbc":
                        from addons.unlockTest import bbciplayer
                        self.tasks.append(bbciplayer.task(self, session, proxy=proxy))
                    elif i == "公主连结":
                        from addons.unlockTest import pcrjp
                        self.tasks.append(pcrjp.task(self, session, proxy=proxy))
                    elif i == "Primevideo":
                        from addons.unlockTest import primevideo
                        self.tasks.append(primevideo.task(self, session, proxy=proxy))
                    elif i == "Myvideo":
                        from addons.unlockTest import myvideo
                        self.tasks.append(myvideo.task(self, session, proxy=proxy))
                    elif i == "Catchplay":
                        from addons.unlockTest import catchplay
                        self.tasks.append(catchplay.task(self, session, proxy=proxy))
                    elif i == "Viu":
                        from addons.unlockTest import viu
                        self.tasks.append(viu.task(self, session, proxy=proxy))
                    elif i == "Iprisk" or i == "落地ip风险":
                        from addons import ip_risk
                        self.tasks.append(ip_risk.task(self, session, proxy=proxy))
                    elif i == "Steam货币":
                        from addons.unlockTest import steam
                        self.tasks.append(steam.task(self, session, proxy=proxy))
                    elif i == "维基百科":
                        from addons.unlockTest import wikipedia
                        self.tasks.append(wikipedia.task(self, session, proxy=proxy))
                    elif item == "HTTP延迟":
                        self.tasks.append(delay_https_task(self, session, proxy=proxy))
                    else:
                        pass
            return self.tasks
        except Exception as e:
            logger.error(e)
            return []

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
            logger.error(str(e))

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
            youtube = await session.get(self.youtubeurl, proxy=proxy, timeout=5, headers=self.youtubeHeaders,
                                        cookies=self.youtubeCookie)
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
                        self.info['disney'] = "解锁({})".format(region)
                    logger.info("disney+ 成功访问(轻检测，检测结果准确率下降)")
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
                        self.info['disney'] = "解锁({})".format(region)
                else:
                    self.info['disney'] = "失败"
                logger.info("disney+ 成功访问")
                dis2.close()
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
                await asyncio.wait(tasks)
            await session.close()
            return self.info
        except Exception as e:
            logger.error(e)
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


async def delay_https(session: aiohttp.ClientSession, proxy=None, testurl="http://www.gstatic.com/generate_204",
                      timeout=10):
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.5005.63 Safari/537.36'
    }
    try:
        s1 = time.time()
        async with session.get(url=testurl, proxy=proxy, headers=_headers,
                               timeout=timeout) as r:
            if r.status == 204:
                delay1 = time.time() - s1
                # print(delay1)
                return delay1
            else:
                return 0
    except Exception as e:
        logger.error(str(e))
        return 0


async def delay_https_task(collector=None, session: aiohttp.ClientSession = None, proxy=None, times=5):
    if session is None:
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(delay_https(session=session, proxy=proxy)) for _ in range(times)]
            result = await asyncio.gather(*tasks)
            sum_num = [r for r in result if r != 0]
            http_delay = sum(sum_num) / len(sum_num) if len(sum_num) else 0
            http_delay = "%.0fms" % (http_delay * 1000)
            # print("http平均延迟:", http_delay)
            if collector is not None:
                collector.info['HTTP延迟'] = http_delay
            return http_delay
    else:
        tasks = [asyncio.create_task(delay_https(session=session, proxy=proxy)) for _ in range(times)]
        result = await asyncio.gather(*tasks)
        sum_num = [r for r in result if r != 0]
        http_delay = sum(sum_num) / len(sum_num) if len(sum_num) else 0
        http_delay = "%.0fms" % (http_delay * 1000)
        # print("http平均延迟:", http_delay)
        if collector is not None:
            collector.info['HTTP延迟'] = http_delay
        return http_delay


if __name__ == "__main__":
    "this is a test demo"
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(delay_https_task())
