import asyncio
import contextlib
from copy import deepcopy
from typing import Union, List

import async_timeout
from loguru import logger
from pyrogram import types, Client
from pyrogram.errors import RPCError
from pyrogram.types import BotCommand, CallbackQuery, Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton as IKB
from pyrogram.handlers import CallbackQueryHandler
from utils.cleaner import addon, config, ArgCleaner
from utils.myqueue import bot_put
from utils.check import get_telegram_id_from_message as getID
from utils import message_delete_queue as mdq
from glovar import __version__
from botmodule.rule import get_rule

from botmodule.init_bot import latest_version_hash as v_hash
from botmodule.command.authority import (Invite, INVITE_SELECT_CACHE as ISC,
                                         BOT_MESSAGE_CACHE, generate_random_string as genkey)

dsc = default_slave_comment = config.getSlaveconfig().get('default-slave', {}).get('comment', "本地后端")
dsi = default_slave_id = config.getSlaveconfig().get('default-slave', {}).get('username', "local")
dbtn = default_button = {
    1: IKB("✅Netflix", callback_data='✅Netflix'),
    2: IKB("✅Youtube", callback_data='✅Youtube'),
    3: IKB("✅Disney+", callback_data='✅Disney+'),
    15: IKB("✅TVB", callback_data="✅TVB"),
    18: IKB("✅Viu", callback_data="✅Viu"),
    19: IKB("✅落地IP风险", callback_data="✅落地IP风险"),
    20: IKB("✅steam货币", callback_data="✅steam货币"),
    21: IKB("✅维基百科", callback_data="✅维基百科"),
    25: IKB("✅OpenAI", callback_data="✅OpenAI"),
    'ok_b': IKB("👌完成设置", callback_data='👌完成设置'),
    'b_reverse': IKB("🪞选项翻转", callback_data='🪞选项翻转'),
    'yusanjia': IKB("御三家(N-Y-D)", callback_data='御三家(N-Y-D)'),
    'b_cancel': IKB("👋点错了，给我取消", callback_data='👋点错了，给我取消'),
    'b_alive': IKB("节点存活率", callback_data="节点存活率"),
    'b_okpage': IKB("🔒锁定本页设置", callback_data="ok_p"),
    'b_all': IKB("全测", callback_data="全测"),
    'b_origin': IKB("♾️订阅原序", callback_data="sort:订阅原序"),
    'b_rhttp': IKB("⬇️HTTP倒序", callback_data="sort:HTTP倒序"),
    'b_http': IKB("⬆️HTTP升序", callback_data="sort:HTTP升序"),
    'b_slave': IKB(dsc, "slave:" + dsi),
    'b_close': IKB("❌关闭页面", callback_data="close"),
    'upper': IKB("⬆️返回上一层", callback_data="preconfig"),
    'b_del_conf': IKB("删除配置", callback_data="del_config"),
    'b_edit_conf': IKB("修改配置", callback_data="edit_config"),
    'b_add_conf': IKB("新增配置", callback_data="add_config"),
}

buttons = [dbtn[1], dbtn[2], dbtn[3], dbtn[25], dbtn[15], dbtn[18], dbtn[20], dbtn[21], dbtn[19]]
buttons.extend(addon.init_button(isreload=True))
max_page_g = int(len(buttons) / 9) + 1
blank_g = IKB(f"{1}/{max_page_g}", callback_data="blank")
next_page_g = IKB("下一页➡️", callback_data=f"page{2}")

IKM2 = InlineKeyboardMarkup(
    [
        # 第一行
        [dbtn['b_origin']],
        [dbtn['b_rhttp'], dbtn['b_http']],
        [dbtn['b_cancel']]
    ]
)

sc = select_cache = {
    # 所有的记录都以 "{chat_id}:{message_id}"作为键
    'script': {},  # 脚本选择
    'lpage': {},  # 记录当前页面是否已锁定
    'sort': {},  # 记录排序选择
    'slaveid': {},  # 记录后端id选择
}
api_route = '/api/getSlaveId'
receiver = {}


