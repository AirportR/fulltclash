from pyrogram.errors import RPCError
from botmodule.init_bot import admin, config
from botmodule.command import testurl


async def grant(client, message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    try:
        grant_text = "该成员已被加入到授权目标"

        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            await client.send_message(chat_id=message.chat.id,
                                      text=grant_text,
                                      reply_to_message_id=message.reply_to_message.id)
            try:
                grant_id = int(message.reply_to_message.from_user.id)
            except AttributeError:
                grant_id = int(message.reply_to_message.sender_chat.id)
            print("授权id:", grant_id)
            config.add_user(grant_id)
            config.reload()
            testurl.reloadUser()

    except RPCError as r:
        print(r)


async def ungrant(client, message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    try:
        ungrant_text = "该成员已被移出授权目标"
        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            try:
                ungrant_id = int(message.reply_to_message.from_user.id)
            except AttributeError:
                ungrant_id = int(message.reply_to_message.sender_chat.id)
            try:
                config.del_user(ungrant_id)
                config.reload()
                testurl.reloadUser()
                await client.send_message(chat_id=message.chat.id,
                                          text=ungrant_text,
                                          reply_to_message_id=message.reply_to_message.id)
            except RPCError:
                await client.send_message(chat_id=message.chat.id,
                                          text="移出失败，找不到该用户(也许该目标本来就不是授权目标哦)",
                                          reply_to_message_id=message.reply_to_message.id)

    except RPCError as r:
        print(r)


async def user(client, message):
    try:
        if int(message.from_user.id) not in admin and str(
                message.from_user.username) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in admin:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您不是bot的管理员，无法使用该命令")
            return
    USER_TARGET = config.getuser()
    text = "当前用户有:" + str(set(USER_TARGET)) + "\n共{}个".format(len(USER_TARGET))
    await message.reply(text)