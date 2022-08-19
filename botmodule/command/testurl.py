import asyncio
import time
from pyrogram.errors import RPCError, FloodWait

import botmodule.init_bot
from libs import cleaner, topotest
import streamingtest
from botmodule.init_bot import config

test_members = 0
USER_TARGET = botmodule.init_bot.USER_TARGET


def reloadUser():
    global USER_TARGET
    USER_TARGET = config.getuser()


async def testurl(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.core(client, message, back_message=back_message, test_members=test_members,
                                 start_time=start_time)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def test(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    suburl = ''
    if len(arg):
        suburl = config.get_sub(subname=arg[0])
    else:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    if suburl is None:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.core(client, message, back_message=back_message, test_members=test_members,
                                 start_time=start_time, suburl=suburl)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def testurl_old(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...(旧版)")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.old_core(client, message, back_message=back_message, test_members=test_members,
                                     start_time=start_time)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def test_old(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    suburl = ''
    if len(arg):
        suburl = config.get_sub(subname=arg[0])
    else:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    if suburl is None:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.old_core(client, message, back_message=back_message, test_members=test_members,
                                     start_time=start_time, suburl=suburl)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def analyzeurl(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await topotest.core(client, message, back_message=back_message, test_members=test_members,
                            start_time=start_time)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def analyze(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    suburl = ''
    if len(arg):
        suburl = config.get_sub(subname=arg[0])
    else:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    if suburl is None:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await topotest.core(client, message, back_message=back_message, test_members=test_members,
                            start_time=start_time, suburl=suburl)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")
