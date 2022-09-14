import asyncio
import re

from pyrogram.errors import RPCError
from loguru import logger

"""
这个模块主要是一些检查函数，用来验证某个值是否合法。一般是返回布尔值
"""


async def check_callback_master(callback_query, USER_TARGET: list):
    username = None
    try:
        username = str(callback_query.from_user.username)
    except Exception as e:
        logger.info("无法获取该目标获取用户名" + str(e))
    try:
        if username:
            if username not in USER_TARGET:
                if int(callback_query.from_user.id) not in USER_TARGET:
                    await callback_query.answer(f"不要乱动别人的操作哟👻", show_alert=True)
                    return True
                else:
                    return False
            else:
                return False
        else:
            if int(callback_query.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
                await callback_query.answer(f"不要乱动别人的操作哟👻", show_alert=True)
                return True
            else:
                return False

    except AttributeError:
        if int(callback_query.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await callback_query.answer(f"不要乱动别人的操作哟👻", show_alert=True)
            return True


async def check_user(message, USER_TARGET: list):
    """
    检查是否是用，如果是返回真
    :param USER_TARGET: 用户列表
    :param message: 消息对象
    :return: bool
    """
    is_allow_visitor = False
    username = None
    if is_allow_visitor:
        return True
    try:
        try:
            username = str(message.from_user.username)
        except Exception as e:
            logger.info("无法获取该目标获取用户名" + str(e))
        if username:
            if username not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
                if int(message.from_user.id) not in USER_TARGET:
                    m2 = await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
                    await asyncio.sleep(10)
                    await m2.delete()
                    return False
                else:
                    return True
            else:
                return True
        else:
            if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
                m2 = await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
                await asyncio.sleep(10)
                await m2.delete()
                return False
            else:
                return True
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            m2 = await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            await asyncio.sleep(10)
            await m2.delete()
            return False
        else:
            return True


async def check_number(message, test_member, max_num=4):
    """
    检查任务数量
    :param message: 消息对象
    :param test_member: 当前任务数量
    :param max_num: 最大测试数量
    :return: bool
    """
    try:
        if test_member > max_num:
            await message.edit_text("⚠️测试任务数量达到最大，请等待一个任务完成。\n提示：可用 /reload 命令重置此状态")
            return True
        if test_member > 1:
            logger.warning("注意，当前测试任务数量大于1，处于多任务同测状态，可能会对测试结果产生影响")
            await message.reply("⚠️注意，当前测试任务数量大于1，处于多任务同测状态，可能会对测试结果产生影响")
        return False
    except RPCError as r:
        logger.error(r)


async def check_url(message, url):
    """
    检查url
    :param message:
    :param url:
    :return: bool
    """
    if not url:
        try:
            m2 = await message.edit_text("⚠️无效的订阅地址，请检查后重试。")
            await asyncio.sleep(10)
            await m2.delete()
        except RPCError as r:
            logger.error(r)
        return True
    return False


async def check_sub(message, subconfig):
    """
    检查订阅是否获取成功
    :param message:
    :param subconfig:
    :return: bool
    """
    if not subconfig:
        logger.warning("ERROR: 无法获取到订阅文件")
        try:
            m2 = await message.edit_text("ERROR: 无法获取到订阅文件")
            await asyncio.sleep(10)
            await m2.delete()
        except RPCError as r:
            logger.error(r)
        return True
    else:
        return False


async def check_nodes(message, nodenum, args: tuple, max_num=300):
    """
    检查获得的关键信息是否为空，以及节点数量是否大于一定数值
    :param max_num: 最大节点数量
    :param message: 消息对象
    :param nodenum: 节点数量
    :param args: 若干信息
    :return: bool
    """
    if nodenum is None:
        try:
            m2 = await message.edit_text("❌发生错误，请检查订阅文件")
            await asyncio.sleep(10)
            await m2.delete()
        except RPCError as r:
            logger.error(r)
    for arg in args:
        if arg is None:
            try:
                m3 = await message.edit_text("❌发生错误，请检查订阅文件")
                await asyncio.sleep(10)
                await m3.delete()
            except RPCError as r:
                logger.error(r)
            return True
        else:
            pass
    if nodenum > max_num:
        logger.warning("❌节点数量过多！已取消本次测试")
        try:
            m4 = await message.edit_text("❌节点数量过多！已取消本次测试")
            await asyncio.sleep(10)
            await m4.delete()
        except RPCError as r:
            logger.error(r)
        return True
    else:
        return False


async def check_photo(message, back_message, name, nodenum, wtime):
    """
    检查图片是否生成成功
    :param wtime: 消耗时间
    :param nodenum: 节点数量
    :param message: 消息对象
    :param back_message: 消息对象
    :param name: 图片名
    :return:
    """
    try:
        if name is None:
            m2 = await back_message.edit_text("⚠️生成图片失败,可能原因:节点名称包含国旗⚠️\n")
            await asyncio.sleep(10)
            await m2.delete()
        else:
            if nodenum > 25:
                await message.reply_document(r"./results/{}.png".format(name),
                                             caption="⏱️总共耗时: {}s".format(wtime))
            else:
                await message.reply_photo(r"./results/{}.png".format(name),
                                          caption="⏱️总共耗时: {}s".format(wtime))
            await back_message.delete()
            await message.delete()
    except RPCError as r:
        logger.error(r)


def check_rtt(rtt, nodenum: int):
    if rtt == 0:
        new_rtt = [0 for _ in range(nodenum)]
        return new_rtt
    else:
        return rtt


def checkIPv4(ip):
    """
    检查合法v4地址，注意，该函数时间开销很大，谨慎使用
    :param ip:
    :return:
    """
    r = re.compile(r"\b((?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:(?<!\.)\b|\.)){4}")
    _ip = r.match(ip)
    if _ip:
        if _ip.group(0) == ip:
            return True
    return False


async def progress(message, prog, *args):
    """
    进度反馈，bot负责发送给TG前端
    :param message:
    :param prog: 已完成节点数量
    :param send_number:
    :param args:
    :return:
    """
    try:
        nodenum = args[0]
        cal = args[1]
        p_text = "╰(*°▽°*)╯流媒体测试进行中...\n\n当前进度:\n" + "%.2f" % cal + "%     [" + str(prog) + "/" + str(nodenum) + "]"
        try:
            await message.edit_text(p_text)  # 实时反馈进度
        except RPCError as r:
            logger.error(str(r))
    except Exception as e:
        logger.error(str(e))

