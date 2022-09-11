import asyncio
from pyrogram import Client, filters
from loguru import logger
import botmodule
from botmodule import init_bot
from libs.myqueue import q, bot_task_queue
from libs.check import check_user as isuser
from libs.check import check_callback_master
from libs.collector import reload_config as r1
from libs.cleaner import reload_config as r2

admin = init_bot.admin  # 管理员
task_num = 0  # 任务数


def loader(app: Client):
    command_loader(app)
    callback_loader(app)


async def bot_put(client, message, put_type: str, test_items: list = None):
    """
    推送任务，bot推送反馈
    :param test_items:
    :param client:
    :param message:
    :param put_type:
    :return:
    """
    global task_num
    task_num += 1
    mes = await message.reply("排队中,前方队列任务数量为: " + str(task_num - 1))
    await q.put(message)
    if test_items:
        logger.info("任务测试项为: " + str(test_items))
        r1(test_items)
        r2(test_items)
    await asyncio.sleep(2)
    await mes.edit_text("任务已提交")
    await bot_task_queue(client, message, put_type, q)
    task_num -= 1
    await asyncio.sleep(10)
    await mes.delete()


def command_loader(app: Client):
    @app.on_message(filters.command(["testurl"]))
    async def testurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await message.reply("请选择想要启用的测试项:", reply_markup=botmodule.IKM, quote=True)

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
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await message.reply("请选择想要启用的测试项:", reply_markup=botmodule.IKM, quote=True)
            # await bot_put(client, message, "test")

    @app.on_message(filters.command(["testold"]), group=8)
    async def test_old(client, message):
        await botmodule.test_old(client, message)

    @app.on_message(filters.command(["help", "start"]), group=9)
    async def help_and_start(client, message):
        await botmodule.helps(client, message)

    @app.on_message(filters.command(["analyzeurl", "topourl"]), group=10)
    async def analyzeurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "analyzeurl")

    @app.on_message(filters.command(["analyze", "topo"]), group=11)
    async def analyze(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "analyze")

    @app.on_message(filters.command(["reload"]) & filters.user(admin), group=12)
    async def reload_testmember(client, message):
        botmodule.reload_test_members()
        botmodule.reloadUser()
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]), group=13)
    async def regis(client, message):
        await botmodule.register.baipiao(client, message)

    @app.on_message(filters.command(["inbound"]), group=14)
    async def inbound(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.analyze(client, message, test_type="inbound")

    @app.on_message(filters.command(["inboundurl"]), group=15)
    async def inboundurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.analyzeurl(client, message, test_type="inbound")

    @app.on_message(filters.command(["outbound"]), group=14)
    async def outbound(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "outbound")

    @app.on_message(filters.command(["outboundurl"]), group=15)
    async def outboundurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "outboundurl")


def callback_loader(app: Client):
    @app.on_callback_query()
    async def settings_test(client, callback_query):
        if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
            return
        test_items, origin_message, message, test_type = await botmodule.test_setting(client, callback_query)
        if message:
            await asyncio.sleep(5)
            await message.delete()
            await bot_put(client, origin_message, test_type, test_items)
