import asyncio.exceptions

import async_timeout
from loguru import logger
from pyrogram.types import Message
from pyrogram import Client
# from libs import safe
from botmodule.init_bot import config, corenum
from botmodule import restart_or_killme
from utils.cron.utils import message_delete_queue
from utils.cleaner import ArgCleaner
from utils.clash import new_batch_start, check_port

connect_list = {}
connect_queue = asyncio.Queue()

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
        # 启动器
        # pystr = "python" if sys.platform == "win32" else "python3"
        # command = fr"{pystr} clash.py"
        # subp = subprocess.Popen(command.split(), encoding="utf-8")
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
    try:
        bridge = config.config.get('bridge', None)
        if bridge is None:
            backmsg1 = await message.reply("❌未配置中继连接桥")
            message_delete_queue.put_nowait((backmsg1.chat.id, backmsg1.id, 10))
            return
        _args = ArgCleaner(message.text).getall()
        if len(_args) < 3:
            backmsg2 = await message.reply("❌使用方式: /connect <bot_id> <备注>")
            message_delete_queue.put_nowait((backmsg2.chat.id, backmsg2.id, 10))
            return
        bot_id = _args[1]
        targetbot = await app.get_users(bot_id)
        if targetbot is None:
            backmsg3 = await message.reply("❌错误的后端bot_id")
            message_delete_queue.put_nowait((backmsg3.chat.id, backmsg3.id, 10))
            return
        bot_username = targetbot.username
        print("中继群组:", bridge)
        connettext = ' '.join(_args[1:])
        backmsg2 = await app.send_message(bridge, text=f"/connect@{bot_username} {connettext}")
        connect_list[str(_args[1])] = _args[1]
        try:
            with async_timeout.timeout(10):
                msg2: Message = await connect_queue.get()
                # print("msg2: ", msg2)
        except asyncio.exceptions.TimeoutError:
            logger.warning("连接超时")
            backmsg = await message.reply("连接超时")
            message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 20))
            return
        print(connect_list)
        msg1 = connect_list.pop(str(msg2.from_user.id), None)
        if msg1 is None:
            logger.info(f"连接列表未找到id为: {str(msg2.from_user.id)}的连接请求。")
            return
        if str(msg2.from_user.id) != _args[1]:
            logger.warning("连接id不匹配")
            return
        if msg2.document is None:
            logger.info(f"消息ID: {msg2.id}, 无文件。")
            return
        await msg2.download(file_name=f'./key/{str(msg2.from_user.id)}fulltclash-public.pem')
        config.add_slave(str(msg2.from_user.id), f'./key/{str(msg2.from_user.id)}fulltclash-public.pem', bot_username,
                         comment=_args[2])
        config.save()
        logger.info(f"已将{msg2.from_user.username}的公钥保存,配置已更新")
        # 发送master公钥
        await app.send_document(bridge, "./key/fulltclash-public.pem", caption=f'/resp_master {bot_username}')
    except Exception as e:
        print(e)
        return


async def response(app: Client, message: Message):
    # ID = getid(message)
    # old_msg = connect_list.pop(ID, None)
    # if old_msg is None:
    #     return
    if message.document is None:
        return
    # await app.send_document()
    await connect_queue.put(message)
    # await old_msg.reply("连接开始建立")
    # _args = ArgCleaner(old_msg.text).getall()
    # bot_username = _args[1] if _args[1].startswith("@") else "@" + _args[1]
    # comment = _args[3] if len(_args) > 3 else 'no comment'
    # file_id = message.document.file_id
    # file_path = await app.download_media(file_id, file_name=f'./key/{ID}')
    # logger.info(f"{ID} 的公钥文件已被保存在 {file_path}")
    # config.add_slave(ID, file_path, bot_username, comment)
    # config.reload()
    # await message.reply_document(r'./key/fulltclash-public.pem', quote=True, caption='/ok')
    # await old_msg.reply("连接建立成功")


async def relay(app: Client, message: Message):
    bridge = config.config.get('bridge', None)
    if bridge is None:
        backmsg = await message.reply("❌未配置连接中继桥，请先设置一个TG私有群组，将其群组id设置为中继桥。")
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        return
    if not isinstance(bridge, int):
        pass
    await app.send_message(message.chat.id, str(message.text) + ' ' + str(message.from_user.id))

