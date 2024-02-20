import asyncio
import contextlib
import secrets
from copy import deepcopy
from typing import Union, List, Dict

import async_timeout
from loguru import logger
from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import BotCommand, CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton as IKB

from utils.cleaner import addon, ArgCleaner
from utils.myqueue import bot_put
from utils.check import get_telegram_id_from_message as getID
from utils import message_delete_queue as mdq
from glovar import __version__
from botmodule.record import get_slave_ranking
from botmodule.rule import get_rule, new_rule
from botmodule.init_bot import latest_version_hash as v_hash, config
from botmodule.command.authority import (Invite, INVITE_SELECT_CACHE as ISC,
                                         BOT_MESSAGE_CACHE, generate_random_string as genkey)

dsc = default_slave_comment = config.getSlaveconfig().get('default-slave', {}).get('comment', "本地后端")
dsi = default_slave_id = config.getSlaveconfig().get('default-slave', {}).get('username', "local")
ds_shadow = bool(config.getSlaveconfig().get('default-slave', {}).get('hidden', False))  # 是否隐藏默认后端
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
    'b_okpage': IKB("🔒完成本页选择", callback_data="ok_p"),
    'b_all': IKB("全测", callback_data="全测"),
    'b_origin': IKB("♾️订阅原序", callback_data="sort:订阅原序"),
    'b_rhttp': IKB("⬇️HTTP降序", callback_data="sort:HTTP降序"),
    'b_http': IKB("⬆️HTTP升序", callback_data="sort:HTTP升序"),
    'b_aspeed': IKB("⬆️平均速度升序", callback_data="sort:平均速度升序"),
    'b_arspeed': IKB("⬇️平均速度降序", callback_data="sort:平均速度降序"),
    'b_mspeed': IKB("⬆️最大速度升序", callback_data="sort:最大速度升序"),
    'b_mrspeed': IKB("⬇️最大速度降序", callback_data="sort:最大速度降序"),
    'b_slave': IKB(dsc, "slave:" + dsi),
    'b_close': IKB("❌关闭页面", callback_data="close"),
    'upper': IKB("⬆️返回上一层", callback_data="preconfig"),
    'b_del_conf': IKB("删除配置", callback_data="del_config"),
    'b_edit_conf': IKB("修改配置", callback_data="edit_config"),
    'b_add_conf': IKB("新增配置", callback_data="add_config"),
    8: IKB("👌完成选择", "/api/script/ok")
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
        [dbtn['b_aspeed'], dbtn['b_arspeed']],
        [dbtn['b_mspeed'], dbtn['b_mrspeed']],
        [dbtn['b_close']]
    ]
)

sc = select_cache = {
    # 所有的记录都以 "{chat_id}:{message_id}"作为键
    'script': {},  # 脚本选择
    'lpage': {},  # 记录当前页面是否已锁定
    'sort': {},  # 记录排序选择
    'slaveid': {},  # 记录后端id选择
}
receiver: Dict[str, asyncio.Queue] = {}  # 临时数据接收器


def reload_button():
    global buttons
    buttons = [dbtn[1], dbtn[2], dbtn[3], dbtn[25], dbtn[15], dbtn[18], dbtn[20], dbtn[21], dbtn[19]]
    buttons.extend(addon.init_button())


async def editkeybord_yes_or_no(_: Client, callback_query: CallbackQuery, mode=0):
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


