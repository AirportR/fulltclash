import asyncio
import contextlib
import copy
import socket
import time

from collections import Counter
from operator import itemgetter
from typing import Union, Callable, Coroutine, Tuple

import aiohttp
import socks
from aiohttp_socks import ProxyConnector
from loguru import logger
from utils.collector import proxies
from libs import pynat
from utils import cleaner, collector, ipstack, proxys, sorter, geoip

# 重写整个测试核心，技术栈分离。


break_speed = []
GCONFIG = cleaner.config  # 全局配置


class Basecore:
    """
    测试核心基类
    """

    def __init__(self, progress_func: Tuple[Union[Callable, Coroutine], Tuple] = None):
        """
        progress_func: 第一个元素是一个进度反馈回调函数，这个函数可以是协程函数。第二个元素是该函数所需要的参数（元组形式），
        其中函数第一和第二位置形参固定为progress --> 当前已经测试的节点数， nodenum --> 这次测试所有节点数 ,
        自己需要的额外参数将从第三个位置开始
        例子:

        假设函数名为 func 它所需的参数为 arg1 arg2 ，则在定义时，需要这样定义：
        func(progress, nodenum, arg1, arg2) ,前两个参数 core核心会自动传入，不需要可以设置为_ __
        func(_, __, arg1, arg2) 不需要默认传入参数的形式
        当然如果参数过多 ，假如有 10个参数： arg1 - arg10 ，也可以这样定义函数：
        func(progress, nodenum, *args)

        如果progress_func为None，则使用默认的: default_progress()
        """
        self.prs = progress_func
        self._info = {}
        self._pre_include_text = GCONFIG.config.get('subconverter', {}).get('include', '')  # 从配置文件里预定义过滤规则
        self._pre_exclude_text = GCONFIG.config.get('subconverter', {}).get('exclude', '')
        self._node_issave = GCONFIG.config.get('clash', {}).get('allow-caching', False)
        self._include_text = ''
        self._exclude_text = ''
        self._start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
        self._config = cleaner.ClashCleaner(":memory:")

    @property
    def start_time(self) -> str:
        return self._start_time

    @staticmethod
    def core(*args, **kwargs) -> dict:
        """
        您必须自主实现这里的方法，因为Basecore是一个基类
        :return:
        """
        raise NotImplementedError

    @staticmethod
    def check_rtt(rtt, nodenum: int) -> list:
        return [0 for _ in range(nodenum)] if rtt == 0 else rtt

    def join_proxy(self, proxyinfo: list, filters: bool = False):
        self._config.setProxies(proxyinfo)
        if filters:
            self._config.node_filter(self._pre_include_text, self._pre_exclude_text, issave=False)  # 从配置文件过滤文件

    def setfilter(self, include_text: str = '', exclude_text: str = ''):
        self._include_text = include_text
        self._exclude_text = exclude_text

    def check_node(self) -> bool:
        """
        有节点则返回真。否则为假
        """
        return bool(self._config.getProxies())

    def getnodeinfo(self) -> tuple:
        nodename = self._config.nodesName()
        nodetype = self._config.nodesType()
        nodenum = self._config.nodesCount()
        nodelist = self._config.getProxies()
        return nodename, nodetype, nodenum, nodelist

    def saveresult(self, info: dict) -> bool:
        """
        保存测试结果
        :return:
        """
        cl1 = cleaner.ConfigManager(configpath=fr"./results/{self.start_time}.yaml", data=info)
        return cl1.save(fr"./results/{self.start_time}.yaml")

    async def progress(self, *args):
        """
        进度反馈用的回调函数，需要实现。
        其中func是一个函数对象，它可以是协程函数，即用 async def func 定义的函数
        """
        progress = args[0]
        nodenum = args[1]
        if self.prs is None:
            self.default_progress(progress, nodenum)
        else:
            func, funcarg = self.prs
            if asyncio.iscoroutinefunction(func):
                await func(progress, nodenum, *funcarg)
            else:
                func(progress, nodenum, *funcarg)
            return

    def default_progress(self, *args, **kwargs):
        raise NotImplementedError


