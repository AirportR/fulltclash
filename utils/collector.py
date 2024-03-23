import asyncio
import ssl
import time
from datetime import datetime
from pathlib import Path

from typing import List, Union
from urllib.parse import quote

import aiohttp
import async_timeout
from aiohttp import ClientSession

from aiohttp.client_exceptions import ClientConnectorError, ContentTypeError
from aiohttp_socks import ProxyConnector, ProxyConnectionError
from loguru import logger

from utils import cleaner
from utils.cleaner import config

"""
这是整个项目最为核心的功能模块之一 —> 采集器。它负责从网络上采集想要的数据。到现在，已经设计了：
1、采集器基类（BaseCollector）。一个简单的采集器示例。
2、IP采集器（IPCollector）。负责采集ip的相关信息
3、订阅采集器（SubCollector）。负责从网络上获取订阅文件
4、采集器（Collector）。负责各种流媒体解锁信息的采集
5、一个批量测试延迟的函数，基于clash core
需要注意的是，这些类/函数仅作采集工作，并不负责清洗。我们需要将拿到的数据给cleaner类清洗。

** 开发建议 **
如果你想自己添加一个流媒体测试项，建议查看 ./resources/dos/新增流媒体测试项指南.md
"""

addon = cleaner.addon
media_items = config.get_media_item()
proxies = config.get_proxy()  # 代理
netflix_url = config.config.get('netflixurl', "https://www.netflix.com/title/70143836")


def reload_config(media: list = None):
    global proxies, media_items
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
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.get(url, proxy=proxy) as response:
                    return await response.content.read()


class DownloadError(aiohttp.ClientError):
    """下载出错抛出的异常"""


class Download(BaseCollector):
    def __init__(self, url: str = None, savepath: Union[str, Path] = None, savename: str = None):
        _formatted_now = f'{datetime.now():%Y-%m-%dT%H-%M-%S}'
        self.url = url
        self.savepath = savepath
        self.savename = savename if savename is not None else f"download-{_formatted_now}"
        super().__init__()

    async def download_common(self, url: str = None, savepath: Union[str, Path] = None, **kwargs) -> bool:
        """
        通用下载函数
        """
        url = url or self.url
        savepath = savepath or self.savepath or "."
        savepath = str(savepath)
        savepath = savepath if savepath.endswith("/") else savepath + "/"
        savename = self.savename.lstrip("/")
        write_path = savepath + savename
        from utils.cleaner import geturl
        url = geturl(url)
        if not url:
            raise DownloadError(f"这不是有效的URL: {url}")
        try:
            async with ClientSession(headers=self._headers) as session:
                async with session.get(url, **kwargs) as resp:
                    if resp.status == 200:
                        content_leagth = resp.content_length if resp.content_length else 10 * 1024 * 1024
                        length = 0
                        with open(write_path, 'wb') as f:
                            while True:
                                chunk = await resp.content.read(1024)
                                length += len(chunk)
                                # 计算进度条长度
                                percent = '=' * int(length * 100 / content_leagth)
                                spaces = ' ' * (100 - len(percent))
                                print(f"\r[{percent}{spaces}] {length} B", end="")
                                if not chunk:
                                    break

                                f.write(chunk)
                            l2 = float(length) / 1024 / 1024
                            l2 = round(l2, 2)
                            spath = str(Path(savepath).absolute())
                            print(f"\r[{'=' * 100}] 共下载{length}B ({l2}MB)"
                                  f"已保存到 {spath}")
                    elif resp.status == 404:
                        raise DownloadError(f"找不到资源: {resp.status}==>\t{url}")
            return True
        except (aiohttp.ClientError, OSError) as e:
            raise DownloadError("Download failed") from e

    async def dowload(self, url: str = None, savepath: Union[str, Path] = None, **kwargs) -> bool:
        """
        执行下载操作
        """
        return await self.download_common(url, savepath, **kwargs)


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
    def __init__(self, suburl: str, include: str = '', exclude: str = '', force_convert: bool = False):
        """
        这里在初始化中读取了subconverter的相关配置，但是由于sunconverter无人维护，容易出问题，因此之后我不会再维护此功能。也就是在下载订阅时
        订阅转换

        :param: force_convert: 是否强制转换，如果传进来的url本身就已经是subconverter拼接过的，那么套娃转换会拖慢拉去订阅的速度。
                                设置为False会检查是否为subconverter拼接过的
        """
        super().__init__()
        self.text = None
        self._headers = {'User-Agent': 'clash'}  # 这个请求头是获取流量信息的关键
        self.subcvt_conf = config.config.get('subconverter', {})
        self.cvt_enable = self.subcvt_conf.get('enable', False)
        self.url = suburl
        self.include = include
        self.exclude = exclude
        self.codeurl = quote(suburl, encoding='utf-8')
        self.code_include = quote(include, encoding='utf-8')
        self.code_exclude = quote(exclude, encoding='utf-8')
        self.cvt_host = str(self.subcvt_conf.get('host', '127.0.0.1:25500'))
        self.cvt_scheme = self.parse_cvt_scheme()
        self.cvt_url = f"{self.cvt_scheme}://{self.cvt_host}/sub?target=clash&new_name=true&url={self.codeurl}" \
                       + f"&include={self.code_include}&exclude={self.code_exclude}"
        self.sub_remote_config = self.subcvt_conf.get('remoteconfig', '')
        self.config_include = quote(self.subcvt_conf.get('include', ''), encoding='utf-8')  # 这两个
        self.config_exclude = quote(self.subcvt_conf.get('exclude', ''), encoding='utf-8')
        # print(f"配置文件过滤,包含：{self.config_include} 排除：{self.config_exclude}")
        if self.config_include or self.config_exclude:
            self.cvt_url = f"{self.cvt_scheme}://{self.cvt_host}/sub?target=clash&new_name=true&url={self.cvt_url}" \
                           + f"&include={self.code_include}&exclude={self.code_exclude}"
        if self.sub_remote_config:
            self.sub_remote_config = quote(self.sub_remote_config, encoding='utf-8')
            self.cvt_url = self.cvt_url + "&config=" + self.sub_remote_config
        if not force_convert:
            if "/sub?target=" in self.url:
                self.cvt_url = self.url

    def parse_cvt_scheme(self) -> str:
        if not bool(self.subcvt_conf.get('tls', False)):
            return "http"
        else:
            return "https"

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

        async def safe_read(_response: aiohttp.ClientResponse, limit: int = 52428800):
            if _response.content_length and _response.content_length > limit:
                logger.warning(f"订阅文件大小超过了{limit / 1024 / 1024}MB的阈值，已取消获取。")
                return False
            _data = b''
            if inmemory:
                while True:
                    _chunk = await _response.content.read(1024)
                    if not _chunk:
                        logger.info("获取订阅成功")
                        break
                    _data += _chunk
                    if len(_data) > limit:
                        logger.warning(f"订阅文件大小超过了{limit / 1024 / 1024}MB的阈值，已取消获取。")
                        return False
                return _data
            else:
                with open(save_path, 'wb+') as fd:
                    while True:
                        _chunk = await _response.content.read(1024)
                        if not _chunk:
                            logger.info("获取订阅成功")
                            break
                        fd.write(_chunk)
            return True

        try:
            async with aiohttp.ClientSession(headers=_headers) as session:
                async with session.get(suburl, proxy=proxy, timeout=20) as response:
                    if response.status == 200:
                        return await safe_read(response)
                    else:
                        if self.url == self.cvt_url:
                            return False
                        self.cvt_url = self.url
                        return await self.getSubConfig(inmemory=True)
        except asyncio.exceptions.TimeoutError:
            logger.info("获取订阅超时")
            return False
        except ClientConnectorError as c:
            logger.warning(c)
            return False


