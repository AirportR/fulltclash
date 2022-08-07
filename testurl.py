import asyncio
import subprocess
import sys
import time

from pyrogram import Client, filters
from pyrogram.errors import RPCError, FloodWait
from botModule.command import base_command
import cleaner
import streamingtest
from cleaner import ConfigManager

config = ConfigManager()
USER_TARGET = config.getuser()  # 这是用户列表，从配置文件读取
clash_path = config.get_clash_path()  # 为clash核心运行路径, Windows系统需要加后缀名.exe
clash_work_path = config.get_clash_work_path()  # clash工作路径
admin = list(config.getAdmin())  # 管理员
print("管理员名单加载:", admin)
# 你的机器人的用户名
USERNAME = "@AirportRoster_bot"
port = config.get_proxy_port()
# 如果是在国内环境，则需要代理环境以供程序连接上TG
proxies = {
    "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
    "hostname": "127.0.0.1",
    "port": port
}
# 如果找不到管理员，程序会被强制退出。
if admin is None:
    print("获取管理员失败，将在5s后退出")
    time.sleep(5)
    sys.exit(1)

# 你需要一个TG的session后缀文件，以下是session文件的名字，应形如 my_bot.session 为后缀。这个文件小心保管，不要泄露。
if port:
    app = Client("my_bot", proxy=proxies)
else:
    app = Client("my_bot")
print("配置已加载")
print("程序已启动!")

# 启动了一个clash常驻进程
command = fr"{clash_path} -f {'./clash/proxy.yaml'} -d {clash_work_path}"
subp = subprocess.Popen(command.split(), encoding="utf-8")
time.sleep(2)
test_members = 0  # 正在测试的成员，如果为零则停止测试，否则一直测试


@app.on_message(filters.command(["testurl"]))
async def mytest(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    if "/testurl" in message.text or "/testurl" + USERNAME in message.text:
        back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...")  # 发送提示
        start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
        test_members += 1
        ma = cleaner.ConfigManager('./clash/proxy.yaml')
        try:
            await streamingtest.testurl(client, message, back_message=back_message, test_members=test_members,
                                        start_time=start_time)
            test_members -= 1
            ma.delsub(subname=start_time)
            ma.save(savePath='./clash/proxy.yaml')
        except RPCError as r:
            print(r)
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=back_message.id,
                text="出错啦"
            )
        except FloodWait as e:
            test_members -= 1
            await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
        except KeyboardInterrupt:
            await back_message.edit_text("程序已被强行中止")


from botModule.command import authority


@app.on_message(filters.command(["invite"]) & filters.user(admin), group=1)
async def invite(client, message):
    await authority.invite(client, message)


@app.on_message(filters.command(["grant"]), group=2)
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
        co = ConfigManager()

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
            co.add_user(grant_id)
            co.save()
            USER_TARGET.append(grant_id)

    except RPCError as r:
        print(r)


@app.on_message(filters.command(["ungrant"]), group=3)
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
        co = ConfigManager()
        ungrant_text = "该成员已被移出授权目标"
        if message.reply_to_message is None:
            await message.reply("请先用该指令回复一个目标")
        else:
            try:
                ungrant_id = int(message.reply_to_message.from_user.id)
            except AttributeError:
                ungrant_id = int(message.reply_to_message.sender_chat.id)
            try:
                co.del_user(ungrant_id)
                co.save()
                USER_TARGET.remove(ungrant_id)
                await client.send_message(chat_id=message.chat.id,
                                          text=ungrant_text,
                                          reply_to_message_id=message.reply_to_message.id)
            except RPCError:
                await client.send_message(chat_id=message.chat.id,
                                          text="移出失败，找不到该用户(也许该目标本来就不是授权目标哦)",
                                          reply_to_message_id=message.reply_to_message.id)

    except RPCError as r:
        print(r)


@app.on_message(filters.command(["user"]), group=4)
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
    text = "当前用户有:" + str(set(USER_TARGET)) + "\n共{}个".format(len(USER_TARGET))
    await message.reply(text)


@app.on_message(filters.command(["new"]) & filters.user(admin), group=5)
async def new(client, message):
    arg = str(message.text).strip().split(' ')
    c = 0
    while len(arg) > c:
        if arg[c] == '':
            del arg[c]
        else:
            c += 1
    if len(arg) < 3:
        await message.reply("请输入正确的格式，如： /new <订阅地址> <订阅名称>")
        return
    else:
        try:
            suburl = arg[1]
            subname = arg[2]
            subinfo = {subname: suburl}
            print(suburl, subname)
            config.newsub(subinfo)
            config.reload()
            await message.reply('新增了一个订阅: ' + subname)
        except IndexError:
            print("错误")


@app.on_message(filters.command(["remove"]) & filters.user(admin), group=6)
async def remove(client, message):
    arg = str(message.text).strip().split(' ')
    c = 0
    while len(arg) > c:
        if arg[c] == '':
            del arg[c]
        else:
            c += 1
    arg.remove('/remove')
    try:
        for i in arg:
            config.removesub(i)
            config.reload()
        try:
            await message.reply('移除了{}个订阅: '.format(len(arg)) + str(arg))
        except RPCError as r:
            print(r)
    except IndexError:
        print("错误")


@app.on_message(filters.command(["sub"]) & filters.user(admin), group=7)
async def sub(client, message):
    subinfo = config.get_sub()
    try:
        await message.reply(str(subinfo))
    except RPCError as r:
        print(r)


@app.on_message(filters.command(["test"]))
async def test(client, message):
    global USER_TARGET, test_members
    try:
        if int(message.from_user.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    except AttributeError:
        if int(message.sender_chat.id) not in USER_TARGET:  # 如果不在USER_TARGET名单是不会有权限的
            await message.reply("⚠️您似乎没有使用权限，请联系bot的管理员获取授权")
            return
    back_message = await message.reply("╰(*°▽°*)╯流媒体测试进行中...")  # 发送提示
    arg = str(message.text).strip().split(' ')
    c = 0
    while len(arg) > c:
        if arg[c] == '':
            del arg[c]
        else:
            c += 1
    del arg[0]
    suburl = ''
    if len(arg):
        suburl = config.get_sub(subname=arg[0])
    else:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    if suburl is None:
        await back_message.edit_text("❌发生错误，请检查订阅文件")
        return
    start_time = time.strftime("%Y-%m-%dT%H-%M-%S", time.localtime())
    test_members += 1
    ma = cleaner.ConfigManager('./clash/proxy.yaml')
    try:
        await streamingtest.testurl(client, message, back_message=back_message, test_members=test_members,
                                    start_time=start_time, suburl=suburl)
        test_members -= 1
        ma.delsub(subname=start_time)
        ma.save(savePath='./clash/proxy.yaml')
    except RPCError as r:
        print(r)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=back_message.id,
            text="出错啦"
        )
    except FloodWait as e:
        test_members -= 1
        await asyncio.sleep(e.value)  # Wait "value" seconds before continuing
    except KeyboardInterrupt:
        await back_message.edit_text("程序已被强行中止")


@app.on_message(filters.command(["help", "start"]))
async def help_and_start(client, message):
    await base_command.helps(client, message)


app.run()
