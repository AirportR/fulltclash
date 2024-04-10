import random
from os import getcwd
import aiohttp

from utils.cron import *
from typing import Callable, Any, Union, Coroutine, Optional

__version__ = "3.6.11"  # 项目版本号
HOME_DIR = getcwd()
__all__ = [
    "cron_delete_message",
    "cron_edit_message",
    "message_delete_queue",
    "message_edit_queue",
    "__version__",
    "retry",
    "script_demo",
    "HOME_DIR",
    "generate_random_string",
    "async_runtime"
]


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
                    if break_func(result):
                        break
                except (aiohttp.ClientError, asyncio.exceptions.TimeoutError, ConnectionResetError):
                    continue
                except Exception as e:
                    logger.info(str(e))

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


def async_runtime(loop: Optional[asyncio.AbstractEventLoop] = None):
    """
    临时的异步运行时，适用于只有一两个异步函数的情况
    :param: loop: 事件循环
    :param: break_func: 触发的回调中止函数，参数为调用函数的返回值，返回值为bool，
    """
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    def wrapper(func):
        def inner(*args, **kwargs):
            result = loop.run_until_complete(func(*args, **kwargs))
            return result

        return inner

    return wrapper