async def setcommands(client: Client):
    await client.set_bot_commands(
        [
            BotCommand("help", "获取帮助"),
            BotCommand("start", "欢迎使用本机器人"),
            BotCommand("topo", "节点落地分析"),
            BotCommand("test", "进行流媒体测试"),
            BotCommand("setting", "bot的相关设置")
        ]
    )


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

    if origin_message is None:
        return test_items, origin_message, message, ''
    with contextlib.suppress(IndexError, ValueError):
        test_type = origin_message.text.split(" ", maxsplit=1)[0].split("@", maxsplit=1)[0] \
            if origin_message is not None else ''

    try:
        if "✅" == callback_data[0]:
            await editkeybord_yes_or_no(client, callback_query, mode=0)
            return test_items, origin_message, message, test_type
        elif "❌" == callback_data[0]:
            await editkeybord_yes_or_no(client, callback_query, mode=1)
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
            test_items += addon.global_test_item(httptest=True)
            if callback_query.message.reply_markup and callback_query.message.reply_markup.inline_keyboard:
                if callback_query.message.reply_markup.inline_keyboard[-1][-1].callback_data == "/api/script/ok":
                    bot_key = gen_msg_key(edit_mess)
                    if bot_key in receiver:
                        q = receiver[bot_key]
                        try:
                            if isinstance(q, asyncio.Queue):
                                q.put_nowait("*")
                            else:
                                await edit_mess.reply("运行发现逻辑错误，请联系管理员~")
                        except asyncio.queues.QueueFull:
                            pass
                    else:
                        await edit_mess.reply("❌无法找到该消息与之对应的队列")
                    return [], None, None, None
            message = await edit_mess.edit_text("⌛正在提交任务~")
            return test_items, origin_message, message, test_type
        elif 'ok_p' == callback_data:
            test_items = sc['script'].get(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
            ok_button = dbtn['ok_b']
            if callback_query.message.reply_markup and callback_query.message.reply_markup.inline_keyboard:
                if callback_query.message.reply_markup.inline_keyboard[-1][-1].callback_data == "/api/script/ok":
                    ok_button = dbtn[8]
            # test_items = select_item_cache.get(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
            for b_1 in inline_keyboard:
                for b in b_1:
                    if "✅" in b.text:
                        test_items.append(str(b.callback_data)[1:])
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
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, next_page], [dbtn['b_cancel'], ok_button], ])
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


@logger.catch()
async def select_page(client: Client, call: CallbackQuery, **kwargs):
    page = kwargs.get('page', 1)
    row = kwargs.get('row', 3)
    ok_button = dbtn['ok_b']
    if call.message.reply_markup and call.message.reply_markup.inline_keyboard:
        if call.message.reply_markup.inline_keyboard[-1][-1].callback_data == "/api/script/ok":
            ok_button = dbtn[8]
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
                                                [dbtn['b_cancel'], dbtn['b_reverse']], ok_button])
            else:
                new_ikm = InlineKeyboardMarkup([[blank1],
                                                [dbtn['b_all'], blank, next_page],
                                                [dbtn['b_cancel'], ok_button]])
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
            keyboard.append([ok_button])
            new_ikm = InlineKeyboardMarkup(keyboard)
    elif page == max_page:
        # if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
        if sc['lpage'].get(msgkey, False):
            new_ikm = InlineKeyboardMarkup([[blank1],
                                            [pre_page, blank, blank_button],
                                            [dbtn['b_cancel'], ok_button]])
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
            keyboard.append([ok_button])
            new_ikm = InlineKeyboardMarkup(keyboard)
    else:
        # if page_is_locked.get(str(chat_id) + ':' + str(mess_id) + ':' + str(page), False):
        if sc['lpage'].get(msgkey, False):
            new_ikm = InlineKeyboardMarkup([[blank1], [pre_page, blank, next_page], [dbtn['b_cancel'], ok_button]])
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
            keyboard.append([ok_button])
            new_ikm = InlineKeyboardMarkup(keyboard)
    await client.edit_message_text(chat_id, mess_id, "请选择想要启用的测试项: ", reply_markup=new_ikm)


def gen_msg_key(message: Message, offset: int = 0) -> str:
    """
    生成针对此消息对象的唯一键

    offset: message.id的偏移量
    """
    return str(message.chat.id) + ":" + str(message.id + offset)


def get_sort_str(message: Message) -> str:
    k = gen_msg_key(message)
    return sc['sort'].pop(k, "订阅原序")


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


def get_ranked_slave_list(slaveconf: dict, sorted_ranking: dict):
    new_dict = {}
    slaveconf_copy = deepcopy(slaveconf)
    for k, _ in sorted_ranking.items():
        if k in slaveconf_copy:
            new_dict[k] = slaveconf_copy.pop(k)
    new_dict.update(slaveconf_copy)
    return new_dict


