import asyncio
import io
import json
from typing import Union

from loguru import logger
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, RPCError
from pyrogram import Client

from botmodule.init_bot import config
from botmodule import restart_or_killme, select_export
from utils import message_delete_queue, safe
from utils.cleaner import ArgCleaner
# from utils.clash import new_batch_start, check_port
from utils.myqueue import bot_put_slave
from glovar import app2


async def startclash(_: Client, message: Message):
    backmsg = await message.reply("恭喜您，此命令将不再需要，可直接去测试啦，未来也许会废弃。")
    message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
    return


async def simple_relay(app: Client, message: Message):
    text = message.caption if message.caption else message.text
    slaveconfig = config.getSlaveconfig()
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
    slave_name = slaveconfig.get(target_id, {}).get('username', '')
    target = slave_name if slave_name else int(target_id)
    command = tgargs[2].strip('/')
    try:
        newtext = f'/{command} {origin_id} '
        if len(tgargs) > 3:
            newtext += ' '.join(tgargs[3:])
        if message.document:
            await app.send_document(target, message.document.file_id, caption=newtext)
        else:
            backmsg = await app.send_message(target, newtext)
            if command == 'edit':
                await asyncio.sleep(2)
                await backmsg.delete(revoke=False)
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
            backmsg2 = await b1.edit_text("❌使用方式: /connect <BO.T用户名> <备注> <连接密码>")
            message_delete_queue.put_nowait((backmsg2.chat.id, backmsg2.id, 10))
            return
        bot_name = _args[1]
        # 判断第一个字符的ASCII码是否属于数字范围
        if 48 <= ord(bot_name[0]) <= 57:
            backmsg2 = await b1.edit_text("❌使用方式: \n/connect <BO.T用户名> <备注> <连接密码>\n\n第一个参数应是bot的用户名！")
            message_delete_queue.put_nowait((backmsg2.chat.id, backmsg2.id, 10))
            return
        conn_pwd = _args[3] if len(_args) > 3 else ''
        # 检查后端id
        try:
            if app2 is None:
                return
            targetbot = await app2.get_chat(bot_name)
        except PeerIdInvalid:
            backmsg3 = await b1.edit_text("❌错误的后端bot_username")
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


@logger.catch()
async def simple_conn_resp(app: Client, message: Message):
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
    await restart_or_killme(app, message)


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
    slavecomment = slaveconfig.get(slaveid, {}).get('comment', 'Local')
    if not key:
        logger.warning(f"无法找到slave_id为{slaveid}的解密密码")
    plaindata = await plain_data(message, key)
    resultdata: dict = json.loads(plaindata)

    info = resultdata.pop('result', {})
    if not info:
        logger.info("无结果数据")
        return
    info['slave'] = {'comment': slavecomment, 'id': int(slaveid)}
    origin_message_d = resultdata.get('origin-message', {})
    botmsg_d = resultdata.get('edit-message', {})
    try:
        origin_msg = await app.get_messages(origin_message_d.get('chat-id', 0), origin_message_d.get('message-id', 0))
        botmsg = await app.get_messages(botmsg_d.get('chat-id', 0), botmsg_d.get('message-id', 0))
    except RPCError as e:
        logger.error(str(e))
        return
    if origin_msg is None or botmsg is None:
        logger.warning("获取消息失败！")
    puttype = {
        1: 'speed',
        2: 'analyze',
        3: 'test',
        -1: 'unknown'
    }
    await select_export(origin_msg, botmsg, puttype[resultdata.get('coreindex', -1)], info)
