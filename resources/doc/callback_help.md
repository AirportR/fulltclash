# FullTClash回调功能

FullTClash拥有回调函数的抽象接口，可以让使用者对bot二次开发出拓展功能。

## 什么是回调函数？

在计算机程序设计中，回调函数，或简称回调（Callback 即call then back 被主函数调用运算后会返回主函数），是指通过参数将函数传递到其它代码的，某一块可执行代码的引用。这一设计允许了底层代码调用在高层定义的子程序。

## 实现细节
本项目回调功能的实现基于Python的装饰器语法糖，我们的抽象接口为：
```python
@AccessCallback()
```

具体实现，请前往项目的源代码文件 ./botmodule/cfilter.py 查看。

在代码实现中，会依次执行 ./addons/callback 文件夹下所有符合接入条件的函数，通过判断返回布尔值的真假，进行取消执行或者继续执行原本功能。

目前，我们的回调函数设计仅支持 阻塞式回调。阻塞式回调里，回调函数的调用发生在原始函数调用返回之前。

## 第一个回调函数

首先请在 ./addons/callback/ 文件夹下，新建一个 .py 后缀文件，比如 mycallback.py

1、导入必要库 
```python
from pyrogram.types import Message
from pyrogram import Client
```
2、定义合法的回调函数。\
我们约定，所有的回调函数名都为 callback ，并且是协程函数（async开头）。
```python
async def callback(app: Client, message: Message) -> bool:
    """
    app 参数为 Bot的客户端主程序
    message 参数为 触发回调的消息对象
    
    返回值一定为布尔值
    """
    try:
        await message.reply("回调函数调用成功！")
        return True
    # 异常检测，固定格式，防止抛异常未返回bool值
    except Exception as e:
        print(e)
        return True
```

以上就是一个简单的回调例子，接下来我们加点料。
这里其实回调可以分为两种使用场景：

1、新添功能

2、拒绝服务

两者的区别主要是一个始终最后返回True，另外一个满足某个条件判断返回False。

## 使用案例

### 让bot离开群组
想使用一个新的指令让bot离开群组，比如 /leave
首先需要在配置文件写入一个配置让bot能识别leave指令，不加该配置，无法在群组使用。
```yaml
bot:
 command:
   - leave
```
```python
from pyrogram.enums import ChatType
from pyrogram.types import Message
from pyrogram import Client
from loguru import logger
from botmodule.init_bot import admin
from utils.cleaner import ArgCleaner
from utils.check import get_telegram_id_from_message


async def callback(app: Client, message: Message) -> bool:
    try:
        tgargs = ArgCleaner().getall(str(message.text))
        if tgargs[0].startswith('/leave'):
            assert message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
            ID = get_telegram_id_from_message(message)
            if ID in admin:
                await message.chat.leave()
            logger.info(f"{app.username} 已离开 {message.chat.id}:{message.chat.title}")
        return True
    except Exception as e:
        print(e)
        return True
```
### 拒绝滥用bot的坏蛋
假设有一个坏蛋故意往你的bot丢一个节点池测速，或者你单纯讨厌TA，不想给TA使用，那么有以下例子。

block.py
```python
from pyrogram.types import Message
from pyrogram import Client
from utils.check import get_telegram_id_from_message  # 项目封装的方法，用于获取用户id
block_id_list = [] # 你要禁止的TG用户id
async def callback(app: Client, message: Message) -> bool:
    """
    app 参数为 Bot的客户端主程序
    message 参数为 触发回调的消息对象
    返回值一定为布尔值
    """
    try:
        # get_telegram_id_from_message 为项目封装好的函数，获取干净的id
        userid = get_telegram_id_from_message(message)
        if userid in block_id_list:
            await message.reply("你已被ban，无法使用！")
            # 因为这个回调属于拒绝服务类型，所以返回False就是告诉bot程序不再往下运行。
            return False
        else:
            return True
    except Exception as e:
        print(e)
        return True
```

### 全局测试订阅链接黑名单
总是有人喜欢那公益的节点订阅进行测试，本来就慢，这下更慢了，所以可以加个禁止测试某些订阅的黑名单。
```python
from urllib.parse import urlparse  # url解析
from pyrogram.filters import private_filter
from pyrogram.types import Message
from pyrogram import Client

from loguru import logger  # 日志记录
from utils.cleaner import ArgCleaner, geturl  # 项目定义的成员变量、方法
from botmodule.init_bot import admin  # 管理员名单

domain_blacklist = []  # 全局域名黑名单，针对机场和订阅转换。
url_blacklist = ["https://baidu.com"]  # 全局url黑名单，针对单个订阅。

async def callback(_: Client, message: Message) -> bool:
    """
    invite指令临时邀请测试的人判定url黑名单
    """
    try:
        # 不是私聊的，跳过，不走这个回调。交给其他回调
        if not await private_filter(_, _, message):
            return True
        # 消息不是http开头说明不是订阅链接，跳过，不走这个回调。
        tgargs = ArgCleaner().getall(str(message.text))
        if not tgargs[0].startswith("http"):
            return True
        # 用 geturl 匹配订阅链接
        suburl = geturl(str(message.text))
        # 没匹配成功，跳过
        if suburl is None:
            return True
        # 管理员怎么能受限制呢，权限肯定拉满！
        if message.from_user.id in admin:
            await message.reply("您是至高的管理员，黑名单对您无效☺️")
            return True
        # 匹配到对应的域名或者URL，拒绝测试！
        elif is_in_blacklist(suburl):
            await message.reply("❌此订阅拒绝服务~")
            return False
        else:
            return True
    except Exception as e:
        logger.info(str(e))
        return True


def is_in_blacklist(url: str) -> bool:
    if url in url_blacklist:
        logger.warning(f"检测到url黑名单: {url}")
        return True
    domain = urlparse(url).netloc
    logger.info("invite指令解析的域名: "+domain)
    if domain in domain_blacklist:
        logger.warning(f"检测到域名黑名单: {domain}\n来源于此订阅: {url}")
        return True
    else:
        return False
```