def reload_button():
    global buttons
    buttons = [dbtn[1], dbtn[2], dbtn[3], dbtn[25], dbtn[15], dbtn[18], dbtn[20], dbtn[21], dbtn[19]]
    buttons.extend(addon.init_button())


async def editkeybord1(_: Client, callback_query: CallbackQuery, mode=0):
    """
    反转✅和❌
    param: mode=0 把✅变成❌，否则把❌变成✅
    """
    callback_data = str(callback_query.data)
    edit_mess = callback_query.message
    edit_text = edit_mess.text
    inline_keyboard = callback_query.message.reply_markup.inline_keyboard
    for b_1 in inline_keyboard:
        for b in b_1:
            if b.text == callback_data:
                b.text = b.text.replace("✅", "❌") if mode == 0 else b.text.replace("❌", "✅")
                b.callback_data = b.text
                IKM22 = InlineKeyboardMarkup(inline_keyboard)
                await edit_mess.edit_text(edit_text, reply_markup=IKM22)


async def editkeybord_reverse(_: Client, callback_query: CallbackQuery):
    """
    翻转所有涉及✅和❌ 的键
    """
    edit_mess = callback_query.message
    edit_text = edit_mess.text
    inline_keyboard = callback_query.message.reply_markup.inline_keyboard
    for b_1 in inline_keyboard:
        for b in b_1:
            if "❌" in b.text:
                b.text = b.text.replace("❌", "✅")
                b.callback_data = b.text
            elif "✅" in b.text:
                b.text = b.text.replace("✅", "❌")
                b.callback_data = b.text
    IKM22 = InlineKeyboardMarkup(inline_keyboard)
    await edit_mess.edit_text(edit_text, reply_markup=IKM22)


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
    page = kwargs.get('page', 1)
    max_page = int(len(buttons) / (row * 3)) + 1
    callback_data = callback_query.data
    edit_mess = callback_query.message
    mess_id = callback_query.message.id
    chat_id = callback_query.message.chat.id
    origin_message = callback_query.message.reply_to_message
    inline_keyboard = callback_query.message.reply_markup.inline_keyboard

    with contextlib.suppress(IndexError, ValueError):
        test_type = origin_message.text.split(" ", maxsplit=1)[0].split("@", maxsplit=1)[0]
    if origin_message is None:
        logger.warning("⚠️无法获取发起该任务的源消息")
        await edit_mess.edit_text("⚠️无法获取发起该任务的源消息")
        return test_items, origin_message, message, test_type
    try:
        if "✅" in callback_data:
            await editkeybord1(client, callback_query, mode=0)
            return test_items, origin_message, message, test_type
        elif "❌" in callback_data:
            await editkeybord1(client, callback_query, mode=1)
            return test_items, origin_message, message, test_type
        elif "🪞选项翻转" in callback_data:
            message = await editkeybord_reverse(client, callback_query)
            return test_items, origin_message, message, test_type
        elif "御三家(N-Y-D)" in callback_data:
            test_items.clear()
            test_items.extend(['HTTP(S)延迟', 'Netflix', 'Youtube', 'Disney+'])
            message = await edit_mess.edit_text("⌛正在提交任务~")
            return test_items, origin_message, message, test_type
        elif "节点存活率" in callback_data:
            test_items.clear()
            test_items.append('HTTP(S)延迟')
            message = await edit_mess.edit_text("⌛正在提交任务~")
            return test_items, origin_message, message, test_type
        elif "👋点错了，给我取消" in callback_data:
            message = await edit_mess.edit_text("❌任务已取消")
            mdq.put_nowait((message.chat.id, message.id, 10))
            message = None
            return test_items, origin_message, message, test_type
        elif "全测" == callback_data:
            test_items = ['HTTP(S)延迟']
            test_items += addon.global_test_item()
            message = await edit_mess.edit_text("⌛正在提交任务~")
            return test_items, origin_message, message, test_type
        elif 'ok_p' == callback_data:
            test_items = sc['script'].get(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
            # test_items = select_item_cache.get(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
            for b_1 in inline_keyboard:
                for b in b_1:
                    if "✅" in b.text:
                        test_items.append(str(b.text)[1:])
            blank1 = IKB("已完成本页提交", callback_data="blank")
            pre_page = IKB("        ", callback_data="blank")
            next_page = IKB("        ", callback_data="blank")
            blank = IKB(f'{page}/{max_page}', callback_data='blank')
            for b_1 in inline_keyboard:
                for b in b_1:
                    if "⬅️上一页" == b.text:
                        pre_page = IKB("⬅️上一页", callback_data=b.callback_data)
                    elif "下一页➡️" == b.text:
                        next_page = IKB("下一页➡️", callback_data=b.callback_data)
                    elif f"/{max_page}" in b.text:
                        blank = IKB(b.text, callback_data='blank')
                        page = str(b.text)[0]
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, next_page], [dbtn['b_cancel'], dbtn['ok_b']], ])
            # 设置状态
            sc['script'][str(chat_id) + ':' + str(mess_id)] = test_items
            # select_item_cache[str(chat_id) + ':' + str(mess_id)] = test_items
            key = str(chat_id) + ':' + str(mess_id) + ':' + str(page)
            sc['lpage'][key] = True
            # page_is_locked[key] = True
            await client.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=new_ikm)
            return test_items, origin_message, message, test_type
        elif "👌完成设置" in callback_data:
            test_items = sc['script'].pop(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
            # test_items = select_item_cache.pop(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
            message = await client.edit_message_text(chat_id, mess_id, "⌛正在提交任务~")
            issuc = []
            for i in range(max_page):
                res1 = sc['lpage'].pop(str(chat_id) + ':' + str(mess_id) + ':' + str(i), '')
                # res1 = page_is_locked.pop(str(chat_id) + ':' + str(mess_id) + ':' + str(i), '')
                if res1:
                    issuc.append(res1)
            if not issuc:
                if test_items[0] != 'HTTP(S)延迟':
                    logger.warning("资源回收失败")
            return test_items, origin_message, message, test_type
    except RPCError as r:
        logger.warning(str(r))
    finally:
        return test_items, origin_message, message, test_type


def get_keyboard(call: CallbackQuery):
    inline_keyboard = call.message.reply_markup.inline_keyboard
    return inline_keyboard


@logger.catch()
async def select_page(client: Client, call: CallbackQuery, **kwargs):
    page = kwargs.get('page', 1)
    row = kwargs.get('row', 3)
    chat_id = call.message.chat.id
    mess_id = call.message.id
    msgkey = str(chat_id) + ':' + str(mess_id) + ':' + str(page)
    max_page = int(len(buttons) / (row * 3)) + 1
    pre_page = IKB('⬅️上一页', callback_data=f'page{page - 1}')
    next_page = IKB('下一页➡️', callback_data=f'page{page + 1}')
    blank1 = IKB("已完成本页提交", callback_data="blank")
    blank_button = IKB('        ', callback_data='blank')
    blank = IKB(f'{page}/{max_page}', callback_data='blank')
    if page == 1:
        sc['lpage'].get(msgkey, False)
        # if page_is_locked.get(msgkey, False):
        if sc['lpage'].get(msgkey, False):
            if max_page == 1:
                new_ikm = InlineKeyboardMarkup([[blank1],
                                                [blank_button, blank, blank_button],
                                                [dbtn['b_cancel'], dbtn['b_reverse']], dbtn['ok_b']])
            else:
                new_ikm = InlineKeyboardMarkup([[blank1],
                                                [dbtn['b_all'], blank, next_page],
                                                [dbtn['b_cancel'], dbtn['ok_b']]])
        else:
            keyboard = [[dbtn['b_okpage']]]
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
                keyboard.append([dbtn['b_all'], blank, next_page])
            keyboard.append([dbtn['yusanjia'], dbtn['b_alive']])
            keyboard.append([dbtn['b_cancel'], dbtn['b_reverse']])
            keyboard.append([dbtn['ok_b']])
            new_ikm = InlineKeyboardMarkup(keyboard)
    elif page == max_page:
        # if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
        if sc['lpage'].get(msgkey, False):
            new_ikm = InlineKeyboardMarkup([[blank1],
                                            [pre_page, blank, blank_button],
                                            [dbtn['b_cancel'], dbtn['ok_b']]])
        else:
            keyboard = [[dbtn['b_okpage']]]
            sindex = (page - 1) * row * 3
            first_row = deepcopy(buttons[sindex:sindex + 3])
            second_row = deepcopy(buttons[sindex + 3:sindex + 6])
            third_row = deepcopy(buttons[sindex + 6:sindex + 9])
            keyboard.append(first_row)
            keyboard.append(second_row)
            keyboard.append(third_row)
            keyboard.append([pre_page, blank, blank_button])
            keyboard.append([dbtn['b_cancel'], dbtn['b_reverse']])
            keyboard.append([dbtn['ok_b']])
            new_ikm = InlineKeyboardMarkup(keyboard)
    else:
        # if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
        if sc['lpage'].get(msgkey, False):
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, next_page], [dbtn['b_cancel'], dbtn['ok_b']]])
        else:
            keyboard = [[dbtn['b_okpage']]]
            sindex = (page - 1) * row * 3
            first_row = deepcopy(buttons[sindex:sindex + 3])
            second_row = deepcopy(buttons[sindex + 3:sindex + 6])
            third_row = deepcopy(buttons[sindex + 6:sindex + 9])
            keyboard.append(first_row)
            keyboard.append(second_row)
            keyboard.append(third_row)
            keyboard.append([pre_page, blank, next_page])
            keyboard.append([dbtn['b_cancel'], dbtn['b_reverse']])
            keyboard.append([dbtn['ok_b']])
            new_ikm = InlineKeyboardMarkup(keyboard)
    await client.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=new_ikm)


