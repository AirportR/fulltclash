import asyncio

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from loguru import logger
import botmodule
from botmodule import init_bot
from botmodule.cfilter import dynamic_data_filter, allfilter, AccessCallback
from botmodule.command.authority import get_url_from_invite
from botmodule.command.leave import leavechat, set_anti_group
from botmodule.command.logs import export_logs
# from utils.cron.utils import message_delete_queue
# from utils.myqueue import q, bot_task_queue
from utils.myqueue import bot_put
from utils.check import check_callback_master
from utils.backend import break_speed
from utils.collector import reload_config as r1
from utils.cleaner import reload_config as r2

config = init_bot.config
admin = init_bot.admin  # 管理员
task_num = 0  # 任务数
bridge = config.config.get('userbot', {}).get('id', [])


def loader(app: Client):
    command_loader(app)
    command_loader2(app)
    callback_loader(app)


def user_loder(app: Client):
    userbotconfig = config.config.get('userbot', {})
    slaveconfig = config.getSlaveconfig()
    slaveID = [int(k) for k in slaveconfig.keys() if k != "default-slave"] if slaveconfig else []
    whitelist = userbotconfig.get('whitelist', [])

    @app.on_message(filters.user(whitelist + slaveID))
    async def _(client: Client, message: Message):
        await botmodule.simple_relay(client, message)

    @app.on_edited_message(filters.user(whitelist + slaveID))
    async def _(client: Client, message: Message):
        await botmodule.simple_relay(client, message)


def command_loader2(app: Client):
    """
    后端专属指令
    """
    masterconfig = config.getMasterconfig()
    master_bridge = [int(i.get('bridge')) for i in masterconfig.values()] if masterconfig else []
    print("userbot白名单：", master_bridge)

    @app.on_message(filters.caption & filters.document & filters.user(master_bridge), 1)
    async def put_task(client: Client, message: Message):
        logger.info("接收任务成功")
        if message.caption.startswith('/send'):
            await botmodule.recvtask(client, message)

    @app.on_message(filters.command(['sconnect']) & filters.user(admin + master_bridge), 2)
    async def resp_conn(client: Client, message: Message):
        await botmodule.simple_conn_resp(client, message)

    @app.on_message(filters.command(['sreboot']) & filters.user(admin + master_bridge), 2)
    async def _(client: Client, message: Message):
        await botmodule.restart_or_killme(client, message)

    @app.on_message(filters.command(['stopspeed']) & filters.user(admin + master_bridge), 2)
    async def _(_: Client, __: Message):
        break_speed.append(True)


