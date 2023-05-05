import io
import json
from typing import Union

from loguru import logger
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, RPCError
from pyrogram import Client

from botmodule.init_bot import config, corenum
from botmodule import restart_or_killme, select_export
from utils import message_delete_queue, safe
from utils.cleaner import ArgCleaner
from utils.clash import new_batch_start, check_port
from utils.myqueue import bot_put_slave
from glovar import app2

async def startclash(app: Client, message: Message):
    tgargs = [i for i in str(message.text).split(" ") if i != '']
    if len(tgargs) < 2:
        backmsg = await message.reply("使用方法: /clash start或 /clash stop")
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return
    if config.config.get('clash', {}).get('auto-start', False):
        backmsg = await message.reply("您在配置中设置了bot启动时clash核心自动启动，此命令已被禁用。\nclash:\n auto-start: true\n")
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return
    start_or_stop = tgargs[1] if len(tgargs) > 1 else ''
    if start_or_stop == "start":
        backmsg = await message.reply("正在启动clash核心...")
        start_port = config.config.get('clash', {}).get('startup', 11220)
        port_list = [start_port + i * 2 for i in range(corenum)]
        res2 = await check_port(start_port, start_port + 1 + corenum * 2)
        if res2:
            print("端口检查中发现已有其他进程占用了端口，请更换端口")
            await backmsg.edit_text("端口检查中发现已有其他进程占用了端口，请更换端口")
            return
        new_batch_start(port_list)
        await backmsg.edit_text("✅clash已启动\n\n注意: 目前启动clash后将无法按Ctrl+C退出，请先进行 /clash stop 操作")
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return
    elif start_or_stop == "stop":
        await message.reply("正在停止clash核心...")
        await restart_or_killme(app, message)
        return
    else:
        backmsg = await message.reply("⚠️未识别的参数，请检查参数")
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return


async def simple_relay(app: Client, message: Message):
    text = message.caption if message.caption else message.text
    if not text.startswith("/relay"):
        return
    tgargs = ArgCleaner().getall(str(text))
    origin_id = message.from_user.id
    if len(tgargs) < 3:
        logger.info("缺少必要参数")
        backmsg = await message.reply("缺少必要参数")
        message_delete_queue.put(backmsg)
        return
    target_id = tgargs[1]
    command = tgargs[2].strip('/')
    try:
        newtext = f'/{command} {origin_id} '
        if len(tgargs) > 3:
            newtext += ' '.join(tgargs[3:])
        if message.document:
            await app.send_document(int(target_id), message.document.file_id, caption=newtext)
        else:
            await app.send_message(int(target_id), newtext)
    except RPCError as r:
        logger.error(str(r))
        return


@logger.catch()
async def conn_simple(app: Client, message: Message):
    """
    简单的连接
    """
    print("群聊id:", message.chat.id)
    try:
        bridge = config.config.get('userbot', {}).get('id', None)
        b1 = await message.reply("开始连接...")
        # 检查连接中继
        if bridge is None:
            backmsg1 = await b1.edit_text("❌未配置中继连接桥")
            await message.reply(f"当前群聊id: {message.chat.id}")
            message_delete_queue.put_nowait((backmsg1.chat.id, backmsg1.id, 10))
            return
        try:
            connchat = await app.get_chat(bridge)
            print("中继桥id:", connchat.id)
        except PeerIdInvalid:
            backmsg3 = await b1.edit_text("❌错误的中继桥")
            message_delete_queue.put_nowait((backmsg3.chat.id, backmsg3.id, 10))
            return

        # 检查连接参数
        _args = ArgCleaner(message.text).getall()
        if len(_args) < 3:
            backmsg2 = await b1.edit_text("❌使用方式: /connect <机器人ID> <备注> <连接密码>")
            message_delete_queue.put_nowait((backmsg2.chat.id, backmsg2.id, 10))
            return
        bot_id = _args[1]
        conn_pwd = _args[3] if len(_args) > 3 else ''
        # 检查后端id
        try:
            if app2 is None:
                return
            targetbot = await app2.get_users(bot_id)
        except PeerIdInvalid:
            backmsg3 = await b1.edit_text("❌错误的后端bot_id")
            message_delete_queue.put_nowait((backmsg3.chat.id, backmsg3.id, 10))
            return
        bot_username = targetbot.username
        print("后端BOT名称：", bot_username)
        me = await app.get_me()
        print(f"主端id: {me.id}")
        await app.send_message(bridge, f"/relay {targetbot.id} sconnect {conn_pwd} {bridge}")
        config.add_slave(str(targetbot.id), conn_pwd, bot_username, comment=_args[2])
        config.reload()
        logger.info(f"已添加id为 {targetbot.id} @{bot_username}的bot为测试后端")
        backmsg4 = await b1.edit_text(f"已添加id为 {targetbot.id} @{bot_username}的bot为测试后端")
        message_delete_queue.put(backmsg4)

    except RPCError as e:
        logger.error(str(e))


# async def response(_: Client, message: Message):
#     """
#     userbot专属
#     """
#     logger.info("接收到后端bot消息")
#     if message.document is None:
#         return
#     await connect_queue.put(message)


# async def response2(_: Client, message: Message):
#     """
#     userbot专属
#     转发测试进度和结果
#     """
#     logger.info("接收来自后端的resp2请求")
#     master_id = int(message.caption.split(' ')[-1])
#     await message.forward(master_id)


# async def relay(app: Client, message: Message, command: str = '/sconnect'):
#     """
#     userbot专属
#     中转初次连接
#     """
#     logger.info("收到relay1，来自：" + str(message.chat.id))
#     tgargs = ArgCleaner().getall(message.text)
#     if len(tgargs) < 2:
#         return
#     bot_id = tgargs[1]
#     await app.send_message(bot_id, f"{command} {message.from_user.id}")


