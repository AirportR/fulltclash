import asyncio
from concurrent.futures import ThreadPoolExecutor

from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
from pyrogram.errors import RPCError
from loguru import logger
import botmodule.init_bot
from libs import cleaner, export, check, collector
from botmodule.init_bot import config
from backend import SpeedCore, ScriptCore, TopoCore
from cron import message_delete_queue

USER_TARGET = botmodule.init_bot.USER_TARGET
coresum = botmodule.init_bot.corenum
admin = botmodule.init_bot.admin


def reloadUser():
    global USER_TARGET
    USER_TARGET = config.getuser()
    return USER_TARGET


def select_core(put_type: str, message: Message):
    """
    1 为速度核心， 2为拓扑核心， 3为解锁脚本测试核心
    """
    if put_type.startswith("speed"):
        IKM = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👋中止测速", callback_data='stop')],
            ]
        )
        return SpeedCore(message.chat.id, message.id, IKM)
    elif put_type.startswith("analyze") or put_type.startswith("topo") or put_type.startswith("inbound") or \
            put_type.startswith("outbound"):
        return TopoCore(message.chat.id, message.id)
    elif put_type.startswith("test"):
        return ScriptCore(message.chat.id, message.id)
    else:
        raise TypeError("Unknown test type, please input again.\n未知的测试类型，请重新输入!")


@logger.catch()
async def select_export(msg: Message, backmsg: Message, put_type: str, info: dict):
    try:
        if put_type.startswith("speed"):
            if info:
                wtime = info.get('wtime', "-1")
                # stime = export.ExportSpeed(name=None, info=info).exportImage()
                ex = export.ExportSpeed(name=None, info=info)
                with ThreadPoolExecutor() as pool:
                    loop = asyncio.get_running_loop()
                    stime = await loop.run_in_executor(
                        pool, ex.exportImage)
                # 发送回TG
                await msg.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
                await check.check_photo(msg, backmsg, stime, wtime)
        elif put_type.startswith("analyze") or put_type.startswith("topo") or put_type.startswith("inbound") \
                or put_type.startswith("outbound"):
            info1 = info.get('inbound', {})
            info2 = info.get('outbound', {})
            if info1:
                if put_type.startswith("inbound"):
                    wtime = info1.get('wtime', "未知")
                    # stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
                    ex = export.ExportTopo(name=None, info=info1)
                    with ThreadPoolExecutor() as pool:
                        loop = asyncio.get_running_loop()
                        stime = await loop.run_in_executor(
                            pool, ex.exportTopoInbound)
                    await check.check_photo(msg, backmsg, 'Topo' + stime, wtime)
                    return
                if info2:
                    # 生成图片
                    wtime = info2.get('wtime', "未知")
                    clone_info2 = {}
                    clone_info2.update(info2)
                    img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None,
                                                                                             info=clone_info2)
                    if put_type.startswith("outbound"):
                        # stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
                        ex = export.ExportTopo(name=None, info=info2)
                        with ThreadPoolExecutor() as pool:
                            loop = asyncio.get_running_loop()
                            stime = await loop.run_in_executor(
                                pool, ex.exportTopoOutbound)
                    else:
                        stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []), info2,
                                                                                           img2_width=image_width2)
                    # 发送回TG
                    await msg.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
                    await check.check_photo(msg, backmsg, 'Topo' + stime, wtime)
        elif put_type.startswith("test"):
            if info:
                wtime = info.get('wtime', "-1")
                # 生成图片
                ex = export.ExportResult(nodename=None, info=info)
                with ThreadPoolExecutor() as pool:
                    loop = asyncio.get_running_loop()
                    stime = await loop.run_in_executor(
                        pool, ex.exportUnlock)
                # 发送回TG
                await msg.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
                await check.check_photo(msg, backmsg, stime, wtime)
        else:
            raise TypeError("Unknown export type, please input again.\n未知的绘图类型，请重新输入!")
    except RPCError as r:
        logger.error(str(r))
    except Exception as e:
        logger.error(str(e))


