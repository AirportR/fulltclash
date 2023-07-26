
from loguru import logger
from pyrogram.errors import RPCError
from utils.check import check_user
from botmodule import init_bot, message_delete_queue
from glovar import __version__

tourist_text = f"""
    欢迎使用FullTclash bot,目前可用指令有:

/help & /start [游客]获取帮助菜单
/version [游客]输出版本信息({__version__})
/traffic & /subinfo & /流量查询 & /流量 <订阅链接> & <订阅名> [游客]获取流量信息
/inboundurl <订阅链接> [游客/用户]临时下载订阅仅作入口分析(需管理员开启)

如有使用问题加入频道 @FullTClash 交流
"""
user_text = f"""
    欢迎使用FullTclash bot,目前可用指令有:

基础指令
/help & /start [游客]获取帮助菜单
/version [游客]输出版本信息({__version__})
/traffic & /subinfo & /流量查询 & /流量 <订阅链接> & <订阅名> [游客]获取流量信息

测试指令
/test <订阅名> <包含过滤器> <排除过滤器> [用户]进行流媒体测试
/speed <订阅名> <包含过滤器> <排除过滤器> [用户]进行速度测试
/analyze & /topo <订阅名> [用户]进行节点链路拓扑测试
/inbound <订阅名> [用户]仅作入口分析
/outbound <订阅名> [用户]仅作出口分析
以上指令在后缀加上 url 表示临时下载订阅进行XX测试
如: /testurl <订阅链接> [用户]临时下载订阅进行流媒体测试

其他指令
/invite <回复一个目标> [用户]临时邀请一个目标进行测试（匿名无法生效）
/share <回复一个目标> [用户]分享订阅的测试权
/register & /baipiao <注册地址> [用户]远程注册并返回一个订阅（必须是V2board且无邮箱验证）
/new <订阅链接> <订阅名> <访问密码> [用户]添加一个订阅
/sub <订阅名> <访问密码> [用户]查看对应名称的订阅

如有使用问题加入频道 @FullTClash 交流
"""

admin_text = f"""
    欢迎使用FullTclash bot,目前可用指令有:

基础指令
/help & /start [游客]获取帮助菜单
/version [游客]输出版本信息({__version__})
/traffic & /subinfo & /流量查询 & /流量 <订阅链接> & <订阅名> [游客]获取流量信息

测试指令
/test <订阅名> <包含过滤器> <排除过滤器> [用户] 进行流媒体测试
/speed <订阅名> <包含过滤器> <排除过滤器> [用户]进行速度测试
/analyze & /topo <订阅名> [用户]进行节点链路拓扑测试
/inbound <订阅名> [用户]仅作入口分析
/outbound <订阅名> [用户]仅作出口分析
以上指令在后缀加上 url 表示临时下载订阅进行XX测试
如: /testurl <订阅链接> [用户]临时下载订阅进行流媒体测试

其他指令
/invite <回复一个目标> [用户]临时邀请一个目标进行测试（匿名无法生效）
/share <回复一个目标> [用户]分享订阅的测试权
/register & /baipiao <注册地址> [用户]远程注册并返回一个订阅（必须是V2board且无邮箱验证）
/new <订阅链接> <订阅名> <访问密码> [用户]新增一个订阅
/sub [管理]查看所有已保存的订阅
/grant <回复一个目标> / <...若干UID> [管理]授权一个目标
/ungrant <回复一个目标> / <...若干UID> [管理]取消授权一个目标
/user [管理]查看所有授权用户的id
/remove [管理]移除一个或多个订阅
/install <回复一个文件>安装脚本
/uninstall <脚本文件名>卸载脚本
/setantigroup[管理] 切换防拉群模式
/restart [管理]重启整个程序
/reload [管理]重载部分配置(一般情况下用不到)
/clash [管理]启动或关闭clash开放的端口服务
/connect [管理][前后端专属]对接一个后端bot
/sconnect [管理][前后端专属]对接一个主端bot
/setting [管理]bot的控制面板
/logs <可选:数字n> [管理]输出本次运行的最后n行日志文件
killme [管理]杀死bot的自身进程(慎用！)
如有使用问题加入频道 @FullTClash 交流
    """


async def version(_, message):
    try:
        version_hash = init_bot.latest_version_hash
        back_message = await message.reply(f"FullTclash版本: {__version__} (__{version_hash}__)")
        message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 30))
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
        message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 30))
    except RPCError as r:
        logger.error(str(r))