class Speedtest:
    """
    此类代码原本来源于 https://github.com/OreosLab/SSRSpeedN 项目。代码已做修改。
    """

    def __init__(self):
        self._config = cleaner.ConfigManager()
        self._stopped = False
        self.speedurls = self.config.get('speedfile',
                                         "https://dl.google.com/dl/android/studio/install/3.4.1.0/" +
                                         "android-studio-ide-183.5522156-windows.exe")
        if isinstance(self.speedurls, str):
            self.speedurl = []
            self.speedurl.append(self.speedurls)
        else:
            self.speedurl = self.speedurls
        self._thread = self.config.get('speedthread', 4)
        self.result = []
        self._total_red = 0
        self._delta_red = 0
        self._start_time = 0
        self._statistics_time = 0
        self._time_used = 0
        self._count = 0
        interval = self.config.get('speedconfig', {}).get('interval', 10)
        self._download_intervals = interval if 0 < interval < 60 else 10
        self._download_interval = self._download_intervals + 1

    @property
    def thread(self) -> int:
        return self._thread

    @property
    def config(self):
        return self._config.config

    @property
    def stopped(self) -> bool:
        return self._stopped

    @property
    def time_used(self) -> Union[int, float]:
        return self._time_used

    @property
    def total_red(self) -> Union[int, float]:
        return self._total_red

    @property
    def speed_list(self) -> list:
        return copy.deepcopy(self.result)

    @property
    def max_speed(self) -> Union[int, float]:
        return max(self.speed_list) if self.speed_list else 0

    async def record(self, received: Union[int, float]):
        cur_time = time.time()
        if not self._start_time:
            self._start_time = cur_time
        delta_time = cur_time - self._statistics_time
        self._time_used = cur_time - self._start_time
        self._total_red += received
        if delta_time > 1:
            self._statistics_time = cur_time
            with contextlib.suppress(StopIteration):
                self._show_progress(delta_time)
        if self._time_used > self._download_interval:
            self._stopped = True

    def _show_progress(self, delta_time: Union[int, float]):
        speed = (self._total_red - self._delta_red) / delta_time
        speed_mb = speed / 1024 / 1024
        self._delta_red = self._total_red
        self._count += 1
        print("\r[" + "=" * self._count + f"> [{speed_mb:.2f} MB/s]", end="")
        if len(self.result) < self._download_interval:
            self.result.append(speed)

    def show_progress_full(self):
        mb_red = self._total_red / 1024 / 1024
        print(
            "\r["
            + "=" * self._count
            + "] ["
            + (f"{mb_red / self._time_used:.2f}" if self._time_used else "0")
            + "MB/s]"
        )
        logger.info(f"Fetched {mb_red:.2f} MB in {self._time_used:.2f}s.")