@logger.catch()
async def process(_, message: Message, **kwargs):
    back_message = await message.reply("⏳任务接收成功，测试进行中...")
    tgtext = str(message.text)
    tgargs = cleaner.ArgCleaner().getall(tgtext)
    suburl = cleaner.geturl(tgtext) if kwargs.get('url', None) is None else kwargs.get('url', None)
    put_type = kwargs.get('put_type', '') if kwargs.get('put_type', '') \
        else message.command[0] if message.command is not None else tgargs[0][1:]
    print("测试指令", put_type)
    if not put_type:
        await message.reply('❌不支持的测试任务类型')
        message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
        return
    core = select_core(put_type, back_message)
    include_text = tgargs[2] if len(tgargs) > 2 else ''
    exclude_text = tgargs[3] if len(tgargs) > 3 else ''
    include_text = kwargs.get('include_text', '') if kwargs.get('include_text', '') else include_text
    exclude_text = kwargs.get('exclude_text', '') if kwargs.get('exclude_text', '') else exclude_text
    core.setfilter(include_text, exclude_text)
    if put_type.endswith("url"):
        if suburl is None:
            await back_message.edit_text("❌参数错误，请重新输入")
            message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
            return
        sub = collector.SubCollector(suburl=suburl, include=include_text, exclude=exclude_text)
        subconfig = await sub.getSubConfig(inmemory=True)
        if isinstance(subconfig, bool):
            logger.warning("获取订阅失败!")
            await back_message.edit_text("❌获取订阅失败！")
            message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
            return
        proxyinfo = cleaner.ClashCleaner(':memory:', subconfig).getProxies()
        info = await core.core(proxyinfo, **kwargs)
        await select_export(message, back_message, put_type, info)
    else:
        subinfo = config.get_sub(subname=tgargs[1])
        pwd = tgargs[4] if len(tgargs) > 4 else tgargs[1]
        if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
            suburl = subinfo.get('url', "http://this_is_a.error")
        else:
            return
        sub = collector.SubCollector(suburl=suburl, include=include_text, exclude=exclude_text)
        subconfig = await sub.getSubConfig(inmemory=True)
        if isinstance(subconfig, bool):
            logger.warning("获取订阅失败!")
            await back_message.edit_text("❌获取订阅失败！")
            message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
            return
        proxyinfo = cleaner.ClashCleaner(':memory:', subconfig).getProxies()
        info = await core.core(proxyinfo, **kwargs)
        await select_export(message, back_message, put_type, info)


