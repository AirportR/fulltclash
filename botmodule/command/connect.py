import asyncio.exceptions

import async_timeout
from loguru import logger
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid
from pyrogram import Client
# from libs import safe
from botmodule.init_bot import config, corenum
from botmodule import restart_or_killme
from utils.cron.utils import message_delete_queue
from utils.cleaner import ArgCleaner
from utils.clash import new_batch_start, check_port

connect_list = {}  # 作为主端
connect_list2 = {}  # 作为后端
connect_queue = asyncio.Queue(1)


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


async def conn(app: Client, message: Message):
    """
    主端主动对后端连接，交换公钥
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
            backmsg2 = await b1.edit_text("❌使用方式: /connect <机器人ID> <备注>")
            message_delete_queue.put_nowait((backmsg2.chat.id, backmsg2.id, 10))
            return
        bot_id = _args[1]
        # 检查后端id
        try:
            targetbot = await app.get_users(bot_id)
        except PeerIdInvalid:
            backmsg3 = await b1.edit_text("❌错误的后端bot_id")
            message_delete_queue.put_nowait((backmsg3.chat.id, backmsg3.id, 10))
            return
        bot_username = targetbot.username
        print("后端BOT名称：", targetbot.username)
        # 将此id放入待连接队列
        connect_list[str(_args[1])] = _args[1]
        await app.send_message(bridge, f"/relay1 {targetbot.id}")
        try:
            with async_timeout.timeout(10):
                msg2: Message = await connect_queue.get()
                # print("msg2: ", msg2)
        except asyncio.exceptions.TimeoutError:
            logger.warning("连接超时")
            backmsg = await b1.edit_text("连接超时")
            message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 20))
            return

        # 走到这说明接收到了响应
        print(connect_list)
        # 尝试匹配待连接队列有无该id
        msg1 = connect_list.pop(str(msg2.from_user.id), None)
        if msg1 is None:
            logger.info(f"待连接列表未找到id为: {str(msg2.from_user.id)}的连接请求。")
            return
        # 防止连接造假
        if str(msg2.from_user.id) != _args[1]:
            logger.warning("连接id不匹配")
            return

        # 检查是否发送了公钥文件
        if msg2.document is None:
            logger.info(f"消息ID: {msg2.id}, 无文件。")
            return
        await msg2.download(file_name=f'./key/slave-{str(msg2.from_user.id)}.pem')
        config.add_slave(str(msg2.from_user.id), f'./key/slave-{str(msg2.from_user.id)}.pem', bot_username,
                         comment=_args[2])
        config.save()
        logger.info(f"已将{msg2.from_user.username}的公钥保存，配置已更新")
        await b1.edit_text(f"已将{msg2.from_user.username}的公钥保存，配置已更新")
        # 发送master公钥
        await app.send_document(bridge, "./key/fulltclash-public.pem", caption=f'/relay2 {bot_id}')

    except Exception as e:
        print(e)
        return


async def response(_: Client, message: Message):
    """
    userbot专属
    """
    logger.info("接收到后端bot消息")
    if message.document is None:
        return
    await connect_queue.put(message)


async def relay(app: Client, message: Message):
    """
    userbot专属
    中转初次连接
    """
    logger.info("收到relay1，来自：" + str(message.chat.id))
    tgargs = ArgCleaner().getall(message.text)
    if len(tgargs) < 2:
        return
    bot_id = tgargs[1]
    await app.send_message(bot_id, f"/sconnect {message.from_user.id}")


async def relay2(app: Client, message: Message):
    """
    userbot专属
    中转主端公钥
    """
    logger.info("收到relay2，来自：" + str(message.chat.id))
    tgargs = ArgCleaner().getall(str(message.caption))
    if len(tgargs) < 2:
        logger.warning("缺少master id")
        return
    bot_id = tgargs[1]
    if tgargs[0].startswith("/relay2") and message.document:
        await app.send_document(bot_id, message.document.file_id, caption=f'/sconnect2 {str(message.from_user.id)}')


@logger.catch()
async def conn_resp(_: Client, message: Message):
    """
    后端bot专属
    发送公钥
    """
    logger.info(f"接收连接请求: {message.chat.id}:{message.id}")
    ID = message.from_user.id
    _config = config
    whitelist = _config.config.get('whitelist', [])
    if whitelist:
        if ID not in whitelist:
            logger.error("非白名单:" + str(ID) + f"在{message.chat.id}中")
            return
    tgargs = ArgCleaner().getall(str(message.text))
    # 发送公钥
    await message.reply_document('./key/fulltclash-public.pem', quote=True, caption='/resp')
    connect_list2[tgargs[-1]] = str(message.chat.id)


@logger.catch()
async def conn_resp2(_: Client, message: Message):
    """
    后端bot专属
    保存主端公钥
    """
    if message.caption is None:
        return
    master_id = str(message.caption).split(' ')[-1]
    chat_id = connect_list2.pop(master_id, None)
    if chat_id is None:
        return
    file = message.document
    if file is None:
        print("未找到文件")
        return
    name = await message.download(fr'./key/master-{master_id}.pem')
    masterconfig = config.getMasterconfig()
    masterconfig[master_id] = {'public-key': fr'./key/master-{master_id}.pem', 'bridge': chat_id}
    config.yaml['masterconfig'] = masterconfig
    config.reload()
    logger.info(f"master公钥 {name} 配置已保存")
