import asyncio
from pyrogram import Client, filters
from loguru import logger
import botmodule
from botmodule import init_bot
from botmodule.cfilter import dynamic_data_filter
from botmodule.command.authority import get_url_from_invite
from libs.myqueue import q, bot_task_queue
from libs.check import check_user as isuser
from libs.check import check_callback_master
from libs.collector import reload_config as r1
from libs.cleaner import reload_config as r2
from libs.speedtest import break_speed

admin = init_bot.admin  # 管理员
task_num = 0  # 任务数


def loader(app: Client):
    command_loader(app)
    callback_loader(app)


def command_loader(app: Client):
    @app.on_message(filters.command(["testurl"]), group=1)
    async def testurl(_, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)

    @app.on_message(filters.command(["test"]), group=1)
    async def test(_, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)

    @app.on_message(filters.command(["invite"]), group=1)
    async def invite(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.invite(client, message)

    @app.on_message(filters.command(["grant"]), group=2)
    async def grant(client, message):
        await botmodule.grant(client, message)

    @app.on_message(filters.command(["ungrant"]), group=2)
    async def ungrant(client, message):
        await botmodule.ungrant(client, message)

    @app.on_message(filters.command(["user"]) & filters.user(admin), group=2)
    async def user(client, message):
        await botmodule.user(client, message)

    @app.on_message(filters.command(["new"]), group=1)
    async def new(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.new(client, message)

    @app.on_message(filters.command(["remove"]), group=1)
    async def remove(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.remove(client, message)

    @app.on_message(filters.command(["sub"]), group=1)
    async def sub(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.sub(client, message)

    @app.on_message(filters.command(["help"]), group=0)
    async def help_and_start(client, message):
        await botmodule.helps(client, message)

    @app.on_message(filters.command(["version"]), group=0)
    async def print_version(client, message):
        await botmodule.version(client, message)

    @app.on_message(filters.command(["analyzeurl", "topourl"]), group=1)
    async def analyzeurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "analyzeurl")

    @app.on_message(filters.command(["analyze", "topo"]), group=1)
    async def analyze(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "analyze")

    @app.on_message(filters.command(["reload"]) & filters.user(admin), group=2)
    async def reload_testmember(_, message):
        botmodule.reloadUser()
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]), group=1)
    async def regis(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.register.baipiao(client, message)

    @app.on_message(filters.command(["inbound"]), group=1)
    async def inbound(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.analyze(client, message, test_type="inbound")

    @app.on_message(filters.command(["inboundurl"]), group=1)
    async def inboundurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.analyzeurl(client, message, test_type="inbound")

    @app.on_message(filters.command(["outbound"]), group=1)
    async def outbound(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "outbound")

    @app.on_message(filters.command(["outboundurl"]), group=1)
    async def outboundurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "outboundurl")

    @app.on_message(filters.command(["speed"]), group=1)
    async def speed(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "speed")

    @app.on_message(filters.command(["speedurl"]), group=1)
    async def speedurl(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await bot_put(client, message, "speedurl")

    @app.on_message(filters.command(["subinfo", "traffic", "流量", "流量信息", "流量查询"]), group=0)
    async def subinfo(client, message):
        await botmodule.subinfo.getSubInfo(client, message)

    @app.on_message(filters.command(["map"]) & filters.user(admin), group=2)
    async def debug(client, message):
        await botmodule.di.debug_interface(client, message)

    @app.on_message(filters.command(["start"]), group=0)
    async def start(client, message):
        await botmodule.invite_pass(client, message)

    @app.on_message(filters.private, group=3)
    async def temp(client, message):
        await get_url_from_invite(client, message)

    @app.on_message(filters.command(["share"]), group=1)
    async def share(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.sub_invite(client, message)

    @app.on_message(filters.command(['install', 'list']) & filters.user(admin), group=2)
    async def install_script(client, message):
        await botmodule.download_script(client, message)

    @app.on_message(filters.command(['uninstall']) & filters.user(admin), group=2)
    async def uninstall_script(client, message):
        await botmodule.uninstall_script(client, message)

    @app.on_message(filters.command(['setting']) & filters.user(admin), group=2)
    async def setting(client, message):
        await botmodule.setting_page(client, message)


def callback_loader(app: Client):
    @app.on_callback_query(filters=dynamic_data_filter('stop') & filters.user(botmodule.init_bot.reloadUser()), group=1)
    async def invite_test(_, callback_query):
        break_speed.append(True)
        logger.info("测速中止")
        callback_query.stop_propagation()

    @app.on_callback_query(filters=dynamic_data_filter('reload:addon') & filters.user(init_bot.admin), group=1)
    async def reload_addon(client, callback_query):
        await botmodule.reload_addon_from_telegram(client, call=callback_query)
        callback_query.stop_propagation()

# TODO(@AirportR): 鉴权可以融合到filter里面
    @app.on_callback_query(group=2)
    async def settings_test(client, callback_query):
        if callback_query.data == "blank":
            return
        if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
            return
        elif "page" in callback_query.data:
            await botmodule.select_page(client, callback_query, page=int(str(callback_query.data)[4:]))
            return
        elif "sort" in callback_query.data:
            await botmodule.select_sort(client, callback_query)
            return
        test_items, origin_message, message, test_type = await botmodule.test_setting(client, callback_query)
        if message:
            sort_str = botmodule.get_sort_str(message)
            await asyncio.sleep(3)
            await message.delete()
            await bot_put(client, origin_message, test_type, test_items, sort=sort_str)


async def bot_put(client, message, put_type: str, test_items: list = None, **kwargs):
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
        await asyncio.sleep(3)
        await bot_task_queue(client, message, put_type, q, **kwargs)
        await mes.delete()
        task_num -= 1

    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))
