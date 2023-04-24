import pyrogram.types
from loguru import logger
from pyrogram import Client
from pyrogram.errors import RPCError
from botmodule.init_bot import admin, config


async def leavechat(client: Client, message: pyrogram.types.Message):
    try:
        if config.config.get('anti-group', False):
            for user in message.new_chat_members :
                if str(user.is_self) == "True":
                    if not int(message.from_user.id) in admin:
                        await message.reply("❌ 机器人已启动防拉群模式，请联系超管拉群")
                        await client.leave_chat(message.chat.id)
        return
    except RPCError as r:
        logger.error(str(r))

async def set_anti_group(client: Client, message: pyrogram.types.Message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    try:
        if config.config.get('anti-group', True):
            config.yaml['anti-group'] = False
            logger.info("关闭了防拉群")
            await message.reply("关闭了防拉群")
        else:
            config.yaml['anti-group'] = True
            logger.info("开启了防拉群")
            await message.reply("开启了防拉群")
    except RPCError as r:
        print(r)
