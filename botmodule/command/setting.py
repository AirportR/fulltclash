import asyncio

from loguru import logger
from pyrogram import types
from pyrogram.types import BotCommand
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from addons.unlockTest.hbomax import b9
from addons.unlockTest.bahamut import b10
from addons.unlockTest.abema import button as b12
from addons.unlockTest.bbciplayer import button as b13
from addons.unlockTest.pcrjp import button as b14
from addons.unlockTest.primevideo import button as b15
from addons.unlockTest.myvideo import button as b16
from addons.unlockTest.catchplay import button as b17
from addons.unlockTest.viu import button as b18
from addons.ip_risk import button as b19
from addons.unlockTest.steam import button as b20
from addons.unlockTest.wikipedia import button as b21
from addons.unlockTest.umajp import button as b22
from addons.unlockTest.hulujp import button as b23

b1 = InlineKeyboardButton("✅Netflix", callback_data='✅Netflix')
b2 = InlineKeyboardButton("✅Youtube", callback_data='✅Youtube')
b3 = InlineKeyboardButton("✅Disney+", callback_data='✅Disney+')
b4 = InlineKeyboardButton("✅Bilibili", callback_data='✅Bilibili')
b5 = InlineKeyboardButton("✅Dazn", callback_data='✅Dazn')
b6 = InlineKeyboardButton("🔒节点类型", callback_data='🔒节点类型')
b7 = InlineKeyboardButton("🔒延迟RTT", callback_data='🔒延迟RTT')
b8 = InlineKeyboardButton("👌完成设置", callback_data='👌完成设置')
http_rtt = InlineKeyboardButton("✅HTTP延迟", callback_data='✅HTTP延迟')
b_reverse = InlineKeyboardButton("🪞选项翻转", callback_data='🪞选项翻转')
yusanjia = InlineKeyboardButton("御三家(N-Y-D)", callback_data='御三家(N-Y-D)')
b_cancel = InlineKeyboardButton("👋点错了，给我取消", callback_data='👋点错了，给我取消')
b_alive = InlineKeyboardButton("节点存活率", callback_data="节点存活率")
buttons = [b1, b2, b3, b4, b5, b8, b9, b10, b12, b13, b14, b15, b16, b17, b18, b19, b20, b21, b22, b23]  # 仅仅是统计按钮数量，目前无用
IKM = InlineKeyboardMarkup(
    [
        # 第一行
        [http_rtt],
        [b1, b2, b3],
        # 第二行
        [b4, b5, b9],
        [b10, b12, b13],
        [b14, b15, b16],
        [b17, b18, b20],
        [b21, b22, b19],
        [b23],
        [yusanjia, b_alive],
        [b_cancel, b_reverse],
        [b8]
    ]
)


async def setcommands(client):
    my = types.BotCommandScopeAllGroupChats()
    await client.set_bot_commands(
        [
            BotCommand("help", "获取帮助"),
            BotCommand("start", "欢迎使用本机器人"),
            BotCommand("topo", "节点落地分析"),
            BotCommand("test", "进行流媒体测试"),
            BotCommand("setting", "bot的相关设置")
        ], scope=my)


@logger.catch()
async def test_setting(client, callback_query):
    """
    收到测试指令后对测试项进行动态调整
    :param client:
    :param callback_query:
    :return: test_items, origin_message, message, test_type
    """
    message = None
    test_items = []
    text = "请选择想要启用的测试项:"
    callback_data = callback_query.data
    mess_id = callback_query.message.id
    chat_id = callback_query.message.chat.id
    origin_message = callback_query.message.reply_to_message
    inline_keyboard = callback_query.message.reply_markup.inline_keyboard
    try:
        test_type = str(origin_message.text).split(" ")[0]
    except Exception as e:
        test_type = "unknown"
        logger.info("test_type:" + test_type)
        logger.warning(str(e))
    if origin_message is None:
        logger.warning("⚠️无法获取发起该任务的源消息")
        await client.edit_message_text(chat_id=chat_id,
                                       message_id=mess_id,
                                       text="⚠️无法获取发起该任务的源消息")
        await asyncio.sleep(1)
        return test_items, origin_message, message, test_type
    if "✅" in callback_data:
        for b_1 in inline_keyboard:
            for b in b_1:
                if b.text == callback_data:
                    b.text = b.text.replace("✅", "❌")
                    b.callback_data = b.text
                    IKM2 = InlineKeyboardMarkup(
                        inline_keyboard
                    )
                    await client.edit_message_text(chat_id=chat_id,
                                                   message_id=mess_id,
                                                   text=text,
                                                   reply_markup=IKM2)
        return test_items, origin_message, message, test_type
    elif "❌" in callback_data:
        for b_1 in inline_keyboard:
            for b in b_1:
                if b.text == callback_data:
                    b.text = b.text.replace("❌", "✅")
                    b.callback_data = b.text
                    IKM2 = InlineKeyboardMarkup(
                        inline_keyboard
                    )
                    await client.edit_message_text(chat_id=chat_id,
                                                   message_id=mess_id,
                                                   text=text,
                                                   reply_markup=IKM2)
        return test_items, origin_message, message, test_type
    elif "🪞选项翻转" in callback_data:
        for b_1 in inline_keyboard:
            for b in b_1:
                if "❌" in b.text:
                    b.text = b.text.replace("❌", "✅")
                    b.callback_data = b.text

                elif "✅" in b.text:
                    b.text = b.text.replace("✅", "❌")
                    b.callback_data = b.text
        IKM2 = InlineKeyboardMarkup(
            inline_keyboard
        )
        await client.edit_message_text(chat_id=chat_id,
                                       message_id=mess_id,
                                       text=text,
                                       reply_markup=IKM2)
        return test_items, origin_message, message, test_type
    elif "御三家(N-Y-D)" in callback_data:
        test_items.clear()
        test_items.extend(['Netflix', 'Youtube', 'Disney+'])
        message = await client.edit_message_text(chat_id=chat_id,
                                                 message_id=mess_id,
                                                 text="⌛正在提交任务~")
        return test_items, origin_message, message, test_type
    elif "节点存活率" in callback_data:
        test_items.clear()
        message = await client.edit_message_text(chat_id=chat_id, message_id=mess_id, text="⌛正在提交任务~")
        return test_items, origin_message, message, test_type
    elif "👋点错了，给我取消" in callback_data:
        message = await client.edit_message_text(chat_id=chat_id,
                                                 message_id=mess_id,
                                                 text="❌任务已取消")
        await asyncio.sleep(10)
        await message.delete()
        message = None
        return test_items, origin_message, message, test_type
    elif "👌完成设置" in callback_data:
        test_items = []
        for b_1 in inline_keyboard:
            for b in b_1:
                if "✅" in b.text:
                    test_items.append(str(b.text)[1:])
                # elif b.text == "✅落地IP风险":
                #     test_items.append("iprisk")
        message = await client.edit_message_text(chat_id=chat_id,
                                                 message_id=mess_id,
                                                 text="⌛正在提交任务~")
        return test_items, origin_message, message, test_type

    return test_items, origin_message, message, test_type