def gen_msg_key(message: Message) -> str:
    """
    生成针对此消息对象的唯一键
    """
    return str(message.chat.id) + ":" + str(message.id)


def get_sort_str(message: Message) -> str:
    k = gen_msg_key(message)
    return sc['sort'].pop(k, "订阅原序")


# def get_slave_id(chat_id: int, message_id: int) -> str:
#     k = str(chat_id) + ":" + str(message_id)
#     return sc['slaveid'].pop(k, "local")


def get_slave_id(message: Message) -> str:
    k = gen_msg_key(message)
    return sc['slaveid'].pop(k, "local")


def page_frame(pageprefix: str, contentprefix: str, content: List[str], split: str = ':', **kwargs) -> list:
    """
    翻页框架，返回一个内联键盘列表：[若干行的内容按钮,(上一页、页数预览、下一页）按钮]
    pageprefix: 页面回调数据的前缀字符串
    contentprefix: 具体翻页内容的回调数据的前缀字符串
    """
    page = int(kwargs.get('page', 1))
    row = int(kwargs.get('row', 5))
    column = int(kwargs.get('column', 1))
    max_page = int(len(content) / (row * column)) + 1
    pre_page_text = page - 1 if page - 1 > 0 else 1
    next_page_text = page + 1 if page < max_page else max_page
    pre_page = IKB('⬅️上一页', callback_data=f'{pageprefix}{pre_page_text}')
    next_page = IKB('下一页➡️', callback_data=f'{pageprefix}{next_page_text}')
    preview = IKB(f'{page}/{max_page}', callback_data='blank')

    if page > max_page:
        logger.error("页数错误")
        return []
    if page == 1:
        pre_page.text = '        '
        pre_page.callback_data = 'blank'

    if page == max_page:
        next_page.text = '        '
        next_page.callback_data = 'blank'
        content_keyboard = []
        temp_row = []
        for i, c in enumerate(content[(max_page - 1) * row * column:]):
            if i % column == 0 and i != 0:
                content_keyboard.append(deepcopy(temp_row))
                temp_row.clear()
            temp_row.append(IKB(c, f'{contentprefix}{split}{c}'))
        content_keyboard.append(deepcopy(temp_row))
    else:
        content_keyboard = []
        temp_row = []
        for i, c in enumerate(content[(page - 1) * row * column:page * row * column]):
            if i % column == 0 and i != 0:
                content_keyboard.append(deepcopy(temp_row))
                temp_row.clear()
            temp_row.append(IKB(c, f'{contentprefix}{split}{c}'))
        content_keyboard.append(deepcopy(temp_row))
    content_keyboard.append([pre_page, preview, next_page])
    return content_keyboard


