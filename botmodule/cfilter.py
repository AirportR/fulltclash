from pyrogram import filters
from pyrogram.types import Message

from botmodule.utils import message_delete_queue
from libs import check
from botmodule.init_bot import reloadUser, admin


# custom filter

def dynamic_data_filter(data):
    """
    特定的回调数据过滤器。比如回调数据 callback.data == "close" ,data == "close"。那么成功命中，返回真
    """

    async def func(flt, _, query):
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)


def admin_filter():
    """
    检查管理员是否在配置文件所加载的的列表中
    """

    async def func(_, __, message):
        try:
            if int(message.from_user.id) not in admin and str(
                    message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
                back_message = await message.reply("❌您不是bot的管理员，无法操作。")
                message_delete_queue.put_nowait([back_message.chat.id, back_message.id, 10])
                return False
            else:
                return True
        except AttributeError:
            if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
                back_message = await message.reply("❌您不是bot的管理员，无法操作。")
                message_delete_queue.put_nowait([back_message.chat.id, back_message.id, 10])
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    return filters.create(func)


def reloaduser():
    """
    检查用户是否在配置文件所加载的的列表中，这是一个装饰器.
    """

    def wrapper(func):
        async def inner(client, message):
            user = reloadUser()
            result = await check.check_user(message, user)
            if result:
                await func(client, message)
            else:
                print("未通过")
                return

        return inner

    return wrapper


def getErrorText(text: str):
    if text.endswith("url"):
        return f"❌ 格式错误哦 QAQ，正确的食用方式为： {text} <订阅链接> <包含过滤器> <排除过滤器>"
    elif text.startswith("/test") or text.startswith("/topo") or text.startswith("/analyze") or text.startswith(
            "/speed"):
        return f"❌ 格式错误哦 QAQ，正确的食用方式为： {text} <任务名称> <包含过滤器> <排除过滤器>"
    elif text.startswith("/invite"):
        return f"❌ 使用方式: {text} <回复一个目标> <...若干检测项>"
    else:
        return f"❌ 使用方式: {text} <参数1> <参数2>"


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
        else:
            back_message = await message.reply(getErrorText(arg[0]))
            message_delete_queue.put_nowait([message.chat.id, message.id, 10])
            message_delete_queue.put_nowait([back_message.chat.id, back_message.id, 10])
            return False

    return filters.create(func)


def allfilter(group: int, *args, **kwargs):
    """
    所有自定义filter
    """
    if group == 1:
        return command_argnum_filter()
    elif group == 2:
        return admin_filter()
    else:
        print("未知权限组")
        return filters.create(lambda x: True)
