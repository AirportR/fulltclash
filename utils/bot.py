from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message
from loguru import logger

import botmodule
from botmodule import init_bot
from botmodule.cfilter import dynamic_data_filter as dyn_flt, pre_filter, AccessCallback, prefix_filter, next_filter, \
    exclude_text_filter as ex_flt, sub_filter
from botmodule.command.authority import get_url_from_invite
from botmodule.command.leave import leavechat, set_anti_group
from botmodule.command.logs import export_logs
from utils.myqueue import bot_put
from utils.check import check_callback_master
from utils.backend import break_speed
from utils.collector import reload_config as r1
from utils.cleaner import reload_config as r2

config = init_bot.config
admin = init_bot.admin  # 管理员
bridge = config.config.get('userbot', {}).get('id', [])
common_cmd = config.getBotconfig().get('command', [])


def loader(app: Client):
    command_loader(app)
    command_loader2(app)
    callback_loader(app)


def user_loder(app: Client):
    userbotconfig = config.config.get('userbot', {})
    slaveconfig = config.getSlaveconfig()
    slaveID = []
    for k in slaveconfig.keys():
        try:
            _k = int(k)
            slaveID.append(_k)
        except (ValueError, TypeError):
            pass
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
    try:
        master_bridge = [int(i.get('bridge')) for i in masterconfig.values()] if masterconfig else []
    except Exception as e:
        logger.info(str(e))
        master_bridge = []

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
    task_list = ["test", "testurl", "analyze", "topo", "analyzeurl", "topourl", "speed", "speedurl", "invite"]

    @app.on_message(filters.command(task_list) & pre_filter(1) & sub_filter(), group=1)
    @AccessCallback()
    async def task(client: Client, message: Message):
        await botmodule.task_handler(client, message, page=1)

    @app.on_message(filters.command(["grant"]) & pre_filter(2), group=2)
    async def grant(client, message):
        await botmodule.grant(client, message)

    @app.on_message(filters.command(["ungrant"]) & pre_filter(2), group=2)
    async def ungrant(client, message):
        await botmodule.ungrant(client, message)

    @app.on_message(filters.command(["user"]) & pre_filter(2), group=2)
    async def user(client, message):
        await botmodule.user(client, message)

    @app.on_message(filters.command(["new"]) & pre_filter(1), group=1)
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

    @app.on_message(filters.command(["reload"]) & pre_filter(2), group=2)
    async def reload_test_items(_, message):
        r1()
        r2()
        await message.reply("已重载配置")

    @app.on_message(filters.command(["register", "baipiao"]) & pre_filter(1), group=1)
    @AccessCallback()
    async def regis(client, message):
        await botmodule.register.baipiao(client, message)

    @app.on_message(filters.command(["subinfo", "traffic", "流量", "流量信息", "流量查询"]), group=0)
    async def subinfo(client, message):
        await botmodule.subinfo.getSubInfo(client, message)

    @app.on_message(filters.command(["start"]), group=0)
    async def start(client, message):
        await botmodule.invite_pass(client, message)

    @app.on_message(next_filter() & filters.private, group=-1)
    async def _(client: Client, message: Message):
        await botmodule.recv_data(client, message)

    @app.on_message(filters.private, group=3)
    @AccessCallback(1)
    async def temp(client, message):
        await get_url_from_invite(client, message)

    @app.on_message(filters.command(common_cmd) & filters.group, group=3)
    @AccessCallback(1)
    async def common_command(client: Client, message: Message):
        await botmodule.common_command(client, message)

    @app.on_message(filters.command(["share"]), group=1)
    @AccessCallback()
    async def share(client, message):
        await botmodule.sub_invite(client, message)

    @app.on_message(filters.command(['rule']) & pre_filter(1), group=1)
    async def _(_: Client, message: Message):
        await message.reply("🚧开发中~🚧")

    @app.on_message(filters.command(['install']) & pre_filter(2), group=2)
    async def install_script(client, message):
        await botmodule.download_script(client, message)

    @app.on_message(filters.command(['uninstall']) & pre_filter(2), group=2)
    async def uninstall_script(client, message):
        await botmodule.uninstall_script(client, message)

    @app.on_message(filters.command(['setting']) & pre_filter(2), group=2)
    async def setting(client, message):
        await botmodule.home_setting(client, message)

    @app.on_message(filters.command(['restart', 'reboot']) & pre_filter(2), group=2)
    async def restart(client, message):
        await botmodule.restart_or_killme(client, message)

    @app.on_message(filters.command(['exit', 'killme']) & pre_filter(2), group=2)
    async def killme(client, message):
        await botmodule.restart_or_killme(client, message, kill=True)

    @app.on_message(filters.command(['connect']) & pre_filter(2), group=2)
    async def conn(client, message):
        await botmodule.conn_simple(client, message)

    @app.on_message(filters.command(['logs']) & pre_filter(2), group=2)
    async def _(client, message):
        await export_logs(client, message)

    @app.on_message(filters.command(['edit']) & filters.user(bridge), group=2)
    async def _(client: Client, message: Message):
        await botmodule.edit(client, message)

    @app.on_message(filters.caption & filters.document & filters.user(bridge))
    async def task_result(client: Client, message: Message):
        if message.caption.startswith('/result'):
            await botmodule.task_result(client, message)

    @app.on_message(filters.command(["setantigroup"]) & pre_filter(2), group=2)
    async def setantigroup(client, message):
        await set_anti_group(client, message)

    @app.on_message(filters.new_chat_members)
    async def auto_leave(client, message):
        await leavechat(client, message)


