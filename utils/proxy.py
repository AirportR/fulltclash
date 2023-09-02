import asyncio
import contextlib
import socket
import subprocess
from random import random, seed
from typing import Union, List
import yaml
import aiohttp

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


async def is_port_in_use(host='127.0.0.1', port=80):
    """
    检查主机端口是否被占用
    :param host: 主机名
    :param port: 端口
    :return: 如果占用返回True否则为False
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        return True
    except ConnectionRefusedError:
        return False


async def get_available_port(portnum: int, retry: int = 10, startup: int = 10000):
    """
    获取随机可用端口，无可以端口抛出 OSError 异常
    portnum: 要获取的端口数
    retry: 重试
    startup: 起始选定端口范围，范围是 startup ~ startup+10000

    return: 可用端口列表, 已使用的重试次数
    """
    seed(21)
    for n in range(retry):
        random_nums = [int(random() * 10001) + startup for _ in range(portnum)]
        tasks = [asyncio.create_task(is_port_in_use(port=rnum)) for rnum in random_nums]
        results = await asyncio.gather(*tasks)
        if True not in results:
            return random_nums
    raise OSError("No free ports are available")


class FullTClash:
    def __init__(self, control_port: Union[str, int] = None, proxy_portlist: List[Union[str, int]] = None):
        """
        control_port: 控制端口
        proxy_port: 代理端口，多个端口
        """
        self.cport = control_port
        self.port = [str(pro) for pro in proxy_portlist]
        self._p = None

    async def start(self):
        """
        启动fulltclash代理程序
        """
        if self.cport is None:
            port0 = await get_available_port(1)
            if port0:
                self.cport = port0[0]
            logger.info(f"未找到预先设置好的端口，将随机分配控制端口: {self.cport}")
        if self.port is None:
            port1 = await get_available_port(1)
            if port1:
                self.port = [str(po) for po in port1]
            logger.info(f"未找到预先设置好的端口，将随机分配代理端口: {str(self.port)}")
        port2 = "|".join(self.port)
        _command = fr"{config.get_clash_path()} -c {self.cport} -p {port2}"
        p = subprocess.Popen(_command.split(), encoding="utf-8")
        self._p = p
        c = 0
        while True:
            c += 1
            if c >= 10:
                raise TimeoutError("某种原因导致启动进程失败！")
            if await is_port_in_use(port=self.cport):
                break
            else:
                await asyncio.sleep(1)
        return self.cport, self.port

    def close(self):
        if self._p is not None and isinstance(self._p, subprocess.Popen):
            self._p.kill()
        else:
            logger.warning("没有进程可供停止!")

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
    async def sock_send(message, key: str, controlport: int, norecv=True):
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
    async def setproxy(proxyinfo: dict, index: int, controlport: int):
        logger.info(f"设置代理: {proxyinfo.get('name', '')}, index: {index}")
        data = yaml.dump({'proxies': proxyinfo, 'index': index, 'command': 'setproxy'})
        await FullTClash.sock_send(data, BUILD_TOKEN, controlport)


if __name__ == "__main__":
    pass
