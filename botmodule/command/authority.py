import asyncio
from contextlib import suppress
import string
import secrets
from dataclasses import dataclass
from typing import List

from async_timeout import timeout
from loguru import logger
from pyrogram.errors import RPCError
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from utils.check import get_telegram_id_from_message as get_id
from utils.cleaner import geturl, addon, ArgCleaner
from botmodule.command.test import convert_core_index

b1 = InlineKeyboardMarkup(
    [
        [  # 第一行
            InlineKeyboardButton("📺 联通性测试", callback_data='test', url='')
        ],
        [  # 第二行
            InlineKeyboardButton("🔗 链路拓扑测试", callback_data='analyze')
        ],
        [
            InlineKeyboardButton("🚗 速度测试", callback_data='speed')
        ]

    ]
)
invite_list = {}  # 被邀请人ID列表
message_list = {}  # 原消息
bot_message_list = {}  # bot回复消息
success_message_list = {}
INVITE_CACHE = {}  # {"<ID>:<key>": msg1} 被邀请人原消息
BOT_MESSAGE_CACHE = {}
INVITE_SELECT_CACHE = {
    # 所有的记录都以 "{chat_id}:{message_id}"作为键
    'script': {},  # 脚本选择
    'sort': {},  # 记录排序选择
    'slaveid': {},  # 记录后端id选择
}
task_type = ['testurl', 'analyzeurl', 'speedurl']
temp_queue = asyncio.Queue(maxsize=1)


def generate_random_string(length: int):
    # 生成随机字符串
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join(secrets.choice(letters_and_digits) for _ in range(length))
    return result_str


async def invite(client: Client, message):
    bot_info = await client.get_me()
    text = str(message.text)
    texts = text.split(' ')
    del texts[0]

    try:
        username = bot_info.username
    except AttributeError as a:
        logger.error(str(a))
        username = ''
    inline_keyboard = b1.inline_keyboard
    key = generate_random_string(8)
    if username:
        num_row = 0
        for row in inline_keyboard:
            for buttun in row:
                buttun.callback_data = None

                if texts:
                    url_text = f"https://t.me/{username}?start={key}_{task_type[num_row]}"
                    for t in texts:
                        url_text = url_text + "_" + t
                else:
                    url_text = f"https://t.me/{username}?start={key}_{task_type[num_row]}_default"

                buttun.url = url_text
            num_row = num_row + 1
    try:
        sender = message.from_user.first_name
    except AttributeError:
        sender = message.sender_chat.title
    invite_text = f"🎯您好, **{sender}** 为您创建了一个测试任务，请选择测试的类型:"
    try:
        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            r_message = message.reply_to_message
            invite_id = str(get_id(r_message))
            logger.info("被邀请人id: " + invite_id)
            invite_list.update({key: invite_id})
            message_list.update({key + invite_id: r_message})
            IKM2 = InlineKeyboardMarkup(
                inline_keyboard
            )
            m2 = await client.send_message(chat_id=message.chat.id,
                                           text=invite_text,
                                           reply_to_message_id=message.reply_to_message.id,
                                           reply_markup=IKM2)
            bot_message_list.update({key + invite_id: m2})

    except RPCError as r:
        print(r)


async def get_url_from_invite(_, message2):
    ID = str(get_id(message2))
    suc_mes = success_message_list.get(ID, None)
    if suc_mes is not None:
        # success_message_list.pop(ID, None)
        if message2.id == (suc_mes.id + 1):
            include_text = ''
            exclude_text = ''
            text_li = str(message2.text)
            texts_li = text_li.split(' ')
            if len(texts_li) > 1:
                include_text = texts_li[1]
            if len(texts_li) > 2:
                exclude_text = texts_li[2]
            url_li = geturl(text_li)
            if url_li:
                await temp_queue.put((url_li, include_text, exclude_text))
            else:
                await message2.reply("无效的URL")


