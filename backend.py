import asyncio
import contextlib
import copy
import socket
import time
import os
from collections import Counter
from operator import itemgetter
from typing import Union

import aiohttp
import socks
from aiohttp_socks import ProxyConnector
from loguru import logger
from libs.collector import proxies
from libs import cleaner, collector, proxys, pynat, sorter

# 重写整个测试核心，技术栈分离。


break_speed = []
GCONFIG = cleaner.config  # 全局配置


class Basecore:
    """
    测试核心基类
    """

    def __init__(self):
        self._info = {}
        self._include_text = GCONFIG.config.get('subconvertor', {}).get('include', '')  # 从配置文件里预定义过滤规则
        self._exclude_text = GCONFIG.config.get('subconvertor', {}).get('exclude', '')
        self._start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())

    @property
    def start_time(self):
        return self._start_time

    @staticmethod
    def core(*args, **kwargs):
        """
        您必须自主实现这里的方法，因为Basecore是一个基类
        :return:
        """

    @staticmethod
    def check_rtt(rtt, nodenum: int):
        if rtt == 0:
            new_rtt = [0 for _ in range(nodenum)]
            return new_rtt
        else:
            return rtt

    async def http_latency(self, nodenum):
        """
        HTTP延迟测试
        :param nodenum: 节点数量
        :return:
        """
        logger.info("开始测试延迟...")
        old_rtt = await collector.delay_providers(providername=self.start_time)
        rtt1 = Basecore.check_rtt(old_rtt, nodenum)
        print("第一次延迟:", rtt1)
        await asyncio.sleep(0.1)
        old_rtt = await collector.delay_providers(providername=self.start_time)
        rtt2 = Basecore.check_rtt(old_rtt, nodenum)
        print("第二次延迟:", rtt2)
        await asyncio.sleep(0.1)
        old_rtt = await collector.delay_providers(providername=self.start_time)
        rtt3 = Basecore.check_rtt(old_rtt, nodenum)
        print("第三次延迟:", rtt3)
        rtt = cleaner.ResultCleaner.get_http_latency([rtt1, rtt2, rtt3])
        return rtt

    def join_proxy(self, proxyinfo: list):
        cl = cleaner.ClashCleaner(':memory:')
        cl.setProxies(proxyinfo)
        cl.node_filter(self._include_text, self._exclude_text, issave=False)  # 从配置文件过滤文件
        cl.save(savePath=f'./clash/sub{self.start_time}.yaml')

    def getnodeinfo(self) -> tuple:
        cl = cleaner.ClashCleaner(f'./clash/sub{self.start_time}.yaml')
        nodename = cl.nodesName()
        nodetype = cl.nodesType()
        nodenum = cl.nodesCount()
        return nodename, nodetype, nodenum

    def saveresult(self, info: dict):
        """
        保存测试结果
        :return:
        """
        cl1 = cleaner.ConfigManager(configpath=fr"./results/{self.start_time}.yaml", data=info)
        cl1.save(fr"./results/{self.start_time}.yaml")
        if GCONFIG.config.get('clash',{}).get('allow-caching', False):
            try:
                os.remove(fr"./clash/sub{self.start_time}.yaml")
            except Exception as e:
                print(e)


