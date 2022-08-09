from pyrogram import Client, filters

import botModule.command.testurl
import botModule.command.grant
from botModule.command import authority
from botModule.command import basic
import botModule.command.basic
import botModule.command.submanage
import botModule.init_bot


config = botModule.init_bot.config
USER_TARGET = botModule.init_bot.USER_TARGET  # 这是用户列表，从配置文件读取
clash_path = botModule.init_bot.clash_path  # 为clash核心运行路径, Windows系统需要加后缀名.exe
clash_work_path = botModule.init_bot.clash_work_path  # clash工作路径
admin = botModule.init_bot.admin  # 管理员
test_members = 0  # 正在测试的成员，如果为零则停止测试，否则一直测试


def loader(app: Client):
    @app.on_message(filters.command(["testurl"]))
    async def testurl(client, message):
        await botModule.command.testurl.testurl(client, message)

    @app.on_message(filters.command(["invite"]) & filters.user(admin), group=1)
    async def invite(client, message):
        await authority.invite(client, message)

    @app.on_message(filters.command(["grant"]), group=2)
    async def grant(client, message):
        await botModule.command.grant.grant(client, message)

    @app.on_message(filters.command(["ungrant"]), group=3)
    async def ungrant(client, message):
        await botModule.command.grant.ungrant(client, message)

    @app.on_message(filters.command(["user"]), group=4)
    async def user(client, message):
        await botModule.command.grant.user(client, message)

    @app.on_message(filters.command(["new"]) & filters.user(admin), group=5)
    async def new(client, message):
        await botModule.command.submanage.new(client, message)

    @app.on_message(filters.command(["remove"]) & filters.user(admin), group=6)
    async def remove(client, message):
        await botModule.command.submanage.remove(client, message)

    @app.on_message(filters.command(["sub"]) & filters.user(admin), group=7)
    async def sub(client, message):
        await botModule.command.submanage.sub(client, message)

    @app.on_message(filters.command(["test"]), group=8)
    async def test(client, message):
        await botModule.command.testurl.test(client, message)

    @app.on_message(filters.command(["help", "start"]), group=9)
    async def help_and_start(client, message):
        await basic.helps(client, message)