async def select_slave_page(_: Client, call: Union[CallbackQuery, Message], content_prefix: str = "slave:", **kwargs):
    """
    选择后端页面的入口
    content_prefix: 后端的回调按钮数据的前缀，默认为slave:
    """
    slaveconfig = config.getSlaveconfig().copy()
    if "default-slave" in slaveconfig:
        slaveconfig.pop("default-slave")
    usermsg = call.message.reply_to_message if isinstance(call, CallbackQuery) else call
    user_ranking = get_slave_ranking(getID(usermsg))
    slaveconfig = get_ranked_slave_list(slaveconfig, user_ranking)
    comment = [i.get('comment', None) for k, i in slaveconfig.items() if i.get('comment', None)]

    page = int(kwargs.get('page', 1))
    row = int(kwargs.get('row', 5))
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
    if not ds_shadow:
        content_keyboard.insert(0, [dbtn['b_slave']])
    content_keyboard.append([pre_page, blank, next_page])
    content_keyboard.append([dbtn['b_cancel']])
    IKM = InlineKeyboardMarkup(content_keyboard)
    if isinstance(call, CallbackQuery):
        botmsg = call.message
        await botmsg.edit_text("请选择测试后端:", reply_markup=IKM)
    else:
        await call.reply("请选择测试后端:", reply_markup=IKM, quote=True)


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


async def select_task(app: Client, originmsg: Message, slaveid: str, sort: str, script: list = None):
    if originmsg.text.startswith('/invite'):
        comment = config.getSlavecomment(slaveid)
        if script is not None:
            tmp_script = deepcopy(script)[::-1]
            scripttext = ",".join(tmp_script[:10]) + f"...共{len(script)}个脚本" if len(script) > 10 else ",".join(script)
        else:
            scripttext = ''
        invite_help_text = f"🤖选中后端: {comment}\n⛓️选中排序: {sort}\n🧵选中脚本: {scripttext}\n\n"
        botmsg = await originmsg.reply(invite_help_text)
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
async def select_slave_only_1(_: Client, call: Union[CallbackQuery, Message], **kwargs):
    """
    receiver: 指定一个列表变量，它将作为slaveid的接收者。
    """
    page_prefix = '/api/slave/page/'
    api_route = '/api/getSlaveId'
    page = 1 if isinstance(call, Message) else int(call.data[len(page_prefix):])
    slaveconfig = config.getSlaveconfig().copy()
    if "default-slave" in slaveconfig:
        slaveconfig.pop("default-slave")
    usermsg = call.message.reply_to_message if isinstance(call, CallbackQuery) else call
    user_ranking = get_slave_ranking(getID(usermsg))
    slaveconfig = get_ranked_slave_list(slaveconfig, user_ranking)
    comment = [i.get('comment', None) for k, i in slaveconfig.items() if i.get('comment', None)]
    content_keyboard = page_frame(page_prefix, api_route, comment, split='?comment=', page=page, **kwargs)
    if page == 1:
        if not ds_shadow:
            localslave = IKB(dsc, api_route + "?comment=" + dsc)
            content_keyboard.insert(0, [localslave])
    content_keyboard.append([dbtn['b_close']])

    IKM = InlineKeyboardMarkup(content_keyboard)
    target = call.message if isinstance(call, CallbackQuery) else call
    if isinstance(call, CallbackQuery):
        await target.edit_text(target.text, reply_markup=IKM)
    else:
        return await target.reply(f"请选择测试后端:\n", quote=True, reply_markup=IKM)


async def select_slave_only(app: Client, call: Union[CallbackQuery, Message], timeout=60, **kwargs) -> tuple[str, str]:
    """
    高层级的选择后端api

    return: (slaveid, comment)
    """
    if isinstance(call, Message):
        botmsg = await select_slave_only_1(app, call, timeout=timeout, **kwargs)

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
                        if str(k) == "default-slave":
                            slaveid = 'local'
                            break
                        slaveid = str(k)
                        break
                if not slaveid and comment == "本地后端":
                    slaveid = "local"
                if slaveid and comment:
                    return str(slaveid), comment
                else:
                    await botmsg.delete()
                    return '', ''

        except asyncio.exceptions.TimeoutError:
            print("获取超时")
            return '', ''
        finally:
            receiver.pop(recvkey, None)
            await botmsg.delete(revoke=True)
    else:
        api_route = '/api/getSlaveId'
        le = len(api_route) + len("?comment=")
        key = gen_msg_key(call.message)
        if key in receiver:
            q = receiver[key]
            try:
                if isinstance(q, asyncio.Queue):
                    q.put_nowait(str(call.data)[le:])
            except asyncio.queues.QueueFull:
                pass
        else:
            await call.answer("❌无法找到该消息与之对应的队列")


