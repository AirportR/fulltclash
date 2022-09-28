import asyncio

from loguru import logger
from pyrogram.errors import RPCError
from libs.check import check_user
from botmodule import init_bot

tourist_text = """
    欢迎使用FullTclash bot,目前可用命令有:

/help & /start [游客]获取帮助菜单
/inboundurl <订阅链接> [游客]临时下载订阅仅作入口分析

如有使用问题加入频道 @FullTClash 交流
"""
user_text = """
    欢迎使用FullTclash bot,目前可用命令有:

/help & /start [游客]获取帮助菜单
/inboundurl <订阅链接> [游客]临时下载订阅仅作入口分析
/testurl <订阅链接> [用户]临时下载订阅进行一次流媒体测试
/test <订阅名> [用户]进行一次流媒体测试测试
/analyzeurl <订阅链接> [用户]临时下载订阅进行一次节点链路拓扑测试
/analyze <订阅名> [用户]进行一次节点链路拓扑测试
/inbound <订阅名> [用户]仅作入口分析
/register & /baipiao <注册地址> [用户]远程注册并返回一个订阅（必须是V2board且无邮箱验证）

如有使用问题加入频道 @FullTClash 交流
"""

admin_text = """
    欢迎使用FullTclash bot,目前可用命令有:

/help & /start [游客]获取帮助菜单
/inboundurl <订阅链接> [游客]临时下载订阅仅作入口分析
/testurl <订阅链接> [用户]临时下载订阅进行一次流媒体测试
/test <订阅名> [用户]进行一次流媒体测试测试
/analyzeurl <订阅链接> [用户]临时下载订阅进行一次节点链路拓扑测试
/analyze <订阅名> [用户]进行一次节点链路拓扑测试
/inbound <订阅名> [用户]仅作入口分析
/register & /baipiao <注册地址> [用户]远程注册并返回一个订阅（必须是V2board且无邮箱验证）
/grant <回复一个目标> [管理]授权一个目标
/ungrant <回复一个目标> [管理]取消授权一个目标
/user [管理]查看所有授权用户的id
/new [管理]新增一个订阅
/remove [管理]移除一个订阅
/reload [管理]重载部分配置
        (若一直提示多任务状态，可尝试此项，该命令不会对正在测试的任务产生影响)
/sub [管理]查看所有已保存的订阅

如有使用问题加入频道 @FullTClash 交流
    """


async def helps(client, message):
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