def command_loader(app: Client):
    @app.on_message(filters.command(["testurl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def testurl(client: Client, message: Message):
        # await botmodule.select_slave_page(client, message, page=1)
        await botmodule.task_handler(client, message, page=1)

    @app.on_message(filters.command(["test"]) & allfilter(1), group=1)
    @AccessCallback()
    async def test(client: Client, message: Message):
        await botmodule.task_handler(client, message, page=1)
        # await botmodule.select_slave_page(client, message, page=1)

    @app.on_message(filters.command(["invite"]), group=1)
    @AccessCallback()
    async def invite(client, message):
        await botmodule.task_handler(client, message, page=1)
        # await botmodule.select_slave_page(client, message, page=1)

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
        # await botmodule.select_slave_page(client, message, page=1)
        await botmodule.task_handler(client, message, page=1)

    @app.on_message(filters.command(["analyze", "topo"]) & allfilter(1), group=1)
    @AccessCallback()
    async def analyze(client, message):
        # await botmodule.select_slave_page(client, message, page=1)
        await botmodule.task_handler(client, message, page=1)

    @app.on_message(filters.command(["reload"]) & allfilter(2), group=2)
    async def reload_testmember(_, message):
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]) & allfilter(1), group=1)
    @AccessCallback()
    async def regis(client, message):
        await botmodule.register.baipiao(client, message)

    # @app.on_message(filters.command(["inbound"]) & allfilter(1), group=1)
    # @AccessCallback()
    # async def inbound(client, message):
    #     await bot_put(client, message, "inbound", test_type='inbound')
    #
    # @app.on_message(filters.command(["inboundurl"]) & allfilter(1), group=1)
    # @AccessCallback()
    # async def inboundurl(client, message):
    #     await bot_put(client, message, "inboundurl", test_type='inbound')
    #
    # @app.on_message(filters.command(["outbound"]) & allfilter(1), group=1)
    # @AccessCallback()
    # async def outbound(client, message):
    #     await bot_put(client, message, "outbound", test_type='outbound')
    #
    # @app.on_message(filters.command(["outboundurl"]) & allfilter(1), group=1)
    # @AccessCallback()
    # async def outboundurl(client, message):
    #     await bot_put(client, message, "outboundurl", test_type='outbound')

    @app.on_message(filters.command(["speed"]) & allfilter(1), group=1)
    @AccessCallback()
    async def speed(client, message):
        await botmodule.task_handler(client, message, page=1)
        # await botmodule.select_slave_page(client, message, page=1)

    @app.on_message(filters.command(["speedurl"]) & allfilter(1), group=1)
    @AccessCallback()
    async def speedurl(client, message):
        await botmodule.task_handler(client, message, page=1)
        # await botmodule.select_slave_page(client, message, page=1)

    @app.on_message(filters.command(["subinfo", "traffic", "流量", "流量信息", "流量查询"]), group=0)
    async def subinfo(client, message):
        await botmodule.subinfo.getSubInfo(client, message)

    @app.on_message(filters.command(["start"]), group=0)
    async def start(client, message):
        await botmodule.invite_pass2(client, message)

    @app.on_message(filters.private, group=3)
    @AccessCallback(1)
    async def temp(client, message):
        await get_url_from_invite(client, message)

    @app.on_message(filters.command(config.getBotconfig().get('command', [])), group=3)
    @AccessCallback(1)
    async def common_command(client: Client, message: Message):
        await botmodule.common_command(client, message)

    @app.on_message(filters.command(["share"]), group=1)
    @AccessCallback()
    async def share(client, message):
        await botmodule.sub_invite(client, message)

    @app.on_message(filters.command(['rule']) & allfilter(1), group=1)
    async def _(_: Client, message: Message):
        await message.reply("🚧开发中~🚧")

    @app.on_message(filters.command(['install', 'list']) & allfilter(2), group=2)
    async def install_script(client, message):
        await botmodule.download_script(client, message)

    @app.on_message(filters.command(['uninstall']) & allfilter(2), group=2)
    async def uninstall_script(client, message):
        await botmodule.uninstall_script(client, message)

    @app.on_message(filters.command(['setting']) & allfilter(2), group=2)
    async def setting(client, message):
        await botmodule.setting_page(client, message)

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

    @app.on_message(filters.command(['logs']) & allfilter(2), group=2)
    async def _(client, message):
        await export_logs(client, message)

    @app.on_message(filters.command(['edit']) & filters.user(bridge), group=2)
    async def _(client: Client, message: Message):
        await botmodule.edit(client, message)

    @app.on_message(filters.caption & filters.document & filters.user(bridge))
    async def task_result(client: Client, message: Message):
        if message.caption.startswith('/result'):
            await botmodule.task_result(client, message)

    @app.on_message(filters.command(["setantigroup"]) & allfilter(2), group=2)
    async def setantigroup(client, message):
        await set_anti_group(client, message)

    @app.on_message(filters.new_chat_members)
    async def auto_leave(client, message):
        await leavechat(client, message)


def callback_loader(app: Client):
    @app.on_callback_query(filters=dynamic_data_filter('stop') & filters.user(botmodule.init_bot.reloadUser()), group=1)
    async def invite_test(client: Client, callback_query: CallbackQuery):
        await botmodule.stopspeed(client, callback_query)

    @app.on_callback_query(filters=dynamic_data_filter('reload:addon') & filters.user(init_bot.admin), group=1)
    async def reload_addon(client, callback_query):
        await botmodule.reload_addon_from_telegram(client, call=callback_query)
        callback_query.stop_propagation()

    @app.on_callback_query(filters.user(init_bot.admin), group=1)
    async def bot_setting(client, callback_query: CallbackQuery):
        if callback_query.data.startswith('cpage'):
            await botmodule.select_config_page(client, callback_query, page=int(callback_query.data[5:]), column=2)
            return
        # elif callback_query.data.startswith('config'):
        #     await botmodule.setting_config(client, callback_query, column=2)
        #     return
        elif callback_query.data == 'setconfig':
            await botmodule.select_config_page(client, callback_query, page=1, column=2)
            return

    @app.on_callback_query(group=2)
    async def settings_test(client, callback_query: CallbackQuery):
        if callback_query.data == "blank":
            return
        if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
            return
        elif callback_query.data == "close":
            await callback_query.message.delete()
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
        # logger.info(str(test_items))
        if message:
            sort_str = botmodule.get_sort_str(message)
            slaveid = botmodule.get_slave_id(message)
            await asyncio.sleep(2)
            await message.delete()
            await bot_put(client, origin_message, test_type, test_items, sort=sort_str, coreindex=3, slaveid=slaveid)
