from loguru import logger
from pyrogram.types import Message
from pyrogram import Client
from botmodule.init_bot import config
from utils.cron.utils import message_delete_queue
from utils.cleaner import ArgCleaner
from utils.check import get_telegram_id_from_message as getid

connect_list = {}


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