async def task_handler(app: Client, message: Message, **kwargs):
    userconfig = config.getUserconfig()
    ruleconfig = userconfig.get('rule', {})
    ID = str(getID(message))
    tgargs = ArgCleaner.getarg(message.text)
    rulename = ''
    if tgargs[0].startswith("/invite"):
        rulename = tgargs[1] if len(tgargs) > 1 else ''
    if rulename and (rulename in ruleconfig):
        slaveid, sort, script = get_rule(rulename)
        if slaveid is None and sort is None and script is None:
            await select_slave_page(app, message, **kwargs)
            return
        await select_task(app, message, slaveid, sort, script)
    elif ID in ruleconfig:
        slaveid, sort, script = get_rule(ID)
        if slaveid is None and sort is None and script is None:
            await select_slave_page(app, message, **kwargs)
            return
        await select_task(app, message, slaveid, sort, script)
    else:
        await select_slave_page(app, message, **kwargs)


async def select_slave_page(_: Client, call: Union[CallbackQuery, Message], content_prefix: str = "slave:", **kwargs):
    """
    选择后端页面的入口
    content_prefix: 后端的回调按钮数据的前缀，默认为slave:
    """
    slaveconfig = config.getSlaveconfig()

    comment = [i.get('comment', None) for k, i in slaveconfig.items() if
               i.get('comment', None) and k != "default-slave"]

    page = kwargs.get('page', 1)
    row = kwargs.get('row', 5)
    max_page = int(len(comment) / row) + 1
    pre_page_text = page - 1 if page - 1 > 0 else 1
    next_page_text = page + 1 if page < max_page else max_page
    pre_page = IKB('⬅️上一页', callback_data=f'spage{pre_page_text}')
    next_page = IKB('下一页➡️', callback_data=f'spage{next_page_text}')
    blank = IKB(f'{page}/{max_page}', callback_data='blank')

    if page > max_page:
        logger.error("页数错误")
        return
    if page == 1:
        pre_page.text = '        '
        pre_page.callback_data = 'blank'
    if page == max_page:
        content_keyboard = [[IKB(c, content_prefix + c)] for c in comment[(max_page - 1) * row:]]
        next_page.text = '        '
        next_page.callback_data = 'blank'
    else:
        content_keyboard = [[IKB(c, content_prefix + c)] for c in comment[(page - 1) * row:page * row]]
    content_keyboard.insert(0, [dbtn['b_slave']])
    content_keyboard.append([pre_page, blank, next_page])
    content_keyboard.append([dbtn['b_cancel']])
    IKM = InlineKeyboardMarkup(content_keyboard)
    if isinstance(call, CallbackQuery):
        botmsg = call.message
        await botmsg.edit_text("请选择测试后端:", reply_markup=IKM)
    else:
        await call.reply("请选择测试后端:", reply_markup=IKM, quote=True)


