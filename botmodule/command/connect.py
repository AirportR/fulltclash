import asyncio

from loguru import logger
from pyrogram.types import Message
from pyrogram import Client
# from libs import safe
from botmodule.init_bot import config, corenum
from botmodule import restart_or_killme
from botmodule.utils import message_delete_queue
from libs.cleaner import ArgCleaner
from libs.check import get_telegram_id_from_message as getid
from libs.proxys import stopclash
from clash import new_batch_start, check_port

connect_list = {}


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
        start_port = config.config.get('clash', {}).get('startup', 1122)
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
            await message.reply("❌未配置中继连接桥")
            message_delete_queue.put_nowait((message.chat.id, message.id, 10))
            return
        _args = ArgCleaner(message.text).getall()
        if len(_args) < 4:
            await message.reply("❌使用方式: /connect <bot用户名> <bot_id> <备注>")
            message_delete_queue.put_nowait((message.chat.id, message.id, 10))
            return
        bot_username = _args[1] if _args[1].startswith("@") else "@" + _args[1]
        print(bridge)
        await app.send_message(bridge, text=f"/connect{bot_username}")
        connect_list[str(_args[2])] = message
    except Exception as e:
        print(e)
        return


async def response(app: Client, message: Message):
    ID = getid(message)
    old_msg = connect_list.pop(ID, None)
    if old_msg is None:
        return
    if message.document is None:
        return
    await old_msg.reply("连接开始建立")
    _args = ArgCleaner(old_msg.text).getall()
    bot_username = _args[1] if _args[1].startswith("@") else "@" + _args[1]
    comment = _args[3] if len(_args) > 3 else 'no comment'
    file_id = message.document.file_id
    file_path = await app.download_media(file_id, file_name=f'./key/{ID}')
    logger.info(f"{ID} 的公钥文件已被保存在 {file_path}")
    config.add_slave(ID, file_path, bot_username, comment)
    config.reload()
    await message.reply_document(fr'./key/fulltclash-public.pem', quote=True, caption='/ok')
    await old_msg.reply("连接建立成功")
