from pyrogram import Client
from pyrogram.types import Message

from loguru import logger
from botmodule.init_bot import config, admin
from utils.check import get_id
from utils.cleaner import ArgCleaner, addon


def get_rule(userid: str):
    """
    返回配置里的规则，选择什么后端，什么测试项，排序方法
    return [slaveid, sort, script]
    """
    if not userid:
        raise ValueError("userid不能为空字符串")
    subuconf = config.getUserconfig().get('rule', {}).get(userid, {})
    if not subuconf:
        if userid == "default":
            return None, None, addon.global_test_item(httptest=True)
        logger.warning(f"找不到 {userid} 规则")
    if not subuconf.get('enable', False):
        if userid == "default":
            return None, None, addon.global_test_item(httptest=True)
        return None, None, None
    slaveid = subuconf.get('slaveid', 'local')
    sort = subuconf.get('sort', '订阅原序')
    script = subuconf.get('script', None)
    if isinstance(script, list):
        script = addon.mix_script(script)
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