async def select_script_only(_: "Client", call: Union["CallbackQuery", "Message"],
                             timeout: int = 120) -> Union[List[str], None]:
    """
    高层级的选择测试脚本api
    timeout: 获取的超时时间，超时返回None

    return: 包含选择的测试项列表
    """
    api_route = "/api/script/ok"
    if isinstance(call, Message):
        IKM = InlineKeyboardMarkup(
            [
                # 第一行
                [dbtn['b_okpage']],
                [dbtn[1], dbtn[2], dbtn[3]],
                # 第二行
                [dbtn[20], dbtn[25], dbtn[18]],
                [dbtn[15], dbtn[21], dbtn[19]],
                [dbtn['b_all'], blank_g, next_page_g],
                [dbtn['b_cancel'], dbtn['b_reverse']],
                [IKB("👌完成选择", api_route)]
            ]
        )
        botmsg = await call.reply(f"请选择想要启用的测试项: ", reply_markup=IKM, quote=True)
        recvkey = gen_msg_key(botmsg)
        q = asyncio.Queue(1)
        receiver[recvkey] = q

        try:
            async with async_timeout.timeout(timeout):
                script_list = await q.get()
                if isinstance(script_list, list):
                    return script_list
                elif isinstance(script_list, str):
                    if script_list == "全测" or script_list == "all" or script_list == "*":
                        script = addon.global_test_item(True)
                    else:
                        new_script = [s for s in addon.global_test_item(True) if script_list in s]
                        script = new_script
                    return script
                else:
                    await botmsg.reply("❌数据类型接收错误")
                    return None

        except asyncio.exceptions.TimeoutError:
            print("获取超时")
            return None
        finally:
            receiver.pop(recvkey, None)
            await botmsg.delete(revoke=True)

    else:
        bot_key = gen_msg_key(call.message)
        test_items = sc['script'].pop(bot_key, ['HTTP(S)延迟'])
        # test_items = select_item_cache.pop(str(chat_id) + ':' + str(mess_id), ['HTTP(S)延迟'])
        # message = await client.edit_message_text(chat_id, mess_id, "⌛正在提交任务~")
        issuc = []
        row = 3
        max_page = int(len(buttons) / (row * 3)) + 1
        for i in range(max_page):
            res1 = sc['lpage'].pop(bot_key + ':' + str(i), '')
            # res1 = page_is_locked.pop(str(chat_id) + ':' + str(mess_id) + ':' + str(i), '')
            if res1:
                issuc.append(res1)
        if not issuc:
            if test_items[0] != 'HTTP(S)延迟':
                logger.warning("资源回收失败")

        if bot_key in receiver:
            q = receiver[bot_key]
            try:
                if isinstance(q, asyncio.Queue):
                    q.put_nowait(test_items)
                else:
                    await call.message.reply("运行发现逻辑错误，请联系管理员~")
            except asyncio.queues.QueueFull:
                pass
        else:
            await call.answer("❌无法找到该消息与之对应的队列")