class Collector:
    def __init__(self, script: List[str] = None):
        self.tasks = []
        self._script = script
        self._headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36"}
        self._headers_json = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/106.0.0.0 Safari/537.36", "Content-Type": 'application/json'}
        self.info = {}
        self.disneyurl1 = "https://www.disneyplus.com/"
        self.disneyurl2 = "https://global.edge.bamgrid.com/token"

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
                        from addons.builtin import youtube
                        self.tasks.append(youtube.task(self, session, proxy=proxy))
                    elif i == "Disney" or i == "Disney+":
                        task5 = asyncio.create_task(self.fetch_dis(session, proxy=proxy))
                        self.tasks.append(task5)
                    elif i == "Netflix":
                        from addons.builtin import netflix
                        self.tasks.append(netflix.task(self, session, proxy=proxy, netflixurl=netflix_url))
                    elif i == "TVB":
                        from addons.builtin import tvb
                        self.tasks.append(tvb.task(self, session, proxy=proxy))
                    elif i == "Viu":
                        from addons.builtin import viu
                        self.tasks.append(viu.task(self, session, proxy=proxy))
                    elif i == "Iprisk" or i == "落地IP风险":
                        from addons.builtin import ip_risk
                        self.tasks.append(ip_risk.task(self, session, proxy=proxy))
                    elif i == "steam货币":
                        from addons.builtin import steam
                        self.tasks.append(steam.task(self, session, proxy=proxy))
                    elif i == "维基百科":
                        from addons.builtin import wikipedia
                        self.tasks.append(wikipedia.task(self, session, proxy=proxy))
                    elif item == "OpenAI":
                        from addons.builtin import openai
                        self.tasks.append(openai.task(self, session, proxy=proxy))
                    else:
                        pass
            return self.tasks
        except Exception as e:
            logger.error(e)
            return []

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
            tasks = self.create_tasks(session, proxy=proxy)
            if tasks:
                try:
                    await asyncio.wait(tasks)
                except (ConnectionRefusedError, ProxyConnectionError, ssl.SSLError) as e:
                    logger.error(str(e))
                    return self.info
            await session.close()
            return self.info
        except Exception as e:
            logger.error(str(e))
            return self.info


async def get_latest_tag(username, repo):
    import re
    url = f'https://github.com/{username}/{repo}/tags'
    async with ClientSession() as session:
        async with session.get(url, proxy=config.get_proxy(), timeout=10) as r:
            text = await r.text()
            tags = re.findall(r'/.*?/tag/(.*?)"', text)
            if tags:
                return tags[0]
            else:
                return None


if __name__ == "__main__":
    pass
