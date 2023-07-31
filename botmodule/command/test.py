import asyncio
import io
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Union

from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import enums, Client
from pyrogram.errors import RPCError
from loguru import logger

from botmodule.init_bot import config, admin
from utils.backend import SpeedCore, ScriptCore, TopoCore, break_speed
from utils.safe import cipher_chacha20, sha256_32bytes
from utils import message_delete_queue, check, cleaner, collector, export

SPEEDTESTIKM = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("👋中止测速", callback_data='stop')],
    ]
)
SPEEDTEST_LIST = []
BOT_MESSAGE_LIST = {}


async def slave_progress(progress, nodenum, botmsg: Message, corenum, master_id, master_chat_id, master_msg_id, name):
    progresstext = f"${corenum}:{progress}:{nodenum}"
    await botmsg.edit_text(f'/relay {master_id} edit {master_chat_id} {master_msg_id} {progresstext} "{name}"')


sp = slave_progress


def convert_core_index(corestr: str) -> int:
    if isinstance(corestr, str):
        if corestr.startswith("speed"):
            return 1
        elif corestr.startswith("analyze") or corestr.startswith("topo"):
            return 2
        elif corestr.startswith("test"):
            return 3
        else:
            return 0
    return 0


async def select_core_slave(coreindex: Union[str, int], botmsg: Message, putinfo: dict):
    edit_chat_id = putinfo.get('edit-chat-id', None)
    edit_msg_id = putinfo.get('edit-message-id', None)
    masterid = putinfo.get('master', {}).get('id', 1)
    slavename = putinfo.get('slave', {}).get('comment', '未知')
    if coreindex == 1:
        if config.nospeed:
            msgtext = f"/relay {masterid} edit {edit_chat_id} {edit_msg_id} ❌此后端禁止测速服务"
            await botmsg.edit_text(msgtext)
            logger.info("由于此后端禁止测速服务，已取消任务")
            return None
        return SpeedCore(botmsg.chat.id, botmsg.id, SPEEDTESTIKM,
                         (sp, (botmsg, 1, masterid, edit_chat_id, edit_msg_id, slavename)))
    elif coreindex == 2:
        return TopoCore(botmsg.chat.id, botmsg.id, (sp, (botmsg, 2, masterid, edit_chat_id, edit_msg_id, slavename)))
    elif coreindex == 3:
        return ScriptCore(botmsg.chat.id, botmsg.id, (sp, (botmsg, 3, masterid, edit_chat_id, edit_msg_id, slavename)))
    else:
        logger.warning("未知的测试核心类型")
        return None


async def select_core(put_type: str, message: Message, **kwargs):
    """
    1 为速度核心， 2为拓扑核心， 3为解锁脚本测试核心
    """
    index = kwargs.get('coreindex', 0)
    if put_type.startswith("speed") or index == 1:
        if config.nospeed:
            backmsg = await message.reply("❌已禁止测速服务")
            message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
            return None
        IKM = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👋中止测速", callback_data='stop')],
            ]
        )
        return SpeedCore(message.chat.id, message.id, IKM)
    elif put_type.startswith("analyze") or put_type.startswith("topo") or put_type.startswith("inbound") or \
            put_type.startswith("outbound") or index == 2:
        return TopoCore(message.chat.id, message.id)
    elif put_type.startswith("test") or index == 3:
        return ScriptCore(message.chat.id, message.id)
    else:
        raise TypeError("Unknown test type, please input again.\n未知的测试类型，请重新输入!")


