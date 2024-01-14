import asyncio
from typing import Union, List

from pyrogram import filters, StopPropagation, Client
from pyrogram.filters import Filter
from pyrogram.types import Message, CallbackQuery
from loguru import logger
from utils.cleaner import addon
from utils.cron.utils import message_delete_queue
from utils import check
from botmodule.init_bot import reloadUser, admin

CALLBACK_FUNC = addon.init_callback()
MESSAGE_LIST: List["Message"] = []  # 这个列表用来存放临时的消息，主要用来给 next_filter使用


# custom filter

def dynamic_data_filter(data: str) -> "Filter":
    """
    特定的回调数据过滤器。比如回调数据 callback.data == "close" ,data == "close"。那么成功命中，返回真
    """

    async def func(flt, _, query):
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)


def exclude_text_filter(text: Union[str, List[str]]) -> "Filter":
    """
    特定文本排除

    :param: text 要排除的文本列表
    """
    text = [text] if isinstance(text, str) else text

    async def func(flt, _, update: Union[Message, CallbackQuery]):
        return update.data not in flt.text if isinstance(update, CallbackQuery) else \
            update.text and update.text not in flt.text

    return filters.create(func, text=text)


def prefix_filter(prefix: str):
    """
    特定文本前缀过滤器，支持回调数据过滤。
    """

    async def func(flt, _, update: Union[Message, CallbackQuery]):
        return update.text.startswith(flt.prefix) if isinstance(update, Message) else update.data.startswith(flt.prefix)

    return filters.create(func, prefix=prefix)


def next_filter():
    """
    特定消息下一条过滤器，比如bot想获取发送完这条消息后读取下一条消息。

    handler_index: handler添加到groups的下标
    """

    async def func(flt, _: "Client", update: "Message"):
        msg_list: List["Message"] = flt.message
        if not isinstance(msg_list, list):
            return False
        for m in msg_list:
            if m.chat.id == update.chat.id:
                if m.id == update.id - 1:
                    return True
        return False
        # return (flt.message.chat.id == update.chat.id) and flt.message.id == update.id - 1

    return filters.create(func, message=MESSAGE_LIST)


def admin_filter():
    """
    检查管理员是否在配置文件所加载的的列表中
    """

    async def func(_, __, message: "Message"):
        try:
            if message.from_user and message.from_user.id not in admin and str(
                    message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
                back_message = await message.reply("❌您不是bot的管理员，无法操作。")
                message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
                return False
            else:
                return True
        except AttributeError:
            if message.sender_chat and message.sender_chat.id not in admin:  # 如果不在USER_TARGET名单是不会有权限的
                back_message = await message.reply("❌您不是bot的管理员，无法操作。")
                message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    return filters.create(func)


async def defaultCallback(message: Message):
    """
    默认的权限回调等级
    """
    return await check.check_user(message, reloadUser())


def AccessCallback(default=0):
    """
    权限回调函数
    检查用户是否在配置文件所加载的的列表中，这是一个装饰器.
    default: 默认的回调函数值，如果不为0，则不会调用默认的回调函数
    """

    def wrapper(func):
        async def inner(client: "Client", message: "Message"):
            for call in CALLBACK_FUNC:
                try:
                    callres = await call(client, message) if asyncio.iscoroutinefunction(call) else True
                except StopPropagation:  # 停止回调传播
                    callres = False
                if not isinstance(callres, bool):
                    if call.__code__ and call.__code__.co_filename and call.__code__.co_firstlineno:
                        logger.warning(f"定义在 {call.__code__.co_filename}:{call.__code__.co_firstlineno} "
                                       f"行的回调函数未返回布尔值，可能会出现意料之外的结果！")
                    else:
                        logger.warning("未返回布尔值，可能会出现意料之外的结果！")
                if not callres:
                    return
            if default == 0:
                result = await defaultCallback(message)
                if result:
                    await func(client, message)
                else:
                    return
            else:
                await func(client, message)

        return inner

    return wrapper


def getErrorText(text: str):
    if text.endswith("url"):
        return f"❌ 格式错误哦 QAQ，正确的食用方式为： \n{text} <订阅链接> <包含过滤器> <排除过滤器>"
    elif text.startswith("/test") or text.startswith("/topo") or text.startswith("/analyze") or text.startswith(
            "/speed"):
        return f"❌ 格式错误哦 QAQ，正确的食用方式为： \n{text} <任务名称> <包含过滤器> <排除过滤器>"
    else:
        return f"❌ 使用方式: \n{text} <参数1> <参数2>"


def sub_filter():
    """
    对订阅名称做预先检查
    """
    async def func(_, __, message: Message) -> bool:
        string = str(message.text)
        arg = string.strip().split(' ')
        arg = [x for x in arg if x != '']
        cmd = arg[0].split('@')[0]
        if cmd.endswith("url") or 'invite' in arg[0]:
            return True
        if check.check_sub_name(arg[1]):
            return True
        else:
            botmsg = await message.reply("❌找不到该任务名称")
            message_delete_queue.put(botmsg, 10)
            message_delete_queue.put(message, 10)
            return False

    return filters.create(func)


def command_argnum_filter(argnum: int = 1):
    """
    命令行参数数量过滤器。
    比如有一条指令是： /testurl <url> <节点过滤器>
    当用户输入 /testurl 后面没有跟随足够的参数数量时，将返回False。
    默认值为1，表示每条指令后方必须至少携带一个参数。
    """
    if argnum < 1:
        raise ValueError("Parameters number at least greater than 1")

    async def func(_, __, message: Message):
        string = str(message.text)
        arg = string.strip().split(' ')
        arg = [x for x in arg if x != '']
        if len(arg) > argnum:
            return True
        elif arg[0].startswith("/invite"):
            return True
        else:
            back_message = await message.reply(getErrorText(arg[0]))
            message_delete_queue.put_nowait((message.chat.id, message.id, 10))
            message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
            return False

    return filters.create(func)


def pre_filter(group: int, *args):
    """
    预定义的filter
    """
    if group == 1:
        return command_argnum_filter(*args)
    elif group == 2:
        return admin_filter()
    else:
        print("未知权限组")
        return filters.create(lambda x: True)
