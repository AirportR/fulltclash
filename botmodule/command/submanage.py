import asyncio
import hashlib
import pyrogram.types
from pyrogram.errors import RPCError
from loguru import logger
from libs import cleaner, check
from botmodule.init_bot import config, admin
from libs.check import check_user


async def sub(_, message):
    ID = get_telegram_id_from_message(message)
    arg = cleaner.ArgCleaner().getall(str(message.text))
    try:
        if len(arg) > 1:
            pwd = arg[2] if len(arg) > 2 else arg[1]
            subinfo = config.get_sub(arg[1])
            if not subinfo:
                m2 = await message.reply("未找到该订阅")
                await asyncio.sleep(5)
                await m2.delete()
                return
            subpwd = subinfo.get('password', '')
            subowner = subinfo.get('owner', '')
            if await check_user(message, admin, isalert=False):
                # 管理员至高权限
                await message.reply(str(subinfo.get('url', '')))
                return
            if subowner and subowner == ID:
                if hashlib.sha256(pwd.encode("utf-8")).hexdigest() == subpwd:
                    await message.reply(str(subinfo.get('url', '')))
                else:
                    m2 = await message.reply("密码错误,请检查后重试")
                    await asyncio.sleep(5)
                    await m2.delete()
            else:
                await message.reply("❌身份ID不匹配，您无权查看该订阅。")
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
    ID = get_telegram_id_from_message(message)
    arg = cleaner.ArgCleaner().getall(str(message.text))

    if len(arg) < 3:
        await message.reply("请输入正确的格式，如： /new <订阅地址> <订阅名称> <访问密码>")
        return
    else:
        subinfo = config.get_sub(arg[2])
        owner = subinfo.get('owner', '')
        if subinfo and ID != owner:
            m2 = await message.reply("⚠️该订阅名称已被占用")
            await asyncio.sleep(5)
            await m2.delete()
            return
        try:
            suburl = arg[1]
            subname = arg[2]
            subpwd = subname if len(arg) < 4 else arg[3]
            safe_pwd = hashlib.sha256(subpwd.encode("utf-8")).hexdigest()
            subinfo = {subname: {'owner': ID, 'url': suburl, 'password': safe_pwd}}
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


def get_telegram_id_from_message(message: pyrogram.types.Message):
    """
    获得唯一确定身份标识的id
    为什么我会写这个方法？因为该死的telegram里有频道匿名身份和普通用户身份，它们的id不是同一个属性。
    :param message:
    :return:
    """
    # print(message)
    try:
        ID = message.from_user.id
        return ID
    except AttributeError:
        ID = message.sender_chat.id
        return ID
    except Exception as e:
        logger.error(str(e))


if __name__ == '__main__':
    pass
