import asyncio
import os
from pyrogram.types import Message
from pyrogram import Client
from pyrogram.errors import RPCError
from loguru import logger
from libs.cleaner import addon,ArgCleaner
from botmodule.command.setting import reload_button


async def download_script(_: Client, message: Message):
    if message.reply_to_message is None:
        base_text = "当前共有脚本:\n\n"
        script = addon.script
        for k in script.keys():
            base_text += f"**{str(k)}**\n"
        base_text += f"\n共{len(script)}个"
        m2 = await message.reply_text(base_text)
        await asyncio.sleep(10)
        await m2.delete(revoke=False)
        return
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
    args = ArgCleaner(str(message.text)).getall()
    print(args)
    del args[0]
    if args:
        success_list = addon.remove_addons(args)
        addon.reload_script()
        reload_button()
        if success_list:
            m2 = await message.reply_text(f"成功卸载以下脚本: \n{str(success_list)}")
        else:
            m2 = await message.reply_text(f"没有找到脚本可供卸载😅")
        await asyncio.sleep(10)
        await m2.delete(revoke=False)
    else:
        m2 = await message.reply_text("无接受参数。使用方法: /uninstall <脚本名1> <脚本名2> ...")
        await asyncio.sleep(10)
        await m2.delete(revoke=False)