import os

from pyrogram import Client
from pyrogram.types import Message
from loguru import logger


async def export_logs(_: Client, message: Message):
    try:
        latest_file = get_latest_log()
        await message.reply_document(latest_file)
    except Exception as e:
        logger.error(str(e))


def get_latest_log():
    # 指定文件夹路径
    folder_path = "./logs/"
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    # 根据最新修改日期排序文件
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    # 获取最新修改日期的文件名
    latest_file = files[0]
    logger.info(f"最新修改日期的文件名：{latest_file}")
    return os.path.join(folder_path, latest_file)