class SpeedCore(Basecore):
    def __init__(self, chat_id=None, message_id=None, IKM=None, prs: Tuple[Union[Callable, Coroutine], Tuple] = None):
        """
        IKM: 内联按钮（中止测速）
        """
        super().__init__()
        self.IKM = IKM
        self.edit = (chat_id, message_id)
        self.prs = prs

    def default_progress(self, progress: int, nodenum: int):
        """
        默认的进度条反馈函数
        """
        edit_text = default_progress_text(self.__class__.__name__, progress, nodenum)
        print(edit_text)

    @staticmethod
    def nat_type_test(proxyaddr=None, proxyport=None):
        mysocket = socks.socksocket(type=socket.SOCK_DGRAM)
        mysocket.set_proxy(socks.PROXY_TYPE_SOCKS5, addr=proxyaddr, port=proxyport)
        _sport = 54320
        try:
            logger.info("Performing UDP NAT Type Test.")
            t, eip, eport, sip = pynat.get_ip_info(
                source_port=_sport,
                include_internal=True,
                sock=mysocket,
            )
            return t, eip, eport, sip, _sport
        except (socket.gaierror, TypeError, ConnectionError) as e:
            logger.error(f"NAT Type Test: {repr(e)}")
            return None, None, None, None, None
        except Exception as e:
            logger.exception(e)
            return None, None, None, None, None
        finally:
            mysocket.close()

    @staticmethod
    async def fetch(self: Speedtest, urls: list, host: str, port: int, buffer: int):
        try:
            async with aiohttp.ClientSession(
                    headers={"User-Agent": "FullTclash"},
                    connector=ProxyConnector(host=host, port=port),
            ) as session:
                flag = 0
                while True:
                    for url in urls:
                        if self._stopped:
                            break
                        async with session.get(url, timeout=self._download_interval + 3) as response:
                            while not self._stopped:
                                if not break_speed:
                                    chunk = await response.content.read(buffer)
                                    if not chunk:
                                        logger.info("polling start")
                                        break
                                    await self.record(len(chunk))
                                else:
                                    flag = 1
                                    break
                        if flag == 1:
                            break
                    if self._stopped:
                        break
                    elif break_speed:
                        break
        except Exception as e:
            logger.error(f"Download link error: {str(e)}")

    @staticmethod
    async def speed_start(
            proxy_host: str,
            proxy_port: int,
            buffer: int,
            workers: int = 0,
    ) -> tuple:
        download_semaphore = asyncio.Semaphore(workers if workers else Speedtest().thread)
        async with download_semaphore:
            st = Speedtest()
            urls = st.speedurl
            # logger.debug(f"Url: {url}")
            thread = workers if workers else st.thread
            logger.info(f"Running st_async, workers: {thread}.")
            tasks = [
                asyncio.create_task(SpeedCore.fetch(st, urls, proxy_host, proxy_port, buffer))
                for _ in range(thread)
            ]
            await asyncio.wait(tasks)
            st.show_progress_full()
            spmean = st.total_red / st.time_used if st.time_used else 0
            spmax = st.max_speed
            if spmean > spmax:
                spmean, spmax = spmax, spmean
            if st.time_used:
                return (
                    spmean,
                    spmax,
                    st.speed_list[1:],
                    st.total_red,
                )

            return 0, 0, [], 0

    # 以下为 另一部分
    async def batch_speed(self, nodelist: list, port: int = 11220, proxy_obj: Union[proxys.FullTClash] = None):
        info = {}
        progress = 0
        sending_time = 0
        nodenum = len(nodelist)
        control_port = proxys.CONTROL_PORT if proxy_obj is None else proxy_obj.cport
        test_items = ["HTTP(S)延迟", "平均速度", "最大速度", "每秒速度", "UDP类型"]
        for item in test_items:
            info[item] = []
        info["消耗流量"] = 0  # 单位:MB
        if not self.check_node():
            return info

        await self.progress(progress, nodenum)
        for name in nodelist:
            # proxys.switchProxy(name, 0)
            await proxys.FullTClash.setproxy(name, 0, control_port)
            # delay = await proxys.http_delay_tls(index=0)
            # delay = await proxys.http_delay(index=0)
            delay = await proxys.FullTClash.urltest(port)
            udptype, _, _, _, _ = self.nat_type_test('127.0.0.1', proxyport=port)
            if udptype is None:
                udptype = "Unknown"
            res = await self.speed_start("127.0.0.1", port, 4096)
            avgspeed_mb = res[0] / 1024 / 1024
            if avgspeed_mb < 1:
                avgspeed = "%.2f" % (res[0] / 1024) + "KB"
            else:
                avgspeed = "%.2f" % avgspeed_mb + "MB"
            maxspeed_mb = res[1] / 1024 / 1024
            if maxspeed_mb < 1:
                maxspeed = "%.2f" % (res[1] / 1024) + "KB"
            else:
                maxspeed = "%.2f" % maxspeed_mb + "MB"
            speedresult = [v / 1024 / 1024 for v in res[2]]
            traffic_used = float("%.2f" % (res[3] / 1024 / 1024))
            info["消耗流量"] += traffic_used
            res2 = [delay, avgspeed, maxspeed, speedresult, udptype]
            for i, _ in enumerate(test_items):
                info[test_items[i]].append(res2[i])

            if break_speed:
                logger.warning("❌测速任务已取消")
                break
            progress += 1
            cal = progress / nodenum * 100
            # p_text = "%.2f" % cal
            if cal >= sending_time:
                sending_time += 10
                await self.progress(progress, nodenum)
        return info

    async def core(self, proxyinfo: list, **kwargs):
        info = {}  # 存放测速结果
        self.join_proxy(proxyinfo)
        # start_port = GCONFIG.config.get('clash', {}).get('startup', 11220)
        # 订阅加载
        nodename, nodetype, _, nodelist = self.getnodeinfo()
        # 开始测试
        s1 = time.time()
        try:
            break_speed.clear()
            # 创建代理实例
            port_list = await proxys.get_available_port(2)
            control_port = port_list.pop(0)
            fulltclash = proxys.FullTClash(control_port, port_list)
            await fulltclash.start()
            await asyncio.sleep(1)
            # 预填充
            info['节点名称'] = nodename
            info['类型'] = nodetype
            try:
                speedinfo = await self.batch_speed(nodelist, port_list[0], fulltclash)
                info.update(speedinfo)
            except Exception as e:
                logger.error(str(e))
            finally:
                fulltclash.close()
            info = cleaner.ResultCleaner(info).start()
            # 计算测试消耗时间
            wtime = "%.1f" % float(time.time() - s1)
            info['wtime'] = wtime
            # 过滤器
            flt = kwargs.get('filter', None)
            info['filter'] = flt if flt else {'include': self._include_text, 'exclude': self._exclude_text}
            info['线程'] = collector.config.config.get('speedthread', 4)
            if break_speed:
                info.clear()
        except Exception as e:
            logger.error(e)
        # 保存结果
        self.saveresult(info)
        # 将结果返回
        return info