async def invite_pass(client: Client, message: Message):
    # temp_queue = asyncio.Queue(maxsize=1)
    ID = str(get_id(message))
    text = str(message.text)
    timeout_value = 60
    if 'testurl' in text or 'analyzeurl' in text or 'speedurl' in text:
        texts = text.split(' ')
        pre_key = texts[1] if len(texts) > 1 else ''
        if not pre_key:
            return
        k = pre_key.split('_')
        key2 = k[0] if k else ''
        A_ID = invite_list.get(key2, '')
        if key2 not in invite_list or A_ID != ID:
            await message.reply("ID验证失败，请不要乱用别人的测试哦！")
            return
        task_type_select = k[1] if len(k) > 1 else ''
        test_type_select = ['HTTP(S)延迟']
        if len(k) > 2:
            if k[2] == 'default':
                test_type_select += addon.global_test_item()
            else:
                for i in k[2:]:
                    if i == 'HTTP(S)延迟':
                        continue
                    test_type_select.append(i)

        if task_type_select in task_type:

            s_text = f"✅身份验证成功\n🚗任务项: {task_type_select} \n\n**接下来请在{timeout_value}s内发送订阅链接** <过滤器> 否则任务取消"
            success_mes = await message.reply(s_text)
            success_message_list.update({ID: success_mes})
            mes = message_list.pop(key2 + ID, None)
            if mes is None:
                return
            bot_mes = bot_message_list.pop(key2 + ID, None)
            if bot_mes:
                await bot_mes.edit_text(f"✅身份验证成功\n🚗任务项: {task_type_select}\n\n⏳正在等待上传订阅链接~~~")
            suburl = ''
            in_text = ''
            ex_text = ''
            try:
                async with timeout(timeout_value):
                    suburl, in_text, ex_text = await temp_queue.get()
            except asyncio.TimeoutError:
                logger.info(f"验证过期: {key2}:{ID}")
                await bot_mes.edit_text("❌任务已取消\n\n原因: 接收订阅链接超时")
            if suburl:
                from utils.bot import bot_put
                await message.reply("✨提交成功，请返回群组查看测试结果。")
                await asyncio.sleep(3)
                await bot_mes.delete()
                test_item = test_type_select
                await bot_put(client, mes, task_type_select, test_items=test_item,
                              include_text=in_text, exclude_text=ex_text, url=suburl)
            else:
                invite_list.pop(key2, '')
        else:
            s_text = "❌未知任务类型，请重试"
            await message.reply(s_text)
            return


async def invite_pass2(client: Client, message: Message):
    tgargs = ArgCleaner.getarg(message.text)
    start_uid = str(get_id(message))
    timeout_value = 60
    # https://t.me/AirportRoster_bot?start=8GImRgzY_testurl_default /start sE8ic4MA_testurl_default
    parsertext = tgargs[1] if len(tgargs) > 1 else ''
    if not parsertext:
        await message.reply("输入 /help 查看使用说明。")
        return
    subtext = ArgCleaner.getarg(parsertext, '_')
    if len(subtext) < 3:
        logger.info(f"参数不全: {tgargs}")
    if subtext[1] not in task_type:
        logger.info("未找到测试类型，取消验证")
        return
    key = f"{start_uid}:{subtext[0]}"
    if key not in INVITE_CACHE:
        await message.reply("❌ID验证失败，请不要乱用别人的测试哦！")
        return

    # 验证成功
    s_text = f"✅身份验证成功\n🚗任务项: {subtext[1]} \n\n**接下来请在{timeout_value}s内发送订阅链接** <过滤器> \n否则任务取消"
    success_mes = await message.reply(s_text)
    success_message_list[start_uid] = success_mes
    mes = INVITE_CACHE.pop(key, None)
    if mes is None:
        return

    # bot_mes = bot_message_list.pop(key2 + ID, None)
    bot_mes = BOT_MESSAGE_CACHE.pop(subtext[0], None)
    if bot_mes is None:
        logger.warning("未找到bot消息")
        return
    await bot_mes.edit_text(f"✅身份验证成功\n🚗任务项: {subtext[1]}\n\n⏳正在等待上传订阅链接~~~")
    suburl = ''
    in_text = ''
    ex_text = ''
    slaveid, sort_str, test_items = get_invite_item(parsertext)
    if sort_str is None:
        sort_str = INVITE_SELECT_CACHE['sort'].pop(str(mes.chat.id) + ":" + str(mes.id), "订阅原序")
    if slaveid is None:
        slaveid = INVITE_SELECT_CACHE['slaveid'].pop(str(mes.chat.id) + ":" + str(mes.id), "local")
    coreindex = convert_core_index(subtext[1])
    if not coreindex:
        logger.info("未知的测试类型，任务取消")
        return
    try:
        async with timeout(timeout_value):
            suburl, in_text, ex_text = await temp_queue.get()
    except asyncio.TimeoutError:
        logger.info(f"验证过期: {key}")
        await bot_mes.edit_text("❌任务已取消\n\n原因: 接收订阅链接超时")
    if suburl:
        from utils.bot import bot_put
        await message.reply("✨提交成功，请返回群组查看测试结果。")
        await asyncio.sleep(3)
        await bot_mes.delete()
        # await bot_put(app, originmsg, put_type, None, sort=sort_str, coreindex=1, slaveid=slaveid)
        print(f"invite提交的任务项: {subtext[1]}\n测试项:{test_items}\n过滤器: {in_text}<->{ex_text}\n排序: {sort_str}\n"
              f"coreindex: {coreindex}\n后端id: {slaveid}")
        await bot_put(client, mes, subtext[1], test_items=test_items,
                      include_text=in_text, exclude_text=ex_text, url=suburl,
                      sort=sort_str, coreindex=coreindex, slaveid=slaveid)
    else:
        INVITE_CACHE.pop(key, '')
    success_message_list.pop(start_uid, None)


