import asyncio
import random
import string
import pyrogram
from async_timeout import timeout
from loguru import logger
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from botmodule.command.submanage import get_telegram_id_from_message as get_id
from libs.cleaner import geturl

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
invite_list = {}
message_list = {}
bot_message_list = {}
success_message_list = {}
task_type = ['testurl', 'analyzeurl', 'speedurl']
temp_queue = asyncio.Queue(maxsize=1)


def generate_random_string(length: int):
    # 生成随机字符串
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for _ in range(length)))
    return result_str


async def invite(client: pyrogram.Client, message):
    bot_info = await client.get_me()
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
                buttun.url = f"https://t.me/{username}?start={key}_{task_type[num_row]}"
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
            success_message_list.pop(ID, None)


async def invite_pass(client: pyrogram.Client, message):
    # temp_queue = asyncio.Queue(maxsize=1)
    ID = str(get_id(message))
    text = str(message.text)
    timeout_value = 20
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
                print(f"验证过期: {key2}:{ID}")
                await bot_mes.edit_text(f"❌任务已取消\n\n原因: 接收订阅链接超时")
                await asyncio.sleep(10)
                await bot_mes.delete()
            if suburl:
                from libs.bot import bot_put
                await message.reply("✨提交成功，请返回群组查看测试结果。")
                await asyncio.sleep(3)
                await bot_mes.delete()
                test_item = ['HTTP延迟', 'Netflix', 'Youtube', 'Disney+', 'Primevideo', 'steam货币', 'Bilibili', 'Dazn',
                             'Hbomax', 'Bahamut', 'Abema', '公主连结', 'BBC', 'Myvideo', 'Catchplay', 'Viu', '维基百科',
                             '维基百科(中文)', 'Hulu JP', '赛马娘', '落地IP风险']
                await bot_put(client, mes, task_type_select, test_items=test_item,
                              include_text=in_text, exclude_text=ex_text, url=suburl)
            else:
                invite_list.pop(key2, '')
        else:
            s_text = "❌未知任务类型，请重试"
            await message.reply(s_text)
            return
