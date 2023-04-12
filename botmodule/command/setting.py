import asyncio
from copy import deepcopy
from loguru import logger
from pyrogram import types, Client
from pyrogram.errors import RPCError
from pyrogram.types import BotCommand, CallbackQuery, Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.cleaner import addon, config
from glovar import __version__
from botmodule.init_bot import latest_version_hash as v_hash
from addons.unlockTest.spotify import button as b15
from addons.unlockTest.viu import button as b18
from addons.unlockTest.ip_risk import button as b19
from addons.unlockTest.steam import button as b20
from addons.unlockTest.wikipedia import button as b21
from addons.unlockTest.openai import button as b25

b1 = InlineKeyboardButton("✅Netflix", callback_data='✅Netflix')
b2 = InlineKeyboardButton("✅Youtube", callback_data='✅Youtube')
b3 = InlineKeyboardButton("✅Disney+", callback_data='✅Disney+')
b4 = InlineKeyboardButton("✅Bilibili", callback_data='✅Bilibili')
b5 = InlineKeyboardButton("✅Dazn", callback_data='✅Dazn')
ok_b = InlineKeyboardButton("👌完成设置", callback_data='👌完成设置')
b_reverse = InlineKeyboardButton("🪞选项翻转", callback_data='🪞选项翻转')
yusanjia = InlineKeyboardButton("御三家(N-Y-D)", callback_data='御三家(N-Y-D)')
b_cancel = InlineKeyboardButton("👋点错了，给我取消", callback_data='👋点错了，给我取消')
b_alive = InlineKeyboardButton("节点存活率", callback_data="节点存活率")
b_okpage = InlineKeyboardButton("🔒锁定本页设置", callback_data="ok_p")
b_all = InlineKeyboardButton("全测", callback_data="全测")
b_origin = InlineKeyboardButton("♾️订阅原序", callback_data="sort:订阅原序")
b_rhttp = InlineKeyboardButton("⬇️HTTP倒序", callback_data="sort:HTTP倒序")
b_http = InlineKeyboardButton("⬆️HTTP升序", callback_data="sort:HTTP升序")
buttons = [b1, b2, b3, b25, b15, b18, b20, b21, b19]  # , b14, b5, b16, b17, b9, b13, b10, b12, b22, b23,
buttons.extend(addon.init_button(isreload=True))
max_page_g = int(len(buttons) / 9) + 1
blank_g = InlineKeyboardButton(f"{1}/{max_page_g}", callback_data="blank")
next_page_g = InlineKeyboardButton("➡️下一页", callback_data=f"page{2}")

IKM2 = InlineKeyboardMarkup(
    [
        # 第一行
        [b_origin],
        [b_rhttp, b_http],
        [b_cancel, ]
    ]
)
select_item_cache = {}
page_is_locked = {}
sort_cache = {}