class ScriptCore(Basecore):
    def __init__(self, chat_id=None, message_id=None, progress_func: Tuple[Union[Callable, Coroutine], Tuple] = None):
        super().__init__()
        self.edit = (chat_id, message_id)
        self.prs = progress_func

    def default_progress(self, progress: int, nodenum: int):
        """
        默认的进度条反馈函数
        """
        edit_text = default_progress_text(self.__class__.__name__, progress, nodenum)
        print(edit_text)

    @staticmethod
    async def unit(test_items: list, host="127.0.0.1", port=11220):
        """
        以一个节点的所有测试项为一个基本单元unit,返回单个节点的测试结果
        :param port: 代理端口
        :param host: 代理主机名
        :param test_items: [Netflix,disney+,etc...]
        :return: list 返回test_items对应顺序的信息
        """
        info = []
        if "HTTP(S)延迟" in test_items:
            delay = await proxys.FullTClash.urltest(port)
            if delay == 0:
                logger.warning("超时节点，跳过测试")
                for t in test_items:
                    if t == "HTTP(S)延迟":
                        info.append(0)
                    else:
                        info.append("N/A")
                return info
            info.append(delay)
        cl = collector.Collector(script=test_items)
        re1 = await cl.start(host, port)
        cnr = cleaner.ReCleaner(re1, script_list=test_items)
        old_info = cnr.get_all()
        for item in test_items:
            i = item
            if i == 'HTTP(S)延迟':
                continue
            try:
                info.append(old_info[i])
            except KeyError:
                info.append("N/A")
                logger.error("KeyError: 无法找到 " + item + " 测试项")
        return info

    async def batch_test_pro(self, proxyinfo: list, test_items: list, pool: dict,
                             proxy_obj: Union[proxys.FullTClash] = None):
        """
        nodename:
        """
        info = {}
        progress = 0
        sending_time = 0
        host = pool.get('host', [])
        port = pool.get('port', [])
        psize = len(port)
        nodenum = len(proxyinfo)
        control_port = proxys.CONTROL_PORT if proxy_obj is None else proxy_obj.cport
        tasks = []

        for item in test_items:
            info[item] = []
        logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
        if not self.check_node():
            return info
        if psize <= 0:
            logger.error("无可用的代理程序接口")
            return {}

        await self.progress(progress, nodenum)

        if nodenum < psize:
            for i in range(len(port[:nodenum])):
                await proxys.FullTClash.setproxy(proxyinfo[i], i, control_port)
                # proxys.switchProxy(nodename[i], i)
                task = asyncio.create_task(self.unit(test_items, host=host[i], port=port[i]))
                tasks.append(task)
            done = await asyncio.gather(*tasks)
            # 简单处理一下数据
            res = []
            for j, _ in enumerate(test_items):
                res.clear()
                for d in done:
                    res.append(d[j])
                info[test_items[j]].extend(res)
            logger.info(str(info))
            return info
        else:
            subbatch = nodenum // psize
            for s in range(subbatch):
                logger.info("当前批次: " + str(s + 1))
                tasks.clear()

                for i in range(psize):
                    await proxys.FullTClash.setproxy(proxyinfo[s * psize + i], i, control_port)
                    # proxys.switchProxy(nodename[s * psize + i], i)
                    task = asyncio.create_task(self.unit(test_items, host=host[i], port=port[i]))
                    tasks.append(task)
                done = await asyncio.gather(*tasks)
                # 反馈进度
                progress += psize
                cal = progress / nodenum * 100
                # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
                if cal > sending_time:
                    sending_time += 20
                    await self.progress(progress, nodenum)

                # 简单处理一下数据
                res = []
                for j in range(len(test_items)):
                    res.clear()
                    for d in done:
                        res.append(d[j])
                    info[test_items[j]].extend(res)

            if nodenum % psize != 0:
                tasks.clear()
                logger.info("最后批次: " + str(subbatch + 1))
                for i in range(nodenum % psize):
                    await proxys.FullTClash.setproxy(proxyinfo[subbatch * psize + i], i, control_port)
                    # proxys.switchProxy(nodename[subbatch * psize + i], i)
                    task = asyncio.create_task(self.unit(test_items, host=host[i], port=port[i]))
                    tasks.append(task)
                done = await asyncio.gather(*tasks)
                res = []
                for j in range(len(test_items)):
                    res.clear()
                    for d in done:
                        res.append(d[j])
                    info[test_items[j]].extend(res)
        # 最终进度条
        if nodenum % psize != 0:
            progress += nodenum % psize
            await self.progress(progress, nodenum)

        return info

    async def core(self, proxyinfo: list, **kwargs):
        info = {}  # 存放测试结果
        media_items = kwargs.get('script', None) or kwargs.get('test_items', None) or kwargs.get('media_items', None)
        test_items = collector.media_items if media_items is None else media_items
        test_items = cleaner.addon.mix_script(test_items, False)
        # 先把节点信息写入文件
        self.join_proxy(proxyinfo)
        # 获取可供测试的测试端口
        thread = GCONFIG.config.get('clash', {}).get('core', 1)
        # startup = GCONFIG.config.get('clash', {}).get('startup', 11220)
        port_list = await proxys.get_available_port(thread + 1)
        control_port = port_list.pop(0)
        # 设置代理端口
        fulltclash = proxys.FullTClash(control_port, port_list)
        await fulltclash.start()
        pool = {'host': ['127.0.0.1' for _ in range(len(port_list))],
                'port': port_list}
        # 订阅加载
        nodename, nodetype, nodenum, nodelist = self.getnodeinfo()
        # 开始测试
        s1 = time.time()
        info['节点名称'] = nodename
        info['类型'] = nodetype
        try:
            test_info = await self.batch_test_pro(nodelist, test_items, pool, fulltclash)
        except Exception as e:
            print(e)
            logger.error(f"{str(e.__class__)}:{str(e)}")
            return {}
        finally:
            fulltclash.close()
            logger.info("子进程已关闭")
        if 'HTTP(S)延迟' in test_info:
            info['HTTP(S)延迟'] = test_info.pop('HTTP(S)延迟')
        info.update(test_info)
        # 排序
        sort = kwargs.get('sort', "订阅原序")
        logger.info("排序：" + sort)
        info = cleaner.ResultCleaner(info).start(sort=sort)
        info['sort'] = sort
        # 计算测试消耗时间
        info['wtime'] = "%.1f" % float(time.time() - s1)
        # 过滤器
        flt = kwargs.get('filter', None)
        info['filter'] = flt if flt else {'include': self._include_text, 'exclude': self._exclude_text}
        # 保存结果
        self.saveresult(info)
        return info