async def select_task(app: Client, originmsg: Message, slaveid: str, sort: str, script: list = None):
    if originmsg.text.startswith('/invite'):
        comment = config.getSlavecomment(slaveid)
        scripttext = ",".join(script) if script is not None else ""
        invite_help_text = f"🍀选中后端: {comment}\n⛓️选中排序: {sort}\n🧵选中脚本: {scripttext}\n\n"
        botmsg = await originmsg.reply(invite_help_text)
        await asyncio.sleep(2)
        key = genkey(8)
        BOT_MESSAGE_CACHE[key] = botmsg
        await Invite(key=key).invite(app, originmsg)
    elif originmsg.text.startswith('/test'):
        put_type = "testurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "test"
        await bot_put(app, originmsg, put_type, script, sort=sort, coreindex=3, slaveid=slaveid)
    elif originmsg.text.startswith('/topo') or originmsg.text.startswith('/analyze'):
        put_type = "analyzeurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "analyze"
        await bot_put(app, originmsg, put_type, None, sort=sort, coreindex=2, slaveid=slaveid)
    elif originmsg.text.startswith('/speed'):
        put_type = "speedurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "speed"
        await bot_put(app, originmsg, put_type, None, sort=sort, coreindex=1, slaveid=slaveid)
    else:
        await originmsg.reply("🐛暂时未适配")
        return


