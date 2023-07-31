from pyrogram import Client
from pyrogram.types import Message

from loguru import logger
from botmodule.init_bot import config, admin
from utils.check import get_id
from utils.cleaner import ArgCleaner, addon


def get_rule(rulename: str):
    """
    返回配置里的规则，选择什么后端，什么测试项，排序方法
    return [slaveid, sort, script]
    """
    if not rulename:
        raise ValueError("规则不能为空字符串")
    subuconf = config.getUserconfig().get('rule', {}).get(rulename, {})
    if not subuconf:
        if rulename == "default":
            return None, None, addon.global_test_item(httptest=True)
        logger.warning(f"找不到 {rulename} 规则")
    if not subuconf.get('enable', False):
        if rulename == "default":
            return None, None, addon.global_test_item(httptest=True)
        return None, None, None
    slaveid = subuconf.get('slaveid', 'local')
    sort = subuconf.get('sort', '订阅原序')
    script = subuconf.get('script', None)
    if isinstance(script, list):
        script = addon.mix_script(script)
    elif isinstance(script, str):
        if script == "全测" or script == "all":
            script = addon.global_test_item(True)
    else:
        script = None
    return slaveid, sort, script


async def bot_rule(_: "Client", message: "Message"):
    """
    bot前端部分
    """
    ID = get_id(message)
    username = None
    tgargs = ArgCleaner.getarg(message.text)
    if message.from_user:
        username = message.from_user.username
    if ID in admin or username in admin:
        # 说明是管理员
        pass