class TopoCore(Basecore):
    """
    拓扑测试核心
    """

    def __init__(self, chat_id=None, message_id=None, progress_func: Tuple[Union[Callable, Coroutine], Tuple] = None):
        super().__init__()
        self.edit = (chat_id, message_id)
        self.ip_choose = GCONFIG.config.get('entrance', {}).get('switch', 'ip')
        self.prs = progress_func

    def default_progress(self, progress: int, nodenum: int):
        """
        默认的进度条反馈函数
        """
        edit_text = default_progress_text(self.__class__.__name__, progress, nodenum)
        print(edit_text)

    async def topo(self):
        if self.ip_choose == "ip":
            info = {'地区': [], 'AS编号': [], '组织': [], '栈': [], '入口ip段': []}
        elif self.ip_choose == "cluster":
            info = {'地区': [], 'AS编号': [], '组织': [], '栈': [], '簇': []}
        else:
            info = {'地区': [], 'AS编号': [], '组织': [], '栈': []}
        cl = copy.deepcopy(self._config)
        _data = GCONFIG.config.get("localip", False)
        if not self.check_node():
            return info, [], cl
        co = collector.IPCollector()
        session = aiohttp.ClientSession()
        # node_addrs = cl.nodehost()
        nodename, inboundinfo, cl, ipstack_list, ipclu = sorter.sort_nodename_topo(cl)
        ipstack_lists = list(ipstack_list.values())
        ipclus = list(ipclu.values())
        info['栈'] = ipstack_lists
        if nodename and inboundinfo and cl:
            # 拿地址，已经转换了域名为ip,hosts变量去除了N/A
            hosts = list(inboundinfo.keys())
            if _data:
                code = []
                org = []
                asns = []
                for ip in hosts:
                    c, o, a = geoip.geo_info(ip)
                    code.append(c)
                    org.append(o)
                    asns.append(a)
                    info.update({'地区': code, 'AS编号': asns, '组织': org})
                    numcount = []
                    for v in inboundinfo.values():
                        numcount.append(int(v))
                    info.update({'出口数量': numcount})
                    new_hosts = []
                    if self.ip_choose == "ip":
                        for host in hosts:
                            if len(host) < 16:  # v4地址最大长度为15
                                try:
                                    old_ip = host.split('.')[:2]
                                    new_ip = old_ip[0] + "." + old_ip[1] + ".*.*"
                                except IndexError:
                                    new_ip = host
                                new_hosts.append(new_ip)
                            elif len(host) > 15:
                                try:
                                    old_ip = host.split(':')[2:4]
                                    new_ip = "*:*:" + old_ip[0] + ":" + old_ip[1] + ":*:*"
                                except IndexError:
                                    new_ip = host
                                new_hosts.append(new_ip)
                            else:
                                new_hosts.append(host)
                        info.update({'入口ip段': new_hosts})
                    elif self.ip_choose == "cluster":
                        info.update({'簇': ipclus})
                return info, hosts, cl
            else:
                co.create_tasks(session=session, hosts=hosts, proxy=proxies)
                res = await co.start()
                await session.close()
                if res:
                    country_code = []
                    asn = []
                    org = []
                    for j in res:
                        ipcl = cleaner.IPCleaner(j)
                        country_code.append(ipcl.get_country_code())
                        asn.append(str(ipcl.get_asn()))
                        org.append(ipcl.get_org())
                    info.update({'地区': country_code, 'AS编号': asn, '组织': org})
                    numcount = []
                    for v in inboundinfo.values():
                        numcount.append(int(v))
                    info.update({'出口数量': numcount})
                    new_hosts = []
                    if self.ip_choose == "ip":
                        for host in hosts:
                            if len(host) < 16:  # v4地址最大长度为15
                                try:
                                    old_ip = host.split('.')[:2]
                                    new_ip = old_ip[0] + "." + old_ip[1] + ".*.*"
                                except IndexError:
                                    new_ip = host
                                new_hosts.append(new_ip)
                            elif len(host) > 15:
                                try:
                                    old_ip = host.split(':')[2:4]
                                    new_ip = "*:*:" + old_ip[0] + ":" + old_ip[1] + ":*:*"
                                except IndexError:
                                    new_ip = host
                                new_hosts.append(new_ip)
                            else:
                                new_hosts.append(host)
                        info.update({'入口ip段': new_hosts})
                    elif self.ip_choose == "cluster":
                        info.update({'簇': ipclus})
                return info, hosts, cl

    async def batch_topo(self, nodename: list, pool: dict, proxy_obj: Union[proxys.FullTClash] = None):
        resdata = []
        ipstackes = []
        progress = 0
        sending_time = 0
        host = pool.get('host', [])
        port = pool.get('port', [])
        psize = len(port)
        nodenum = len(nodename)
        ipstack_enable = GCONFIG.config.get('ipstack', False)
        control_port = proxys.CONTROL_PORT if proxy_obj is None else proxy_obj.cport
        if psize <= 0:
            logger.error("无可用的代理程序接口")
            return [], []
        if not self.check_node():
            return resdata, ipstackes

        logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
        logger.info("⏳节点链路拓扑测试进行中...")
        await self.progress(progress, nodenum)
        if nodenum < psize:
            for i in range(nodenum):
                await proxys.FullTClash.setproxy(nodename[i], i, control_port)
                # proxys.switchProxy(nodename[i], i)
            ipcol = collector.IPCollector()
            sub_res = await ipcol.batch(proxyhost=host[:nodenum], proxyport=port[:nodenum])
            resdata.extend(sub_res)
            if ipstack_enable:
                ipstat = await ipstack.get_ips(proxyhost=host[:nodenum], proxyport=port[:nodenum])
                ipstackes.append({'ips': ipstat})
            else:
                ipstackes.extend([{'ips': '-'} for _ in range(nodenum)])
            return resdata, ipstackes
        else:
            subbatch = nodenum // psize
            for s in range(subbatch):
                logger.info("当前批次: " + str(s + 1))
                for i in range(psize):
                    await proxys.FullTClash.setproxy(nodename[s * psize + i], i, control_port)
                    # proxys.switchProxy(nodename[s * psize + i], i)
                ipcol = collector.IPCollector()
                sub_res = await ipcol.batch(proxyhost=host, proxyport=port)
                resdata.extend(sub_res)
                if ipstack_enable:
                    ipstat = await ipstack.get_ips(proxyhost=host, proxyport=port)
                    ipstackes.append({'ips': ipstat})
                else:
                    ipstackes.extend([{'ips': '-'} for _ in range(psize)])

                # 反馈进度
                progress += psize
                cal = progress / nodenum * 100
                if cal >= sending_time:
                    sending_time += 10
                    await self.progress(progress, nodenum)

            if nodenum % psize != 0:
                logger.info("最后批次: " + str(subbatch + 1))
                for i in range(nodenum % psize):
                    await proxys.FullTClash.setproxy(nodename[subbatch * psize + i], i, control_port)
                    # proxys.switchProxy(nodename[subbatch * psize + i], i)
                ipcol = collector.IPCollector()
                sub_res = await ipcol.batch(proxyhost=host[:nodenum % psize],
                                            proxyport=port[:nodenum % psize])
                resdata.extend(sub_res)
                if ipstack_enable:
                    ipstat = await ipstack.get_ips(proxyhost=host[:nodenum % psize], proxyport=port[:nodenum % psize])
                    ipstackes.append({'ips': ipstat})
                else:
                    ipstackes.extend([{'ips': '-'} for _ in range(nodenum % psize)])

            # 最终进度条
            if nodenum % psize != 0:
                progress += nodenum % psize
                await self.progress(progress, nodenum)
            return resdata, ipstackes

    async def core(self, proxyinfo: list, **kwargs):
        # info1 = {}  # 存放测试结果
        info2 = {}  # 存放测试结果
        test_type = kwargs.get('test_type', 'all')
        _data = GCONFIG.config.get("localip", False)
        # 先把节点信息写入文件
        self.join_proxy(proxyinfo)
        # 获取可供测试的测试端口
        thread = GCONFIG.config.get('clash', {}).get('core', 1)
        port_list = await proxys.get_available_port(thread + 1)
        control_port = port_list.pop(0)
        # startup = GCONFIG.config.get('clash', {}).get('startup', 11220)
        # 创建代理实例
        fulltclash = proxys.FullTClash(control_port, port_list)
        await fulltclash.start()
        pool = {'host': ['127.0.0.1' for _ in range(len(port_list))],
                'port': port_list}
        # 开始测试
        s1 = time.time()
        info1, _, cl = await self.topo()
        nodelist = cl.getProxies()
        nodename = cl.nodesName()
        print("入口测试结束: ", info1)
        if test_type == "inbound":
            wtime = "%.1f" % float(time.time() - s1)
            info1['wtime'] = wtime
            return {'inbound': info1, 'outbound': info2}
        # 启动链路拓扑测试
        try:
            info2.update({'入口': [], '地区': [], 'AS编号': [], '组织': [], '栈': [], '簇': [], '节点名称': []})
            res, ras = await self.batch_topo(nodelist, pool, fulltclash)

            if res:
                country_code = []
                asn = []
                org = []
                ipaddr = []
                ipstackes = []
                for j in res:
                    ipcl = cleaner.IPCleaner(j)
                    ip = ipcl.get_ip()
                    ipaddr.append(ip)
                    if not _data:
                        country_code.append(ipcl.get_country_code())
                        asn.append(str(ipcl.get_asn()))
                        org.append(ipcl.get_org())
                    else:
                        pass
                if _data:
                    for ip in ipaddr:
                        d, g, h = geoip.geo_info(ip)
                        country_code.append(d)
                        asn.append(h)
                        org.append(g)
                else:
                    pass
                for dictionary in ras:
                    if 'ips' in dictionary:
                        ipstackes.extend(dictionary['ips'])
                out_num = info1.get('出口数量', [])
                num_c = 1
                d0 = []
                for i in out_num:
                    d0 += [num_c for _ in range(int(i))]
                    num_c += 1
                b6 = ipstackes
                all_data = zip(d0, country_code, asn, org, ipaddr, nodename, b6)
                sorted_data = sorted(all_data, key=itemgetter(4), reverse=True)
                d0, d1, d2, d3, d4, d5, d6 = zip(*sorted_data)
                for i, _ in enumerate(d6):
                    if d6[i] == "N/A" and d4[i]:
                        if ":" in d4[i]:
                            d6 = d6[:i] + ("6",) + d6[i + 1:]
                        elif "." in d4[i]:
                            d6 = d6[:i] + ("4",) + d6[i + 1:]
                        else:
                            pass
                    elif d6[i] == "4" and ":" in d4[i]:
                        d6 = d6[:i] + ("46",) + d6[i + 1:]
                    elif d6[i] == "6" and "." in d4[i]:
                        d6 = d6[:i] + ("46",) + d6[i + 1:]
                    else:
                        pass
                d4_count = Counter(d4)
                results4 = [v for k, v in d4_count.items()]
                info2.update({'入口': d0, '地区': d1, 'AS编号': d2, '组织': d3, '栈': d6, '簇': results4})
                info2.update({'节点名称': d5})
                if not GCONFIG.config.get('ipstack', False):
                    info2.pop('栈', [])
            # 计算测试消耗时间
            wtime = "%.1f" % float(time.time() - s1)
            info2.update({'wtime': wtime})
            # info2['filter'] = {'include': self._include_text, 'exclude': self._exclude_text} #这里注释了，不然绘图会出错
        except Exception as e:
            logger.error(str(e))
        finally:
            fulltclash.close()
        # 保存结果
        self.saveresult({'inbound': info1, 'outbound': info2})
        return {'inbound': info1, 'outbound': info2}


