import json
import os
import aiohttp
import async_timeout
import requests
from loguru import logger


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
    url = "http://{}:{}/configs/".format(clashHost, str(clashPort))
    payload = json.dumps({"path": pwd})
    _headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=_headers, timeout=5, data=payload) as r:
            if r.status == 204:
                logger.info("切换配置文件成功，当前配置文件路径:" + pwd)
            else:
                logger.error("发送错误: 状态码" + str(r.status))
