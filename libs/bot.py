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


def command_loader(app: Client):
    @app.on_message(filters.command(["testurl"]))
    async def testurl(_, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await message.reply("请选择想要启用的测试项:", reply_markup=botmodule.IKM, quote=True)

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
    async def test(_, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await message.reply("请选择想要启用的测试项:", reply_markup=botmodule.IKM, quote=True)
            # await bot_put(client, message, "test")

    @app.on_message(filters.command(["help", "start"]), group=9)
    async def help_and_start(client, message):
        await botmodule.helps(client, message)

    @app.on_message(filters.command(["version"]), group=9)
    async def print_version(client, message):
        await botmodule.version(client, message)

    @app.on_message(filters.command(["analyzeurl", "topourl"]), group=10)
    async def analyzeurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "analyzeurl")

    @app.on_message(filters.command(["analyze", "topo"]), group=11)
    async def analyze(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "analyze")

    @app.on_message(filters.command(["reload"]) & filters.user(admin), group=12)
    async def reload_testmember(_, message):
        botmodule.reloadUser()
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]), group=13)
    async def regis(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
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

    @app.on_message(filters.command(["speed"]), group=16)
    async def speed(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "speed")

    @app.on_message(filters.command(["speedurl"]), group=17)
    async def speedurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "speedurl")

    @app.on_message(filters.command(["subinfo", "traffic", "流量", "流量信息", "流量查询"]), group=18)
    async def subinfo(client, message):
        await botmodule.subinfo.getSubInfo(client, message)

    @app.on_message(filters.command(["map"]) & filters.user(admin), group=19)
    async def debug(client, message):
        await botmodule.di.debug_interface(client, message)

    @app.on_message(filters.command(["delay"]), group=20)
    async def delay(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "delay")

def callback_loader(app: Client):
    @app.on_callback_query()
    async def settings_test(client, callback_query):
        if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
            return
        test_items, origin_message, message, test_type = await botmodule.test_setting(client, callback_query)
        if message:
            await asyncio.sleep(3)
            await message.delete()
            await bot_put(client, origin_message, test_type, test_items)


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
    try:
        if test_items is None:
            test_items = []
        logger.info("任务测试项为: " + str(test_items))
        mes = await message.reply("排队中,前方队列任务数量为: " + str(task_num - 1))
        await q.put(message)
        r1(test_items)
        r2(test_items)
        await mes.edit_text("任务已提交")
        await bot_task_queue(client, message, put_type, q)
        task_num -= 1
        await asyncio.sleep(10)
        await mes.delete()
    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))