@logger.catch()
async def select_export(msg: Message, backmsg: Message, put_type: str, info: dict, **kwargs):
    try:
        if put_type.startswith("speed") or kwargs.get('coreindex', -1) == 1:
            if info:
                wtime = info.get('wtime', "-1")
                # stime = export.ExportSpeed(name=None, info=info).exportImage()
                ex = export.ExportSpeed(name=None, info=info)
                with ThreadPoolExecutor() as pool:
                    loop = asyncio.get_running_loop()
                    stime, img_size = await loop.run_in_executor(
                        pool, ex.exportImage)
                # 发送回TG
                await msg.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
                await check.check_photo(msg, backmsg, stime, wtime, img_size)
        elif put_type.startswith("analyze") or put_type.startswith("topo") or put_type.startswith("inbound") \
                or put_type.startswith("outbound") or kwargs.get('coreindex', -1) == 2:
            info1 = info.get('inbound', {})
            info2 = info.get('outbound', {})
            info2['slave'] = info.get('slave', {})
            if info1:
                if put_type.startswith("inbound"):
                    wtime = info1.get('wtime', "未知")
                    # stime = export.ExportTopo(name=None, info=info1).exportTopoInbound()
                    ex = export.ExportTopo(name=None, info=info1)
                    with ThreadPoolExecutor() as pool:
                        loop = asyncio.get_running_loop()
                        stime, img_size = await loop.run_in_executor(
                            pool, ex.exportTopoInbound)
                    await check.check_photo(msg, backmsg, 'Topo' + stime, wtime, img_size)
                    return
                if info2:
                    # 生成图片
                    wtime = info2.get('wtime', "未知")
                    clone_info2 = {}
                    clone_info2.update(info2)
                    _, __, image_width2 = export.ExportTopo().exportTopoOutbound(nodename=None,
                                                                                 info=clone_info2)
                    if put_type.startswith("outbound"):
                        # stime = export.ExportTopo(name=None, info=info2).exportTopoOutbound()
                        ex = export.ExportTopo(name=None, info=info2)
                        with ThreadPoolExecutor() as pool:
                            loop = asyncio.get_running_loop()
                            stime, h, w = await loop.run_in_executor(
                                pool, ex.exportTopoOutbound)
                            img_size = (w, h)
                    else:
                        stime, img_size = export.ExportTopo(name=None, info=info1).exportTopoInbound(
                            info2.get('节点名称', []), info2,
                            img2_width=image_width2)
                    # 发送回TG
                    await msg.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
                    await check.check_photo(msg, backmsg, 'Topo' + stime, wtime, img_size)
        elif put_type.startswith("test") or kwargs.get('coreindex', -1) == 3:
            if info:
                wtime = info.get('wtime', "-1")
                # 生成图片
                file_name, img_size = export.ExportCommon(info.pop('节点名称', []), info).draw()
                # 发送回TG
                await msg.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
                await check.check_photo(msg, backmsg, file_name, wtime, img_size)
        else:
            raise TypeError("Unknown export type, please input again.\n未知的绘图类型，请重新输入!")
    except RPCError as r:
        logger.error(str(r))
    except Exception as e:
        logger.error(str(e))


@logger.catch()
async def process(app: Client, message: Message, **kwargs):
    back_message = await message.reply("⏳任务接收成功，测试进行中...", quote=True)
    tgtext = str(message.text)
    tgargs = cleaner.ArgCleaner().getall(tgtext)
    suburl = cleaner.geturl(tgtext) if kwargs.get('url', None) is None else kwargs.get('url', None)
    put_type = kwargs.pop('put_type', '') if kwargs.get('put_type', '') else tgargs[0].split("@")[0]
    logger.info("测试指令: " + str(put_type))
    if not put_type:
        await message.reply('❌不支持的测试任务类型')
        message_delete_queue.put_nowait((back_message.chat.id, back_message.id, 10))
        return
    core = await select_core(put_type, back_message, **kwargs)
    if core is None:
        logger.warning("未找到测试逻辑核心")
        return
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
    pre_cl = cleaner.ClashCleaner(':memory:', subconfig)
    pre_cl.node_filter(include_text, exclude_text)
    proxynum = pre_cl.nodesCount()
    if await check.check_node(back_message, core, proxynum):
        return
    proxyinfo = pre_cl.getProxies()
    info = await put_slave_task(app, message, proxyinfo, core=core, backmsg=back_message, **kwargs)
    if isinstance(info, dict):
        await select_export(message, back_message, put_type, info, **kwargs)


