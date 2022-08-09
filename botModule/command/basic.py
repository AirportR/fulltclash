from pyrogram.errors import RPCError


async def helps(client, message):
    send_text = """
    欢迎使用FullTclash bot,目前可用命令有:

/testurl [用户]临时下载订阅来进行一项测试
/test [用户]进行一项测试
/grant [管理]授权一个目标
/ungrant [管理]取消授权一个目标
/user [管理]查看所有授权用户的id
/new [管理]新增一个订阅
/remove [管理]移除一个订阅
/sub [管理]查看所有已保存的订阅
    """
    try:
        await message.reply(send_text)
    except RPCError as r:
        print(r)
