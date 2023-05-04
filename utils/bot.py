import asyncio

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from loguru import logger
import botmodule
from botmodule import init_bot
from botmodule.cfilter import dynamic_data_filter, allfilter, AccessCallback
from botmodule.command.authority import get_url_from_invite
from botmodule.command.leave import leavechat, set_anti_group
from utils.cron.utils import message_delete_queue
# from utils.myqueue import q, bot_task_queue
from utils.myqueue import bot_put
from utils.check import check_callback_master
from utils.backend import break_speed
from utils.collector import reload_config as r1
from utils.cleaner import reload_config as r2

config = init_bot.config
admin = init_bot.admin  # 管理员
task_num = 0  # 任务数
bridge = config.getBridge()


def loader(app: Client):
    command_loader(app)
    command_loader2(app)
    callback_loader(app)


def user_loder(app: Client):
    userbotconfig = config.config.get('userbot', {})
    slaveconfig = config.getSlaveconfig()
    slaveID = [int(k) for k in slaveconfig.keys()] if slaveconfig else []
    whitelist = userbotconfig.get('whitelist', [])

    @app.on_message(filters.user(whitelist + slaveID))
    async def _(client: Client, message: Message):
        await botmodule.simple_relay(client, message)

    @app.on_edited_message(filters.user(whitelist + slaveID))
    async def _(client: Client, message: Message):
        await botmodule.simple_relay(client, message)

    # @app.on_message(filters.user(whitelist))
    # async def relay(client: Client, message: Message):
    #     if str(message.text).startswith('/relay1'):
    #         await botmodule.relay(client, message)
    #         message.stop_propagation()
    #
    # @app.on_message(filters.user(whitelist) & filters.document & filters.caption, 2)
    # async def relay2(client: Client, message: Message):
    #     await botmodule.relay2(client, message)
    #
    # @app.on_message(filters.bot & filters.caption, 1)
    # async def resp1(client: Client, message: Message):
    #     if str(message.caption) == "/resp" and message.document:
    #         await botmodule.response(client, message)
    #         message.stop_propagation()
    #
    # @app.on_message(filters.user(slaveID) & filters.caption, 2)
    # async def resp2(client: Client, message: Message):
    #     if str(message.caption).startswith("/resp2") and message.document:
    #         await botmodule.response2(client, message)
    #         message.stop_propagation()


def command_loader2(app: Client):
    """
    后端专属指令
    """
    masterconfig = config.getMasterconfig()
    master_bridge = [int(i.get('bridge')) for i in masterconfig.values()] if masterconfig else []
    print(master_bridge)

    @app.on_message(filters.caption & filters.document & filters.user(master_bridge))
    async def put_task(client: Client, message: Message):
        if message.caption.startswith('/send'):
            await botmodule.recvtask(client, message)

    # @app.on_message(filters.user(master_bridge))
    # async def simple_resp(client: Client, message: Message):
    #     print("")

    @app.on_message(filters.command(['sconnect']) & filters.user(admin + master_bridge), 2)
    async def resp_conn(client: Client, message: Message):
        await botmodule.simple_conn_resp(client, message)

    # @app.on_message(filters.command(['sconnect']) & filters.user(admin))
    # async def resp_conn(client: Client, message: Message):
    #     await botmodule.conn_resp(client, message)
    #
    # @app.on_message(filters.command(['sconnect2']))
    # async def resp_conn(client: Client, message: Message):
    #     await botmodule.conn_resp2(client, message)
    #