def reload_button():
    global buttons
    buttons = [b1, b2, b3, b25, b18, b20, b15, b21, b19]
    buttons.extend(addon.init_button())


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
async def test_setting(client: Client, callback_query: CallbackQuery, row=3, **kwargs):
    """
    收到测试指令后对测试项进行动态调整
    :param client:
    :param callback_query:
    :return: test_items, origin_message, message, test_type
    """
    message = None
    test_items = []
    text = "请选择想要启用的测试项:"
    page = kwargs.get('page', 1)
    max_page = int(len(buttons) / (row * 3)) + 1
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
    try:
        if "✅" in callback_data:
            for b_1 in inline_keyboard:
                for b in b_1:
                    if b.text == callback_data:
                        b.text = b.text.replace("✅", "❌")
                        b.callback_data = b.text
                        IKM22 = InlineKeyboardMarkup(
                            inline_keyboard
                        )
                        await client.edit_message_text(chat_id=chat_id,
                                                       message_id=mess_id,
                                                       text=text,
                                                       reply_markup=IKM22)
            return test_items, origin_message, message, test_type
        elif "❌" in callback_data:
            for b_1 in inline_keyboard:
                for b in b_1:
                    if b.text == callback_data:
                        b.text = b.text.replace("❌", "✅")
                        b.callback_data = b.text
                        IKM22 = InlineKeyboardMarkup(
                            inline_keyboard
                        )
                        await client.edit_message_text(chat_id=chat_id,
                                                       message_id=mess_id,
                                                       text=text,
                                                       reply_markup=IKM22)
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
            IKM22 = InlineKeyboardMarkup(
                inline_keyboard
            )
            await client.edit_message_text(chat_id=chat_id,
                                           message_id=mess_id,
                                           text=text,
                                           reply_markup=IKM22)
            return test_items, origin_message, message, test_type
        elif "御三家(N-Y-D)" in callback_data:
            test_items.clear()
            test_items.extend(['HTTP延迟', 'Netflix', 'Youtube', 'Disney+'])
            message = await client.edit_message_text(chat_id=chat_id,
                                                     message_id=mess_id,
                                                     text="⌛正在提交任务~")
            return test_items, origin_message, message, test_type
        elif "节点存活率" in callback_data:
            test_items.clear()
            test_items.append('HTTP延迟')
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
        elif "全测" == callback_data:
            test_items = ['HTTP延迟']
            test_items += addon.global_test_item()
            message = await client.edit_message_text(chat_id, mess_id, text="⌛正在提交任务~")
            return test_items, origin_message, message, test_type
        elif 'ok_p' == callback_data:
            test_items = select_item_cache.get(str(chat_id) + ':' + str(mess_id), ['HTTP延迟'])
            for b_1 in inline_keyboard:
                for b in b_1:
                    if "✅" in b.text:
                        test_items.append(str(b.text)[1:])
            blank1 = InlineKeyboardButton("已完成本页提交", callback_data="blank")
            pre_page = InlineKeyboardButton("        ", callback_data="blank")
            next_page = InlineKeyboardButton("        ", callback_data="blank")
            blank = InlineKeyboardButton(f'{page}/{max_page}', callback_data='blank')
            for b_1 in inline_keyboard:
                for b in b_1:
                    if "⬅️上一页" == b.text:
                        pre_page = InlineKeyboardButton("⬅️上一页", callback_data=b.callback_data)
                    elif "➡️下一页" == b.text:
                        next_page = InlineKeyboardButton("➡️下一页", callback_data=b.callback_data)
                    elif f"/{max_page}" in b.text:
                        blank = InlineKeyboardButton(b.text, callback_data='blank')
                        page = str(b.text)[0]
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, next_page], [b_cancel, ok_b], ])
            # 设置状态
            select_item_cache[str(chat_id) + ':' + str(mess_id)] = test_items
            key = str(chat_id) + ':' + str(mess_id) + ':' + str(page)
            page_is_locked[key] = True
            await client.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=new_ikm)
            return test_items, origin_message, message, test_type
        elif "👌完成设置" in callback_data:
            test_items = select_item_cache.pop(str(chat_id) + ':' + str(mess_id), ['HTTP延迟'])
            message = await client.edit_message_text(chat_id, mess_id, "⌛正在提交任务~")
            issuc = []
            for i in range(max_page):
                res1 = page_is_locked.pop(str(chat_id) + ':' + str(mess_id) + ':' + str(i), '')
                if res1:
                    issuc.append(res1)
            if not issuc:
                logger.warning("资源回收失败")
            return test_items, origin_message, message, test_type
    except RPCError as r:
        logger.warning(str(r))
    finally:
        return test_items, origin_message, message, test_type


def get_keyboard(call: CallbackQuery):
    inline_keyboard = call.message.reply_markup.inline_keyboard
    return inline_keyboard


