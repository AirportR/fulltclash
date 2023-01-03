from pyrogram.errors import RPCError

from libs import cleaner, check
from botmodule.init_bot import config, admin
import hashlib


async def sub(_, message):
    arg = cleaner.ArgCleaner().getall(str(message.text))
    try:
        if len(arg) > 1:
            pwd = arg[2] if len(arg) > 2 else arg[1]
            subinfo = config.get_sub(arg[1])
            subpwd = subinfo.get('password', '')
            if hashlib.sha256(pwd.encode("utf-8")).hexdigest() == subpwd:
                await message.reply(str(subinfo.get('url', '')))
            else:
                await message.reply("密码错误,请检查后重试")
        else:

            if await check.check_user(message, admin, isalert=False):
                subinfo = config.get_sub()
                item = []
                for k in subinfo.keys():
                    item.append(k)
                await message.reply(str(item))
            else:
                await message.reply("使用方法： /sub <订阅名称> <访问密码>")
    except RPCError as r:
        print(r)


async def new(_, message):
    arg = cleaner.ArgCleaner().getall(str(message.text))
    if len(arg) < 3:
        await message.reply("请输入正确的格式，如： /new <订阅地址> <订阅名称> <访问密码>")
        return
    else:
        try:
            suburl = arg[1]
            subname = arg[2]
            subpwd = subname if len(arg) < 4 else arg[3]
            safe_pwd = hashlib.sha256(subpwd.encode("utf-8")).hexdigest()
            subinfo = {subname: {'url': suburl, 'password': safe_pwd}}
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


if __name__ == '__main__':
    pass