# 部分内容已被修改  Some codes has been modified
class Speedtest:
    """
    保留原作者信息
    author: https://github.com/Oreomeow
    """

    def __init__(self):
        self._config = cleaner.ConfigManager()
        self._stopped = False
        self.speedurl = self.config.get('speedfile',
                                        "https://dl.google.com/dl/android/studio/install/3.4.1.0/" +
                                        "android-studio-ide-183.5522156-windows.exe")
        self._thread = self.config.get('speedthread', 4)
        self.result = []
        self._total_red = 0
        self._delta_red = 0
        self._start_time = 0
        self._statistics_time = 0
        self._time_used = 0
        self._count = 0

    @property
    def thread(self):
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
        tmp_speed_list = self.speed_list
        return max(tmp_speed_list)

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
        if self._time_used > 10:
            self._stopped = True

    def _show_progress(self, delta_time: Union[int, float]):
        speed = (self._total_red - self._delta_red) / delta_time
        speed_mb = speed / 1024 / 1024
        self._delta_red = self._total_red
        self._count += 1
        print("\r[" + "=" * self._count + f"> [{speed_mb:.2f} MB/s]", end="")
        if len(self.result) < 10:
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
    def __init__(self, ):
        super().__init__()

    @staticmethod
    def check_speed_nodes(nodenum, args: tuple, speed_max_num=GCONFIG.speednodes()):
        """
        检查获得的关键信息是否为空，以及节点数量是否大于一定数值
        :param speed_max_num: 最大节点数量
        :param nodenum: 节点数量
        :param args: 若干信息
        :return: bool
        """
        if not nodenum:
            logger.warning("❌发生错误，请检查订阅文件")
            return True
        for a in args:
            if a is None:
                logger.warning("❌发生错误，请检查订阅文件")
                return True
            else:
                pass
        if nodenum > speed_max_num:
            logger.warning(f"❌节点数量超过了{speed_max_num}个的限制！已取消本次测试")
            return True
        else:
            return False

    @staticmethod
    def nat_type_test(proxyaddr=None, proxyport=None):
        mysocket = socks.socksocket(type=socket.SOCK_DGRAM)
        mysocket.set_proxy(socks.PROXY_TYPE_SOCKS5, addr=proxyaddr, port=proxyport)
        _sport = 54320
        try:
            logger.info("Performing UDP NAT Type Test.")
            t, eip, eport, sip = pynat.get_ip_info(
                source_ip="0.0.0.0",
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
    async def fetch(self, url: str, host: str, port: int, buffer: int):
        try:
            # logger.info(f"Fetching {url} via {host}:{port}.")
            async with aiohttp.ClientSession(
                    headers={"User-Agent": "FullTclash"},
                    connector=ProxyConnector(host=host, port=port),
                    timeout=aiohttp.ClientTimeout(connect=10),
            ) as session:
                # logger.debug("Session created.")
                async with session.get(url) as response:
                    # logger.debug("Awaiting response.")
                    while not self._stopped:
                        if not break_speed:
                            chunk = await response.content.read(buffer)
                            if not chunk:
                                logger.info("No chunk, task stopped.")
                                break
                            await self.record(len(chunk))
                        else:
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
            url = st.speedurl
            # logger.debug(f"Url: {url}")
            thread = workers if workers else st.thread
            logger.info(f"Running st_async, workers: {thread}.")
            tasks = [
                asyncio.create_task(SpeedCore.fetch(st, url, proxy_host, proxy_port, buffer))
                for _ in range(thread)
            ]
            await asyncio.wait(tasks)
            st.show_progress_full()
            if st.time_used:
                return (
                    st.total_red / st.time_used,
                    st.max_speed,
                    st.speed_list[1:],
                    st.total_red,
                )

            return 0, 0, [], 0

    # 以下为 另一部分
    @staticmethod
    async def batch_speed(nodename: list, proxygroup='auto'):
        info = {}
        progress = 0
        sending_time = 0
        nodenum = len(nodename)
        test_items = ["平均速度", "最大速度", "速度变化", "UDP类型"]
        for item in test_items:
            info[item] = []
        info["消耗流量"] = 0  # 单位:MB
        for name in nodename:
            proxys.switchProxy_old(proxyName=name, proxyGroup=proxygroup, clashPort=1123)
            udptype, _, _, _, _ = SpeedCore.nat_type_test('127.0.0.1', proxyport=1122)
            if udptype is None:
                udptype = "Unknown"
            res = await SpeedCore.speed_start("127.0.0.1", 1122, 4096)
            avgspeed = "%.2f" % (res[0] / 1024 / 1024) + "MB"
            maxspeed = "%.2f" % (res[1] / 1024 / 1024) + "MB"
            speedresult = [v / 1024 / 1024 for v in res[2]]
            traffic_used = float("%.2f" % (res[3] / 1024 / 1024))
            info["消耗流量"] += traffic_used
            res2 = [avgspeed, maxspeed, speedresult, udptype]
            for i in range(len(test_items)):
                info[test_items[i]].append(res2[i])

            if break_speed:
                logger.warning("❌测速任务已取消")
                break
            progress += 1
            cal = progress / nodenum * 100
            p_text = "%.2f" % cal
            if cal >= sending_time:
                sending_time += 10
                print("╰(*°▽°*)╯速度测试进行中...\n\n" +
                      "当前进度:\n" + p_text +
                      "%     [" + str(progress) + "/" + str(nodenum) + "]")
        return info

    async def core(self, proxyinfo: list):
        info = {}  # 存放测速结果
        self.join_proxy(proxyinfo)
        # 获取可供测试的测试端口
        "测速仅需要一个端口，因此这里不处理"
        # 订阅加载
        nodename, nodetype, nodenum = self.getnodeinfo()
        # 进行节点数量检查
        if SpeedCore.check_speed_nodes(nodenum, (nodename, nodetype,)):
            return info
        # 重载配置文件
        ma = cleaner.ConfigManager(':memory:')
        ma.addsub2provider(subname=self.start_time, subpath=f'./sub{self.start_time}.yaml')
        ma.save('./clash/proxy.yaml')
        if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123):
            return info
        # 开始测试
        s1 = time.time()
        rtt = await self.http_latency(nodenum)  # HTTP延迟测试
        print("HTTP延迟: ", rtt)
        try:
            break_speed.clear()
            speedinfo = await SpeedCore.batch_speed(nodename)
            info['节点名称'] = nodename
            info['类型'] = nodetype
            info['HTTP延迟'] = rtt
            info.update(speedinfo)
            info = cleaner.ResultCleaner(info).start()
            # 计算测试消耗时间
            wtime = "%.1f" % float(time.time() - s1)
            info['wtime'] = wtime
            info['线程'] = collector.config.config.get('speedthread', 4)
            if break_speed:
                info.clear()
        except Exception as e:
            logger.error(e)
        # 保存结果
        self.saveresult(info)
        # 恢复proxy-provider处于默认状态，否则会造成clash core的加载负担。
        ma.delsub2provider(subname=self.start_time)
        ma.save(savePath='./clash/proxy.yaml')
        # 将结果返回
        return info


