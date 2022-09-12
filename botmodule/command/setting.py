import loguru
from pyrogram import types
from pyrogram.types import BotCommand
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton



b1 = InlineKeyboardButton("✅Netflix", callback_data='✅Netflix')
b2 = InlineKeyboardButton("✅Youtube", callback_data='✅Youtube')
b3 = InlineKeyboardButton("✅Disney+", callback_data='✅Disney+')
b4 = InlineKeyboardButton("✅Bilibili", callback_data='✅Bilibili')
b5 = InlineKeyboardButton("✅Dazn", callback_data='✅Dazn')
b6 = InlineKeyboardButton("🔒节点类型", callback_data='🔒节点类型')
b7 = InlineKeyboardButton("🔒延迟RTT", callback_data='🔒延迟RTT')
b8 = InlineKeyboardButton("👌完成设置", callback_data='👌完成设置')
buttons = [b1, b2, b3, b4, b5, b8]
IKM = InlineKeyboardMarkup(
    [
        # 第一行
        [b1, b2, b3],
        # 第二行
        [b4, b5],
        [b6, b7],
        [b8]
    ]
)
# test_items = []


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


async def test_setting(client, callback_query):
    """
    收到测试指令后对测试项进行动态调整
    :param client:
    :param callback_query:
    :return: test_items, origin_message, message, test_type
    """
    message = None
    test_items = []
    b11 = b1
    b22 = b2
    b33 = b3
    b44 = b4
    b55 = b5
    b88 = b8
    buttonss = [b11, b22, b33, b44, b55, b88]
    text = "请选择想要启用的测试项:"
    origin_message = callback_query.message.reply_to_message
    try:
        test_type = str(origin_message.text).split(" ")[0]
    except:
        test_type = "unknown"
        loguru.logger.warning("test_type:" + test_type)
    callback_data = callback_query.data
    mess_id = callback_query.message.id
    chat_id = callback_query.message.chat.id
    if "✅" in callback_data:
        for b in buttonss:
            if b.text == callback_data:
                b.text = b.text.replace("✅", "❌")
                b.callback_data = b.text
                IKM2 = InlineKeyboardMarkup(
                    [
                        # 第一行
                        [b11, b22, b33],
                        # 第二行
                        [b44, b55],
                        [b6, b7],
                        [b88]
                    ]
                )
                await client.edit_message_text(chat_id=chat_id,
                                               message_id=mess_id,
                                               text=text,
                                               reply_markup=IKM2)
        return test_items, origin_message, message, test_type
    elif "❌" in callback_data:
        for b in buttonss:
            if b.text == callback_data:
                b.text = b.text.replace("❌", "✅")
                b.callback_data = b.text
                IKM2 = InlineKeyboardMarkup(
                    [
                        # 第一行
                        [b11, b22, b33],
                        # 第二行
                        [b44, b55],
                        [b6, b7],
                        [b88]
                    ]
                )
                await client.edit_message_text(chat_id=chat_id,
                                               message_id=mess_id,
                                               text=text,
                                               reply_markup=IKM2)
        return test_items, origin_message, message, test_type
    elif "👌完成设置" in callback_data:
        test_items = []
        for b in buttonss:
            if "✅" in b.text:
                test_items.append(str(b.text)[1:])
        message = await client.edit_message_text(chat_id=chat_id,
                                                 message_id=mess_id,
                                                 text="⌛正在提交任务~")
        return test_items, origin_message, message, test_type
    return test_items, origin_message, message, test_type