def command_loader(app: Client):
    @app.on_message(filters.command(["testurl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def testurl(_, message):
        await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)

    @app.on_message(filters.command(["test"]) & allfilter(1), group=1)
    @AccessCallback()
    async def test(client: Client, message: Message):
        await botmodule.select_slave_page(client, message, page=1)
        # await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)

    @app.on_message(filters.command(["invite"]), group=1)
    @AccessCallback()
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
    @AccessCallback()
    async def new(client, message):
        await botmodule.new(client, message)

    @app.on_message(filters.command(["remove"]), group=1)
    @AccessCallback()
    async def remove(client, message):
        await botmodule.remove(client, message)

    @app.on_message(filters.command(["sub"]), group=1)
    @AccessCallback()
    async def sub(client, message):
        await botmodule.sub(client, message)

    @app.on_message(filters.command(["help"]), group=0)
    async def help_and_start(client, message):
        await botmodule.helps(client, message)

    @app.on_message(filters.command(["version"]), group=0)
    async def print_version(client, message):
        await botmodule.version(client, message)

    @app.on_message(filters.command(["analyzeurl", "topourl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def analyzeurl(client, message):
        await bot_put(client, message, "analyzeurl")

    @app.on_message(filters.command(["analyze", "topo"]) & allfilter(1), group=1)
    @AccessCallback()
    async def analyze(client, message):
        await bot_put(client, message, "analyze")

    @app.on_message(filters.command(["reload"]) & allfilter(2), group=2)
    async def reload_testmember(_, message):
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]) & allfilter(1), group=1)
    @AccessCallback()
    async def regis(client, message):
        await botmodule.register.baipiao(client, message)

    @app.on_message(filters.command(["inbound"]) & allfilter(1), group=1)
    @AccessCallback()
    async def inbound(client, message):
        await bot_put(client, message, "inbound", test_type='inbound')

    @app.on_message(filters.command(["inboundurl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def inboundurl(client, message):
        await bot_put(client, message, "inboundurl", test_type='inbound')

    @app.on_message(filters.command(["outbound"]) & allfilter(1), group=1)
    @AccessCallback()
    async def outbound(client, message):
        await bot_put(client, message, "outbound", test_type='outbound')

    @app.on_message(filters.command(["outboundurl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def outboundurl(client, message):
        await bot_put(client, message, "outboundurl", test_type='outbound')

    @app.on_message(filters.command(["speed"]) & allfilter(1), group=1)
    @AccessCallback()
    async def speed(client, message):
        await bot_put(client, message, "speed")

    @app.on_message(filters.command(["speedurl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def speedurl(client, message):
        await bot_put(client, message, "speedurl")

    @app.on_message(filters.command(["subinfo", "traffic", "流量", "流量信息", "流量查询"]), group=0)
    async def subinfo(client, message):
        await botmodule.subinfo.getSubInfo(client, message)

    @app.on_message(filters.command(["start"]), group=0)
    async def start(client, message):
        await botmodule.invite_pass(client, message)

    @app.on_message(filters.private, group=3)
    @AccessCallback(1)
    async def temp(client, message):
        await get_url_from_invite(client, message)

    @app.on_message(filters.command(config.config.get('bot', {}).get('command', [])), group=3)
    @AccessCallback(1)
    async def common_command(client: Client, message: Message):
        await botmodule.common_command(client, message)

    @app.on_message(filters.command(["share"]), group=1)
    @AccessCallback()
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
    @AccessCallback()
    async def fulltest(client, message):
        await message.reply("请选择排序方式:", reply_markup=botmodule.IKM2, quote=True)
        await bot_put(client, message, "analyze", coreindex=2)
        await bot_put(client, message, "speed", coreindex=1)

    @app.on_message(filters.command(['restart', 'reboot']) & allfilter(2), group=2)
    async def restart(client, message):
        await botmodule.restart_or_killme(client, message)

    @app.on_message(filters.command(['clash']) & allfilter(2), group=2)
    async def clash(client, message):
        await botmodule.startclash(client, message)

    @app.on_message(filters.command(['exit', 'killme']) & allfilter(2), group=2)
    async def killme(client, message):
        await botmodule.restart_or_killme(client, message, kill=True)

    @app.on_message(filters.command(['connect']) & allfilter(2), group=2)
    async def conn(client, message):
        await botmodule.conn_simple(client, message)

    @app.on_message(filters.command(['edit']) & filters.user(bridge), group=2)
    async def _(client: Client, message: Message):
        await botmodule.edit(client, message)

    @app.on_message(filters.command('resp'), group=0)
    async def resp(client, message):
        await botmodule.response(client, message)
        message.stop_propagation()

    @app.on_message(filters.command(["setantigroup"]) & allfilter(2), group=2)
    async def setantigroup(client, message):
        await set_anti_group(client, message)

    @app.on_message(filters.new_chat_members)
    @AccessCallback(1)
    async def auto_leave(client, message):
        await leavechat(client, message)


def callback_loader(app: Client):
    @app.on_callback_query(filters=dynamic_data_filter('stop') & filters.user(botmodule.init_bot.reloadUser()), group=1)
    async def invite_test(_, callback_query: CallbackQuery):
        break_speed.append(True)
        logger.info("测速中止")
        backmsg = await callback_query.message.edit_text("❌测速任务已取消")
        message_delete_queue.put_nowait((backmsg.chat.id, backmsg.id, 10))
        callback_query.stop_propagation()

    @app.on_callback_query(filters=dynamic_data_filter('reload:addon') & filters.user(init_bot.admin), group=1)
    async def reload_addon(client, callback_query):
        await botmodule.reload_addon_from_telegram(client, call=callback_query)
        callback_query.stop_propagation()

    @app.on_callback_query(group=2)
    async def settings_test(client, callback_query: CallbackQuery):
        if callback_query.data == "blank":
            return
        if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
            return
        elif callback_query.data.startswith('page'):
            await botmodule.select_page(client, callback_query, page=int(str(callback_query.data)[4:]))
            return
        elif callback_query.data.startswith('spage'):
            await botmodule.select_slave_page(client, callback_query, page=int(callback_query.data[5:]))
            return
        elif callback_query.data.startswith('slave'):
            await botmodule.select_slave(client, callback_query)
            return
        elif "sort" in callback_query.data:
            await botmodule.select_sort(client, callback_query)
            return
        test_items, origin_message, message, test_type = await botmodule.test_setting(client, callback_query)
        if message:
            sort_str = botmodule.get_sort_str(message)
            slaveid = botmodule.get_slave_id(message.chat.id, message.id)
            await asyncio.sleep(2)
            await message.delete()
            await bot_put(client, origin_message, test_type, test_items, sort=sort_str, coreindex=3, slaveid=slaveid)

# async def bot_put(client: Client, message: Message, put_type: str, test_items: list = None, **kwargs):
#     """
#     推送任务，bot推送反馈
#     :param test_items:
#     :param client:
#     :param message:
#     :param put_type:
#     :return:
#     """
#     global task_num
#     task_num += 1
#     try:
#         if test_items is None:
#             test_items = []
#         logger.info("任务测试项为: " + str(test_items))
#         mes = await message.reply("排队中,前方队列任务数量为: " + str(task_num - 1))
#         await q.put(message)
#         r1(test_items)
#         r2(test_items)
#         await mes.delete()
#         await bot_task_queue(client, message, put_type, q, **kwargs)
#         task_num -= 1
#
#     except AttributeError as a:
#         logger.error(str(a))
#     except Exception as e:
#         logger.error(str(e))
