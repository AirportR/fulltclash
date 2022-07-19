import json
import aiohttp
import async_timeout
import requests


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
        print("切换节点: {}".format(proxyName))
        r = requests.request("PUT", url, headers=_headers, data=payload)
        return r
    except Exception as e:
        print(e)


async def switchProxy(proxyName, proxyGroup, clashHost: str = "127.0.0.1", clashPort: int = 9090):
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
        print(e)