# async def select_slave_()
async def select_slave_only_pre(_: Client, call: Union[CallbackQuery, Message], **kwargs):
    """
    receiver: 指定一个列表变量，它将作为slaveid的接收者。
    """
    page_prefix = '/api/slave/page/'
    page = 1 if isinstance(call, Message) else call.data[len(page_prefix)]
    slaveconfig = config.getSlaveconfig()
    comment = [i.get('comment', None) for k, i in slaveconfig.items() if
               i.get('comment', None) and k != "default-slave"]
    content_keyboard = page_frame(page_prefix, api_route, comment, split='?comment=', page=page, **kwargs)
    content_keyboard.append([dbtn['b_close']])

    IKM = InlineKeyboardMarkup(content_keyboard)
    target = call.message if isinstance(call, CallbackQuery) else call
    if isinstance(call, CallbackQuery):
        await target.edit_text(target.text, reply_markup=IKM)
    else:
        return await target.reply(f"请选择测试后端, 你有{kwargs.get('timeout', 60)}s的时间选择:\n", quote=True, reply_markup=IKM)


async def get_s_id(_: Client, c: CallbackQuery):
    le = len(api_route) + len("?comment=")
    key = gen_msg_key(c.message)
    if key in receiver:
        q = receiver[key]
        try:
            if isinstance(q, asyncio.Queue):
                q.put_nowait(str(c.data)[le:])
        except asyncio.queues.QueueFull:
            return
    else:
        await c.message.reply("❌无法找到该消息与之对应的队列")


async def select_slave_only(app: Client, call: Union[CallbackQuery, Message], **kwargs) -> tuple[str, str]:
    """
    高层级的选择后端api

    return: (slaveid, comment)
    """
    timeout = 60
    botmsg = await select_slave_only_pre(app, call, timeout=timeout, **kwargs)

    recvkey = gen_msg_key(botmsg)
    q = asyncio.Queue(1)
    receiver[recvkey] = q

    try:
        async with async_timeout.timeout(timeout):
            comment = await q.get()
            slaveconfig = config.getSlaveconfig()
            slaveid = ''
            for k, v in slaveconfig.items():
                if v.get('comment', '') == comment:
                    slaveid = str(k)
                    break
            if slaveid and comment:
                await botmsg.delete()
                return str(slaveid), comment
            else:
                await botmsg.delete()
                return '', comment

    except asyncio.exceptions.TimeoutError:
        print("获取超时")
        return '', ''
    finally:
        receiver.pop(recvkey, None)


