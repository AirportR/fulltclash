import asyncio
import json
import os
import subprocess
from time import sleep

import aiohttp
import async_timeout
import requests
from loguru import logger
from libs.cleaner import ClashCleaner, config

"""
这个模块主要是一些对clash restful api的python实现
"""


# 切换节点
def switchProxy_old(proxyName, proxyGroup, clashHost: str = "127.0.0.1", clashPort: int = 1123):
    """
    切换clash核心中的代理节点，此版本为requests库实现
    :param proxyName: 想要切换代理节点的名称
    :param proxyGroup: 代理组名称
    :param clashHost: clash的地址
    :param clashPort: clash的api端口
    :return:
    """
    url = "http://{}:{}/proxies/{}".format(clashHost, str(clashPort), proxyGroup)
    payload = json.dumps({"name": proxyName})
    _headers = {'Content-Type': 'application/json'}
    try:
        r = requests.request("PUT", url, headers=_headers, data=payload)
        logger.info("切换节点: {} ".format(proxyName) + str(r.status_code))
        return r
    except Exception as e:
        logger.error(e)


async def switchProxy(proxyName, proxyGroup, clashHost: str = "127.0.0.1", clashPort: int = 1123):
    """
    切换clash核心中的代理节点，此版本为aiohttp库实现
    :param proxyName: 想要切换代理节点的名称
    :param proxyGroup: 代理组名称
    :param clashHost: clash的地址
    :param clashPort: clash的api端口
    :return: response
    """
    url = "http://{}:{}/proxies/{}".format(clashHost, str(clashPort), proxyGroup)
    payload = json.dumps({"name": proxyName})
    _headers = {'Content-Type': 'application/json'}
    try:
        with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=_headers, data=payload) as r:
                    return r
    except Exception as e:
        logger.error(e)


async def reloadConfig(filePath: str, clashHost: str = "127.0.0.1", clashPort: int = 1123):
    """

    :param filePath: 文件路径,最好是绝对路径，如果是相对路径，则会尝试处理成绝对路径
    :param clashHost:
    :param clashPort:
    :return:
    """
    pwd = os.path.abspath(filePath)
    print(pwd)
    url = "http://{}:{}/configs/".format(clashHost, str(clashPort))
    payload = json.dumps({"path": pwd})
    _headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=_headers, timeout=5, data=payload) as r:
            if r.status == 204:
                logger.info("切换配置文件成功，当前配置文件路径:" + pwd)
            else:
                logger.error("发送错误: 状态码" + str(r.status))


def start_client(path: str, workpath: str = "./clash", config: str = './clash/proxy.yaml', ):
    # 启动了一个clash常驻进程
    command = fr"{path} -f {config} -d {workpath}"
    subprocess.Popen(command.split(), encoding="utf-8")
    sleep(2)
    logger.info("程序已启动!")


def batch_start(portlist: list, proxy_file_path="./clash/proxy.yaml"):
    """
    批量启动多个clash进程
    :param proxy_file_path: 代理配置文件路径
    :param portlist: 端口列表，请至少间隔一个数字，如[1124,1126,1128,...]
    :return:
    """

    ecport = [i + 1 for i in portlist]
    if len(list(set(portlist).intersection(set(ecport)))):
        logger.error("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
        raise ValueError("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
    for i in range(len(portlist)):
        clashconf = ClashCleaner(proxy_file_path)
        clashconf.changeClashPort(port=portlist[i])
        clashconf.changeClashEC(ec="127.0.0.1:" + str(ecport[i]))
        clashconf.save(proxy_file_path)
        start_client(path=config.get_clash_path(), workpath=config.get_clash_work_path(), config=proxy_file_path)
    clashconf = ClashCleaner(proxy_file_path)
    clashconf.changeClashPort(port=1122)
    clashconf.changeClashEC(ec="127.0.0.1:1123")
    clashconf.save(proxy_file_path)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


    async def test():
        pass
        # await batch_start([1124, 1126, 1128, 1130],)


    loop.run_until_complete(test())
