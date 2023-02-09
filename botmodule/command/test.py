import asyncio
import time
from pyrogram.types import Message
from pyrogram.errors import RPCError, FloodWait
from loguru import logger
import botmodule.init_bot
from libs import cleaner, topotest, streamingtest, speedtest, export, check
from botmodule.init_bot import config

USER_TARGET = botmodule.init_bot.USER_TARGET
coresum = botmodule.init_bot.corenum
admin = botmodule.init_bot.admin


def reloadUser():
    global USER_TARGET
    USER_TARGET = config.getuser()
    return USER_TARGET


@logger.catch()
async def testurl(_, message: Message, **kwargs):
    """

    :param _:
    :param message:
    :param kwargs:
    :return:
    """
    back_message = await message.reply("╰(*°▽°*)╯联通性测试进行中...")
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    suburl = kwargs.get('url', None)
    try:
        info = await streamingtest.core(message, back_message=back_message,
                                        start_time=start_time, thread=coresum, suburl=suburl, **kwargs)
        if info:
            wtime = info.get('wtime', "-1")
            # 生成图片
            stime = export.ExportResult(nodename=None, info=info).exportUnlock()
            # 发送回TG
            await check.check_photo(message, back_message, stime, wtime)
            ma.delsub2provider(subname=start_time)
            ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        await message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def test(_, message: Message, **kwargs):
    back_message = await message.reply("╰(*°▽°*)╯联通性测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    try:
        if len(arg):
            subinfo = config.get_sub(subname=arg[0])
            # subpwd = subinfo.get('password', '')
            pwd = arg[3] if len(arg) > 3 else arg[0]
            if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
                suburl = subinfo.get('url', "http://this_is_a.error")
            else:
                return
            start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
            ma = cleaner.ConfigManager('./clash/proxy.yaml')
            info = await streamingtest.core(message, back_message=back_message,
                                            start_time=start_time, suburl=suburl, thread=coresum, **kwargs)
            if info:
                wtime = info.get('wtime', "-1")
                # 生成图片
                stime = export.ExportResult(nodename=None, info=info).exportUnlock()
                # 发送回TG
                await check.check_photo(message, back_message, stime, wtime)
                ma.delsub2provider(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
        else:
            await back_message.edit_text("❌无接受参数，使用方法: /test <订阅名>")
            await asyncio.sleep(10)
            await back_message.delete()
            return
    except RPCError as r:
        logger.error(str(r))
        await message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def analyzeurl(_, message: Message, test_type="all", **kwargs):
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    suburl = kwargs.get('url', None)
    try:
        info1, info2 = await topotest.core(message, back_message,
                                           start_time=start_time, suburl=suburl,
                                           test_type=test_type, thread=coresum, **kwargs)
        if info1:
            if test_type == "inbound":
                wtime = info1.get('wtime', "未知")
                stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
                await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                ma.delsub2provider(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
                return
            if info2:
                # 生成图片
                wtime = info2.get('wtime', "未知")
                clone_info2 = {}
                clone_info2.update(info2)
                img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None,
                                                                                         info=clone_info2)
                if test_type == "outbound":
                    stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
                else:
                    stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []), info2,
                                                                                       img2_width=image_width2)
                # 发送回TG
                await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                ma.delsub2provider(subname=start_time)
                ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        logger.error(str(r))
        await message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def analyze(_, message: Message, test_type="all"):
    back_message = await message.reply("╰(*°▽°*)╯节点链路拓扑测试进行中...")  # 发送提示
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    try:
        if len(arg):
            subinfo = config.get_sub(subname=arg[0])
            pwd = arg[3] if len(arg) > 3 else arg[0]
            if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
                suburl = subinfo.get('url', "http://this_is_a.error")
            else:
                return
            start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
            ma = cleaner.ConfigManager('./clash/proxy.yaml')

            info1, info2 = await topotest.core(message, back_message=back_message,
                                               start_time=start_time, suburl=suburl, test_type=test_type,
                                               thread=coresum)
            if info1:
                # 生成图片
                if test_type == "inbound":
                    wtime = info1.get('wtime', "未知")
                    stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
                    await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                    ma.delsub2provider(subname=start_time)
                    ma.save(savePath='./clash/proxy.yaml')
                    return
                if info2:
                    wtime = info2.get('wtime', '未知')
                    clone_info2 = {}
                    clone_info2.update(info2)
                    img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None,
                                                                                             info=clone_info2)
                    if test_type == "outbound":
                        stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
                    else:
                        stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []), info2,
                                                                                           img2_width=image_width2)
                    # 发送回TG
                    await check.check_photo(message, back_message, 'Topo' + stime, wtime)
                    ma.delsub2provider(subname=start_time)
                    ma.save(savePath='./clash/proxy.yaml')
        else:
            await back_message.edit_text("❌无接受参数，使用方法: /analyze <订阅名>")
            await asyncio.sleep(10)
            await back_message.delete()
            return
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except RPCError as r:
        logger.error(str(r))
        await message.reply(str(r))
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")
    except Exception as e:
        logger.error(e)


@logger.catch()
async def speedurl(_, message: Message, **kwargs):
    back_message = await message.reply("╰(*°▽°*)╯速度测试进行中...", quote=True)  # 发送提示
    if config.nospeed:
        await back_message.edit_text("❌已禁止测速服务")
        await asyncio.sleep(10)
        await back_message.delete(revoke=False)
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    suburl = kwargs.get('url', None)
    try:
        info = await speedtest.core(message, back_message,
                                    start_time=start_time, suburl=suburl, **kwargs)
        ma.delsub2provider(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
        if info:
            wtime = info.get('wtime', "-1")
            stime = export.ExportSpeed(name=None, info=info).exportImage()
            # 发送回TG
            await check.check_photo(message, back_message, stime, wtime)
    except RPCError as r:
        logger.error(str(r))
        await message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)


@logger.catch()
async def speed(_, message: Message):
    back_message = await message.reply("╰(*°▽°*)╯速度测试进行中...", quote=True)  # 发送提示
    if config.nospeed:
        await back_message.edit_text("❌已禁止测速服务")
        await asyncio.sleep(10)
        await back_message.delete(revoke=False)
        return
    arg = cleaner.ArgCleaner().getall(str(message.text))
    del arg[0]
    try:
        if len(arg):
            subinfo = config.get_sub(subname=arg[0])
            pwd = arg[3] if len(arg) > 3 else arg[0]
            if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
                suburl = subinfo.get('url', 'http://this_is_a.error')
            else:
                return
            start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
            ma = cleaner.ConfigManager('./clash/proxy.yaml')
            info = await speedtest.core(message, back_message=back_message,
                                        start_time=start_time, suburl=suburl)
            ma.delsub2provider(subname=start_time)
            ma.save(savePath='./clash/proxy.yaml')
            if info:
                wtime = info.get('wtime', "-1")
                stime = export.ExportSpeed(name=None, info=info).exportImage()
                # 发送回TG
                await check.check_photo(message, back_message, stime, wtime)
        else:
            await back_message.edit_text("❌无接受参数，使用方法: /speed <订阅名>")
            await asyncio.sleep(10)
            await back_message.delete()
            return
    except RPCError as r:
        logger.error(str(r))
        await message.reply(str(r))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(e)
