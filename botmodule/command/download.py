import asyncio

from pyrogram.types import Message
from pyrogram import Client
from pyrogram.errors import RPCError
from loguru import logger
from libs.cleaner import addon
from botmodule.command.setting import reload_button


async def download_script(_: Client, message: Message):
    m2 = await message.reply_text(f"正在识别脚本...")
    # 下载文件到本地
    try:
        # print(message)
        target = message.reply_to_message
        if target.document is None:
            await m2.edit_text(f"该消息未找到文件！")
            return
        file_name = target.document.file_name
        if file_name[-3:] == '.py' and file_name != "__init__.py":
            file_path = await target.download(file_name=f'./addons/{file_name}')
            if file_path:
                logger.info("文件已下载到本地:", file_path)
                bm = await m2.edit_text(f"**{file_name}** 下载成功,正在重载...")
                await asyncio.sleep(3)
                addon.reload_script()
                reload_button()
                await bm.edit_text("已完成重载")
        else:
            await message.reply_text("上传失败，请确认格式是否为 .py")
    except RPCError as r:
        logger.error(str(r))
    except Exception as e:
        logger.error(str(e))


async def uninstall_script(_: Client, message: Message):
    pass
