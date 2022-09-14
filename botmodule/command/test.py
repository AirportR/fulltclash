import asyncio
import time
from pyrogram.errors import RPCError, FloodWait

import botmodule.init_bot
from libs import cleaner, topotest, streamingtest
from botmodule.init_bot import config

USER_TARGET = botmodule.init_bot.USER_TARGET


def reloadUser():
    global USER_TARGET
    USER_TARGET = config.getuser()
    return USER_TARGET


async def testurl(client, message):
    back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...")
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.core(client, message, back_message=back_message,
                                 start_time=start_time)
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
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def test(client, message):
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
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.core(client, message, back_message=back_message,
                                 start_time=start_time, suburl=suburl)
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
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def analyzeurl(client, message, test_type="all"):
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await topotest.core(client, message, back_message=back_message,
                            start_time=start_time, test_type=test_type)
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
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


async def analyze(client, message, test_type="all"):
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    if len(arg):
        suburl = config.get_sub(subname=arg[0])
    else:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    if suburl is None:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await topotest.core(client, message, back_message=back_message,
                            start_time=start_time, suburl=suburl, test_type=test_type)
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
        await asyncio.sleep(e.value)
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")