def callback_loader(app: Client):
    @app.on_callback_query(prefix_filter("/api/rule/disable") | prefix_filter("/api/rule/enable"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.bot_rule_action(client, call)

    @app.on_callback_query(prefix_filter("/api/rule/delete"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.bot_rule_delete(client, call)

    @app.on_callback_query(prefix_filter("/api/rule/getrule"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.bot_rule_page(client, call)

    @app.on_callback_query(prefix_filter("/api/setting/home"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.home_setting(client, call)

    @app.on_callback_query(prefix_filter("/api/rule/page/") | dyn_flt("/api/rule/home"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.home_rule(client, call)

    @app.on_callback_query(prefix_filter("/api/slave/page/"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.select_slave_only_1(client, call)

    @app.on_callback_query(prefix_filter("/api/sort/"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.select_sort_only(client, call)

    @app.on_callback_query(prefix_filter("/api/getSlaveId"))
    async def _(client: Client, call: CallbackQuery):
        await botmodule.select_slave_only(client, call)

    @app.on_callback_query(dyn_flt("/api/script/ok"))
    async def _(client: Client, call: CallbackQuery):
        await botmodule.select_script_only(client, call)

    @app.on_callback_query(dyn_flt("/api/rule/new"), 1)
    async def _(client: Client, call: CallbackQuery):
        await botmodule.bot_new_rule(client, call)

    @app.on_callback_query(filters=dyn_flt('stop') & filters.user(botmodule.init_bot.reloadUser()), group=1)
    async def invite_test(client: Client, callback_query: CallbackQuery):
        await botmodule.stopspeed(client, callback_query)

    @app.on_callback_query(filters=dyn_flt('reload:addon') & filters.user(init_bot.admin), group=1)
    async def reload_addon(client, callback_query):
        await botmodule.reload_addon_from_telegram(client, call=callback_query)
        callback_query.stop_propagation()

    @app.on_callback_query(filters.user(init_bot.admin) & (prefix_filter("/api/config/page/") |
                                                           dyn_flt("/api/config/home")), group=1)
    async def bot_setting(client, callback_query: CallbackQuery):
        await botmodule.select_config_page(client, callback_query, column=2)

    @app.on_callback_query(filters=ex_flt(["blank"]), group=2)
    async def settings_test(client, callback_query: CallbackQuery):
        if callback_query.data == "close":
            await callback_query.message.delete()
            return

        elif callback_query.data.startswith('page'):
            if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
                return
            await botmodule.select_page(client, callback_query, page=int(str(callback_query.data)[4:]))
            return
        elif callback_query.data.startswith('spage'):
            if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
                return
            await botmodule.select_slave_page(client, callback_query, page=int(callback_query.data[5:]))
            return
        elif callback_query.data.startswith('slave'):
            if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
                return
            await botmodule.select_slave(client, callback_query)
            return
        elif callback_query.data.startswith('sort:'):
            if await check_callback_master(callback_query, botmodule.init_bot.reloadUser()):
                return
            await botmodule.select_sort(client, callback_query)
            return

        # 注意以下代码为历史遗留问题，可能会让人迷惑
        test_items, origin_message, message, test_type = await botmodule.test_setting(client, callback_query)
        # logger.info(str(test_items))
        if message:
            sort_str = botmodule.get_sort_str(message)
            slaveid = botmodule.get_slave_id(message)
            await message.delete()
            await bot_put(client, origin_message, test_type, test_items, sort=sort_str, coreindex=3, slaveid=slaveid)
