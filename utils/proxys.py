import asyncio
import contextlib
import json
import socket
import os
import subprocess
from typing import Union, List
import yaml
import aiohttp
import requests
from aiohttp import ClientConnectorError
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from loguru import logger
from utils.cleaner import config
from utils.safe import sha256_32bytes, DEFAULT_NONCE2

"""
这个模块主要是一些对clash 动态库 api的python调用
"""
CLASH_PATH = config.get_clash_path()
START_PORT = config.config.get('clash', {}).get('startup', 11220)
CONTROL_PORT = START_PORT - 1
BUILD_TOKEN = config.getBuildToken()


class FullTClash:
    def __init__(self, control_port: Union[str, int], proxy_portlist: List[Union[str, int]]):
        """
        control_port: 控制端口
        proxy_port: 代理端口，多个端口
        """
        self.cport = control_port
        self.port = proxy_portlist

    def start(self, controlport: int = CONTROL_PORT):
        """
        启动fulltclash代理程序
        """
        port2 = "|".join(self.port)
        _command = fr"{config.get_clash_path()} -c {controlport} -p {port2}"
        subprocess.Popen(_command.split(), encoding="utf-8")

    @staticmethod
    async def connect(controlport: int = CONTROL_PORT):
        # 创建一个socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置socket为非阻塞模式
        s.setblocking(False)
        # 连接服务器的IP地址和端口号
        try:
            await asyncio.get_event_loop().sock_connect(s, ("127.0.0.1", controlport))
        except ConnectionRefusedError:
            logger.error(f"远程计算机拒绝网络连接。请检查是否在 {CONTROL_PORT} 端口开启了监听")
            return None
        return s

    @staticmethod
    async def sock_send(message, key: str, controlport: int = CONTROL_PORT, norecv=True):
        """
        message: 数据报文
        key: 加密密钥
        controlport: 控制端口
        norecv: 仅发送不接受数据
        """
        _loop = asyncio.get_running_loop()
        s = await FullTClash.connect(controlport)
        if s is None:
            logger.warning("socket连接失败！")
            return
            # 使用chacha20算法加密消息，使用固定的nonce
        chacha = ChaCha20Poly1305(sha256_32bytes(key))
        ciphertext = chacha.encrypt(DEFAULT_NONCE2, message.encode(), None)
        # 发送加密后的消息给服务器
        await _loop.sock_sendall(s, ciphertext)
        # await _loop.sock_sendall(s, ciphertext)
        if not norecv:
            print("开始接受数据")
            recv = await _loop.sock_recv(s, 1)
            print("数据: ", recv)
        # 关闭socket连接
        s.close()

    @staticmethod
    def sock_send_noasync(message, key: str, controlport: int = CONTROL_PORT):
        # 创建一个socket对象
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置socket为非阻塞模式
        # 连接服务器的IP地址和端口号
        try:
            s.connect(("127.0.0.1", controlport))
        except ConnectionRefusedError:
            logger.error(f"远程计算机拒绝网络连接。请检查是否在 {CONTROL_PORT} 端口开启了监听")
            return
        newkey = sha256_32bytes(key)
        # 使用chacha20算法加密消息，使用固定的nonce
        chacha = ChaCha20Poly1305(newkey)
        ciphertext = chacha.encrypt(DEFAULT_NONCE2, message.encode(), None)
        # 发送加密后的消息给服务器
        s.sendall(ciphertext)
        # await asyncio.get_event_loop().sock_sendall(s, ciphertext)
        recv = s.recv(3)
        print("延迟:", recv)
        # 关闭socket连接
        s.close()

    @staticmethod
    async def urltest(port: int = START_PORT, pingurl: str = config.getGstatic(), timeout: int = 5):
        """
        测定指定index的代理
        """
        addr = f"http://127.0.0.1:{port}"
        ttfb = 0
        loop = asyncio.get_running_loop()
        try:
            async with aiohttp.ClientSession() as session:
                start = loop.time()
                with contextlib.suppress(asyncio.exceptions.TimeoutError):
                    async with session.get(pingurl, proxy=addr, timeout=5) as _:
                        pass
                async with session.get(pingurl, proxy=addr, timeout=timeout) as _:
                    end = loop.time()
                    ttfb2 = end - start
                    # print(f"TTFB for {pingurl} is {ttfb2:.3f} seconds")
                ttfb = int(ttfb2 / 2 * 1000)
        except Exception as e:
            logger.warning(str(e))
        return ttfb

    @staticmethod
    async def setproxy(proxyinfo: dict, index: int):
        logger.info(f"设置代理: {proxyinfo.get('name', '')}, index: {index}")
        data = yaml.dump({'proxies': proxyinfo, 'index': index, 'command': 'setproxy'})
        await FullTClash.sock_send(data, BUILD_TOKEN)


# async def http_delay(url: str = config.getGstatic(), index: int = 0) -> int:
#     mean_delay = await asyncio.to_thread(_myURLTest, url.encode(), index)
#     return mean_delay


# async def http_delay_tls(url: str = config.getGstatic(), index: int = 0, timeout=10):
#     mean_delay1 = None
#     try:
#         async with async_timeout.timeout(20):
#             mean_delay1 = await asyncio.to_thread(_urlTest, url.encode(), index, timeout)
#             print(mean_delay1.decode())
#             mean_delay = json.loads(mean_delay1.decode()).get('delay', 0)
#     except asyncio.TimeoutError:
#         logger.error("HTTP(S)延迟测试已超时")
#         mean_delay = 0
#     except Exception as e:
#         logger.error(repr(e))
#         mean_delay = 0
#     finally:
#         if mean_delay1 is not None:
#             pass
#             # _free_me(ctypes.pointer(mean_delay1))
#     return mean_delay


# def switchProxy(_nodeinfo: dict, _index: int) -> bool:
#     """
#     切换clash核心中的代理节点，会将数据直接发往动态链接库
#     :param _nodeinfo: 节点信息
#     :param _index: 索引
#     :return: bool
#     """
#     if type(_nodeinfo).__name__ != "dict":
#         return False
#     try:
#         _payload = yaml.dump({'proxies': _nodeinfo})
#         _status = _setProxy(_payload.encode(), _index)
#         # logger.info(f"切换结果: {_status}")
#         if not _status:
#             logger.info(f"切换节点: {_nodeinfo.get('name', 'not found')} 成功")
#             # _free_me(_status)
#             return True
#         else:
#             logger.error(str(_status))
#             # _free_me(_status)
#             return False
#     except Exception as e:
#         logger.error(str(e))
#         return False


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


# def killclash():
#     stop = getattr(lib, 'stop')
#     stop.argtypes = [ctypes.c_int64]
#     stop(1)


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
    pass
