import os
import sys
import pyrogram.types
from loguru import logger
from pyrogram import Client
from pyrogram.errors import RPCError
from botmodule.init_bot import admin, config, reloadUser
from botmodule.command.test import reloadUser as r2
from botmodule.utils import message_delete_queue


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

        if not message.reply_to_message:
            await message.reply("请先用该指令回复一个目标")
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
            r2()
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
        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            try:
                ungrant_id = int(message.reply_to_message.from_user.id)
            except AttributeError:
                ungrant_id = int(message.reply_to_message.sender_chat.id)
            config.del_user(ungrant_id)
            config.reload()
            r2()
            reloadUser()
            await message.reply(ungrant_text)

    except RPCError as r:
        logger.error(str(r))


async def user(_, message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    USER_TARGET = config.getuser()
    text = "当前用户有:" + str(set(USER_TARGET)) + "\n共{}个".format(len(USER_TARGET))
    await message.reply(text)


async def restart(_, message):
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
        await message.reply("开始重启")
        p = sys.executable
        os.execl(p, p, *sys.argv)
        sys.exit()
    except RPCError as r:
        logger.error(str(r))
