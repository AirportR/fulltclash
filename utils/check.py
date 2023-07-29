import asyncio
import hashlib
import re
import contextlib

import pyrogram.types
from pyrogram.types import Message
from pyrogram.errors import RPCError, MessageDeleteForbidden
from loguru import logger
from pyrogram.filters import private_filter
from botmodule.init_bot import config
from utils.cron.utils import message_delete_queue

"""
这个模块主要是一些检查函数，用来验证某个值是否合法。一般是返回布尔值
"""


def get_telegram_id_from_message(message: Message):
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


get_id = get_telegram_id_from_message  # 别名


async def is_port_in_use(host='127.0.0.1', port=80):
    """
    检查主机端口是否被占用
    :param host:
    :param port:
    :return:
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        logger.warning(fr"{port} 已被占用，请更换。")
        return True
    except ConnectionRefusedError:
        return False


async def check_port(start: int, end: int):
    tasks = []
    for i in range(start, end):
        tasks.append(asyncio.create_task(is_port_in_use(port=i)))
    results = await asyncio.gather(*tasks)
    return True in results


async def check_share(message, shareid: list):
    """
    检查是否在分享名单中,若在返回真，否则返回假。
    :param message: 消息对象
    :param shareid: 共享名单
    :return: [true, false]
    """
    try:
        ID = message.from_user.id
    except AttributeError:
        ID = message.sender_chat.id
    return str(ID) in shareid


async def check_callback_master(callback_query, USER_TARGET=None, strict: bool = False):
    """

    :param callback_query: 回调数据结构
    :param USER_TARGET: 用户名单
    :param strict: 严格模式，如果为true,则每个任务的内联键盘只有任务的发起者能操作，若为false，则所有用户都能操作内联键盘。
    :return:
    """
    master = []
    if USER_TARGET and not strict:
        master.extend(USER_TARGET)
    try:
        master.append(callback_query.message.reply_to_message.from_user.id)  # 发起测试任务的用户id
        if int(callback_query.from_user.id) not in master:
            await callback_query.answer("不要乱动别人的操作哟👻", show_alert=True)
            return True
        else:
            return False

    except AttributeError:
        master.append(callback_query.message.reply_to_message.sender_chat.id)
        if int(callback_query.from_user.id) in master:  # 如果不在USER_TARGET名单是不会有权限的
            return False
        if str(callback_query.from_user.username) in master:
            return False
        else:
            await callback_query.answer(f"不要乱动别人的操作哟👻", show_alert=True)
            return True
    except Exception as e:
        logger.error(str(e))
        return True


async def check_node(backmsg: Message, core, nodenum: int) -> bool:
    """
    检查节点数量是否超出限制
    """
    flag = False
    if nodenum == 0:
        await backmsg.edit_text("❌节点数量为空，请检查你的过滤器或者订阅格式是否正确")
        flag = True
    if type(core).__name__ == 'SpeedCore':
        if config.speednodes() < nodenum:
            await backmsg.edit_text("⚠️节点数量超出限制，已取消测试。")
            flag = True
    if flag:
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return True
    return False


async def check_subowner(message, back_message, subinfo: dict, admin: list, password: str):
    """
    检查是否是订阅的拥有者
    :param password:
    :param admin: 管理员列表名单
    :param back_message: 消息对象
    :param message: 消息对象
    :param subinfo: config.get_sub()返回的字典
    :return: True|False
    """
    try:
        ID = message.from_user.id
    except AttributeError:
        ID = message.sender_chat.id
    if not subinfo:
        await back_message.edit_text("❌找不到该任务名称，请检查参数是否正确。")
        message_delete_queue.put_nowait([back_message.chat.id, back_message.id, 10])
        # await back_message.delete()
        return False
    subpwd = subinfo.get('password', '')
    subowner = subinfo.get('owner', '')
    subuser = subinfo.get('share', [])
    if await check_user(message, admin, isalert=False):
        # 管理员至高权限
        return True
    if (subowner and subowner == ID) or await check_share(message, subuser):
        if hashlib.sha256(password.encode("utf-8")).hexdigest() == subpwd:
            return True
        else:
            await back_message.edit_text('❌访问密码错误')
            await asyncio.sleep(10)
            await back_message.delete()
            return False
    else:
        await back_message.edit_text("❌身份ID不匹配，您无权使用该订阅。")
        await asyncio.sleep(10)
        await back_message.delete()
        return False


async def check_user(message, USER_TARGET: list, isalert=True):
    """
    检查是否是用户，如果是返回真
    :param isalert: 是否发送反馈给bot前端
    :param USER_TARGET: 用户列表
    :param message: 消息对象
    :return: bool
    """
    await asyncio.sleep(0.1)
    is_allow_visitor = False
    username = None
    if is_allow_visitor:
        return True
    try:
        try:
            username = str(message.from_user.username)
        except AttributeError:
            pass
            # logger.info("无法获取该目标获取用户名" + str(e))
        if username:
            if username not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
                if int(message.from_user.id) not in USER_TARGET:
                    if isalert:
                        m2 = await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
                        message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
                        # await asyncio.sleep(10)
                        # await m2.delete()
                    return False
                else:
                    return True
            else:
                return True
        else:
            if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
                if isalert:
                    m2 = await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
                    message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
                    # await asyncio.sleep(10)
                    # await m2.delete()
                return False
            else:
                return True
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            if isalert:
                m2 = await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
                message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
                # await asyncio.sleep(10)
                # await m2.delete()
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
            message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
            # await asyncio.sleep(10)
            # await m2.delete()
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
            message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
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
    if not nodenum:
        try:
            m2 = await message.edit_text("❌发生错误，请检查订阅文件")
            message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
            return True
        except RPCError as r:
            logger.error(r)
    for arg in args:
        if arg is None:
            try:
                m3 = await message.edit_text("❌发生错误，请检查订阅文件")
                message_delete_queue.put_nowait((m3.chat.id, m3.id, 10))
            except RPCError as r:
                logger.error(r)
            return True
        else:
            pass
    if nodenum > max_num:
        logger.warning("❌节点数量过多！已取消本次测试")
        try:
            m4 = await message.edit_text("❌节点数量过多！已取消本次测试")
            message_delete_queue.put_nowait((m4.chat.id, m4.id, 10))
        except RPCError as r:
            logger.error(r)
        return True
    else:
        return False


async def check_speed_nodes(message, nodenum, args: tuple, speed_max_num=config.speednodes()):
    """
    检查获得的关键信息是否为空，以及节点数量是否大于一定数值
    :param speed_max_num: 最大节点数量
    :param message: 消息对象
    :param nodenum: 节点数量
    :param args: 若干信息
    :return: bool
    """
    if not nodenum:
        try:
            m2 = await message.edit_text("❌发生错误，请检查订阅文件")
            message_delete_queue.put_nowait((m2.chat.id, m2.id, 10))
            return True
        except RPCError as r:
            logger.error(r)
    for arg in args:
        if arg is None:
            try:
                m3 = await message.edit_text("❌发生错误，请检查订阅文件")
                message_delete_queue.put_nowait((m3.chat.id, m3.id, 10))
            except RPCError as r:
                logger.error(r)
            return True
        else:
            pass
    if nodenum > speed_max_num:
        logger.warning(f"❌节点数量超过了{speed_max_num}个的限制！已取消本次测试")
        try:
            m4 = await message.edit_text(f"❌节点数量超过了{speed_max_num}个的限制！已取消本次测试")
            message_delete_queue.put_nowait((m4.chat.id, m4.id, 10))
        except RPCError as r:
            logger.error(r)
        return True
    else:
        return False


async def check_photo(message: pyrogram.types.Message, back_message, name, wtime, size: tuple = None):
    """
    检查图片是否生成成功
    :param wtime: 消耗时间
    :param message: 消息对象
    :param back_message: 消息对象
    :param name: 图片名
    :param size: 图片大小
    :return:
    """
    try:
        if name == '' or name is None:
            await back_message.edit_text("⚠️生成图片失败,可能原因: 节点过多/网络不稳定")
        else:
            x, y = size if size is not None else (0, 0)
            if x > 0 and y > 0:
                if x < 2500 and y < 3500:
                    await message.reply_photo(fr'./results/{name}.png', caption=f"⏱️总共耗时: {wtime}s")
                else:
                    await message.reply_document(fr"./results/{name}.png", caption=f"⏱️总共耗时: {wtime}s")
            else:
                await message.reply_document(fr"./results/{name}.png", caption=f"⏱️总共耗时: {wtime}s")
            await back_message.delete()
            if not await private_filter(name, name, message):
                with contextlib.suppress(MessageDeleteForbidden):
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
    r = re.compile(r"\b((?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?:(?<!\.)\b|\.)){4}")
    _ip = r.match(ip)
    if _ip:
        if _ip.group(0) == ip:
            return True
    return False


# 已废弃
async def progress(message, prog, *args):
    """
    进度反馈，bot负责发送给TG前端
    :param message:
    :param prog: 已完成节点数量
    :param args:
    :return:
    """
    try:
        nodenum = args[0]
        cal = args[1]
        try:
            subtext = args[2]
        except IndexError:
            subtext = ""
        p_text = f"{subtext}\n\n当前进度:\n" + "%.2f" % cal + "%     [" + str(prog) + "/" + str(nodenum) + "]"
        try:
            await message.edit_text(p_text)  # 实时反馈进度
        except RPCError as r:
            logger.error(str(r))
    except Exception as e:
        logger.error(str(e))