async def select_slave(app: Client, call: CallbackQuery):
    botmsg = call.message
    originmsg = call.message.reply_to_message
    slavename = call.data[6:]
    slaveconfig = config.getSlaveconfig()
    slaveid = 'local'
    for k, v in slaveconfig.items():
        if v.get('comment', '') == slavename:
            slaveid = str(k)
            break
    if not slaveid:
        await botmsg.edit_text("❌未知的后端id")
        mdq.put(botmsg)
        return
    sc['slaveid'][str(botmsg.chat.id) + ":" + str(botmsg.id)] = slaveid
    # slaveid_cache[str(botmsg.chat.id) + ":" + str(botmsg.id)] = slaveid
    if originmsg.text.startswith('/invite'):
        target = originmsg if originmsg.reply_to_message is None else originmsg.reply_to_message
        ISC['slaveid'][gen_msg_key(target)] = slaveid
        await botmsg.edit_text("请选择排序方式：", reply_markup=IKM2)
    elif originmsg.text.startswith('/test'):
        await botmsg.edit_text("请选择排序方式：", reply_markup=IKM2)
    elif originmsg.text.startswith('/topo') or originmsg.text.startswith('/analyze'):
        sort_str = get_sort_str(botmsg)
        slaveid = get_slave_id(botmsg)
        put_type = "analyzeurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "analyze"
        await botmsg.delete()
        await bot_put(app, originmsg, put_type, None, sort=sort_str, coreindex=2, slaveid=slaveid)
    elif originmsg.text.startswith('/speed'):
        sort_str = get_sort_str(botmsg)
        slaveid = get_slave_id(botmsg)
        put_type = "speedurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "speed"
        await botmsg.delete()
        await bot_put(app, originmsg, put_type, None, sort=sort_str, coreindex=1, slaveid=slaveid)
    else:
        await botmsg.edit_text("🐛暂时未适配")
        return


async def select_sort(app: Client, call: CallbackQuery):
    originmsg = call.message.reply_to_message
    sort_str = str(call.data)[5:]
    if originmsg.text.startswith('/invite'):
        ISC['sort'][gen_msg_key(originmsg)] = sort_str
        key = genkey(8)
        BOT_MESSAGE_CACHE[key] = call.message
        await Invite(key=key).invite(app, originmsg)
        return
    IKM = InlineKeyboardMarkup(
        [
            # 第一行
            [dbtn['b_okpage']],
            [dbtn[1], dbtn[2], dbtn[3]],
            # 第二行
            [dbtn[20], dbtn[25], dbtn[18]],
            [dbtn[15], dbtn[21], dbtn[19]],
            [dbtn['b_all'], blank_g, next_page_g],
            [dbtn['yusanjia'], dbtn['b_alive']],
            [dbtn['b_cancel'], dbtn['b_reverse']],
            [dbtn['ok_b']]
        ]
    )
    chat_id = call.message.chat.id
    mess_id = call.message.id
    # sort_cache[str(chat_id) + ":" + str(mess_id)] = sort_str
    sc['sort'][str(chat_id) + ":" + str(mess_id)] = sort_str
    await app.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=IKM)


async def setting_page(_: Client, message: Message):
    text = config.config.get('bot', {}).get('description', f"🛠️FullTclash bot管理总枢🛠️\n\n版本: {__version__}({v_hash})")
    addon_button = IKB("🧩插件管理(开发中)", callback_data="blank")
    config_button = IKB("⚙️配置管理", callback_data="setconfig")
    sub_button = IKB("🌐订阅管理(开发中)", callback_data="blank")
    slave_button = IKB("🧰后端管理(开发中)", callback_data="blank")
    IKM = InlineKeyboardMarkup([[addon_button], [config_button], [sub_button], [slave_button]])
    await message.reply_text(text, reply_markup=IKM, quote=True)


async def select_config_page(_: Client, callback: Union[CallbackQuery, Message], **kwargs):
    # page = kwargs.get('page', 1)
    # row = kwargs.get('row', 5)
    configkeys = list(config.config.keys())
    # max_page = int(len(configkeys) / row * 2) + 1
    content_keyboard = page_frame('cpage', 'config', configkeys, **kwargs)
    content_keyboard.append([dbtn['b_close']])

    IKM = InlineKeyboardMarkup(content_keyboard)
    if isinstance(callback, CallbackQuery):
        botmsg = callback.message
        await botmsg.edit_text(f"⚙️以下是配置项预览: \n\n共找到{len(configkeys)}条配置项", reply_markup=IKM)
    else:
        await callback.reply("请选择测试后端:", reply_markup=IKM, quote=True)
