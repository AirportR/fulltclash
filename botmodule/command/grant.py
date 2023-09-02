import os
import signal
import subprocess
import sys
import pyrogram.types
from loguru import logger
from pyrogram import Client
from pyrogram.errors import RPCError
from botmodule.init_bot import admin, config, reloadUser, proxy_subprocess
from utils.cron.utils import message_delete_queue
# from utils.proxys import killclash


async def grant(client: Client, message: pyrogram.types.Message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    try:
        grant_text = "该成员已被加入到授权目标"
        _args = [x for x in str(message.text).strip().split(' ') if x != '']
        if not message.reply_to_message:
            if len(_args) < 2:
                await message.reply("请先用该指令回复一个目标")
            else:
                for i in _args[1:]:
                    config.add_user(int(i))
                logger.info("授权id:" + str(_args[1:]))
                config.reload()
                reloadUser()
                back_msg = await message.reply(f"已授权{len(_args) - 1}个目标: \n{str(_args[1:])}")
                message_delete_queue.put_nowait((back_msg.chat.id, back_msg.id, 10))
        else:
            back_msg = await client.send_message(chat_id=message.chat.id,
                                                 text=grant_text,
                                                 reply_to_message_id=message.reply_to_message.id)
            message_delete_queue.put_nowait((back_msg.chat.id, back_msg.id, 10))
            try:
                grant_id = int(message.reply_to_message.from_user.id)
            except AttributeError:
                grant_id = int(message.reply_to_message.sender_chat.id)
            logger.info("授权id:" + str(grant_id))
            config.add_user(grant_id)
            config.reload()
            reloadUser()

    except RPCError as r:
        print(r)


async def ungrant(_, message: pyrogram.types.Message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    try:
        ungrant_text = "该成员已被移出授权目标"
        _args = [x for x in str(message.text).strip().split(' ') if x != '']
        if message.reply_to_message is None:
            if len(_args) < 2:
                back_msg = await message.reply("请先用该指令回复一个目标")
                message_delete_queue.put_nowait((back_msg.chat.id, back_msg.id, 10))
            else:
                for i in _args[1:]:
                    config.del_user(i)
                config.reload()
                reloadUser()
                logger.info(f"{len(_args) - 1}个目标已取消授权: \n{str(_args[1:])}")
                back_msg = await message.reply(f"{len(_args) - 1}个目标已取消授权: \n{str(_args[1:])}")
                message_delete_queue.put_nowait((back_msg.chat.id, back_msg.id, 10))
        else:
            try:
                ungrant_id = int(message.reply_to_message.from_user.id)
            except AttributeError:
                ungrant_id = int(message.reply_to_message.sender_chat.id)
            config.del_user(ungrant_id)
            config.reload()
            reloadUser()
            back_msg = await message.reply(ungrant_text)
            message_delete_queue.put_nowait((back_msg.chat.id, back_msg.id, 10))

    except RPCError as r:
        logger.error(str(r))


async def user(_, message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    USER_TARGET = config.getuser()
    text = "当前用户有:" + str(set(USER_TARGET)) + "\n共{}个".format(len(USER_TARGET))
    await message.reply(text)


async def restart_or_killme(_, message, kill=False):
    try:
        if isinstance(proxy_subprocess, subprocess.Popen):
            proxy_subprocess.kill()
        if kill:
            await message.reply("再见~")
            os.kill(os.getpid(), signal.SIGINT)
        else:
            await message.reply("开始重启(大约等待五秒)")
            # p = sys.executable
            # 用 main.py 替换当前进程，传递 sys.argv 中的参数
            # 注意：这个函数不会返回，除非出现错误
            os.execlp(sys.executable, "main.py", *sys.argv)
            # os.execl(p, p, *sys.argv)
            sys.exit()
    except RPCError as r:
        logger.error(str(r))