async def select_page(client: Client, call: CallbackQuery, **kwargs):
    page = kwargs.get('page', 1)
    row = kwargs.get('row', 3)
    chat_id = call.message.chat.id
    mess_id = call.message.id
    max_page = int(len(buttons) / (row * 3)) + 1
    pre_page = InlineKeyboardButton('⬅️上一页', callback_data=f'page{page - 1}')
    next_page = InlineKeyboardButton('➡️下一页', callback_data=f'page{page + 1}')
    blank1 = InlineKeyboardButton("已完成本页提交", callback_data="blank")
    blank_button = InlineKeyboardButton('        ', callback_data=f'blank')
    blank = InlineKeyboardButton(f'{page}/{max_page}', callback_data=f'blank')
    if page == 1:
        if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
            if max_page == 1:
                new_ikm = InlineKeyboardMarkup([[blank1], [blank_button, blank, blank_button],
                                                [b_cancel, b_reverse], [ok_b]])
            else:
                new_ikm = InlineKeyboardMarkup([[blank1], [b_all, blank, next_page],
                                                [b_cancel, ok_b]])
        else:
            keyboard = [[b_okpage]]
            if len(buttons) > 8:
                first_row = deepcopy(buttons[:3])
                second_row = deepcopy(buttons[3:6])
                third_row = deepcopy(buttons[6:9])
                keyboard.append(first_row)
                keyboard.append(second_row)
                keyboard.append(third_row)
            if max_page == 1:
                keyboard.append([blank_button, blank, blank_button])
            else:
                keyboard.append([b_all, blank, next_page])
            keyboard.append([yusanjia, b_alive])
            keyboard.append([b_cancel, b_reverse])
            keyboard.append([ok_b])
            new_ikm = InlineKeyboardMarkup(keyboard)
    elif page == max_page:
        if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, blank_button], [b_cancel, ok_b]])
        else:
            keyboard = [[b_okpage]]
            sindex = (page - 1) * row * 3
            first_row = deepcopy(buttons[sindex:sindex + 3])
            second_row = deepcopy(buttons[sindex + 3:sindex + 6])
            third_row = deepcopy(buttons[sindex + 6:sindex + 9])
            keyboard.append(first_row)
            keyboard.append(second_row)
            keyboard.append(third_row)
            keyboard.append([pre_page, blank, blank_button])
            keyboard.append([b_cancel, b_reverse])
            keyboard.append([ok_b])
            new_ikm = InlineKeyboardMarkup(keyboard)
    else:
        if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, next_page], [b_cancel, ok_b]])
        else:
            keyboard = [[b_okpage]]
            sindex = (page - 1) * row * 3
            first_row = deepcopy(buttons[sindex:sindex + 3])
            second_row = deepcopy(buttons[sindex + 3:sindex + 6])
            third_row = deepcopy(buttons[sindex + 6:sindex + 9])
            keyboard.append(first_row)
            keyboard.append(second_row)
            keyboard.append(third_row)
            keyboard.append([pre_page, blank, next_page])
            keyboard.append([b_cancel, b_reverse])
            keyboard.append([ok_b])
            new_ikm = InlineKeyboardMarkup(keyboard)
    await client.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=new_ikm)


def get_sort_str(message: Message):
    k = str(message.chat.id) + ":" + str(message.id)
    return sort_cache.pop(k, "订阅原序")


async def select_sort(app: Client, call: CallbackQuery):
    IKM = InlineKeyboardMarkup(
        [
            # 第一行
            [b_okpage],
            [b1, b2, b3],
            # 第二行
            [b20, b25, b18],
            [b15, b21, b19],
            [b_all, blank_g, next_page_g],
            [yusanjia, b_alive],
            [b_cancel, b_reverse],
            [ok_b]
        ]
    )
    sort_str = str(call.data)[5:]
    chat_id = call.message.chat.id
    mess_id = call.message.id
    sort_cache[str(chat_id) + ":" + str(mess_id)] = sort_str
    await app.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=IKM)


async def setting_page(_: Client, message: Message):
    text = config.config.get('bot', {}).get('description', f"🛠️FullTclash bot管理总枢🛠️\n\n版本: {__version__}({v_hash})")
    addon_button = InlineKeyboardButton("🧰插件管理(开发中)", callback_data="blank")
    config_button = InlineKeyboardButton("⚙️配置管理(开发中)", callback_data="blank")
    sub_button = InlineKeyboardButton("🌐订阅管理(开发中)", callback_data="blank")
    IKM = InlineKeyboardMarkup([[addon_button], [config_button], [sub_button]])
    await message.reply_text(text, reply_markup=IKM, quote=True)
