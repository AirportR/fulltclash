import asyncio
import json
import os
import threading
from typing import Union
import async_timeout
import yaml
import ctypes
import aiohttp
import requests
from aiohttp import ClientConnectorError
from loguru import logger
from utils.cleaner import config

"""
这个模块主要是一些对clash 动态库 api的python调用
"""
clash_path = config.get_clash_path()
lib = ctypes.cdll.LoadLibrary(clash_path)
_setProxy = getattr(lib, 'setProxy')
_setProxy.argtypes = [ctypes.c_char_p, ctypes.c_int64]
# _setProxy.restype = ctypes.c_char_p
_setProxy.restype = ctypes.c_int8
_free_me = getattr(lib, 'freeMe')
_free_me.argtypes = [ctypes.POINTER(ctypes.c_char)]
_myURLTest = getattr(lib, 'myURLTest')
_myURLTest.argtypes = [ctypes.c_char_p, ctypes.c_int64]
_myURLTest.restype = ctypes.c_ushort
_urlTest = getattr(lib, 'urltestJson')
_urlTest.argtypes = [ctypes.c_char_p, ctypes.c_int64, ctypes.c_int64]
_urlTest.restype = ctypes.c_char_p


class Clash(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, _port: Union[str, int], _index: int):
        threading.Thread.__init__(self)
        self._port = _port
        self._index = _index

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        self.run_2()

    def run_1(self):
        _myclash = lib.myclash
        _myclash.argtypes = [ctypes.c_char_p, ctypes.c_longlong]
        # create a task for myclash
        _addr = "127.0.0.1:" + str(self._port)
        _myclash(_addr.encode(), self._index)

    def run_2(self):
        _myclash2 = lib.myclash2
        _myclash2.argtypes = [ctypes.c_char_p, ctypes.c_longlong]
        # create a task for myclash
        _addr = "127.0.0.1:" + str(self._port)
        _myclash2(_addr.encode(), self._index)

    def stoplisten(self, index: int = None):
        closeclash = getattr(lib, 'closeclash')
        closeclash.argtypes = [ctypes.c_longlong]
        if index is None:
            closeclash(self._index)
        else:
            closeclash(index)


async def http_delay(url: str = config.getGstatic(), index: int = 0) -> int:
    mean_delay = await asyncio.to_thread(_myURLTest, url.encode(), index)
    return mean_delay


async def http_delay_tls(url: str = config.getGstatic(), index: int = 0, timeout=10):
    mean_delay1 = None
    try:
        async with async_timeout.timeout(20):
            mean_delay1 = await asyncio.to_thread(_urlTest, url.encode(), index, timeout)
            print(mean_delay1.decode())
            mean_delay = json.loads(mean_delay1.decode()).get('delay', 0)
    except asyncio.TimeoutError:
        logger.error("HTTP(S)延迟测试已超时")
        mean_delay = 0
    except Exception as e:
        logger.error(repr(e))
        mean_delay = 0
    finally:
        if mean_delay1 is not None:
            pass
            # _free_me(ctypes.pointer(mean_delay1))
    return mean_delay


def switchProxy(_nodeinfo: dict, _index: int) -> bool:
    """
    切换clash核心中的代理节点，会将数据直接发往动态链接库
    :param _nodeinfo: 节点信息
    :param _index: 索引
    :return: bool
    """
    if type(_nodeinfo).__name__ != "dict":
        return False
    try:
        _payload = yaml.dump({'proxies': _nodeinfo})
        _status = _setProxy(_payload.encode(), _index)
        # logger.info(f"切换结果: {_status}")
        if not _status:
            logger.info(f"切换节点: {_nodeinfo.get('name', 'not found')} 成功")
            # _free_me(_status)
            return True
        else:
            logger.error(str(_status))
            # _free_me(_status)
            return False
    except Exception as e:
        logger.error(str(e))
        return False


# 切换节点
def switchProxy_old(proxyName, proxyGroup, clashHost: str = "127.0.0.1", clashPort: int = 11230):
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


def killclash():
    stop = getattr(lib, 'stop')
    stop.argtypes = [ctypes.c_int64]
    stop(1)


async def reloadConfig(filePath: str, clashHost: str = "127.0.0.1", clashPort: int = 11230):
    """
    若重载成功返回True，否则为False
    :param filePath: 文件路径,最好是绝对路径，如果是相对路径，则会尝试处理成绝对路径
    :param clashHost:
    :param clashPort:
    :return:
    """
    pwd = os.path.abspath(filePath)
    # print(pwd)
    url = "http://{}:{}/configs/".format(clashHost, str(clashPort))
    payload = json.dumps({"path": pwd})
    _headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.put(url, headers=_headers, timeout=5, data=payload) as r:
                if r.status == 204:
                    logger.info("切换配置文件成功，当前配置文件路径:" + pwd)
                    return True
                else:
                    logger.error("发送错误: 状态码" + str(r.status))
                    return False
        except ClientConnectorError as c:
            logger.error(str(c))
            return False


async def reloadConfig_batch(nodenum: int, pool: dict):
    if not await reloadConfig(filePath='./clash/proxy.yaml', clashPort=11230):
        return False
    try:
        if nodenum < len(pool.get('port', [])):
            for i in pool.get('port', [])[:nodenum]:
                if not await reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1):
                    return False
            return True
        else:
            for i in pool.get('port', []):
                if not await reloadConfig(filePath='./clash/proxy.yaml', clashPort=i + 1):
                    return False
            return True
    except Exception as e:
        logger.error(str(e))
        return False


# def start_client(path: str, workpath: str = "./clash", _config: str = './clash/proxy.yaml', ):
#     # 启动了一个clash常驻进程
#     command = fr"{path} -f {_config} -d {workpath}"
#     subprocess.Popen(command.split(), encoding="utf-8")
#     sleep(2)


# def batch_start(portlist: list, proxy_file_path="./clash/proxy.yaml"):
#     """
#     批量启动多个clash进程
#     :param proxy_file_path: 代理配置文件路径
#     :param portlist: 端口列表，请至少间隔一个数字，如[1124,1126,1128,...]
#     :return:
#     """
#
#     ecport = [i + 1 for i in portlist]
#     if len(list(set(portlist).intersection(set(ecport)))):
#         logger.error("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
#         raise ValueError("代理端口组请至少间隔一个数字，如[1124,1126,1128,...]")
#     for i in range(len(portlist)):
#         clashconf = ClashCleaner(proxy_file_path)
#         clashconf.changeClashPort(port=portlist[i])
#         clashconf.changeClashEC(ec="127.0.0.1:" + str(ecport[i]))
#         clashconf.save(proxy_file_path)
#         start_client(path=config.get_clash_path(), workpath=config.get_clash_work_path(), _config=proxy_file_path)
#     clashconf = ClashCleaner(proxy_file_path)
#     clashconf.changeClashPort(port=11220)
#     clashconf.changeClashEC(ec="127.0.0.1:11230")
#     clashconf.save(proxy_file_path)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


    async def test():
        pass
        # await batch_start([1124, 1126, 1128, 1130],)


    loop.run_until_complete(test())