class ScriptCore(Basecore):
    def __init__(self):
        super().__init__()

    @staticmethod
    async def unit(test_items: list, delay: int, host="127.0.0.1", port=1122):
        """
        以一个节点的所有测试项为一个基本单元unit,返回单个节点的测试结果
        :param port: 代理端口
        :param host: 代理主机名
        :param test_items: [Netflix,disney+,etc...]
        :param delay: 节点延迟，可选参数，若为0，则测试项全部返回N/A
        :return: list 返回test_items对应顺序的信息
        """
        info = []
        if delay == 0:
            logger.warning("超时节点，跳过测试")
            for t in test_items:
                if t == "HTTP延迟":
                    info.append(0)
                else:
                    info.append("N/A")
            return info
        else:
            info.append(delay)
            cl = collector.Collector()
            re1 = await cl.start(proxy=f"http://{host}:{port}")
            cnr = cleaner.ReCleaner(re1)
            old_info = cnr.get_all()
            for item in test_items:
                i = item
                if i == 'HTTP延迟':
                    continue
                try:
                    info.append(old_info[i])
                except KeyError:
                    info.append("N/A")
                    logger.error("KeyError: 无法找到 " + item + " 测试项")
            return info

    @staticmethod
    async def batch_test_pro(nodename: list, delays: list, test_items: list, pool: dict, proxygroup='auto'):
        info = {}
        progress = 0
        sending_time = 0
        host = pool.get('host', [])
        port = pool.get('port', [])
        psize = len(port)
        nodenum = len(nodename)
        tasks = []
        for item in test_items:
            info[item] = []
        logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
        if psize <= 0:
            logger.error("无可用的代理程序接口")
            return {}
        logger.info("╰(*°▽°*)╯联通性测试进行中...")
        if nodenum < psize:
            for i in range(len(port[:nodenum])):
                proxys.switchProxy_old(proxyName=nodename[i], proxyGroup=proxygroup, clashHost=host[i],
                                       clashPort=port[i] + 1)
                task = asyncio.create_task(ScriptCore.unit(test_items, delays[i], host=host[i], port=port[i]))
                tasks.append(task)
            done = await asyncio.gather(*tasks)
            # 简单处理一下数据
            res = []
            for j in range(len(test_items)):
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
                    proxys.switchProxy_old(proxyName=nodename[s * psize + i], proxyGroup=proxygroup, clashHost=host[i],
                                           clashPort=port[i] + 1)

                    task = asyncio.create_task(ScriptCore.unit(test_items, delays[s * psize + i],
                                                               host=host[i],
                                                               port=port[i]))
                    tasks.append(task)
                done = await asyncio.gather(*tasks)

                # 反馈进度
                progress += psize
                cal = progress / nodenum * 100
                p_text = "%.2f" % cal
                # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
                if cal > sending_time:
                    sending_time += 20
                    print("╰(*°▽°*)╯联通性测试进行中...\n\n" +
                          "当前进度:\n" + p_text +
                          "%     [" + str(progress) + "/" + str(nodenum) + "]")
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
                    proxys.switchProxy_old(proxyName=nodename[subbatch * psize + i], proxyGroup=proxygroup,
                                           clashHost=host[i],
                                           clashPort=port[i] + 1)
                    task = asyncio.create_task(
                        ScriptCore.unit(test_items, delays[subbatch * psize + i], host=host[i], port=port[i]))
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
                print("╰(*°▽°*)╯联通性测试进行中...\n\n" +
                      "当前进度:\n" + '100' +
                      "%     [" + str(progress) + "/" + str(nodenum) + "]")
            logger.info(str(info))
            return info

    async def core(self, proxyinfo: list, **kwargs):
        info = {}  # 存放测速结果
        media_items = kwargs.get('media_items', None)
        test_items = collector.media_items if media_items is None else media_items
        # 先把节点信息写入文件
        self.join_proxy(proxyinfo)
        # 获取可供测试的测试端口
        thread = GCONFIG.config.get('clash', {}).get('core', 1)
        startup = GCONFIG.config.get('clash', {}).get('startup', 1124)
        pool = {'host': ['127.0.0.1' for _ in range(thread)],
                'port': [startup + t * 2 for t in range(thread)]}
        # 订阅加载
        nodename, nodetype, nodenum = self.getnodeinfo()
        # 进行节点数量检查
        if SpeedCore.check_speed_nodes(nodenum, (nodename, nodetype,)):
            return info
        # 重载配置文件
        ma = cleaner.ConfigManager(':memory:')
        ma.addsub2provider(subname=self.start_time, subpath=f'./sub{self.start_time}.yaml')
        ma.save('./clash/proxy.yaml')
        if not await proxys.reloadConfig_batch(nodenum, pool):
            return info
        # 开始测试
        s1 = time.time()
        rtt = await self.http_latency(nodenum)  # HTTP延迟测试
        print("HTTP延迟: ", rtt)
        info['节点名称'] = nodename
        info['类型'] = nodetype
        test_info = await ScriptCore.batch_test_pro(nodename, rtt, test_items, pool)
        info['HTTP延迟'] = test_info.pop('HTTP延迟')
        info.update(test_info)
        sort = kwargs.get('sort', "订阅原序")
        logger.info("排序：" + sort)
        info = cleaner.ResultCleaner(info).start(sort=sort)
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        info['sort'] = sort
        # 保存结果
        self.saveresult(info)
        # 恢复proxy-provider处于默认状态，否则会造成clash core的加载负担。
        ma.delsub2provider(subname=self.start_time)
        ma.save(savePath='./clash/proxy.yaml')
        return info