def get_invite_item(text: str):
    """
    获取邀请测试里面的参数，然后得到测试项的值,[slaveid,sort,script]。
    """
    subtext = ArgCleaner.getarg(text, '_')
    if len(subtext) < 3:
        return None
    if subtext[2]:
        from botmodule.rule import get_rule
        slaveid, sort, script = get_rule(subtext[2])
        if slaveid is None:
            slaveid = 'local'
        if sort is None:
            sort = '订阅原序'
        # script 允许为None
        return slaveid, sort, script

    return None, None, None


@dataclass
class Invite:
    username: str = ''
    key: str = generate_random_string(8)

    def set_username(self, username: str):
        self.username = username

    def gen_keyboard(self, additional_option: List):
        if not self.username:
            raise ValueError("无法找到BOT的用户名，邀请测试无法进行。")
        inline_keyboard = b1.inline_keyboard
        if len(inline_keyboard) > len(task_type):
            raise ValueError("无法填充更多的的测试按钮。")
        for n, row in enumerate(inline_keyboard):
            for buttun in row:
                buttun.callback_data = None

                if additional_option:
                    url_text = f"https://t.me/{self.username}?start={self.key}_{task_type[n]}"
                    for t in additional_option:
                        url_text = url_text + "_" + t
                else:
                    url_text = f"https://t.me/{self.username}?start={self.key}_{task_type[n]}_default"

                buttun.url = url_text
        return inline_keyboard

    async def invite(self, app: Client, message: Message):
        # 获取bot的用户名
        bot_info = await app.get_me()

        with suppress(AttributeError):
            username = bot_info.username
            self.set_username(username)
        # 获取invite的发起者名称
        try:
            sender = message.from_user.first_name
        except AttributeError:
            sender = message.sender_chat.title
        invite_text = f"🎯您好, **{sender}** 为您创建了一个测试任务，请选择测试的类型:"
        texts = message.text.split(" ")
        del texts[0]

        if username:
            inline_keyboard = self.gen_keyboard(texts)
            IKM2 = InlineKeyboardMarkup(inline_keyboard)
            target = message if message.reply_to_message is None else message.reply_to_message
            target_id = str(get_id(target))
            logger.info(f"被邀请人id: {target_id}")
            try:
                cache_key = target_id + ":" + self.key
                INVITE_CACHE[cache_key] = target
                bot_mes = BOT_MESSAGE_CACHE.get(self.key, None)
                if bot_mes is None:
                    await target.reply("⚠️bot消息已被删除，任务取消", quote=True)
                    return
                invite_text = bot_mes.text + "\n\n" + invite_text
                await bot_mes.edit_text(invite_text, reply_markup=IKM2)

            except RPCError as r:
                print(r)
