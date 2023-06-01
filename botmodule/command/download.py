import asyncio
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from pyrogram.errors import RPCError
from loguru import logger
from utils.cleaner import addon, ArgCleaner
from botmodule.command.setting import reload_button


async def download_script(_: Client, message: Message):
    if message.reply_to_message is None:
        base_text = "当前共有脚本:\n\n"
        script = addon.script
        for k in script:
            base_text += f"**{str(k)}**\n"
        base_text += f"\n共{len(script)}个"
        m2 = await message.reply_text(base_text)
        await asyncio.sleep(10)
        await m2.delete(revoke=False)
        return
    m2 = await message.reply_text("正在识别脚本...", quote=True)
    # 下载文件到本地
    try:
        # print(message)
        target = message.reply_to_message
        if target.document is None:
            await m2.edit_text("该消息未找到文件！")
            return
        file_name = target.document.file_name
        if file_name[-3:] == '.py' and file_name != "__init__.py":
            file_path = await target.download(file_name=f'./addons/{file_name}')
            if file_path:
                logger.info("文件已下载到本地:" + file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    await m2.edit_text("下载成功，即将进入脚本预览，每5秒翻页一次")
                    await asyncio.sleep(10)
                    source = f.read(512)
                    pre_source = source
                    while source:
                        await m2.edit_text(source)
                        await asyncio.sleep(5)
                        pre_source = source
                        source = f.read(512)

                IKM = InlineKeyboardMarkup([[InlineKeyboardButton("⚙️确认重载", callback_data="reload:addon")]])
                await m2.edit_text(pre_source, reply_markup=IKM)
        else:
            await message.reply_text("上传失败，请确认格式是否为 .py")
    except RPCError as r:
        logger.error(str(r))
    except Exception as e:
        logger.error(str(e))


async def reload_addon_from_telegram(_: Client, call: CallbackQuery):
    bot_mess = call.message
    bm = await bot_mess.edit_text("⚠️操作确认,正在重载...⚠️")
    addon.reload_script()
    reload_button()
    await asyncio.sleep(5)
    await bm.edit_text("✅已完成重载")
    await asyncio.sleep(5)
    await bm.delete(revoke=False)


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
            m2 = await message.reply_text("没有找到脚本可供卸载😅")
        await asyncio.sleep(10)
        await m2.delete(revoke=False)
    else:
        m2 = await message.reply_text("无接受参数。使用方法: /uninstall <脚本名1> <脚本名2> ...")
        await asyncio.sleep(10)
        await m2.delete(revoke=False)