# async def relay2(app: Client, message: Message, command: str = 'sconnect2'):
#     """
#     userbot专属
#     中转主端文件
#     """
#     logger.info("收到relay2，来自：" + str(message.chat.id))
#     tgargs = ArgCleaner().getall(str(message.caption))
#     if len(tgargs) < 2:
#         logger.warning("缺少slave id")
#         return
#     bot_id = tgargs[1]
#     command = command if len(tgargs) < 3 else tgargs[2].lstrip('/')
#     if tgargs[0].startswith("/relay2") and message.document:
#         await app.send_document(bot_id, message.document.file_id, caption=f'/{command} {str(message.from_user.id)}')


@logger.catch()
async def simple_conn_resp(_: Client, message: Message):
    """
    后端bot专属
    """
    logger.info("有新的master请求")
    tgargs = ArgCleaner().getall(message.text)
    if len(tgargs) < 3:
        return
    master_id = tgargs[1]
    conn_pwd = tgargs[2]
    bridge = tgargs[3] if len(tgargs) > 3 else ''
    masterconfig = config.getMasterconfig()
    masterconfig[master_id] = {'public-key': conn_pwd, 'bridge': bridge}
    config.yaml['masterconfig'] = masterconfig
    config.reload()
    logger.info("master连接配置已保存")
    await message.reply("已收到master请求，配置已保存，重启生效", quote=True)


# @logger.catch()
# async def conn_resp(_: Client, message: Message):
#     """
#     后端bot专属
#     发送公钥
#     """
#     logger.info(f"接收连接请求: {message.chat.id}:{message.id}")
#     ID = message.from_user.id
#     _config = config
#     whitelist = _config.config.get('whitelist', [])
#     if whitelist:
#         if ID not in whitelist:
#             logger.error("非白名单:" + str(ID) + f"在{message.chat.id}中")
#             return
#     tgargs = ArgCleaner().getall(str(message.text))
#     # 发送公钥
#     await message.reply_document('./key/fulltclash-public.pem', quote=True, caption='/resp')
#     connect_list2[tgargs[-1]] = str(message.chat.id)


# @logger.catch()
# async def conn_resp2(_: Client, message: Message):
#     """
#     后端bot专属
#     保存主端公钥
#     """
#     if message.caption is None:
#         return
#     master_id = str(message.caption).split(' ')[-1]
#     chat_id = connect_list2.pop(master_id, None)
#     if chat_id is None:
#         return
#     file = message.document
#     if file is None:
#         print("未找到文件")
#         return
#     name = await message.download(fr'./key/master-{master_id}.pem')
#     masterconfig = config.getMasterconfig()
#     masterconfig[master_id] = {'public-key': fr'./key/master-{master_id}.pem', 'bridge': chat_id}
#     config.yaml['masterconfig'] = masterconfig
#     config.reload()
#     logger.info(f"master公钥 {name} 配置已保存")


async def recvtask(app: Client, message: Message):
    masterconfig = config.getMasterconfig()
    tgargs = ArgCleaner().getall(message.caption)
    if tgargs[0] != '/send':
        logger.info("未知指令")
        return
    master_id = tgargs[1] if len(tgargs) > 1 else ''
    if not master_id:
        logger.info("无master_id")
        return
    key = masterconfig.get(master_id, {}).get('public-key', '')
    if not key:
        logger.warning(f"无法找到master_id为{master_id}的解密密码")
    plaindata = await plain_data(message, key)
    await message.reply("Get data success!\nplease wait.", quote=True)
    putinfo: dict = json.loads(plaindata)
    # coreindex = putinfo.get('coreindex', 0)
    await bot_put_slave(app, message, putinfo, master_id=master_id)


async def plain_data(message: Message, key: str):
    key = safe.sha256_32bytes(key)
    file: Union[str, io.BytesIO] = await message.download(in_memory=True)
    data = file.getvalue()
    plaindata = ''
    try:
        plaindata = safe.plain_chahcha20(data, key)
        print("已接收并解密文件")
        print(plaindata)
    except Exception as e:
        logger.warning(str(e))
        logger.warning("解密数据失败！")
    finally:
        return plaindata


async def task_result(app: Client, message: Message):
    """
    接收来自后端的最终结果
    """
    slaveconfig = config.getSlaveconfig()
    tgargs = ArgCleaner().getall(message.caption)
    slaveid = tgargs[1] if len(tgargs) > 1 else ''
    key = slaveconfig.get(slaveid, {}).get('public-key', '')
    if not key:
        logger.warning(f"无法找到slave_id为{slaveid}的解密密码")
    logger.info(f"当前后端id:{slaveid}，解密密码：{key}")
    plaindata = await plain_data(message, key)
    resultdata: dict = json.loads(plaindata)

    info = resultdata.pop('result', {})
    info['slave'] = resultdata.pop('slave', {})
    origin_message_d = resultdata.get('origin-message', {})
    botmsg_d = resultdata.get('edit-message', {})
    try:
        origin_msg = await app.get_messages(origin_message_d.get('chat-id', 0), origin_message_d.get('message-id', 0))
        botmsg = await app.get_messages(botmsg_d.get('chat-id', 0), botmsg_d.get('message-id', 0))
    except RPCError as e:
        logger.error(str(e))
        return
    puttype = {
        1: 'speed',
        2: 'analyze',
        3: 'test',
        -1: 'unknown'
    }
    await select_export(origin_msg, botmsg, puttype[resultdata.get('coreindex', -1)], info)