async def select_sort_only(_: "Client", call: Union["CallbackQuery", "Message"],
                           timeout: int = 60, speed: bool = False) -> str:
    """
    高层级的选择排序api
    timeout: 获取的超时时间，超时返回空字符串
    speed: 是否是speed的排序

    return: 排序字符串: ["订阅原序", "HTTP升序", "HTTP降序", ...]
    """
    api_route = "/api/sort/"
    if isinstance(call, Message):

        content_keyboard = [
            [IKB("♾️订阅原序", f"{api_route}origin")],
            [IKB("⬇️HTTP降序", f"{api_route}rhttp"), IKB("⬆️HTTP升序", f"{api_route}http")],
        ]
        if speed:
            content_keyboard.append([IKB("⬆️平均速度升序", f"{api_route}aspeed"),
                                     IKB("⬇️平均速度降序", f"{api_route}arspeed")])
            content_keyboard.append([IKB("⬆️最大速度升序", f"{api_route}mspeed"),
                                     IKB("⬇️最大速度降序", f"{api_route}mrspeed")])
        content_keyboard.append([dbtn['b_close']])
        botmsg = await call.reply(f"请选择排序方式: ",
                                  reply_markup=InlineKeyboardMarkup(content_keyboard), quote=True)
        recvkey = gen_msg_key(botmsg)
        q = asyncio.Queue(1)
        receiver[recvkey] = q

        try:
            sort_str_parser = {
                "origin": "订阅原序",
                "rhttp": "HTTP降序",
                "http": "HTTP升序",
                "aspeed": "平均速度升序",
                "arspeed": "平均速度降序",
                "mspeed": "最大速度升序",
                "mrspeed": "最大速度降序",
            }
            async with async_timeout.timeout(timeout):
                sort_str = await q.get()
                sort_str = sort_str_parser.get(sort_str, "")
                return sort_str

        except asyncio.exceptions.TimeoutError:
            print("获取超时")
            return ""
        finally:
            await botmsg.delete(revoke=True)
            receiver.pop(recvkey, None)

    elif isinstance(call, CallbackQuery):
        key = gen_msg_key(call.message)
        le = len(api_route)
        if key in receiver:
            q = receiver[key]
            try:
                if isinstance(q, asyncio.Queue):
                    q.put_nowait(call.data[le:])
            except asyncio.queues.QueueFull:
                pass
        else:
            await call.answer("❌无法找到该消息与之对应的队列")


async def select_slave(app: Client, call: CallbackQuery):
    """
    内置的旧版选择后端回调查询
    """
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
        await botmsg.edit_text("请选择排序方式(速度相关的排序无效): ", reply_markup=IKM2)
    elif originmsg.text.startswith('/topo') or originmsg.text.startswith('/analyze'):
        sort_str = get_sort_str(botmsg)
        slaveid = get_slave_id(botmsg)
        put_type = "analyzeurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "analyze"
        await botmsg.delete()
        await bot_put(app, originmsg, put_type, None, sort=sort_str, coreindex=2, slaveid=slaveid)
    elif originmsg.text.startswith('/speed'):
        slaveid = get_slave_id(botmsg)
        await botmsg.delete()
        sort_str = await select_sort_only(app, call.message, 20, speed=True)
        if sort_str:
            put_type = "speedurl" if originmsg.text.split(' ', 1)[0].split('@', 1)[0].endswith('url') else "speed"
            await bot_put(app, originmsg, put_type, None, sort=sort_str, coreindex=1, slaveid=slaveid)
        # else:
        #     b = await botmsg.reply("❌选择超时，已取消任务。")
        #     mdq.put(b, 5)
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


async def home_setting(_: Client, call: Union[Message, CallbackQuery]):
    text = config.config.get('bot', {}).get('description', f"🛠️FullTclash bot管理总枢🛠️\n\n版本: {__version__}({v_hash})")
    addon_button = IKB("🧩插件管理(开发中)", callback_data="blank")
    config_button = IKB("⚙️配置管理", callback_data="/api/config/home")
    sub_button = IKB("🌐订阅管理(开发中)", callback_data="blank")
    slave_button = IKB("🧰后端管理(开发中)", callback_data="blank")
    rule_button = IKB("🚦规则管理", callback_data="/api/rule/home")
    IKM = InlineKeyboardMarkup([[addon_button], [config_button], [sub_button], [slave_button], [rule_button]])
    if isinstance(call, CallbackQuery):
        await call.message.edit_text(text, reply_markup=IKM)
    else:
        await call.reply_text(text, reply_markup=IKM, quote=True)