# @logger.catch()
# async def testurl(_, message: Message, **kwargs):
#     """
#
#     :param _:
#     :param message:
#     :param kwargs:
#     :return:
#     """
#     scripttext = config.config.get('bot', {}).get('scripttext', "⏳联通性测试进行中...")
#     back_message = await message.reply(scripttext)
#     start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
#     ma = cleaner.ConfigManager('./clash/proxy.yaml')
#     suburl = kwargs.get('url', None)
#     try:
#         info = await streamingtest.core(message, back_message=back_message,
#                                         start_time=start_time, thread=coresum, suburl=suburl, **kwargs)
#         if info:
#             wtime = info.get('wtime', "-1")
#             # 生成图片
#             ex = export.ExportResult(nodename=None, info=info)
#             with ThreadPoolExecutor() as pool:
#                 loop = asyncio.get_running_loop()
#                 stime = await loop.run_in_executor(
#                     pool, ex.exportUnlock)
#             # 发送回TG
#             await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#             await check.check_photo(message, back_message, stime, wtime)
#             ma.delsub2provider(subname=start_time)
#             ma.save(savePath='./clash/proxy.yaml')
#     except RPCError as r:
#         logger.error(str(r))
#         await message.reply(str(r))
#     except FloodWait as e:
#         await asyncio.sleep(e.value)
#     except Exception as e:
#         logger.error(e)
#
#
# @logger.catch()
# async def test(_, message: Message, **kwargs):
#     scripttext = config.config.get('bot', {}).get('scripttext', "⏳联通性测试进行中...")
#     back_message = await message.reply(scripttext)  # 发送提示
#     arg = cleaner.ArgCleaner().getall(str(message.text))
#     del arg[0]
#     try:
#         if len(arg):
#             subinfo = config.get_sub(subname=arg[0])
#             # subpwd = subinfo.get('password', '')
#             pwd = arg[3] if len(arg) > 3 else arg[0]
#             if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
#                 suburl = subinfo.get('url', "http://this_is_a.error")
#             else:
#                 return
#             start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
#             ma = cleaner.ConfigManager('./clash/proxy.yaml')
#             info = await streamingtest.newcore(message, back_message=back_message,
#                                                start_time=start_time, suburl=suburl, thread=coresum, **kwargs)
#             if info:
#                 wtime = info.get('wtime', "-1")
#                 # 生成图片
#                 ex = export.ExportResult(nodename=None, info=info)
#                 with ThreadPoolExecutor() as pool:
#                     loop = asyncio.get_running_loop()
#                     stime = await loop.run_in_executor(
#                         pool, ex.exportUnlock)
#                 # 发送回TG
#                 await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#                 await check.check_photo(message, back_message, stime, wtime)
#                 ma.delsub2provider(subname=start_time)
#                 ma.save(savePath='./clash/proxy.yaml')
#         else:
#             await back_message.edit_text("❌无接受参数，使用方法: /test <订阅名>")
#             await asyncio.sleep(10)
#             await back_message.delete()
#             return
#     except RPCError as r:
#         logger.error(str(r))
#         await message.reply(str(r))
#     except FloodWait as e:
#         await asyncio.sleep(e.value)
#     except Exception as e:
#         logger.error(e)
#
#
# @logger.catch()
# async def analyzeurl(_, message: Message, test_type="all", **kwargs):
#     analyzetext = config.config.get('bot', {}).get('analyzetext', "⏳节点拓扑分析测试进行中...")
#     back_message = await message.reply(analyzetext)  # 发送提示
#     start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
#     ma = cleaner.ConfigManager('./clash/proxy.yaml')
#     suburl = kwargs.get('url', None)
#     try:
#         info1, info2 = await topotest.core(message, back_message,
#                                            start_time=start_time, suburl=suburl,
#                                            test_type=test_type, thread=coresum, **kwargs)
#         if info1:
#             if test_type == "inbound":
#                 wtime = info1.get('wtime', "未知")
#                 # stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
#                 ex = export.ExportTopo(name=None, info=info1)
#                 with ThreadPoolExecutor() as pool:
#                     loop = asyncio.get_running_loop()
#                     stime = await loop.run_in_executor(
#                         pool, ex.exportTopoInbound)
#                 await check.check_photo(message, back_message, 'Topo' + stime, wtime)
#                 ma.delsub2provider(subname=start_time)
#                 ma.save(savePath='./clash/proxy.yaml')
#                 return
#             if info2:
#                 # 生成图片
#                 wtime = info2.get('wtime', "未知")
#                 clone_info2 = {}
#                 clone_info2.update(info2)
#                 img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None,
#                                                                                          info=clone_info2)
#                 if test_type == "outbound":
#                     # stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
#                     ex = export.ExportTopo(name=None, info=info2)
#                     with ThreadPoolExecutor() as pool:
#                         loop = asyncio.get_running_loop()
#                         stime = await loop.run_in_executor(
#                             pool, ex.exportTopoOutbound)
#                 else:
#                     stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []), info2,
#                                                                                        img2_width=image_width2)
#                 # 发送回TG
#                 await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#                 await check.check_photo(message, back_message, 'Topo' + stime, wtime)
#                 ma.delsub2provider(subname=start_time)
#                 ma.save(savePath='./clash/proxy.yaml')
#     except RPCError as r:
#         logger.error(str(r))
#         await message.reply(str(r))
#     except FloodWait as e:
#         await asyncio.sleep(e.value)
#     except Exception as e:
#         logger.error(e)
#
#
# @logger.catch()
# async def analyze(_, message: Message, test_type="all"):
#     analyzetext = config.config.get('bot', {}).get('analyzetext', "⏳节点拓扑分析测试进行中...")
#     back_message = await message.reply(analyzetext)  # 发送提示
#     arg = cleaner.ArgCleaner().getall(str(message.text))
#     del arg[0]
#     try:
#         if len(arg):
#             subinfo = config.get_sub(subname=arg[0])
#             pwd = arg[3] if len(arg) > 3 else arg[0]
#             if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
#                 suburl = subinfo.get('url', "http://this_is_a.error")
#             else:
#                 return
#             start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
#             ma = cleaner.ConfigManager('./clash/proxy.yaml')
#
#             info1, info2 = await topotest.core(message, back_message=back_message,
#                                                start_time=start_time, suburl=suburl, test_type=test_type,
#                                                thread=coresum)
#             if info1:
#                 # 生成图片
#                 if test_type == "inbound":
#                     wtime = info1.get('wtime', "未知")
#                     # stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
#                     ex = export.ExportTopo(name=None, info=info1)
#                     with ThreadPoolExecutor() as pool:
#                         loop = asyncio.get_running_loop()
#                         stime = await loop.run_in_executor(
#                             pool, ex.exportTopoInbound)
#                     await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#                     await check.check_photo(message, back_message, 'Topo' + stime, wtime)
#                     ma.delsub2provider(subname=start_time)
#                     ma.save(savePath='./clash/proxy.yaml')
#                     return
#                 if info2:
#                     wtime = info2.get('wtime', '未知')
#                     clone_info2 = {}
#                     clone_info2.update(info2)
#                     img_outbound, yug, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None,
#                                                                                              info=clone_info2)
#                     if test_type == "outbound":
#                         # stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
#                         ex = export.ExportTopo(name=None, info=info2)
#                         with ThreadPoolExecutor() as pool:
#                             loop = asyncio.get_running_loop()
#                             stime = await loop.run_in_executor(
#                                 pool, ex.exportTopoOutbound)
#                     else:
#                         stime = export.ExportTopo(name=None, info=info1).exportTopoInbound(info2.get('节点名称', []),
#                         info2, img2_width=image_width2)
#                     # 发送回TG
#                     await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#                     await check.check_photo(message, back_message, 'Topo' + stime, wtime)
#                     ma.delsub2provider(subname=start_time)
#                     ma.save(savePath='./clash/proxy.yaml')
#         else:
#             await back_message.edit_text("❌无接受参数，使用方法: /analyze <订阅名>")
#             await asyncio.sleep(10)
#             await back_message.delete()
#             return
#     except FloodWait as e:
#         await asyncio.sleep(e.value)
#     except RPCError as r:
#         logger.error(str(r))
#         await message.reply(str(r))
#     except KeyboardInterrupt:
#         await back_message.edit_text("程序已被强行中止")
#     except Exception as e:
#         logger.error(e)
#
#
# @logger.catch()
# async def speedurl(_, message: Message, **kwargs):
#     speedtext = config.config.get('bot', {}).get('speedtext', "⏳速度测试进行中...")
#     back_message = await message.reply(speedtext, quote=True)  # 发送提示
#     start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
#     ma = cleaner.ConfigManager('./clash/proxy.yaml')
#     suburl = kwargs.get('url', None)
#     if config.nospeed:
#         await back_message.edit_text("❌已禁止测速服务")
#         await asyncio.sleep(10)
#         await back_message.delete(revoke=False)
#         return
#     try:
#         info = await speedtest.core(message, back_message,
#                                     start_time=start_time, suburl=suburl, **kwargs)
#         ma.delsub2provider(subname=start_time)
#         ma.save(savePath='./clash/proxy.yaml')
#         if info:
#             wtime = info.get('wtime', "-1")
#             # stime = export.ExportSpeed(name=None, info=info).exportImage()
#             ex = export.ExportSpeed(name=None, info=info)
#             with ThreadPoolExecutor() as pool:
#                 loop = asyncio.get_running_loop()
#                 stime = await loop.run_in_executor(
#                     pool, ex.exportImage)
#             # 发送回TG
#             await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#             await check.check_photo(message, back_message, stime, wtime)
#     except RPCError as r:
#         logger.error(str(r))
#         await message.reply(str(r))
#     except FloodWait as e:
#         await asyncio.sleep(e.value)
#     except Exception as e:
#         logger.error(e)
#
#
# @logger.catch()
# async def speed(_, message: Message):
#     speedtext = config.config.get('bot', {}).get('speedtext', "⏳速度测试进行中...")
#     back_message = await message.reply(speedtext, quote=True)  # 发送提示
#     arg = cleaner.ArgCleaner().getall(str(message.text))
#     del arg[0]
#     if config.nospeed:
#         await back_message.edit_text("❌已禁止测速服务")
#         await asyncio.sleep(10)
#         await back_message.delete(revoke=False)
#         return
#     try:
#         if len(arg):
#             subinfo = config.get_sub(subname=arg[0])
#             pwd = arg[3] if len(arg) > 3 else arg[0]
#             if await check.check_subowner(message, back_message, subinfo=subinfo, admin=admin, password=pwd):
#                 suburl = subinfo.get('url', 'http://this_is_a.error')
#             else:
#                 return
#             start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
#             ma = cleaner.ConfigManager('./clash/proxy.yaml')
#             info = await speedtest.core(message, back_message=back_message,
#                                         start_time=start_time, suburl=suburl)
#             ma.delsub2provider(subname=start_time)
#             ma.save(savePath='./clash/proxy.yaml')
#             if info:
#                 wtime = info.get('wtime', "-1")
#                 # stime = export.ExportSpeed(name=None, info=info).exportImage()
#                 ex = export.ExportSpeed(name=None, info=info)
#                 with ThreadPoolExecutor() as pool:
#                     loop = asyncio.get_running_loop()
#                     stime = await loop.run_in_executor(
#                         pool, ex.exportImage)
#                 # 发送回TG
#                 await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
#                 await check.check_photo(message, back_message, stime, wtime)
#         else:
#             await back_message.edit_text("❌无接受参数，使用方法: /speed <订阅名>")
#             await asyncio.sleep(10)
#             await back_message.delete()
#             return
#     except RPCError as r:
#         logger.error(str(r))
#         await message.reply(str(r))
#     except FloodWait as e:
#         await asyncio.sleep(e.value)
#     except Exception as e:
#         logger.error(e)