async def put_slave_task(app: Client, message: Message, proxyinfo: list, **kwargs):
    slaveid = kwargs.pop('slaveid', 'local')
    raw_backmsg: Message = kwargs.get('backmsg', None)
    if raw_backmsg is None:
        logger.warning("已丢失BOT消息！")
        return
    else:
        logger.info(f"BOT进度条编辑的chat_id:{raw_backmsg.chat.id},message_id:{raw_backmsg.id}")
        BOT_MESSAGE_LIST[str(raw_backmsg.chat.id) + ':' + str(raw_backmsg.id)] = raw_backmsg
    coreindex = kwargs.get('coreindex', 0)
    userbot_id = config.config.get('userbot', {}).get('id', '')
    bot_info = await app.get_me()
    if slaveid == 'local':
        core = kwargs.pop('core', None)
        if core is None:
            await message.reply("找不到测试核心")
            return None
        info = await core.core(proxyinfo, **kwargs)
        return info
    if not userbot_id:
        backmsg = await message.reply("❌读取中继桥id错误")
        message_delete_queue.put(backmsg)
        return
    slaveconfig = config.getSlaveconfig()
    key = slaveconfig.get(slaveid, {}).get('public-key', '')
    key = sha256_32bytes(key)

    payload = {
        'proxies': proxyinfo,
        'master': {'id': bot_info.id},
        'coreindex': coreindex,
        'test-items': kwargs.get('test_items', None),
        'edit-message-id': raw_backmsg.id,
        'edit-chat-id': raw_backmsg.chat.id,
        'edit-message': {'message-id': raw_backmsg.id, 'chat-id': raw_backmsg.chat.id},
        'origin-message': {'chat-id': message.chat.id, 'message-id': message.id},
        'slave': {
            'id': slaveid,
            'comment': slaveconfig.get(slaveid, {}).get('comment', '')
        },
        'sort': kwargs.get('sort', '订阅原序')
    }
    # 设置指定的后端为测速状态
    if coreindex == 1:
        SPEEDTEST_LIST.append(slaveid)
    data1 = json.dumps(payload)
    cipherdata = cipher_chacha20(data1.encode(), key)
    bytesio = io.BytesIO(cipherdata)
    bytesio.name = "subinfo"
    await app.send_document(userbot_id, bytesio, caption=f'/relay {slaveid} send')
    return None


@logger.catch()
async def process_slave(app: Client, message: Message, putinfo: dict, **kwargs):
    masterconfig = config.getMasterconfig()
    master_id = putinfo.get('master', {}).get('id', 1)
    coreindex = putinfo.get('coreindex', None)
    proxyinfo = putinfo.pop('proxies', [])
    kwargs.update(putinfo)
    core = await select_core_slave(coreindex, message, putinfo)
    if core is None:
        return
    info = await core.core(proxyinfo, **kwargs) if proxyinfo else {}

    putinfo['result'] = info
    infostr = json.dumps(putinfo)
    key = masterconfig.get(str(master_id), {}).get('public-key', '')
    key = sha256_32bytes(key)
    cipherdata = cipher_chacha20(infostr.encode(), key)
    bytesio = io.BytesIO(cipherdata)
    bytesio.name = "result"
    await app.send_document(message.chat.id, bytesio, caption=f'/relay {master_id} result')


async def stopspeed(app: Client, callback_query: CallbackQuery):
    slaveconfig = config.getSlaveconfig()
    bridge = config.getBridge()
    botmsg = callback_query.message
    commenttext = botmsg.text.split('\n', 1)[0].split(':')[1]
    default_comment = config.get_default_slave().get('comment', 'Local')
    if commenttext == default_comment:
        break_speed.append(True)
        await botmsg.edit_text("❌测速任务已取消")
        return
    slaveid = 0
    for k, v in slaveconfig.items():
        comment = v.get('comment', '')
        if comment == commenttext:
            slaveid = int(k) if k != "default-slave" else 'local'
            break
    if slaveid:
        await app.send_message(bridge, f'/relay {slaveid} stopspeed')
        backmsg = await botmsg.edit_text("❌测速任务已取消")
        message_delete_queue.put(backmsg)
    logger.info("测速中止")
    callback_query.stop_propagation()
