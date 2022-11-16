from pyrogram.errors import RPCError

from libs import cleaner
from botmodule.init_bot import config


async def sub(_, message):
    subinfo = config.get_sub()
    try:
        await message.reply(str(subinfo))
    except RPCError as r:
        print(r)


async def new(_, message):
    arg = cleaner.ArgCleaner().getall(str(message.text))
    if len(arg) < 3:
        await message.reply("请输入正确的格式，如： /new <订阅地址> <订阅名称>")
        return
    else:
        try:
            suburl = arg[1]
            subname = arg[2]
            subinfo = {subname: suburl}
            print(suburl, subname)
            config.newsub(subinfo)
            config.reload()
            await message.reply('新增了一个订阅: ' + subname)
        except IndexError:
            print("错误")


async def remove(_, message):
    arg = cleaner.ArgCleaner().getall(str(message.text))
    try:
        del arg[0]
        for i in arg:
            config.removesub(i)
        config.reload()
        try:
            await message.reply('移除了{}个订阅: '.format(len(arg)) + str(arg))
        except RPCError as r:
            print(r)
    except IndexError:
        print("错误")
