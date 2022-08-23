from pyrogram import Client, filters

import botmodule
from botmodule import init_bot

admin = init_bot.admin  # 管理员


def loader(app: Client):
    @app.on_message(filters.command(["testurl"]))
    async def testurl(client, message):
        await botmodule.testurl(client, message)

    @app.on_message(filters.command(["testurlold"]))
    async def testurl_old(client, message):
        await botmodule.testurl_old(client, message)

    @app.on_message(filters.command(["invite"]) & filters.user(admin), group=1)
    async def invite(client, message):
        await botmodule.invite(client, message)

    @app.on_message(filters.command(["grant"]), group=2)
    async def grant(client, message):
        await botmodule.grant(client, message)

    @app.on_message(filters.command(["ungrant"]), group=3)
    async def ungrant(client, message):
        await botmodule.ungrant(client, message)

    @app.on_message(filters.command(["user"]), group=4)
    async def user(client, message):
        await botmodule.user(client, message)

    @app.on_message(filters.command(["new"]) & filters.user(admin), group=5)
    async def new(client, message):
        await botmodule.new(client, message)

    @app.on_message(filters.command(["remove"]) & filters.user(admin), group=6)
    async def remove(client, message):
        await botmodule.remove(client, message)

    @app.on_message(filters.command(["sub"]) & filters.user(admin), group=7)
    async def sub(client, message):
        await botmodule.sub(client, message)

    @app.on_message(filters.command(["test"]), group=8)
    async def test(client, message):
        await botmodule.test(client, message)

    @app.on_message(filters.command(["testold"]), group=8)
    async def test_old(client, message):
        await botmodule.test_old(client, message)

    @app.on_message(filters.command(["help", "start"]), group=9)
    async def help_and_start(client, message):
        await botmodule.helps(client, message)

    @app.on_message(filters.command(["analyzeurl"]), group=10)
    async def analyzeurl(client, message):
        await botmodule.analyzeurl(client, message)

    @app.on_message(filters.command(["analyze"]), group=11)
    async def analyze(client, message):
        await botmodule.analyze(client, message)

    @app.on_message(filters.command(["reload"]) & filters.user(admin), group=12)
    async def reload_testmember(client, message):
        from libs.collector import reload_config as r1
        from libs.cleaner import reload_config as r2
        botmodule.reload_test_members()
        botmodule.reloadUser()
        r1()
        r2()
        await message.reply("已重载配置")

