from typing import Union

from pyrogram.types import Message
from botmodule.init_bot import config
from utils.check import get_telegram_id_from_message as getID

MEM_RANKING = {}


def init_memory_ranking():
    global MEM_RANKING
    MEM_RANKING = config.get_slave_ranking()


def get_slave_ranking(ID: Union[str, int]):
    return MEM_RANKING.get(ID, {})


def update_ranking(ID: Union[str, int], slaveid: Union[str, int], value: int):
    userconf = config.getUserconfig()
    usage_ranking = userconf.get('usage-ranking', {})
    if not isinstance(usage_ranking, dict):
        usage_ranking = {}
    user_ranking = usage_ranking.get(ID, {})
    if not isinstance(user_ranking, dict):
        return {}
    user_ranking[slaveid] = value
    usage_ranking[ID] = user_ranking
    config.yaml['userconfig']['usage-ranking'] = usage_ranking
    config.reload()


def record_ranking(message: "Message", slaveid: Union[str, int]):
    ID = getID(message)
    if ID not in MEM_RANKING:
        MEM_RANKING[ID] = {}
        MEM_RANKING[ID][slaveid] = 0
    try:
        num = int(MEM_RANKING.get(ID, {}).get(slaveid, 0))
    except (ValueError, TypeError):
        num = 0
    num += 1
    MEM_RANKING[ID][slaveid] = num

    if num and (num % 5 == 0 or num == 1):
        update_ranking(ID, slaveid, num)
