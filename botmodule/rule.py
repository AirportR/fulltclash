from typing import List

from loguru import logger
from botmodule.init_bot import config
from utils.cleaner import addon


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
        if script == "全测" or script == "all" or script == "*":
            script = addon.global_test_item(True)
        else:
            new_script = [s for s in addon.global_test_item(True) if script in s]
            script = new_script
    else:
        script = None
    return slaveid, sort, script


def new_rule(rulename: str, slaveid: str, sort: str, script: List[str]) -> str:
    """
    新增规则的接口
    """
    rule_conf = config.getUserconfig().get('rule', {})
    if isinstance(rule_conf, dict):
        if sorted(addon.global_test_item(True)) == sorted(script):
            script = "*"
        rule = {
            'enable': True,
            'slaveid': slaveid,
            'sort': sort,
            'script': script
        }
        flag = 0
        if rulename in rule_conf:
            flag = 1
        rule_conf[rulename] = rule
        if not config.getUserconfig():
            temp = {'rule': rule_conf}
            config.yaml['userconfig'] = temp
        else:
            config.yaml['userconfig']['rule'] = rule_conf
        if not config.reload():
            return "❌规则添加失败"
        if flag != 0:
            return "⚠️此规则名先前已存在，规则已被覆盖。"
        return ""
    return "❌读取配置错误"