def default_progress_text(corelabel: Union[int, str], progress: int, nodenum: int, slavecomment: str = "Local"):
    if corelabel == 'SpeedCore' or corelabel == 1:
        testtext = GCONFIG.config.get('bot', {}).get('speedtext', "⏳速度测试进行中...")
    elif corelabel == 'TopoCore' or corelabel == 2:
        testtext = GCONFIG.config.get('bot', {}).get('analyzetext', "⏳节点拓扑分析测试进行中...")
    elif corelabel == 'ScriptCore' or corelabel == 3:
        testtext = GCONFIG.config.get('bot', {}).get('scripttext', "⏳连通性测试进行中...")
    else:
        testtext = "未知测试进行中"
    if slavecomment == "Local":
        slavecomment = GCONFIG.get_default_slave().get('comment', 'Local')
    progress_bars = GCONFIG.config.get('bot', {}).get('bar', "=")
    bracketsleft = GCONFIG.config.get('bot', {}).get('bleft', "[")
    bracketsright = GCONFIG.config.get('bot', {}).get('bright', "]")
    bracketsspace = GCONFIG.config.get('bot', {}).get('bspace', "  ")

    cal = progress / nodenum * 100
    p_text = "%.2f" % cal
    equal_signs = int(cal / 5)
    space_count = 20 - equal_signs
    progress_bar = f"{bracketsleft}" + f"{progress_bars}" * equal_signs + \
                   f"{bracketsspace}" * space_count + f"{bracketsright}"
    edit_text = f"🍀后端:{slavecomment}\n{testtext}\n\n" + progress_bar + "\n\n" + "当前进度:\n" + \
                p_text + "%     [" + str(progress) + "/" + str(nodenum) + "]"
    # print(edit_text)
    return edit_text


