from pyrogram import types
from pyrogram.types import BotCommand
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def setcommands(client, message):
    my = types.BotCommandScopeAllGroupChats()
    await client.set_bot_commands(
        [
            BotCommand("help", "获取帮助"),
            BotCommand("start", "欢迎使用本机器人"),
            BotCommand("topo", "节点落地分析"),
            BotCommand("test", "进行流媒体测试"),
            BotCommand("setting", "bot的相关设置")
        ], scope=my)


async def setting(client, callback_query):
    print(callback_query)