class TopoCore(Basecore):
    """
    拓扑测试核心
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    async def topo(file_path: str):
        info = {'地区': [], 'AS编号': [], '组织': [], '入口ip段': []}
        cl = cleaner.ClashCleaner(file_path)
        co = collector.IPCollector()
        session = aiohttp.ClientSession()
        nodename, inboundinfo, cl = sorter.sort_nodename_topo(cl)
        if nodename and inboundinfo and cl:
            # 拿地址，已经转换了域名为ip,hosts变量去除了N/A
            hosts = list(inboundinfo.keys())
            # 创建任务并开始采集ip信息
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
                new_hosts = []
                for host in hosts:
                    if len(host) < 16:  # v4地址最大长度为15
                        try:
                            old_ip = host.split('.')[:2]
                            new_ip = old_ip[0] + "." + old_ip[1] + ".*.*"
                        except IndexError:
                            new_ip = host
                        new_hosts.append(new_ip)
                    else:
                        new_hosts.append(host)
                info.update({'入口ip段': new_hosts})
                info.update({'出口数量': numcount})
            return info, hosts, cl

    @staticmethod
    async def batch_topo(nodename: list, pool: dict, proxygroup='auto'):
        resdata = []
        progress = 0
        sending_time = 0
        host = pool.get('host', [])
        port = pool.get('port', [])
        psize = len(port)
        nodenum = len(nodename)
        logger.info("接受任务数量: {} 线程数: {}".format(nodenum, psize))
        if psize <= 0:
            logger.error("无可用的代理程序接口")
            return []
        logger.info("╰(*°▽°*)╯节点链路拓扑测试进行中...")
        if nodenum < psize:
            for i in range(nodenum):
                proxys.switchProxy_old(proxyName=nodename[i], proxyGroup=proxygroup, clashHost=host[i],
                                       clashPort=port[i] + 1)
            ipcol = collector.IPCollector()
            sub_res = await ipcol.batch(proxyhost=host[:nodenum], proxyport=port[:nodenum])
            resdata.extend(sub_res)
            return resdata
        else:
            subbatch = nodenum // psize
            for s in range(subbatch):
                logger.info("当前批次: " + str(s + 1))
                for i in range(psize):
                    proxys.switchProxy_old(proxyName=nodename[s * psize + i], proxyGroup=proxygroup, clashHost=host[i],
                                           clashPort=port[i] + 1)
                ipcol = collector.IPCollector()
                sub_res = await ipcol.batch(proxyhost=host, proxyport=port)
                resdata.extend(sub_res)
                # 反馈进度

                progress += psize
                cal = progress / nodenum * 100
                p_text = "%.2f" % cal
                if cal >= sending_time:
                    sending_time += 10
                    print("╰(*°▽°*)╯节点链路拓扑测试进行中...\n\n" +
                          "当前进度:\n" + p_text +
                          "%     [" + str(progress) + "/" + str(nodenum) + "]")

            if nodenum % psize != 0:
                logger.info("最后批次: " + str(subbatch + 1))
                for i in range(nodenum % psize):
                    proxys.switchProxy_old(proxyName=nodename[subbatch * psize + i], proxyGroup=proxygroup,
                                           clashHost=host[i], clashPort=port[i] + 1)
                ipcol = collector.IPCollector()
                sub_res = await ipcol.batch(proxyhost=host[:nodenum % psize],
                                            proxyport=port[:nodenum % psize])
                resdata.extend(sub_res)

            # 最终进度条
            if nodenum % psize != 0:
                print("╰(*°▽°*)╯节点链路拓扑测试进行中...\n\n" +
                      "当前进度:\n" + "100" +
                      "%     [" + str(nodenum) + "/" + str(nodenum) + "]")
            return resdata

    async def core(self, proxyinfo: list, test_type='all'):
        info1 = {}  # 存放测试结果
        info2 = {}  # 存放测试结果
        # 先把节点信息写入文件
        self.join_proxy(proxyinfo)
        # 获取可供测试的测试端口
        thread = GCONFIG.config.get('clash', {}).get('core', 1)
        startup = GCONFIG.config.get('clash', {}).get('startup', 1124)
        pool = {'host': ['127.0.0.1' for _ in range(thread)],
                'port': [startup + t * 2 for t in range(thread)]}
        # 订阅加载
        nodename, nodetype, nodenum = self.getnodeinfo()
        # 进行节点数量检查
        if SpeedCore.check_speed_nodes(nodenum, (nodename, nodetype,), 1000):
            return info1, info2
        # 重载配置文件
        ma = cleaner.ConfigManager(':memory:')
        ma.addsub2provider(subname=self.start_time, subpath=f'./sub{self.start_time}.yaml')
        ma.save('./clash/proxy.yaml')
        if not await proxys.reloadConfig_batch(nodenum, pool):
            return info1, info2
        # 开始测试
        s1 = time.time()
        info1, hosts, cl = await TopoCore.topo(f'./clash/sub{self.start_time}.yaml')
        nodename = cl.nodesName()
        if test_type == "inbound":
            wtime = "%.1f" % float(time.time() - s1)
            info1['wtime'] = wtime
            return info1, info2

        # 启动链路拓扑测试
        try:
            info2 = {}
            res = await TopoCore.batch_topo(nodename, pool)
            if res:
                country_code = []
                asn = []
                org = []
                ipaddr = []
                for j in res:
                    ipcl = cleaner.IPCleaner(j)
                    country_code.append(ipcl.get_country_code())
                    asn.append(str(ipcl.get_asn()))
                    org.append(ipcl.get_org())
                    ip = ipcl.get_ip()
                    ipaddr.append(ip)
                out_num = info1.get('出口数量', [])
                num_c = 1
                d0 = []
                for i in out_num:
                    d0 += [num_c for _ in range(int(i))]
                    num_c += 1
                all_data = zip(d0, country_code, asn, org, ipaddr, nodename)
                sorted_data = sorted(all_data, key=itemgetter(4), reverse=True)
                d0, d1, d2, d3, d4, d5 = zip(*sorted_data)
                d4_count = Counter(d4)
                results4 = [v for k, v in d4_count.items()]
                info2.update({'入口': d0, '地区': d1, 'AS编号': d2, '组织': d3, '簇': results4})
                info2.update({'节点名称': d5})
        except Exception as e:
            logger.error(str(e))
        # 保存结果
        self.saveresult({'inbound': info1, 'outbound': info2})
        # 恢复proxy-provider处于默认状态，否则会造成clash core的加载负担。
        ma.delsub2provider(subname=self.start_time)
        ma.save(savePath='./clash/proxy.yaml')
        return info1, info2


def check_init():
    import os
    dirs = os.listdir()
    if "clash" in dirs and "logs" in dirs and "results" in dirs:
        return
    logger.info("检测到初次使用，正在初始化...")
    if not os.path.isdir('clash'):
        os.mkdir("clash")
        logger.info("创建文件夹: clash 用于保存订阅")
    if not os.path.isdir('logs'):
        os.mkdir("logs")
        logger.info("创建文件夹: logs 用于保存日志")
    if not os.path.isdir('results'):
        os.mkdir("results")
        logger.info("创建文件夹: results 用于保存测试结果")


def select_core(index: int):
    if index == 1 or index == 'speed':
        return SpeedCore()
    elif index == 2 or index == 'analyze' or index == 'topo':
        return TopoCore()
    elif index == 3 or index == 'script':
        return ScriptCore()
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