async def select_config_page(_: Client, call: Union[CallbackQuery, Message], **kwargs):
    # page = kwargs.get('page', 1)
    # row = kwargs.get('row', 5)
    page_prefix = "/api/config/page/"
    contentprefix = '/api/config/getConfig'
    page = 1 if isinstance(call, Message) else 1 \
        if call.data == "/api/config/home" else int(call.data[len(page_prefix):])
    configkeys = list(config.config.keys())
    # max_page = int(len(configkeys) / row * 2) + 1
    content_keyboard = page_frame(page_prefix, contentprefix, configkeys, "?key=", page=page, **kwargs)
    content_keyboard.append([IKB("🔙返回上一级", "/api/setting/home"), dbtn['b_close']])

    IKM = InlineKeyboardMarkup(content_keyboard)
    if isinstance(call, CallbackQuery):
        botmsg = call.message
        await botmsg.edit_text(f"⚙️以下是配置项预览: \n\n共找到{len(configkeys)}条配置项", reply_markup=IKM)
    else:
        await call.reply("⚙️以下是配置项预览: \n\n共找到{len(configkeys)}条配置项", reply_markup=IKM, quote=True)


async def home_rule(_: Client, call: Union[CallbackQuery, Message], **kwargs):
    page_prefix = "/api/rule/page/"
    api_route = '/api/rule/getrule'
    msg = call.message if isinstance(call, CallbackQuery) else call
    page = 1 if isinstance(call, Message) else 1 if call.data == "/api/rule/home" else int(call.data[len(page_prefix):])
    rule_conf = config.getUserconfig().get('rule', {})
    if not isinstance(rule_conf, dict):
        logger.warning("配置文件反序列化类型错误！")
        return
    rulename = list(rule_conf.keys())
    bot_text = f"当前已注册{len(rulename)}条规则，点击具体规则了解详细信息"
    content_keyboard = page_frame(page_prefix, api_route, rulename, split='?name=', page=page, **kwargs)
    content_keyboard.append([IKB("🔙返回上一级", "/api/setting/home"), dbtn['b_close']])
    content_keyboard.insert(0, [IKB("新增规则", "/api/rule/new")])
    if isinstance(call, CallbackQuery):
        await msg.edit_text(bot_text, reply_markup=InlineKeyboardMarkup(content_keyboard))
    else:
        await msg.reply(bot_text, reply_markup=InlineKeyboardMarkup(content_keyboard), quote=True)


async def recv_data(_: "Client", msg: "Message"):
    try:
        key0 = gen_msg_key(msg)
        if key0 in receiver:
            temp_q = receiver[key0]
            if isinstance(temp_q, asyncio.Queue):
                temp_q.put_nowait(msg.text.strip())
    except asyncio.queues.QueueFull:
        logger.error("队列已满")


async def bot_rule_action(_: 'Client', call: "CallbackQuery"):
    api_route = "/api/rule/disable?name=" if "disable" in str(call.data) else "/api/rule/enable?name="
    api_route2 = "/api/rule/enable?name=" if "disable" in str(call.data) else "/api/rule/disable?name="
    rule_name = str(call.data)[len(api_route):]
    rule_conf = config.getUserconfig().get('rule', {})
    rule = rule_conf.get(rule_name, None)
    rule['enable'] = False if "disable" in str(call.data) else True
    rule_conf[rule_name] = rule
    config.yaml['userconfig']['rule'] = rule_conf
    if config.reload():
        new_keyboard = deepcopy(call.message.reply_markup.inline_keyboard)
        status_button = new_keyboard[0][0]
        status_button.text = " ✅状态：启用" if rule.get('enable', True) else " ❌状态：禁用"
        status_button.callback_data = api_route2 + rule_name
        new_keyboard[0][0] = status_button
        await call.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))


async def bot_rule_delete(_: 'Client', call: "CallbackQuery"):
    api_route = "/api/rule/delete?name="
    rule_name = str(call.data)[len(api_route):]
    rule_conf = config.getUserconfig().get('rule', {})
    rule_conf.pop(rule_name, None)
    config.yaml['userconfig']['rule'] = rule_conf
    if config.reload():
        new_keyboard = [call.message.reply_markup.inline_keyboard[-1]]
        await call.message.edit_text(f"删除规则：**{rule_name}** 成功", reply_markup=InlineKeyboardMarkup(new_keyboard))
        await call.answer(f"删除规则：{rule_name} 成功~", show_alert=True)


