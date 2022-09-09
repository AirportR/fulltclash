from pyrogram import types
from pyrogram.types import BotCommand
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from botmodule import USER_TARGET
from libs.collector import reload_config as r1
from libs.cleaner import reload_config as r2

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
test_items = []


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
    b11 = b1
    b22 = b2
    b33 = b3
    b44 = b4
    b55 = b5
    b88 = b8
    buttonss = [b11, b22, b33, b44, b55, b88]
    text = "请选择想要启用的测试项:"
    # print(callback_query)
    mess_test = callback_query.message.reply_to_message
    callback_data = callback_query.data
    mess_id = callback_query.message.id
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    try:
        if int(callback_query.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await callback_query.answer(f"不要乱动别人的操作哟👻", show_alert=True)
            return
    except AttributeError:
        if int(callback_query.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await callback_query.answer(f"不要乱动别人的操作哟👻", show_alert=True)
            return
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
    elif "👌完成设置" in callback_data:
        test_items.clear()
        for b in buttonss:
            if "✅" in b.text:
                test_items.append(str(b.text)[1:])
        message = await client.edit_message_text(chat_id=chat_id,
                                                 message_id=mess_id,
                                                 text="任务已提交~")
        r1(test_items)
        r2(test_items)
        # if test_items:
        #     await botmodule.testurl(client, message)
        return test_items


async def task_begin(client, callback_query):
    test_items, message = await setting(client, callback_query)
