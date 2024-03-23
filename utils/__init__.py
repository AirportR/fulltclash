import asyncio
import random
from os import getcwd
from typing import Callable, Any, Union, Coroutine

import aiohttp
from aiohttp import http

__version__ = "4.1.5"
APP_VERSION = __version__
HOME_DIR = getcwd()
__all__ = [__version__, APP_VERSION]


def generate_random_string():
    length = random.randint(10, 30)
    rand_str = ''
    range_start = 48
    range_end = 122

    for _ in range(length):
        random_integer = random.randint(range_start, range_end)
        # Validate ascii range
        if random_integer <= 57 or random_integer >= 65:
            rand_str += chr(random_integer)

    return rand_str


def block_aiohttp_version():
    # 随机响应头，迷惑网络探测，降低在网络中的存在感
    http.SERVER_SOFTWARE = generate_random_string()


def default_breakfunc(ret_val: bool) -> bool:
    return True if isinstance(ret_val, bool) and ret_val else False


def retry(count=5, break_func: Callable[[Any], bool] = None):
    """
    重试装饰器，网络请求可能会出错，所以需要重试
    :param: count: 重试次数
    :param: break_func: 触发的回调中止函数，参数为调用函数的返回值，返回值为bool，
    """
    if break_func is None:
        break_func = default_breakfunc

    def wrapper(func):
        async def inner(*args, **kwargs):
            for _ in range(count):
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                except (aiohttp.ClientError, asyncio.exceptions.TimeoutError, ConnectionResetError, Exception):
                    continue
                if break_func(result):
                    break

        return inner

    return wrapper


async def script_demo(script_func: Union[Callable, Coroutine], *arg, **kwargs):
    class FakeColl:
        def __init__(self):
            self.info = {}
            self.data = self.info

    fakecl = FakeColl()

    session = aiohttp.ClientSession()
    if asyncio.iscoroutine(script_func):
        await script_func
    else:
        await script_func(fakecl, session, *arg, **kwargs)
    print(fakecl.info)
    await session.close()


block_aiohttp_version()