async def bot_rule_page(_: 'Client', call: "CallbackQuery"):
    api_route = '/api/rule/getrule?name='
    rule_conf = config.getUserconfig().get('rule', {})
    rule_name = str(call.data[len(api_route):])
    if not isinstance(rule_conf, dict):
        logger.warning("配置文件反序列化类型错误！")
        return
    rule = rule_conf.get(rule_name, None)
    if not isinstance(rule, dict):
        logger.warning("找不到此规则")
        await call.message.reply("找不到此规则")
        return
    slaveid = rule.get('slaveid', '')
    comment = config.getSlavecomment(str(slaveid))
    sort = rule.get('sort', '')
    script = rule.get('script', [])
    text = f"🚦规则名: {rule_name}\n🤖选中后端: {comment}\n⛓️选中排序: {sort}\n🧵选中脚本: {str(script)}\n\n"
    status = " ✅状态：启用" if rule.get('enable', True) else " ❌状态：禁用"
    status_action = f"/api/rule/disable?name={rule_name}" if rule.get('enable', True) else \
        f"/api/rule/enable?name={rule_name}"
    status_button = IKB(status, status_action)
    keyboard = [
        [status_button],
        [IKB("🗑️删除此规则", f"/api/rule/delete?name={rule_name}")],
        [IKB("🔙返回上一级", "/api/rule/home"), dbtn['b_close']]
    ]
    IKM = InlineKeyboardMarkup(keyboard)
    await call.message.edit_text(text, reply_markup=IKM)


async def bot_new_rule(app: Client, call: CallbackQuery):
    caidan = "彩蛋: 试试把规则名设置成自己的userid(ง •_•)ง"
    trigger_prob = 13
    msg_text0 = "很好！请在**60s**内给规则取一个名字(直接打字发送, 不能是中文)："
    if secrets.randbelow(100) < trigger_prob:
        msg_text0 += f"\n\n{caidan}"
    msg_text = "接下来请完成后端、排序方式、测试项选择。\n提示："
    reply_markup = call.message.reply_markup if call.message.reply_markup is not None else None
    if reply_markup:
        reply_markup.inline_keyboard = [reply_markup.inline_keyboard[-1]]
    await call.message.edit_text(msg_text, reply_markup=reply_markup)
    botmsg_0 = await call.message.reply(msg_text0)
    from botmodule.cfilter import MESSAGE_LIST

    recvkey = gen_msg_key(botmsg_0, 1)
    q = asyncio.Queue(1)
    receiver[recvkey] = q
    MESSAGE_LIST.append(botmsg_0)
    try:
        async with async_timeout.timeout(60):
            rulename = await q.get()

    except asyncio.exceptions.TimeoutError:
        await botmsg_0.edit_text("⚠️获取规则名超时，取消操作")
        mdq.put(botmsg_0)
        return
    finally:
        receiver.pop(recvkey, None)
        MESSAGE_LIST.remove(botmsg_0)
    msg_text0 = f"获取到的规则名: {rulename}\n"
    await botmsg_0.edit_text(f"获取到的规则名: {rulename}\n")
    slaveid, comment = await select_slave_only(app, botmsg_0)
    if slaveid and comment:
        msg_text0 += f"已选择的后端名称: {comment}\n"
        await botmsg_0.edit_text(msg_text0)
        sort_str = await select_sort_only(app, botmsg_0, 20, speed=True)
        if sort_str:
            msg_text0 += f"已选择的排序方式: {sort_str}\n"
            await botmsg_0.edit_text(msg_text0)
            script = await select_script_only(app, botmsg_0)
            if script:
                msg_text0 += f"已选择的测试脚本: {str(script)}\n"
                await botmsg_0.edit_text(msg_text0)
                status = new_rule(rulename, slaveid, sort_str, script)
                if status:
                    await botmsg_0.reply(status, quote=True)
                await botmsg_0.reply(f"✅规则 **{rulename}**已成功写入到配置文件，"
                                     f"快去使用:\n\n `/invite {rulename}`\n\n进行测试吧~")
                mdq.put(botmsg_0)
                await call.message.delete()
                return
    await botmsg_0.edit_text(botmsg_0.text + f"\n❌选择超时，取消操作。")
