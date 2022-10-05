import asyncio
import contextlib
import copy
import time
from typing import Union

import aiohttp
import requests
from aiohttp_socks import ProxyConnector
from loguru import logger
from pyrogram.errors import RPCError

from libs import cleaner, check, collector, proxys, export

# ----------------------------------------------------------------------------------------------------------------------
"""
保留原作者信息
author: https://github.com/Oreomeow
"""


# 部分内容已被修改  Some codes has been modified
class Speedtest:
    def __init__(self):
        self._stopped = False
        self.speedurl = "https://dl.google.com/dl/android/studio/install/3.4.1.0/android-studio-ide-183.5522156-windows.exe"
        self.result = []
        self._total_red = 0
        self._delta_red = 0
        self._start_time = 0
        self._statistics_time = 0
        self._time_used = 0
        self._count = 0

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
        # tmp_speed_list.sort()
        # max_speed: Union[int, float] = 0
        # if len(tmp_speed_list) > 12:
        #     msum = 0
        #     for i in range(12, len(tmp_speed_list) - 2):
        #         msum += tmp_speed_list[i]
        #         max_speed = msum / (len(tmp_speed_list) - 2 - 12)
        # else:
        #     max_speed = self._total_red / self._time_used
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
        logger.info(f"Fetching {url} via {host}:{port}.")
        async with aiohttp.ClientSession(
                headers={"User-Agent": "curl/11.45.14"},
                connector=ProxyConnector(host=host, port=port),
                timeout=aiohttp.ClientTimeout(connect=10),
        ) as session:
            # logger.debug("Session created.")
            async with session.get(url) as response:
                # logger.debug("Awaiting response.")
                while not self._stopped:
                    chunk = await response.content.read(buffer)
                    if not chunk:
                        logger.info("No chunk, task stopped.")
                        break
                    await self.record(len(chunk))

    except Exception as e:
        logger.error(f"Download link error: {str(e)}")


async def start(
        download_semaphore: asyncio.Semaphore,
        proxy_host: str,
        proxy_port: int,
        buffer: int,
        workers: int,
) -> tuple:
    async with download_semaphore:
        st = Speedtest()
        url = st.speedurl
        # logger.debug(f"Url: {url}")
        logger.info(f"Running st_async, workers: {workers}.")
        tasks = [
            asyncio.create_task(fetch(st, url, proxy_host, proxy_port, buffer))
            for _ in range(workers)
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
async def batch_speed(message, nodename: list, delays: list, proxygroup='auto'):
    info = {}
    progress = 0
    sending_time = 0
    nodenum = len(nodename)
    test_items = ["平均速度", "最大速度", "速度变化"]
    for item in test_items:
        info[item] = []
    info["消耗流量"] = 0  # 单位:MB
    for name in nodename:
        proxys.switchProxy_old(proxyName=name, proxyGroup=proxygroup, clashPort=1123)
        res = await start(asyncio.Semaphore(4), "127.0.0.1", 1122, 4096, 4)
        avgspeed = "%.2f" % (res[0] / 1024 / 1024) + "MB"
        maxspeed = "%.2f" % (res[1] / 1024 / 1024) + "MB"
        speedresult = res[2]
        traffic_used = float("%.2f" % (res[3] / 1024 / 1024))
        info["消耗流量"] += traffic_used
        res2 = [avgspeed, maxspeed, speedresult]
        for i in range(len(test_items)):
            info[test_items[i]].append(res2[i])

        progress += 1
        cal = progress / nodenum * 100
        p_text = "%.2f" % cal
        # 判断进度条，每隔10%发送一次反馈，有效防止洪水等待(FloodWait)
        if cal >= sending_time:
            sending_time += 10
            try:
                await message.edit_text("╰(*°▽°*)╯速度测试进行中...\n\n" +
                                        "当前进度:\n" + p_text +
                                        "%     [" + str(progress) + "/" + str(nodenum) + "]")  # 实时反馈进度
            except RPCError as r:
                logger.error(r)
    return info


async def core(client, message, back_message, start_time, suburl: str = None):
    info = {}
    if suburl is not None:
        url = suburl
    else:
        text = str(message.text)
        url = cleaner.geturl(text)
        if await check.check_url(back_message, url):
            return
    print(url)
    # 订阅采集
    sub = collector.SubCollector(suburl=url)
    subconfig = await sub.getSubConfig(save_path='./clash/sub{}.yaml'.format(start_time))
    if await check.check_sub(back_message, subconfig):
        return
    try:
        # 启动订阅清洗
        with open('./clash/sub{}.yaml'.format(start_time), "r", encoding="UTF-8") as fp:
            cl = cleaner.ClashCleaner(fp)
            nodenum = cl.nodesCount()
            nodename = cl.nodesName()
            nodetype = cl.nodesType()
    except Exception as e:
        logger.error(e)
        nodenum = 0
        nodename = None
        nodetype = None
    # 检查获得的数据
    if await check.check_nodes(back_message, nodenum, (nodename, nodetype,)):
        return
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    ma.addsub(subname=start_time, subpath='./sub{}.yaml'.format(start_time))
    ma.save('./clash/proxy.yaml')
    # 重载配置文件
    await proxys.reloadConfig(filePath='./clash/proxy.yaml', clashPort=1123)
    s1 = time.time()
    old_rtt = await collector.delay_providers(providername=start_time)
    rtt = check.check_rtt(old_rtt, nodenum)
    print("延迟:", rtt)
    try:
        speedinfo = await batch_speed(back_message, nodename, delays=rtt)
        info['类型'] = nodetype
        info['延迟RTT'] = rtt
        info.update(speedinfo)
        info = cleaner.ResultCleaner(info).start()
        # 计算测试消耗时间
        wtime = "%.1f" % float(time.time() - s1)
        info['wtime'] = wtime
        info['线程'] = 4
        cl1 = cleaner.ConfigManager(configpath=r"./results/{}.yaml".format(start_time.replace(':', '-')),data=info)
        cl1.save(r"./results/{}.yaml".format(start_time.replace(':', '-')))
        try:
            stime = export.ExportSpeed(name=nodename, info=info).exportImage()
            # 发送回TG
            await check.check_photo(message, back_message, stime, nodenum, wtime)
        except requests.exceptions.ConnectionError:
            # 出现这个异常大概率是因为 pilmoji这个库抽风了
            stime = ''
            # 遇到错误就发送错误信息给TG
            await check.check_photo(message, back_message, stime, nodenum, wtime)
    except Exception as e:
        logger.error(e)
