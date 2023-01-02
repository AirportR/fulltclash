import asyncio

from loguru import logger
from pyrogram.errors import RPCError
from libs.check import check_user
from botmodule import init_bot
from libs.export import __version__

tourist_text = f"""
    欢迎使用FullTclash bot,目前可用指令有:

/help & /start [游客]获取帮助菜单
/version [游客]输出版本信息({__version__})
/traffic & /subinfo & /流量查询 & /流量 <订阅链接> [游客]获取流量信息
/inboundurl <订阅链接> [游客/用户]临时下载订阅仅作入口分析(需管理员开启)

如有使用问题加入频道 @FullTClash 交流
"""
user_text = f"""
    欢迎使用FullTclash bot,目前可用指令有:

基础指令
/help & /start [游客]获取帮助菜单
/version [游客]输出版本信息({__version__})
/traffic & /subinfo & /流量查询 & /流量 <订阅链接> [游客]获取流量信息

测试指令
/test <订阅名> <包含过滤器> <排除过滤器> [用户]进行流媒体测试
/speed <订阅名> <包含过滤器> <排除过滤器> [用户]进行速度测试
/analyze & /topo <订阅名> [用户]进行节点链路拓扑测试
/inbound <订阅名> [用户]仅作入口分析
/outbound <订阅名> [用户]仅作出口分析
/delay <订阅名> [用户]进行节点延时测试
以上指令在后缀加上 url 表示临时下载订阅进行XX测试
如: /testurl <订阅链接> [用户]临时下载订阅进行流媒体测试

其他指令
/register & /baipiao <注册地址> [用户]远程注册并返回一个订阅（必须是V2board且无邮箱验证）

如有使用问题加入频道 @FullTClash 交流
"""

admin_text = f"""
    欢迎使用FullTclash bot,目前可用指令有:

基础指令
/help & /start [游客]获取帮助菜单
/version [游客]输出版本信息({__version__})
/traffic & /subinfo & /流量查询 & /流量 <订阅链接> [游客]获取流量信息

测试指令
/test <订阅名> <包含过滤器> <排除过滤器> [用户]进行流媒体测试
/speed <订阅名> <包含过滤器> <排除过滤器> [用户]进行速度测试
/analyze & /topo <订阅名> [用户]进行节点链路拓扑测试
/inbound <订阅名> [用户]仅作入口分析
/outbound <订阅名> [用户]仅作出口分析
/delay <订阅名> [用户]进行节点延时测试
以上指令在后缀加上 url 表示临时下载订阅进行XX测试
如: /testurl <订阅链接> [用户]临时下载订阅进行流媒体测试

其他指令
/register & /baipiao <注册地址> [用户]远程注册并返回一个订阅（必须是V2board且无邮箱验证）
/grant <回复一个目标> [管理]授权一个目标
/ungrant <回复一个目标> [管理]取消授权一个目标
/user [管理]查看所有授权用户的id
/new [管理]新增一个订阅
/remove [管理]移除一个订阅
/reload [管理]重载部分配置(一般情况下用不到)
/sub [管理]查看所有已保存的订阅

如有使用问题加入频道 @FullTClash 交流
    """


async def version(_, message):
    try:
        back_message = await message.reply(f"FullTclash版本: {__version__}")
        await asyncio.sleep(30)
        await back_message.delete()
    except RPCError as r:
        logger.error(str(r))


async def helps(_, message):
    USER_TARGET = init_bot.USER_TARGET
    admin = init_bot.admin

    if await check_user(message, admin, isalert=False):
        send_text = admin_text
    else:
        if await check_user(message, USER_TARGET, isalert=False):
            send_text = user_text
        else:
            send_text = tourist_text
    try:
        back_message = await message.reply(send_text)
        await asyncio.sleep(30)
        await back_message.delete()
    except RPCError as r:
        logger.error(str(r))
