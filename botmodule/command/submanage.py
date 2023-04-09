import asyncio
import hashlib
import pyrogram.types
from pyrogram.errors import RPCError
from loguru import logger
from utils import check, cleaner
from botmodule.init_bot import config, admin
from utils.check import check_user, get_telegram_id_from_message


async def sub_invite(_, message: pyrogram.types.Message):
    """
    分享订阅测试权限给其他人
    :param _:
    :param message:
    :return:
    """
    ID = get_telegram_id_from_message(message)
    arg = cleaner.ArgCleaner().getall(str(message.text))
    try:
        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            r_message = message.reply_to_message
            invite_id = str(get_telegram_id_from_message(r_message))
            logger.info("被邀请人id: " + invite_id)
            if len(arg) < 2:
                m4 = await message.reply("使用方法: /share <订阅名>")
                await asyncio.sleep(10)
                await m4.delete()
                return
            else:
                subinfo = config.get_sub(arg[1])
                owner = subinfo.get('owner', '')
                if not subinfo:
                    m3 = await message.reply("❌未找到该订阅")
                    await asyncio.sleep(10)
                    await m3.delete()
                    return
                if ID != owner:
                    m2 = await message.reply("❌身份ID不匹配，您无法操作该订阅！")
                    await asyncio.sleep(10)
                    await m2.delete()
                    return
                else:
                    subname = arg[1]
                    share_ID = subinfo.get('share', [])
                    if invite_id in share_ID:
                        m3 = await message.reply(f"TA已经有 **{subname}** 测试权限啦")
                        await asyncio.sleep(10)
                        await m3.delete()
                        return
                    share_ID.append(invite_id)
                    subinfo['share'] = share_ID
                    subinfo2 = {subname: subinfo}
                    config.newsub(subinfo2)
                    config.reload()
                    try:
                        invite_name = r_message.from_user.first_name
                    except AttributeError:
                        invite_name = r_message.sender_chat.title
                    await message.reply(f"**{invite_name}** 现在开始拥有 **{subname}** 的测试权限")

    except RPCError as r:
        print(r)


# async def remove_sub_invite(_, message: pyrogram.types.Message):
#     ID = get_telegram_id_from_message(message)
#     arg = cleaner.ArgCleaner().getall(str(message.text))
#     try:
#         print("等待实现")
#     except RPCError as r:
#         print(r)


async def sub(_, message):
    ID = get_telegram_id_from_message(message)
    arg = cleaner.ArgCleaner().getall(str(message.text))
    try:
        if len(arg) > 1:
            pwd = arg[2] if len(arg) > 2 else arg[1]
            subinfo = config.get_sub(arg[1])
            if not subinfo:
                m2 = await message.reply("❌未找到该订阅")
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
                    m2 = await message.reply("❌密码错误,请检查后重试")
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
                subinfo = config.get_sub()
                item = list(subinfo.keys())
                allsub = []
                for subname in item:
                    subsubinfo = subinfo.get(subname, {})
                    subowner = subsubinfo.get('owner', '')
                    if subowner and subowner == ID:
                        allsub.append(subname)
                if allsub:
                    await message.reply(str(allsub))
                else:
                    await message.reply("您尚未保存订阅！\n使用方法： /sub <订阅名称> <访问密码>")
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
            subinfo = {subname: {'owner': ID, 'url': suburl, 'password': safe_pwd, 'share': []}}
            print(suburl, subname)
            config.newsub(subinfo)
            config.reload()
            await message.reply('新增了一个订阅: ' + subname)
        except IndexError:
            print("错误")


async def remove(_, message):
    ID = get_telegram_id_from_message(message)
    arg = cleaner.ArgCleaner().getall(str(message.text))
    arg2 = []
    arg3 = []
    try:
        del arg[0]
        s_num = 0  # 删除成功数量
        f_num = 0  # 删除失败数量
        for i in arg:
            subinfo = config.get_sub(i)
            owner = subinfo.get('owner', '')
            if await check_user(message, admin, isalert=False) or owner == ID:
                # 管理员和订阅主人可以删除
                if subinfo:
                    config.removesub(i)
                    arg2.append(i)
                    s_num += 1
                else:
                    f_num += 1
                    arg3.append(i)
            else:
                arg3.append(i)
                f_num += 1
        config.reload()
        try:
            if f_num:
                await message.reply(f'成功移除了{s_num}个订阅: \n{str(arg2)}\n\n'
                                    f'以下有{f_num}个移除失败(名称不符或您不是该订阅的所有者): \n{str(arg3)}')
            else:
                await message.reply(f'成功移除了{s_num}个订阅: \n{str(arg2)}\n\n')
        except RPCError as r:
            print(r)
    except IndexError:
        print("错误")


if __name__ == '__main__':
    pass
