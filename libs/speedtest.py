import asyncio
import contextlib
import copy
import socket
import time
from typing import Union

import aiohttp
import socks
from aiohttp_socks import ProxyConnector
from loguru import logger
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from libs import cleaner, check, collector, proxys, pynat

# ----------------------------------------------------------------------------------------------------------------------
"""
保留原作者信息
author: https://github.com/Oreomeow
"""
break_speed = []


# 部分内容已被修改  Some codes has been modified
class Speedtest:
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


async def start(
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
            asyncio.create_task(fetch(st, url, proxy_host, proxy_port, buffer))
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


# ----------------------------------------------------------------------------------------------------------------------
# 以下为 另一部分
async def batch_speed(message: Message, nodename: list, proxygroup='auto'):
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
        udptype, _, _, _, _ = nat_type_test('127.0.0.1', proxyport=1122)
        if udptype is None:
            udptype = "Unknown"
        res = await start("127.0.0.1", 1122, 4096)
        avgspeed = "%.2f" % (res[0] / 1024 / 1024) + "MB"
        maxspeed = "%.2f" % (res[1] / 1024 / 1024) + "MB"
        speedresult = [v / 1024 / 1024 for v in res[2]]
        traffic_used = float("%.2f" % (res[3] / 1024 / 1024))
        info["消耗流量"] += traffic_used
        res2 = [avgspeed, maxspeed, speedresult, udptype]
        for i in range(len(test_items)):
            info[test_items[i]].append(res2[i])

        if break_speed:
            await message.edit_text("❌测速任务已取消")
            await asyncio.sleep(10)
            await message.delete(revoke=False)
            break
        progress += 1
        cal = progress / nodenum * 100
        p_text = "%.2f" % cal
        IKM = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👋中止测速", callback_data='stop')],
            ]
        )
        # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
        if cal >= sending_time:
            sending_time += 10
            try:
                # 实时反馈进度
                await message.edit_text("╰(*°▽°*)╯速度测试进行中...\n\n" +
                                        "当前进度:\n" + p_text +
                                        "%     [" + str(progress) + "/" + str(nodenum) + "]", reply_markup=IKM)
            except RPCError as r:
                logger.error(r)
    return info


async def batch_udp(message, nodename: list, proxygroup='auto'):
    info = {}
    progress = 0
    sending_time = 0
    nodenum = len(nodename)
    test_items = ["UDP类型"]
    for item in test_items:
        info[item] = []
    info["消耗流量"] = 0  # 单位:MB
    for name in nodename:
        proxys.switchProxy_old(proxyName=name, proxyGroup=proxygroup, clashPort=1123)
        udptype, _, _, _, _ = nat_type_test('127.0.0.1', proxyport=1122)
        res2 = [udptype]
        for i in range(len(test_items)):
            info[test_items[i]].append(res2[i])

        progress += 1
        cal = progress / nodenum * 100
        p_text = "%.2f" % cal
        # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
        if cal >= sending_time:
            sending_time += 10
            try:
                await message.edit_text("╰(*°▽°*)╯UDP类型测试进行中...\n\n" +
                                        "当前进度:\n" + p_text +
                                        "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
            except RPCError as r:
                logger.error(r)
    return info


async def core(message, back_message, start_time, suburl: str = None, **kwargs):
    info = {}
    include_text = ''
    exclude_text = ''
    if suburl is not None:
        url = suburl
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
        if kwargs.get('include_text', ''):
            include_text = kwargs.get('include_text', '')
        if kwargs.get('exclude_text', ''):
            exclude_text = kwargs.get('exclude_text', '')
    else:
        text = str(message.text)
        texts = text.split(' ')
        if len(texts) > 2:
            include_text = texts[2]
        if len(texts) > 3:
            exclude_text = texts[3]
        url = cleaner.geturl(text)
    if await check.check_url(back_message, url):
        return info
    print(url)
    # 订阅采集
    logger.info(f"过滤器: 包含: [{include_text}], 排除: [{exclude_text}]")
    sub = collector.SubCollector(suburl=url, include=include_text, exclude=exclude_text)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return info
    try:
        # 启动订阅清洗
        cl = cleaner.ClashCleaner('./clash/sub{}.yaml'.format(start_time))
        cl.node_filter(include_text, exclude_text)
        nodenum = cl.nodesCount()
        nodename = cl.nodesName()
        nodetype = cl.nodesType()
    except Exception as e:
        logger.error(e)
        nodenum = 0
        nodename = None
        nodetype = None
    # 检查获得的数据
    if await check.check_speed_nodes(back_message, nodenum, (nodename, nodetype,)):
        return info
    ma = cleaner.ConfigManager(':memory:')
    ma.addsub2provider(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    if not await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123):
        return info
    logger.info("开始测试延迟...")
    s1 = time.time()
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt1 = check.check_rtt(old_rtt, nodenum)
    print("第一次延迟:", rtt1)
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt2 = check.check_rtt(old_rtt, nodenum)
    print("第二次延迟:", rtt2)
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt3 = check.check_rtt(old_rtt, nodenum)
    print("第三次延迟:", rtt3)
    rtt = cleaner.ResultCleaner.get_http_latency([rtt1, rtt2, rtt3])
    try:
        break_speed.clear()
        speedinfo = await batch_speed(back_message, nodename)
        info['节点名称'] = nodename
        info['类型'] = nodetype
        info['HTTP延迟'] = rtt
        info.update(speedinfo)
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        info['线程'] = collector.config.config.get('speedthread', 4)
        # 过滤器内容
        info['filter'] = {'include': include_text, 'exclude': exclude_text}
        if break_speed:
            info.clear()
        cl1 = cleaner.ConfigManager(configpath=r"./results/{}.yaml".format(start_time.replace(':', '-')), data=info)
        cl1.save(r"./results/{}.yaml".format(start_time.replace(':', '-')))
    except Exception as e:
        logger.error(e)
    finally:
        return info


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

# if __name__ == "__main__":
#     topology, ext_ip, ext_port, source_ip, sport = nat_type_test('127.0.0.1', 1111)
#     print(
#         "Network type:",
#         topology,
#         f"\nInternal address: {source_ip}:{sport}",
#         f"\nExternal address: {ext_ip}:{ext_port}",
#     )
