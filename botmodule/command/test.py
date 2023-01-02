import asyncio
import hashlib
import time
from pyrogram.errors import RPCError, FloodWait
from loguru import logger
import botmodule.init_bot
from libs import cleaner, topotest, streamingtest, speedtest, export, check
from botmodule.init_bot import config

USER_TARGET = botmodule.init_bot.USER_TARGET
coresum = botmodule.init_bot.corenum


def reloadUser():
    global USER_TARGET
    USER_TARGET = config.getuser()
    return USER_TARGET


@logger.catch()
async def testurl(_, message):
    back_message = await message.reply("╰(*°▽°*)╯联通性测试进行中...")
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        info = await streamingtest.core(message, back_message=back_message,
                                        start_time=start_time, thread=coresum)
        if info:
            wtime = info.get('wtime', "-1")
            # 生成图片
            stime = export.ExportResult(nodename=None, info=info).exportUnlock()
            # 发送回TG
            await check.check_photo(message, back_message, stime, wtime)
            ma.delsub(subname=start_time)
            ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def test(_, message):
    back_message = await message.reply("╰(*°▽°*)╯联通性测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    if len(arg):
        suburl = config.get_sub(subname=arg[0]).get('url', None)
    else:
        await back_message.edit_text("❌找不到该任务名称，请检查参数是否正确")
        await asyncio.sleep(10)
        await back_message.delete()
        return
    if suburl is None:
        await back_message.edit_text("❌找不到该任务名称，请检查参数是否正确")
        await asyncio.sleep(10)
        await back_message.delete()
        return
    subpwd = config.get_sub(subname=arg[0]).get('password', '')
    pwd = arg[3] if len(arg) > 3 else arg[0]
    if hashlib.sha256(pwd.encode("utf-8")).hexdigest() != subpwd:
        await back_message.edit_text('❌访问密码错误')
        await asyncio.sleep(10)
        await back_message.delete()
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        info = await streamingtest.core(message, back_message=back_message,
                                        start_time=start_time, suburl=suburl, thread=coresum)
        if info:
            wtime = info.get('wtime', "-1")
            # 生成图片
            stime = export.ExportResult(nodename=None, info=info).exportUnlock()
            # 发送回TG
            await check.check_photo(message, back_message, stime, wtime)
            ma.delsub(subname=start_time)
            ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except Exception as e:
        logger.error(e)


@logger.catch()
async def analyzeurl(_, message, test_type="all"):
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        info1, info2 = await topotest.core(message, back_message=back_message,
                                           start_time=start_time, test_type=test_type, thread=coresum)
        if info1:
            if test_type == "inbound":
                wtime = info1.get('wtime', "未知")
                stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
                await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                ma.delsub(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
                return
            if info2:
                # 生成图片
                wtime = info2.get('wtime', "未知")
                clone_info2 = {}
                clone_info2.update(info2)
                img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None, info=clone_info2)
                if test_type == "outbound":
                    stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
                else:
                    stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []), info2,
                                                                                       img2_width=image_width2)
                # 发送回TG
                await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                ma.delsub(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def analyze(_, message, test_type="all"):
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    if len(arg):
        suburl = config.get_sub(subname=arg[0]).get('url', None)
    else:
        await back_message.edit_text("❌找不到该任务名称，请检查参数是否正确")
        await asyncio.sleep(10)
        await back_message.delete()
        return
    if suburl is None:
        await back_message.edit_text("❌❌找不到该任务名称，请检查参数是否正确")
        await asyncio.sleep(10)
        await back_message.delete()
        return
    subpwd = config.get_sub(subname=arg[0]).get('password', '')
    pwd = arg[3] if len(arg) > 3 else arg[0]
    if hashlib.sha256(pwd.encode("utf-8")).hexdigest() != subpwd:
        await back_message.edit_text('❌访问密码错误')
        await asyncio.sleep(10)
        await back_message.delete()
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        info1, info2 = await topotest.core(message, back_message=back_message,
                                           start_time=start_time, suburl=suburl, test_type=test_type, thread=coresum)
        if info1:
            # 生成图片
            if test_type == "inbound":
                wtime = info1.get('wtime', "未知")
                stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
                await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                ma.delsub(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
                return
            if info2:
                wtime = info2.get('wtime', '未知')
                clone_info2 = {}
                clone_info2.update(info2)
                img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None, info=clone_info2)
                if test_type == "outbound":
                    stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
                else:
                    stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []), info2,
                                                                                       img2_width=image_width2)
                # 发送回TG
                await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                ma.delsub(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except RPCError as r:
        logger.error(str(r))
        message.reply(str(r))
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")
    except Exception as e:
        logger.error(e)


@logger.catch()
async def speedurl(_, message):
    back_message = await message.reply("╰(*°▽°*)╯速度测试进行中...")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        info = await speedtest.core(message, back_message=back_message,
                                    start_time=start_time)
        wtime = info.get('wtime', "-1")
        stime = export.ExportSpeed(name=None, info=info).exportImage()
        # 发送回TG
        await check.check_photo(message, back_message, stime, wtime)
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def speed(_, message):
    back_message = await message.reply("╰(*°▽°*)╯速度测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text)).get('url', None)
    del arg[0]
    if len(arg):
        suburl = config.get_sub(subname=arg[0])
    else:
        await back_message.edit_text("❌找不到该任务名称，请检查参数是否正确")
        return
    if suburl is None:
        await back_message.edit_text("❌找不到该任务名称，请检查参数是否正确")
        return
    subpwd = config.get_sub(subname=arg[0]).get('password', '')
    pwd = arg[3] if len(arg) > 3 else arg[0]
    if hashlib.sha256(pwd.encode("utf-8")).hexdigest() != subpwd:
        await back_message.edit_text('❌访问密码错误')
        await asyncio.sleep(10)
        await back_message.delete()
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        info = await speedtest.core(message, back_message=back_message,
                                    start_time=start_time, suburl=suburl)
        if info:
            wtime = info.get('wtime', "-1")
            stime = export.ExportSpeed(name=None, info=info).exportImage()
            # 发送回TG
            await check.check_photo(message, back_message, stime, wtime)
            ma.delsub(subname=start_time)
            ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)