### 权限回调，让游客权限在特定群组使用invite
```python
import time

from pyrogram.types import Message
from pyrogram import Client
from botmodule import invite
from botmodule.init_bot import reloadUser  # 拿到用户名单
from utils import message_delete_queue as mdq  # 消息定时删除队列，调用 mdq.put(message, 5)将在5秒后删除消息
from utils.cleaner import ArgCleaner
from utils.check import get_telegram_id_from_message

group_whitelist = []  # 群组id白名单，只有在名单的群组 /invite指令才有效
cooling_queue = {}
cooling_interval = 60  # 调用invite的冷却时间


async def callback(bot: Client, message: Message) -> bool:
    try:
        tgargs = ArgCleaner().getall(str(message.text))
        # 匹配invite指令，不是的话不走这个回调
        if tgargs[0].startswith('/invite'):
            user = reloadUser()
            print("群组id:", message.chat.id)
            ID = get_telegram_id_from_message(message)
            # 用户权限就直接返回了，因为自己本身有权限。
            if ID in user:
                return True
            # invite指令需要回复一个目标
            if message.reply_to_message is None:
                backmsg = await message.reply("请先回复一个目标")
                mdq.put_nowait((backmsg.chat.id, backmsg.id, 5))
                return False
            if message.chat.id in group_whitelist:
                if ID in cooling_queue:
                    pre_time = cooling_queue[ID]
                    if time.time() - pre_time < cooling_interval:
                        backmsg = await message.reply(f"❌您在{cooling_interval}秒内发起过测试，请稍后再试~")
                        mdq.put_nowait((backmsg.chat.id, backmsg.id, 5)) # 旧版本写法，为了兼容3.5.3。用mdq.put(不支持3.5.3)也可以
                        return False
                    else:
                        cooling_queue[ID] = time.time()
                        await select_slave_page(bot, message, page=1)
                        # await invite(bot, message)
                        # 这里返回False是因为我们上面已经发起了一个invite，我们不再需要走原来的invite逻辑了，返回True就会触发两个，不信你试试。
                        return False
                else:
                    cooling_queue[ID] = time.time()
                    await select_slave_page(bot, message, page=1)
                    # await invite(bot, message)
                    return False
        # 匹配invite指令，不是的话不走这个回调
        return True
    except Exception as e:
        print(e)
        return True
```
## 项目中所定义的变量、方法总览

你可以导入这些方法和变量，就不需要自己造太多轮子了

1、消息删除队列

bot进行发送消息后，你可以设定若干秒数后删除某个消息
```python
from utils.check import message_delete_queue as mdq
# 使用方法
# 10秒后删除（默认值）
mdq.put(message)  # 此方法在3.5.3不适用
# 5秒后删除
mdq.put(message, 5)
# 3.5.3 请使用这个：
mdq.put_nowait((message.chat.id, message.id, 10))
```

2、拿到用户名单、管理员名单

```python
from botmodule.init_bot import admin, USER_TARGET
# 或者
from botmodule.init_bot import reloadUser

#区别在于 reloadUser会进行重载操作，配置文件会重新加载然后读取用户列表返回，USER_TARGET是启动bot加载好的，出于安全考虑，admin名单列表无重载，只会在启动时加载。
```

3、拿到配置文件中的所有值

我们定义了一个存放着配置文件的全局变量，它属于 cleaner.ConfigManager() 类

```python
from botmodule.init_bot import config

# 当然 utils.cleaner下也有一个，你用哪个都没问题，和bot有关的配置最好用上面这个
# from utils.cleaner import config

myconfig = config.config  # 第一个config是实例，第二个config才是成员变量，它是yaml反序列化而来一个字典。
```

4、消息编辑队列
这个用得不是很多。主要是针对编辑同一条消息可能会出现顺序不一致的问题而设计。
```python
from utils import message_edit_queue as meq
# 使用方法：meq.put(chat.id, message.id, text, seconds, reply_markup)
```
5、正则匹配url地址
```python
from utils.cleaner import geturl
url = geturl("http字符串")
if url is not None:
    print(f"匹配成功的URL: {url}")
```

6、切片tg消息中的指令参数，返回命令参数列表
```python
from utils.cleaner import ArgCleaner
tgargs = ArgCleaner().getall(message.text)
```

更多的方法和变量，就自己阅读源码或者手搓吧

