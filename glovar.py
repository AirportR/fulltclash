import time

import tzlocal
from pyrogram import Client
from loguru import logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils import cron_delete_message as cdm
from utils import cron_edit_message as cem

# from utils import cron_websocket_task as cwt

program_run_time = time.time()

# 项目版本号
__version__ = '3.6.0'

# scheduler.add_job(cwt, IntervalTrigger(seconds=10, timezone=str(tzlocal.get_localzone())), max_instances=10,
#                   id='ws1', name="Websocket Task", args=())

print("""# --------------------------- [ Start bot AsyncIOScheduler Successful ] ---------------------------- # """)


# ---------------------------- [ Print the bot ] ---------------------------- #
# def bot_info(_app, _app2):
#     bot_me = _app.get_me()
#     logger.info('>> Bot Started')
#     logger.info(f'>> Bot ID: {bot_me.id} Username: @{bot_me.username}')
#     if _app2 is not None:
#         bot_me2 = _app2.get_me()
#         whitelist = userbot_config.get('whitelist', [])
#         userbot_config['id'] = bot_me2.id
#         if bot_me.id not in whitelist:
#             whitelist.append(bot_me.id)
#         userbot_config['whitelist'] = whitelist
#         bot_config.yaml['userbot'] = userbot_config
#         bot_config.reload()
#         logger.info('>> UserBot enable')
#         logger.info(f'>> UserBot ID: {bot_me2.id} Username: @{bot_me2.username}')
#
#     print("""# ---------------------------- [ Start the bot ] ---------------------------- #   """)
#     print("""# ---------------------------- [ Check Bot Successful ] ---------------------------- #   """)
