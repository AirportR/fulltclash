import io
import os

from pyrogram import Client
from pyrogram.types import Message
from loguru import logger

from utils.cleaner import ArgCleaner


def get_last_line(file_path: str, line_num: int = 1):
    """
    获取一个文件的最后n行
    """
    from collections import deque

    if line_num <= 0:
        raise ValueError("行数必须大于0")
    n = line_num
    last_lines = deque(maxlen=n)
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            last_lines.append(line)
    str1 = ''.join(last_lines)
    return str1


async def export_logs(_: Client, message: Message):
    try:
        latest_file = get_latest_log()
        tgargs = ArgCleaner.getarg(message.text)
        n = tgargs[1] if len(tgargs) > 1 else 0
        try:
            n = int(n)
        except Exception as e:
            logger.warning(str(e))

        if n:
            if not isinstance(n, int):
                await message.reply("❌非法参数，请检查!")
                return
            content = get_last_line(latest_file, n)
            bytesio = io.BytesIO(content.encode())
            bytesio.name = f"logs-{n}.txt"
            await message.reply_document(bytesio, quote=True, caption=f'已输出最后{n}行结果')
        else:
            await message.reply_document(latest_file)

    except Exception as e:
        logger.error(str(e))


def get_latest_log(folder_path: str = './logs/'):
    """
    获取最新一次日志的文件名
    """
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    # 根据最新修改日期排序文件
    files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
    # 获取最新修改日期的文件名
    latest_file = files[0]
    logger.info(f"最新修改日期的文件名：{latest_file}")
    return os.path.join(folder_path, latest_file)
