from pyrogram.errors import RPCError

# 如果是在国内环境，则需要代理环境以供程序连接上TG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

b1 = InlineKeyboardMarkup(
    [
        [  # 第一行
            InlineKeyboardButton(  # Generates a callback query when pressed
                "📺 流媒体测试 📺", callback_data='✅Netflix'
            )

        ],
        [  # 第二行
            InlineKeyboardButton(  # Generates a callback query when pressed
                "🔗 链路拓扑测试 🔗(未开放)", callback_data='2'
            )

        ]

    ]
)


async def invite(client, message):
    invite_text = f"🎯您好, {message.from_user.first_name} 为您创建了一个测试任务，请选择测试的类型:"
    try:
        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            await client.send_message(chat_id=message.chat.id,
                                      text=invite_text,
                                      reply_to_message_id=message.reply_to_message.id,
                                      reply_markup=b1)
    except RPCError as r:
        print(r)