def check_init():
    import os
    dirs = os.listdir()
    if "logs" in dirs and "results" in dirs:
        return
    logger.info("检测到初次使用，正在初始化...")
    if not os.path.isdir('../logs'):
        os.mkdir("../logs")
        logger.info("创建文件夹: logs 用于保存日志")
    if not os.path.isdir('../results'):
        os.mkdir("../results")
        logger.info("创建文件夹: results 用于保存测试结果")


def select_core(index: Union[int, str], progress_func: Tuple[Union[Callable, Coroutine], Tuple] = None):
    """
    1 为速度核心， 2为拓扑核心， 3为解锁脚本测试核心
    """
    progress = None if progress_func is None else (progress_func[0], progress_func[1])
    if index == 1 or index == 'speed':
        return SpeedCore(prs=progress)
    elif index == 2 or index == 'analyze' or index == 'topo':
        return TopoCore(progress_func=progress)
    elif index == 3 or index == 'script':
        return ScriptCore(progress_func=progress)
    else:
        raise TypeError("Unknown test type, please input again.\n未知的测试类型，请重新输入!")


if __name__ == '__main__':
    import sys
    import getopt

    check_init()
    # os.chdir(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    # sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
    help_text = """
Usage(使用帮助):
 -h, --help     Display the help info.
                输出帮助
 -f, --file     Subscription file path
                订阅文件路径
 -c, --core     Select the test type(speed,topo,script)
                测试类型(speed,topo,script)
"""
    config_path = ''
    core = None
    try:
        opts, _args = getopt.getopt(sys.argv[1:], "hf:c:", ["help", "file=", "core="])
    except getopt.GetoptError:
        print(help_text)
        sys.exit(1)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(help_text)
            sys.exit()
        elif opt in ("-c", "--core"):
            if arg == 'speed':
                core = SpeedCore()
            elif arg == 'script':
                core = ScriptCore()
            elif arg == 'topo':
                core = TopoCore()
            else:
                raise TypeError("Unknown test type, please input again.\n未知的测试类型，请重新输入!")
        elif opt in ("-f", "--file"):
            config_path = arg
    if core is None and not config_path:
        raise ValueError("Unable start the tasks,please input the config path.\n请输入配置文件路径")
    with open(config_path, 'r', encoding='utf-8') as fp:
        data = cleaner.ClashCleaner(fp)
        my_proxies = data.getProxies()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resd = loop.run_until_complete(core.core(my_proxies))
    print(resd)
