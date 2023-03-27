import asyncio
from pyrogram import Client, filters
from loguru import logger
import botmodule
from botmodule import init_bot
from botmodule.cfilter import dynamic_data_filter, allfilter, reloaduser
from botmodule.command.authority import get_url_from_invite
from botmodule.utils import message_delete_queue
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


config = init_bot.config


def command_loader(app: Client):
    @app.on_message(filters.command(["testurl"]) & allfilter(1), group=1)
    @reloaduser()
    async def testurl(_, message):
        await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)

    @app.on_message(filters.command(["test"]) & allfilter(1), group=1)
    @reloaduser()
    async def test(_, message):
        if not config.get_sub(subname=message.command[1]):
            back_message = await message.reply("❌找不到该任务名称，请检查参数是否正确 (TEST DELETE MESSAGE)")
            message_delete_queue.put_nowait([message.chat.id, message.id, 10])
            message_delete_queue.put_nowait([back_message.chat.id, back_message.id, 10])
            return
        await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)

    @app.on_message(filters.command(["invite"]), group=1)
    @reloaduser()
    async def invite(client, message):
        await botmodule.invite(client, message)

    @app.on_message(filters.command(["grant"]) & allfilter(2), group=2)
    async def grant(client, message):
        await botmodule.grant(client, message)

    @app.on_message(filters.command(["ungrant"]) & allfilter(2), group=2)
    async def ungrant(client, message):
        await botmodule.ungrant(client, message)

    @app.on_message(filters.command(["user"]) & allfilter(2), group=2)
    async def user(client, message):
        await botmodule.user(client, message)

    @app.on_message(filters.command(["new"]) & allfilter(1), group=1)
    @reloaduser()
    async def new(client, message):
        await botmodule.new(client, message)

    @app.on_message(filters.command(["remove"]), group=1)
    @reloaduser()
    async def remove(client, message):
        if await isuser(message, botmodule.init_bot.reloadUser()):
            await botmodule.remove(client, message)

    @app.on_message(filters.command(["sub"]), group=1)
    @reloaduser()
    async def sub(client, message):
        await botmodule.sub(client, message)

    @app.on_message(filters.command(["help"]), group=0)
    async def help_and_start(client, message):
        await botmodule.helps(client, message)

    @app.on_message(filters.command(["version"]), group=0)
    async def print_version(client, message):
        await botmodule.version(client, message)

    @app.on_message(filters.command(["analyzeurl", "topourl"]) & allfilter(1), group=1)
    @reloaduser()
    async def analyzeurl(client, message):
        await bot_put(client, message, "analyzeurl")

    @app.on_message(filters.command(["analyze", "topo"]) & allfilter(1), group=1)
    @reloaduser()
    async def analyze(client, message):
        await bot_put(client, message, "analyze")

    @app.on_message(filters.command(["reload"]) & allfilter(2), group=2)
    async def reload_testmember(_, message):
        botmodule.reloadUser()
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]) & allfilter(1), group=1)
    @reloaduser()
    async def regis(client, message):
        await botmodule.register.baipiao(client, message)

    @app.on_message(filters.command(["inbound"]) & allfilter(1), group=1)
    @reloaduser()
    async def inbound(client, message):
        await botmodule.analyze(client, message, test_type="inbound")

    @app.on_message(filters.command(["inboundurl"]) & allfilter(1), group=1)
    @reloaduser()
    async def inboundurl(client, message):
        await botmodule.analyzeurl(client, message, test_type="inbound")

    @app.on_message(filters.command(["outbound"]) & allfilter(1), group=1)
    @reloaduser()
    async def outbound(client, message):
        await bot_put(client, message, "outbound")

    @app.on_message(filters.command(["outboundurl"]) & allfilter(1), group=1)
    @reloaduser()
    async def outboundurl(client, message):
        await bot_put(client, message, "outboundurl")

    @app.on_message(filters.command(["speed"]) & allfilter(1), group=1)
    @reloaduser()
    async def speed(client, message):
        await bot_put(client, message, "speed")

    @app.on_message(filters.command(["speedurl"]) & allfilter(1), group=1)
    @reloaduser()
    async def speedurl(client, message):
        await bot_put(client, message, "speedurl")

    @app.on_message(filters.command(["subinfo", "traffic", "流量", "流量信息", "流量查询"]), group=0)
    async def subinfo(client, message):
        await botmodule.subinfo.getSubInfo(client, message)

    @app.on_message(filters.command(["map"]) & allfilter(2), group=2)
    async def debug(client, message):
        await botmodule.di.debug_interface(client, message)

    @app.on_message(filters.command(["start"]), group=0)
    async def start(client, message):
        await botmodule.invite_pass(client, message)

    @app.on_message(filters.private, group=3)
    async def temp(client, message):
        await get_url_from_invite(client, message)

    @app.on_message(filters.command(["share"]), group=1)
    @reloaduser()
    async def share(client, message):
        await botmodule.sub_invite(client, message)

    @app.on_message(filters.command(['install', 'list']) & allfilter(2), group=2)
    async def install_script(client, message):
        await botmodule.download_script(client, message)

    @app.on_message(filters.command(['uninstall']) & allfilter(2), group=2)
    async def uninstall_script(client, message):
        await botmodule.uninstall_script(client, message)

    @app.on_message(filters.command(['setting']) & allfilter(2), group=2)
    async def setting(client, message):
        await botmodule.setting_page(client, message)

    @app.on_message(filters.command(['fulltest']), group=1)
    @reloaduser()
    async def fulltest(client, message):
        await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)
        await bot_put(client, message, "analyze")
        await bot_put(client, message, "speed")

    @app.on_message(filters.command(['restart', 'reboot']) & allfilter(2), group=2)
    async def restart(client, message):
        await botmodule.restart(client, message)

    @app.on_message(filters.command(['connect']) & allfilter(2), group=2)
    async def conn(client, message):
        await botmodule.conn(client, message)

    @app.on_message(filters.command('resp'), group=0)
    async def resp(client, message):
        await botmodule.response(client, message)
        message.stop_propagation()


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
        message_delete_queue.put_nowait((mes.chat.id, mes.id, 5))
        await asyncio.sleep(3)
        await bot_task_queue(client, message, put_type, q, **kwargs)
        task_num -= 1

    except AttributeError as a:
        logger.error(str(a))
    except Exception as e:
        logger.error(str(e))
