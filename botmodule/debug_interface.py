from loguru import logger
from pyrogram.errors import RPCError
from libs.cleaner import ConfigManager


@logger.catch()
async def debug_interface(_, message):
    config = ConfigManager().config
    name = config.get('bot', {}).get('name', 'bot')
    name = name.replace('@', '')
    text = str(message.text).replace(f'/map@{name} ', '')
    text = text.replace('/map ', '')
    try:
        result = []
        exec(text)
        await message.reply(str(result))
    except RPCError as r:
        await message.reply(str(r))
        logger.error(str(text))
        logger.error(str(r))
    except Exception as e:
        await message.reply(str(e))
        logger.error(str(text))
        logger.error(str(e))
